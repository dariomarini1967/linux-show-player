# This file is part of Linux Show Player
#
# Copyright 2022 Francesco Ceruti <ceppofrancy@gmail.com>
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

import logging
import re

import jack
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPolygon, QPainterPath
from PyQt5.QtWidgets import (
    QGroupBox,
    QWidget,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QGridLayout,
    QDialog,
    QDialogButtonBox,
    QPushButton,
    QVBoxLayout,
    QFrame,
    QCheckBox,
    QMessageBox
)

from lisp.plugins.gst_backend.elements.jack_sink import JackSink
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

logger = logging.getLogger(__name__)


class JackSinkSettings(SettingsPage):
    ELEMENT = JackSink
    Name = ELEMENT.Name

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.jackGroup = QGroupBox(self)
        self.jackGroup.setLayout(QHBoxLayout())
        self.layout().addWidget(self.jackGroup)

        self.connectionsEdit = QPushButton(self.jackGroup)
        self.connectionsEdit.clicked.connect(self.__edit_connections)
        self.jackGroup.layout().addWidget(self.connectionsEdit)

        self.__jack_client = None
        try:
            self.__jack_client = jack.Client(
                "LinuxShowPlayer_SettingsControl", no_start_server=True
            )
        except jack.JackError:
            # Disable the widget
            self.setEnabled(False)
            logger.error(
                "Cannot connect with a running Jack server.", exc_info=True
            )

        # if __jack_client is None this will return a default value
        self.connections = JackSink.default_connections(self.__jack_client)

        self.retranslateUi()

    def retranslateUi(self):
        self.jackGroup.setTitle(translate("JackSinkSettings", "Connections"))
        self.connectionsEdit.setText(
            translate("JackSinkSettings", "Edit connections")
        )

    def closeEvent(self, event):
        if self.__jack_client is not None:
            self.__jack_client.close()
        super().closeEvent(event)

    def getSettings(self):
        if self.isGroupEnabled(self.jackGroup):
            return {"connections": self.connections}

        return {}

    def loadSettings(self, settings):
        connections = settings.get("connections", [])
        if connections:
            self.connections = connections.copy()

    def enableCheck(self, enabled):
        self.setGroupEnabled(self.jackGroup, enabled)

    def __edit_connections(self):
        # invoked when editing jack connections for given selected cue
        dialog = JackConnectionsDialog(self.__jack_client, parent=self)
        dialog.set_connections(self.connections.copy())
        dialog.exec()

        if dialog.result() == dialog.Accepted:
            self.connections = dialog.connections


class ClientItem(QTreeWidgetItem):
    def __init__(self, client_name):
        super().__init__([client_name])

        self.name = client_name
        self.ports = {}

    def add_port(self, full_name, display_name):
        self.ports[full_name] = PortItem(full_name, display_name)
        self.addChild(self.ports[full_name])


class PortItem(QTreeWidgetItem):
    def __init__(self, full_name, display_name):
        super().__init__([display_name])

        self.name = full_name


