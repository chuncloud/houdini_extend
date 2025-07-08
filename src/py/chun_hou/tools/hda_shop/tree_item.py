# -*- coding:utf-8 -*-
import sys

from BQt import QtCore, QtWidgets
from bfx_resources import icons
from bfx.ui import get_icon
import os
python_version = sys.version_info[0]


class MenuItem(QtWidgets.QTreeWidgetItem):
    """
    create a menu item that can store some info
    """

    def __init__(self, tool=None, parent=None):
        super(MenuItem, self).__init__(parent)

        if tool:
            self.name = tool.name
        self.setText(1, 'menu')
        self.setFlags(
            QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled |
            QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        )

        self.setIcon(0, get_icon(icons.FOLDER_OPEN))

    def get_all_tools(self):
        tools = []
        for index in range(self.childCount()):
            item = self.child(index)
            if isinstance(item, ToolItem):
                tools.append(item)
            elif isinstance(item, MenuItem):
                tools.extend(item.get_all_tools())
        return tools

    def get_full_name(self):
        if self.parent() is None:
            return self.name
        return '{0}/{1}'.format(self.parent().get_full_name(), self.name)

    @property
    def name(self):
        return self.text(0)

    @name.setter
    def name(self, value):
        if isinstance(value, str):
            self.setText(0, value)
        else:
            self.setText(0, value.decode("utf-8"))

    @property
    def tool_type(self):
        return self.text(1)

    @property
    def author(self):
        return None

    @property
    def about(self):
        return None


class ToolItem(QtWidgets.QTreeWidgetItem):
    """
    create a tool item that can store some info
    """

    def __init__(self, tool=None, parent=None):
        super(ToolItem, self).__init__(parent)

        self.item_data = tool    # dict class
        self._menu = tool.menu
        self._path = tool.path
        self._version = tool.version
        self._date = tool.date
        self._hda_path = tool.hda_path
        self._hda_name = tool.hda_name
        self._hou_version = tool.hou_version
        self._definition = tool.definition

        if self.item_data:    # if dict class exist
            self.name = self.item_data.name
            self.author = self.item_data.author
            self.about = self.item_data.about
            self.hou_version = self.item_data.hou_version
            self.definition = self.item_data.definition
        # set treewidgetitem flag
        self.setFlags(
            QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsSelectable |
            QtCore.Qt.ItemIsEnabled
        )

    def get_full_name(self):
        if self.parent() is None:
            return self.name
        return '{0}/{1}'.format(self.parent().get_full_name(), self.name)

    def set_value(self, index, value):
        if python_version == 2:
            self.setText(index, value)
        elif isinstance(value, str):
            self.setText(index, value)
        else:
            self.setText(index, value.decode("utf-8"))

    @property
    def name(self):
        return self.text(0)

    @name.setter
    def name(self, value):
        self.set_value(0, value)

    @property
    def tool_type(self):
        return self.text(1)

    @tool_type.setter
    def tool_type(self, value):
        self.set_value(1, value)

    @property
    def author(self):
        return self.text(2)

    @author.setter
    def author(self, value):
        self.set_value(2, value)

    @property
    def about(self):
        return self.text(3)

    @about.setter
    def about(self, value):
        self.set_value(3, value)

    @property
    def menu(self):
        return self._menu

    @menu.setter
    def menu(self, value):
        self._menu = value

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        self._date = value

    @property
    def hda_path(self):
        return self._hda_path

    @hda_path.setter
    def hda_path(self, value):
        self._hda_path = value

    @property
    def hda_name(self):
        return self._hda_name

    @hda_name.setter
    def hda_name(self, value):
        self._hda_name = value

    @property
    def hou_version(self):
        return self._hou_version

    @hou_version.setter
    def hou_version(self, value):
        self._hou_version = value

    @property
    def definition(self):
        return self._definition

    @definition.setter
    def definition(self, value):
        self._definition = value
