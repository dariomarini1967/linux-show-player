# This file is part of Linux Show Player
#
# Copyright 2016 Francesco Ceruti <ceppofrancy@gmail.com>
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
    QDialog,
    QGridLayout,
    QComboBox,
    QListWidget,
    QAbstractItemView,
    QVBoxLayout,
    QPushButton,
    QDialogButtonBox,
    QWidget,
    QListWidgetItem,
    QLabel,
    QSizePolicy,
)

from lisp.plugins.gst_backend import elements
from lisp.ui.icons import IconTheme
from lisp.ui.ui_utils import translate


class GstPipeEdit(QWidget):
    def __init__(self, pipe, app_mode=False, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QGridLayout())
        self.layout().setAlignment(Qt.AlignTop)
        self.layout().setContentsMargins(0, 0, 0, 0)

        self._app_mode = app_mode

        # Input selection (label & combo)
        self.inputLabel = QLabel(translate("GstPipelineEdit", "Input"), self)
        self.inputLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.layout().addWidget(self.inputLabel, 0, 0, 1, 1)  
        self.inputBox = QComboBox(self)
        self.inputBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout().addWidget(self.inputBox, 0, 1, 1, 3)
        self.__init_inputs()

        # Current plugins list
        self.currentList = QListWidget(self)
        self.currentList.setDragEnabled(True)
        self.currentList.setDragDropMode(QAbstractItemView.InternalMove)
        self.layout().addWidget(self.currentList, 1, 0, 1, 2)

        # Available plugins list
        self.availableList = QListWidget(self)
        self.layout().addWidget(self.availableList, 1, 3, 1, 2)

        # Output selection (label & combo)
        self.outputLabel = QLabel(translate("GstPipelineEdit", "Output"), self)
        self.outputLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.layout().addWidget(self.outputLabel, 4, 0, 1, 1)
        self.outputBox = QComboBox(self)
        self.outputBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout().addWidget(self.outputBox, 4, 1, 1, 3)
        self.__init_outputs()

        # Add/Remove plugins buttons
        self.buttonsLayout = QVBoxLayout()
        self.layout().addLayout(self.buttonsLayout, 1, 2)
        self.layout().setAlignment(self.buttonsLayout, Qt.AlignHCenter)

        self.addButton = QPushButton(self)
        self.addButton.setIcon(IconTheme.get("go-previous-symbolic"))
        self.addButton.clicked.connect(self.__add_plugin)
        self.buttonsLayout.addWidget(self.addButton)
        self.buttonsLayout.setAlignment(self.addButton, Qt.AlignHCenter)

        self.delButton = QPushButton(self)
        self.delButton.setIcon(IconTheme.get("go-next-symbolic"))
        self.delButton.clicked.connect(self.__remove_plugin)
        self.buttonsLayout.addWidget(self.delButton)
        self.buttonsLayout.setAlignment(self.delButton, Qt.AlignHCenter)

        # Load the pipeline
        self.set_pipe(pipe)

    def set_pipe(self, pipe):
        if pipe:
            if not self._app_mode:
                # Select input by its canonical key (itemData) to avoid fragile
                # selection by visible text. Also show both display name and
                # canonical key in the combo items (see __init_inputs).
                target_input = pipe[0]
                found_index = -1
                for i in range(self.inputBox.count()):
                    if self.inputBox.itemData(i) == target_input:
                        found_index = i
                        break

                if found_index >= 0:
                    self.inputBox.setCurrentIndex(found_index)

            # Select output by its canonical key (itemData) instead of visible
            # text. The visible text contains both the translated name and the
            # element key.
            target_output = pipe[-1]
            found_index = -1
            for i in range(self.outputBox.count()):
                if self.outputBox.itemData(i) == target_output:
                    found_index = i
                    break

            if found_index >= 0:
                self.outputBox.setCurrentIndex(found_index)

        self.__init_current_plugins(pipe)
        self.__init_available_plugins(pipe)

    def get_pipe(self):
        pipe = [] if self._app_mode else [self.inputBox.currentData()]
        for n in range(self.currentList.count()):
            pipe.append(self.currentList.item(n).data(Qt.UserRole))
        pipe.append(self.outputBox.currentData())

        return tuple(pipe)

    def __init_inputs(self):
        if self._app_mode:
            self.inputBox.setEnabled(False)
        else:
            inputs_by_name = {}
            for key, input in elements.inputs().items():
                # Map translated display name -> canonical key
                inputs_by_name[translate("MediaElementName", input.Name)] = key

            for name in sorted(inputs_by_name):
                display = f"{name} ({inputs_by_name[name]})"
                # Visible text shows both name and key, data stores the key
                self.inputBox.addItem(display, inputs_by_name[name])

            self.inputBox.setEnabled(self.inputBox.count() > 1)

    def __init_outputs(self):
        outputs_by_name = {}
        for key, output in elements.outputs().items():
            outputs_by_name[translate("MediaElementName", output.Name)] = key

        for name in sorted(outputs_by_name):
            display = f"{name} ({outputs_by_name[name]})"
            # Visible text shows both name and key, data stores the key
            self.outputBox.addItem(display, outputs_by_name[name])

        self.outputBox.setEnabled(self.outputBox.count() > 1)

    def __init_current_plugins(self, pipe):
        self.currentList.clear()

        # If not in app_mode, the first pipe element is the input
        # the last the output
        start = 0 if self._app_mode else 1
        for plugin in pipe[start:-1]:
            item = QListWidgetItem(
                translate("MediaElementName", elements.plugin_name(plugin))
            )
            item.setData(Qt.UserRole, plugin)
            self.currentList.addItem(item)

    def __init_available_plugins(self, pipe):
        self.availableList.clear()

        for plugin in elements.plugins():
            if plugin not in pipe:
                item = QListWidgetItem(
                    translate("MediaElementName", elements.plugin_name(plugin))
                )
                item.setData(Qt.UserRole, plugin)
                self.availableList.addItem(item)

    def __add_plugin(self):
        item = self.availableList.takeItem(self.availableList.currentRow())
        self.currentList.addItem(item)

    def __remove_plugin(self):
        item = self.currentList.takeItem(self.currentList.currentRow())
        self.availableList.addItem(item)


class GstPipeEditDialog(QDialog):
    def __init__(self, pipe, app_mode=False, **kwargs):
        super().__init__(**kwargs)
        self.setWindowTitle(translate("GstPipelineEdit", "Edit Pipeline"))
        self.setWindowModality(Qt.ApplicationModal)
        self.setMaximumSize(500, 400)
        self.setMinimumSize(500, 400)
        self.resize(500, 400)
        self.setLayout(QVBoxLayout())

        # GstPipeEdit
        self.pipeEdit = GstPipeEdit(pipe, app_mode=app_mode, parent=self)
        self.layout().addWidget(self.pipeEdit)

        # Confirm/Cancel buttons
        self.dialogButtons = QDialogButtonBox(self)
        self.dialogButtons.setStandardButtons(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok
        )
        self.layout().addWidget(self.dialogButtons)

        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

    def get_pipe(self):
        return self.pipeEdit.get_pipe()