class ConnectionsWidget(QWidget):
    """Code ported from QJackCtl (http://qjackctl.sourceforge.net)"""

    def __init__(self, output_widget, input_widget, parent=None, **kwargs):
        super().__init__(parent)

        self._output_widget = output_widget
        self._input_widget = input_widget
        self.connections = []

    def paintEvent(self, QPaintEvent):
        yc = self.y()
        yo = self._output_widget.y()
        yi = self._input_widget.y()

        x1 = 0
        x2 = self.width()
        h1 = self._output_widget.header().sizeHint().height()
        h2 = self._input_widget.header().sizeHint().height()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for output, out_conn in enumerate(self.connections):
            y1 = int(
                self.item_y(self._output_widget.topLevelItem(output))
                + (yo - yc)
            )

            for client in range(self._input_widget.topLevelItemCount()):
                client = self._input_widget.topLevelItem(client)

                for port in client.ports:
                    if port in self.connections[output]:
                        y2 = int(self.item_y(client.ports[port]) + (yi - yc))
                        self.draw_connection_line(
                            painter, x1, y1, x2, y2, h1, h2
                        )

        painter.end()

    @staticmethod
    def draw_connection_line(painter, x1, y1, x2, y2, h1, h2):
        # Account for list view headers.
        y1 += h1
        y2 += h2

        # Invisible output ports don't get a connecting dot.
        if y1 > h1:
            painter.drawLine(x1, y1, x1 + 4, y1)

        # Setup control points
        spline = QPolygon(4)
        cp = int((x2 - x1 - 8) * 0.4)
        spline.setPoints(
            x1 + 4, y1, x1 + 4 + cp, y1, x2 - 4 - cp, y2, x2 - 4, y2
        )
        # The connection line
        path = QPainterPath()
        path.moveTo(spline.at(0))
        path.cubicTo(spline.at(1), spline.at(2), spline.at(3))
        painter.strokePath(path, painter.pen())

        # painter.drawLine(x1 + 4, y1, x2 - 4, y2)

        # Invisible input ports don't get a connecting dot.
        if y2 > h2:
            painter.drawLine(x2 - 4, y2, x2, y2)

    @staticmethod
    def item_y(item):
        tree_widget = item.treeWidget()
        parent = item.parent()

        if parent is not None and not parent.isExpanded():
            rect = tree_widget.visualItemRect(parent)
        else:
            rect = tree_widget.visualItemRect(item)

        return rect.top() + rect.height() / 2


