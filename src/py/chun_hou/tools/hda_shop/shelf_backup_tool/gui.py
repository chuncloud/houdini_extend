# -*- coding: utf-8 -*-

import os
import hou
import getpass
import shutil
from BQt import QtWidgets
from bfx.ui import get_icon
from bfx.ui.base.widget import TranslateMixin
from bfx.ui.component.toast import ToastWidget
from . import constants
from .backup_ui import Ui_MainWindow
from ..constants import Icons
from bfx_hou.tools.hda_shop.utils import get_filtered_directory_contents
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path


class Shelf_Backup_Tool(QtWidgets.QMainWindow, TranslateMixin, Ui_MainWindow):
    def __init__(self, parent=None):
        super(Shelf_Backup_Tool, self).__init__()

        self.setupUi(self)
        self.getuser = getpass.getuser()

        self.init_ui_icon()
        self.update_upload_cbbox()
        self.update_user_cbbox()
        self.update_shelf_cbbox()

        self.create_connect()

    def init_ui_icon(self):
        # set icons ----------------------------------------------------
        self.button_update.setIcon(get_icon(Icons.UPDATE))

    def update_upload_cbbox(self):
        self.upload_cbbox.clear()
        if not Path(constants.SHELF_DIR).exists():
            hou.ui.displayMessage(
                "Can't find shelf in home!, "
                "If you want to upload shelf files, please create shelf Tool in Houdini\n "
                "Click OK to load shelf files\n"
                "没有在本地找到 shelf 文件！"
                "如果想上传备份文件， 请先在Houdini 里创建shelf 工具\n"
                "点击 OK 读取shelf 文件"
            )
            self.upload_cbbox.setEnabled(False)
            self.up_button.setEnabled(False)
            self.upload_cbbox.addItems(['None'])
        else:
            self.upload_cbbox.setEnabled(True)
            self.up_button.setEnabled(True)

            self.home_shelf_dir_path = constants.SHELF_DIR
            upload_list = get_filtered_directory_contents(self.home_shelf_dir_path, filter_type="shelf")
            self.upload_cbbox.addItems(sorted(upload_list))

            self.home_current_file = str(self.upload_cbbox.currentText())

    def update_user_cbbox(self):
        self.username_cbbox.clear()

        USER_MEMBER = get_filtered_directory_contents("/sw/PLE/shared/Houdini/toolbar/users/BJ", filter_type="dir")
        self.current_user = self.getuser
        if self.current_user not in USER_MEMBER:
            USER_MEMBER.append(self.current_user)

        self.username_cbbox.addItems(sorted(USER_MEMBER))
        self.username_cbbox.setCurrentIndex(self.username_cbbox.findText(self.current_user))

    def update_shelf_cbbox(self, update=None):
        self.shelf_cbbox.clear()
        if update:
            self.current_user = update

        self.server_shelf_dir_path = os.path.join(constants.TOOLFILES_PATH, self.current_user)
        if not os.path.exists(self.server_shelf_dir_path):
            server_shelf_list = ["None"]
        else:
            server_shelf_list = get_filtered_directory_contents(self.server_shelf_dir_path, filter_type="shelf")
        self.shelf_cbbox.addItems(sorted(server_shelf_list))

        self.server_current_file = str(self.shelf_cbbox.currentText())

    def create_connect(self):
        self.shelf_cbbox.activated.connect(self.shelf_cbbox_actived)
        self.username_cbbox.activated.connect(self.username_cbbox_actived)
        self.upload_cbbox.activated.connect(self.upload_cbbox_actived)
        self.up_button.clicked.connect(self.up_button_clicked)
        self.down_button.clicked.connect(self.down_button_clicked)
        self.button_update.clicked.connect(self.button_update_actived)

    def upload_cbbox_actived(self):
        self.home_current_file = str(self.upload_cbbox.currentText())

    def username_cbbox_actived(self):
        self.current_user = str(self.username_cbbox.currentText())
        self.update_shelf_cbbox(update=self.current_user)

    def shelf_cbbox_actived(self):
        self.server_current_file = str(self.shelf_cbbox.currentText())

    def button_update_actived(self):
        self.update_user_cbbox()
        self.update_upload_cbbox()
        self.update_shelf_cbbox()

    def up_button_clicked(self):
        home_file_path = os.path.join(constants.SHELF_DIR, str(self.home_current_file))
        if not os.path.exists(self.server_shelf_dir_path):
            os.makedirs(self.server_shelf_dir_path)
        backup_file_path = os.path.join(
            self.server_shelf_dir_path, str(self.home_current_file)
        )

        shutil.copy(home_file_path, backup_file_path)
        toast = ToastWidget(parent=self)
        toast.showText(u'backup succeed\n备份成功!')

    def down_button_clicked(self):
        if not Path(constants.SHELF_DIR).exists():
            os.makedirs(constants.SHELF_DIR)

        backup_file_path = os.path.join(constants.TOOLFILES_PATH, self.current_user, self.server_current_file)
        load_file_path = os.path.join(constants.SHELF_DIR, str(self.server_current_file))
        try:
            shutil.copy(backup_file_path, load_file_path)
            hou.shelves.loadFile(load_file_path)
            toast = ToastWidget(parent=self)
            toast.showText(u'load succeed\n导入成功!')
        except IOError as e:
            hou.ui.displayMessage("load failed!\n{}".format(e))

