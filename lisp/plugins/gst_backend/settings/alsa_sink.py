# This file is part of Linux Show Player
#
# Copyright 2021 Francesco Ceruti <ceppofrancy@gmail.com>
#
# Linux Show Player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linux Show Player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linux Show Player.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGroupBox,
    QComboBox,
    QLabel,
    QVBoxLayout,
    QPushButton
)
from pyalsa import alsacard

from lisp.plugins.gst_backend import GstBackend
from lisp.plugins.gst_backend.elements.alsa_sink import AlsaSink
from lisp.plugins.gst_backend.settings.jack_sink import JackConnectionsDialog
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

import logging
import jack

logger = logging.getLogger(__name__)



class AlsaSinkSettings(SettingsPage):
    ELEMENT = AlsaSink
    Name = ELEMENT.Name

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.devices = {}
        self.discover_output_pcm_devices()

        self.deviceGroup = QGroupBox(self)
        self.deviceGroup.setGeometry(0, 0, self.width(), 100)
        self.deviceGroup.setLayout(QVBoxLayout())
        self.layout().addWidget(self.deviceGroup)

        self.deviceComboBox = QComboBox(self.deviceGroup)
        for name, description in self.devices.items():
            self.deviceComboBox.addItem(description, name)

        self.deviceGroup.layout().addWidget(self.deviceComboBox)

        self.helpLabel = QLabel(self.deviceGroup)
        self.helpLabel.setWordWrap(True)
        self.deviceGroup.layout().addWidget(self.helpLabel)

        self.darioLabel = QLabel(self.deviceGroup)
        self.darioLabel.setWordWrap(True)
        self.darioLabel.setText("messaggio di prova")
        self.deviceGroup.layout().addWidget(self.darioLabel)

        self.retranslateUi()
        
        # Create a new button
        open_jack_connections_button = QPushButton("Open Jack Connections", self)
        # Add the button to the layout
        self.layout().addWidget(open_jack_connections_button)
        # Connect the button's clicked signal to a slot that opens the JackConnectionsDialog
        open_jack_connections_button.clicked.connect(self.open_jack_connections_dialog)

    def open_jack_connections_dialog(self):
        # Create and show the JackConnectionsDialog
        self._temp_jack_client = None
        try:
            self._temp_jack_client = jack.Client(
                "LinuxShowPlayer_SettingsControl", no_start_server=True
            )
        except jack.JackError:
            # Disable the widget
            self.setEnabled(False)
            logger.error(
                "Cannot connect with a running Jack server.", exc_info=True
            )

        dialog = JackConnectionsDialog(self._temp_jack_client, parent=self)
        from lisp.plugins.gst_backend.elements.jack_sink import JackSink
        dialog.set_connections(JackSink.default_connections(self._temp_jack_client).copy())
        dialog.exec()
        if dialog.result() == dialog.Accepted:
            from lisp import backend
            backend.CurrentBackend.Config["default_jack_connections"] = dialog.connections
            backend.CurrentBackend.Config.write()

    def retranslateUi(self):
        self.deviceGroup.setTitle(translate("AlsaSinkSettings", "ALSA device"))
        self.helpLabel.setText(
            translate(
                "AlsaSinkSettings",
                "To make your custom PCM objects appear correctly in this list "
                "requires adding a 'hint.description' line to them.",
            )
        )

    def enableCheck(self, enabled):
        self.setGroupEnabled(self.deviceGroup, enabled)

    def loadSettings(self, settings):
        device = settings.get(
            "device",
            GstBackend.Config.get("alsa_device", AlsaSink.FALLBACK_DEVICE),
        )

        self.deviceComboBox.setCurrentText(
            self.devices.get(device, self.devices.get(AlsaSink.FALLBACK_DEVICE))
        )

    def getSettings(self):
        if self.isGroupEnabled(self.deviceGroup):
            return {"device": self.deviceComboBox.currentData()}

        return {}

    def discover_output_pcm_devices(self):
        self.devices = {}

        # Get a list of the pcm devices "hints", the result is a combination of
        # "snd_device_name_hint()" and "snd_device_name_get_hint()"
        for pcm in alsacard.device_name_hint(-1, "pcm"):
            ioid = pcm.get("IOID")
            # Keep only bi-directional and output devices
            if ioid is None or ioid == "Output":
                self.devices[pcm["NAME"]] = pcm.get("DESC", pcm["NAME"])
