# -*- coding: utf-8 -*-

import sys
import os
from . import constants

from BQt import QtWidgets, uic

from bfx.ui import get_icon
from bfx.util.log import bfx_get_logger

try:
    import hou

except ImportError:
    pass

logger = bfx_get_logger(__name__)
logger.debug("loading module {0} at {1}".format(__name__, __file__))


class AddNodes(QtWidgets.QDialog):

    def __init__(self):
        super(AddNodes, self).__init__()

        # setup UI----------------------------------------------- #
        ui_file = os.path.join(os.path.dirname(__file__), 'designer', 'addNode.ui')
        uic.loadUi(ui_file, self)

        self.name_undo_icon.setIcon(get_icon(constants.Icons.UNDO))
        self.author_undo_icon.setIcon(get_icon(constants.Icons.UNDO))

        self.create_connect()
        self.check_name()

    def create_connect(self):
        self.name_undo_icon.clicked.connect(self.name_undo_clicked)
        self.author_undo_icon.clicked.connect(self.author_undo_clicked)
        self.name_edit.textChanged.connect(self.check_name)

    def name_undo_clicked(self):
        self.name_edit.setText('')

    def author_undo_clicked(self):
        self.author_edit.setText("")

    def check_name(self):
        if self.name_edit.text() != '':
            self.button_box.setDisabled(False)
        else:
            self.button_box.setDisabled(True)

    @property
    def node_name(self):
        return self.name_edit.text()

    @node_name.setter
    def node_name(self, value):
        self.name_edit.setText(value)

    @property
    def author(self):
        return self.author_edit.text()

    @author.setter
    def author(self, value):
        self.author_edit.setText(value)

    @property
    def about(self):
        return self.about_edit.toPlainText().replace('\n', '  ')

    @about.setter
    def about(self, value):
        self.about_edit.setText(value)

    @property
    def definition(self):
        return self.definition_linedit.text()

    @definition.setter
    def definition(self, value):
        self.definition_linedit.setText(value)

def main():
    """main function that's render when the script is render as a standalone script."""

    app = QtWidgets.QApplication(sys.argv)
    window = AddNodes()
    window.author = 'chiyr'
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