class JackConnectionsDialog(QDialog):
    def __init__(self, jack_client, parent=None, **kwargs):
        super().__init__(parent)
        self.setWindowTitle("JACK CONNECTIONS editor")


        self.resize(600, 400)

        self.setLayout(QGridLayout())

        self.output_widget = QTreeWidget(self)
        self.input_widget = QTreeWidget(self)

        self.connections_widget = ConnectionsWidget(
            self.output_widget, self.input_widget, parent=self
        )
        self.output_widget.itemExpanded.connect(self.connections_widget.update)
        self.output_widget.itemCollapsed.connect(self.connections_widget.update)
        self.input_widget.itemExpanded.connect(self.connections_widget.update)
        self.input_widget.itemCollapsed.connect(self.connections_widget.update)

        self.stereo_mode_checkbox = QCheckBox("Stereo mode")
        self.stereo_mode_checkbox.setChecked(True)  # Set to True by default

        self.input_widget.itemSelectionChanged.connect(
            self.__input_selection_changed
        )
        self.output_widget.itemSelectionChanged.connect(
            self.__output_selection_changed
        )

        self.layout().addWidget(self.output_widget, 0, 0)
        self.layout().addWidget(self.connections_widget, 0, 1)
        self.layout().addWidget(self.input_widget, 0, 2)

        self.layout().setColumnStretch(0, 2)
        self.layout().setColumnStretch(1, 1)
        self.layout().setColumnStretch(2, 2)

        self.connectButton = QPushButton(self)
        self.connectButton.clicked.connect(self.__disconnect_selected)
        self.connectButton.setEnabled(False)

        self.disconnect_all_button = QPushButton(self)
        self.disconnect_all_button.clicked.connect(self.__disconnect_all)
        self.disconnect_all_button.setText("Disconnect all")

        # Create a horizontal layout to center the controls (i.e. the 2 buttons and the checkbox)
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Add stretch to push controls to the center
        button_layout.addWidget(self.connectButton)
        button_layout.addWidget(self.disconnect_all_button)
        button_layout.addWidget(self.stereo_mode_checkbox)
        button_layout.addStretch()  # Add stretch to push controls tons to the center

        # Create a QFrame to hold the button layout and add a border
        button_frame = QFrame(self)
        button_frame.setLayout(button_layout)
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setFrameShadow(QFrame.Raised)

        # Add the button layout to the main layout
        self.layout().addWidget(button_frame, 1, 1, 1, 1)

        self.dialogButtons = QDialogButtonBox(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok
        )
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)
        self.layout().addWidget(self.dialogButtons, 2, 0, 1, 3)

        self.retranslateUi()

        self.__jack_client = jack_client
        self.__selected_in = None
        self.__selected_out = None

        self.connections = []
        self.update_graph()
        self.input_widget.expandAll()


    def retranslateUi(self):
        self.output_widget.setHeaderLabels(
            [translate("JackSinkSettings", "Output ports")]
        )
        self.input_widget.setHeaderLabels(
            [translate("JackSinkSettings", "Input ports")]
        )
        self.connectButton.setText(translate("JackSinkSettings", "Connect"))

    def set_connections(self, connections):
        self.connections = connections
        self.connections_widget.connections = self.connections
        self.connections_widget.update()

    def update_graph(self):
        input_ports = self.__jack_client.get_ports(is_audio=True, is_input=True)

        self.output_widget.clear()
        for port in range(8):
            self.output_widget.addTopLevelItem(
                QTreeWidgetItem(["output_" + str(port)])
            )

        self.input_widget.clear()
        clients = {}
        for port in input_ports:
            try:
                colon_index = port.name.index(":")
                client_name = port.name[:colon_index]
                port_display_name = port.name[colon_index + 1 :]

                if client_name not in clients:
                    clients[client_name] = ClientItem(client_name)
                    self.input_widget.addTopLevelItem(clients[client_name])

                clients[client_name].add_port(port.name, port_display_name)
            except ValueError:
                pass

    def __input_selection_changed(self):
        if self.input_widget.selectedItems():
            self.__selected_in = self.input_widget.selectedItems()[0]
        else:
            self.__selected_in = None

        self.__check_selection()

    def __output_selection_changed(self):
        if self.output_widget.selectedItems():
            self.__selected_out = self.output_widget.selectedItems()[0]
        else:
            self.__selected_out = None

        self.__check_selection()

    def __check_selection(self):
        if self.__selected_in is not None and self.__selected_out is not None:
            output = self.output_widget.indexOfTopLevelItem(self.__selected_out)

            self.connectButton.clicked.disconnect()
            self.connectButton.setEnabled(True)

            if self.__selected_in.name in self.connections[output]:
                self.connectButton.setText(
                    translate("JackSinkSettings", "Disconnect")
                )
                self.connectButton.clicked.connect(self.__disconnect_selected)
            else:
                self.connectButton.setText(
                    translate("JackSinkSettings", "Connect")
                )
                self.connectButton.clicked.connect(self.__connect_selected)
        else:
            self.connectButton.setEnabled(False)
        # Check if there are any connections set
        if any(self.connections):
            self.disconnect_all_button.setEnabled(True)
        else:
            self.disconnect_all_button.setEnabled(False)
   
    def __connect_selected(self):
        output = self.output_widget.indexOfTopLevelItem(self.__selected_out)
        self.connections[output].append(self.__selected_in.name)
        if self.stereo_mode_checkbox.isChecked():
            # stereo mode: checking if next pain of output and input ports are available for automatically connecting channel 2
            # first, calculate name of next input port
            match = re.match(r"^(.*?)(\d+)$", self.__selected_in.name)
            if match:
                base_name, number = match.groups()
                next_input_port_name = f"{base_name}{int(number) + 1}"
            else:
                next_input_port_name = self.__selected_in.name + "_1"
            # then, check availability of next input port
            available_input_ports = self.__jack_client.get_ports()
            if next_input_port_name in [one_port.name for one_port in available_input_ports]:
                # input port is available, so check if output port is available: as output port is identified simply by an index, increment by 1 and check
                next_output = output + 1
                if(next_output < self.output_widget.topLevelItemCount()):
                    # both input and outpuport are available, connect channel 2
                    self.connections[next_output].append(next_input_port_name)
                else:
                    QMessageBox.information(
                        self,
                        "No output ports left",
                        "No output ports are available for stereo mode.",
                        QMessageBox.Ok
                    )
            else:
                QMessageBox.information(
                    self,
                    "No input ports left",
                    "No input ports are available for stereo mode.",
                    QMessageBox.Ok
                )
        self.connections_widget.update()
        self.__check_selection()

    def __disconnect_selected(self):
        output = self.output_widget.indexOfTopLevelItem(self.__selected_out)
        self.connections[output].remove(self.__selected_in.name)
        self.connections_widget.update()
        self.__check_selection()

    def __disconnect_all(self):
        for output in range(len(self.connections)):
            self.connections[output] = []
        self.connections_widget.update()
        self.__check_selection()
