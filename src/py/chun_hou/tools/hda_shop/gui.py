# -*- coding: utf-8 -*-
import os
import getpass
import shutil
import time
import webbrowser
import bfx.rpc.client as brpc
from BQt import QtCore, QtWidgets

from bfx.data.prod.shotgun.production2 import Person
from bfx.data.ple.task_context import TaskContext
from bfx_resources import icons
from bfx.ui import get_icon
from bfx.ui.base.widget import TranslateMixin
from bfx.ui.component.toast import ToastWidget
from bfx.util.log import bfx_get_logger
from bfx.data.prod.shotside import get_approved_shows
from bfx.data.ple.assets import Entity
from bfx.env.constants import LOCATIONS
from bfx.pipeline.kuaidi.models import create_package

from .add_node import AddNodes
from .upload_file import Uploadfiles
from .errors import ConfigNotExists
from .designer.mainWindow_new import Ui_MainWindow
from .import_tool import ShowImport
from .shelf_backup_tool.gui import Shelf_Backup_Tool
from .tree_item import ToolItem, MenuItem
from .core import ConfigJson, ToolSet, set_config_path, get_config_path, get_last_version
from .utils import CommonHelper
from . import constants
from .constants import Names
from bfx_hou.tools.hda_shop.utils import get_filtered_directory_contents


try:
    import hou

except ImportError:
    pass

logger = bfx_get_logger(__name__)
logger.debug("loading module {0} at {1}".format(__name__, __file__))


class HDAShopMainWindow(QtWidgets.QMainWindow, TranslateMixin, Ui_MainWindow):

    def __init__(self, parent=None):
        super(HDAShopMainWindow, self).__init__(parent=parent)

        # setup UI -----------------------------------------------#
        # ui_file = os.path.join(
        #     os.path.dirname(__file__), 'designer', 'mainWindow_new.ui'
        # )
        # uic.loadUi(ui_file, self)
        self.setupUi(self)
        self.tree_widget.dropEvent = self.tree_drop_event
        self.tree_widget.mousePressEvent = self.tree_mouse_press_event
        self.tree_widget.mouseDoubleClickEvent = self.edit_tools

        self.tc = TaskContext.from_env()
        self.current_show = self.tc.show_name if self.tc else ''
        self.current_city = constants.CurrentLocation
        self.preference_mode = Names.shows
        self.item_type = ''
        self.retranslate_ui()
        self.toolsets_data = []
        self.text = QtWidgets.QLabel(
            '<font color=#ff6600>  Modify permission denied, '
            'Please contact PLE</font>'
        )
        self.user_text = QtWidgets.QLabel(
            '<font color=#ffcc00>  '
            'You don`t have permission to Modify</font>'
        )
        self.label.addWidget(self.text)
        self.label.addWidget(self.user_text)

        self.getuser = getpass.getuser()

        self.config_path = None
        self.is_dirty = False
        self.delete_file = []
        self.init_ui_icon()
        self.update_ui()

        self.create_connect()

        # set StyleSheet
        stylefile = os.path.join(os.path.dirname(__file__), 'qss', 'style.qss')
        qssStyle = CommonHelper.readqss(stylefile)
        self.setStyleSheet(qssStyle)

        self._create_version_tree_context_menu()
        self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)

    def init_ui_icon(self):
        # set icons ----------------------------------------------------
        self.button_add_HDA.setIcon(get_icon(constants.Icons.ADD_NODE))
        self.button_upload_HDA.setIcon(get_icon(icons.ADD_FILE_GREY))
        self.button_add_menu.setIcon(get_icon(constants.Icons.ADD_MENU))
        self.button_delete.setIcon(get_icon(constants.Icons.DELETE))
        self.button_save.setIcon(get_icon(constants.Icons.SAVE))
        self.button_help.setIcon(get_icon(constants.Icons.HELP))
        self.button_update.setIcon(get_icon(constants.Icons.UPDATE))
        self.button_shelf_backup.setIcon(get_icon(constants.Icons.SHELF_BACKUP))

    def retranslate_ui(self):
        # TODO: to support translate ui,it is not under using now
        self.label_add_HDA.setText(self.translate('Add HDA'))
        self.label_upload_HDA.setText(self.translate("Upload HDA"))
        self.label_add_menu.setText(self.translate("Add Menu"))
        self.label_delete.setText(self.translate("Delete"))
        self.label_save.setText(self.translate("Save"))
        self.label_help.setText(self.translate("Help"))
        self.label_update.setText(self.translate("Update"))
        self.label_shelf_backup.setText(self.translate("Shelf Backup"))

    def update_ui(self, update=None):
        self.project_cbbox.clear()
        self.project_cbbox.setEnabled(False)
        self.update_city_cbbox(show_folder=False)

        if self.preference_mode == Names.shows:
        # set show cbbox
            self.project_cbbox.setEnabled(True)

            show_list = []
            show_list.extend(constants.SHOW_MEMBER)
            current_show = self.current_show
            if (current_show not in show_list):
                show_list.append(current_show)

            self.project_cbbox.addItems(sorted(show_list))

            # judge current show is blank
            if self.current_show == '':
                self.current_show = str(self.project_cbbox.currentText())
                if update:
                    self.current_show = update
                self.project_cbbox.setCurrentIndex(
                    self.project_cbbox.findText(self.current_show)
                )
                self.city_cbbox.setCurrentIndex(
                    self.city_cbbox.findText(self.current_city)
                )
                self.load_project_data(
                    name=self.current_show, obj_data=self.preference_mode,
                    location=True
                )
                self.current_show = ''
            else:
                if update:
                    self.current_show = update
                self.project_cbbox.setCurrentIndex(
                    self.project_cbbox.findText(self.current_show)
                )
                self.city_cbbox.setCurrentIndex(
                    self.city_cbbox.findText(self.current_city)
                )

                self.load_project_data(
                    name=self.current_show, obj_data=self.preference_mode,
                    location=True
                )
                self.update_city_cbbox(project=self.current_show, type=self.preference_mode)
        elif self.preference_mode == Names.users:
        # set user cbbox
            self.project_cbbox.setEnabled(True)

            user_list = []
            user_list.extend(constants.USER_MEMBER)
            current_user = self.getuser
            if (current_user not in user_list):
                user_list.append(current_user)

            if update:
                current_user = update
            self.project_cbbox.addItems(sorted(user_list))
            self.project_cbbox.setCurrentIndex(
                self.project_cbbox.findText(current_user)
            )
            self.load_project_data(
                name=current_user, obj_data=self.preference_mode
            )
        else:
        # set base cbbox
            base_list = []
            base_list.append('BFX')
            self.project_cbbox.addItems(base_list)
            self.update_city_cbbox(project=None, type=self.preference_mode)
            self.load_project_data(
                obj_data=self.preference_mode, location=True
            )

    def set_permission(self, item=None):
        '''
        check current selected HDA is created by the current user:
            if so, open permission
            if not, close addMenu, delete, save permission

        :param self: ToolSetManager
        :param item: current selected item object
        '''
        self.text.hide()
        self.user_text.hide()
        if item:
            if item.author == None:
                logger.info('current menu name: {0}'.format(item.name))
            # set display user_text and permission in users
            elif(self.preference_mode == Names.users and
                    self.getuser != item.author and
                    self.getuser not in constants.PERMISSION_MEMBERS and
                    self.getuser not in constants.PLE_MEMBERS
            ):
                self.user_text.show()
                self.button_add_menu.setDisabled(True)
                self.button_delete.setDisabled(True)
                self.button_save.setDisabled(True)
            # set display text and permission in shows and base
            elif (self.getuser != item.author and
                    self.getuser not in constants.PERMISSION_MEMBERS and
                    self.getuser not in constants.PLE_MEMBERS
            ):
                self.text.show()
                self.button_add_menu.setDisabled(True)
                self.button_delete.setDisabled(True)
                self.button_save.setDisabled(True)
            else:
                self.tree_widget.setDisabled(False)
                self.button_add_HDA.setDisabled(False)
                self.button_add_menu.setDisabled(False)
                self.button_delete.setDisabled(False)
                self.button_save.setDisabled(False)
                self.button_upload_HDA.setDisabled(False)
        else:
            logger.info("item == None")
        if self.label_save.text() == ("Save*"):
            self.button_save.setDisabled(False)


    def load_project_data(self, name=None, obj_data=None, location=False):
        # logger.info('loading project data: {0}'.format(name))
        self.tree_widget.clear()

        # set shows and base level permission
        self.set_permission()

        # get tools path
        if location:
            path = os.path.join(get_config_path(project=name, type=obj_data),
                                self.city_cbbox.currentText())
        else:
            path = get_config_path(project=name, type=obj_data)

        self.tree_widget.setDisabled(False)
        if not path:
            self.tree_widget.setDisabled(True)
            return
        self.config_path = path

        # load tools from config
        config = ConfigJson()
        try:
            config.load_from_json(path)
        except ConfigNotExists as e:
            logger.error("Error:{}".format(e))
            return

        toolsets = config.get_all_tools()
        self.toolsets_data = toolsets

        # generate toolsets tree
        for tool in toolsets:
            menu_path = tool.menu.lstrip('/')

            # generate item
            if not menu_path:
            # generate item that not in any menu
                tool_item = ToolItem(tool=tool, parent=self.tree_widget)

            else:
            # generate item that in some menus
                for depth, menu_name in enumerate(menu_path.split('/')):

                    # generate menu item
                    if depth == 0:
                        if self.tree_widget.topLevelItemCount() == 0:
                            p = MenuItem(tool=tool, parent=self.tree_widget)
                            p.name = menu_name
                        else:
                            is_found = False
                            for i in range(self.tree_widget.topLevelItemCount()):
                                top = self.tree_widget.topLevelItem(i)
                                if top.name == menu_name:
                                    is_found = True
                                    p = top
                                    break
                            if not is_found:
                                p = MenuItem(tool=tool, parent=self.tree_widget)
                                p.name = menu_name
                    else:
                        if p.childCount() == 0:
                            p = MenuItem(tool=tool, parent=p)
                            p.name = menu_name
                        else:
                            is_found = False
                            for i in range(p.childCount()):
                                c = p.child(i)
                                if c.name == menu_name:
                                    is_found = True
                                    p = c
                                    break
                            if not is_found:
                                p = MenuItem(tool=tool, parent=p)
                                p.name = menu_name

                tool_item = ToolItem(tool=tool, parent=p)
            tool_item.tool_type = tool.type

        self.tree_widget.expandAll()
        for index in range(self.tree_widget.columnCount()):
            self.tree_widget.resizeColumnToContents(index)


    # ================================= Event ==================================== #
    def create_connect(self):
        self.button_add_HDA.clicked.connect(self.button_add_hda_clicked)
        self.button_upload_HDA.clicked.connect(self.button_upload_hda_clicked)
        self.button_add_menu.clicked.connect(self.button_add_menu_clicked)
        self.button_delete.clicked.connect(self.button_delete_clicked)
        self.button_save.clicked.connect(self.button_save_clicked)
        self.button_help.clicked.connect(self.button_help_clicked)
        self.button_update.clicked.connect(self.button_update_clicked)
        self.button_shelf_backup.clicked.connect(self.button_shelf_backup_clicked)
        self.project_cbbox.activated.connect(self.project_cbbox_activated)
        self.city_cbbox.activated.connect(self.city_cbbox_activated)
        self.radio_button_base.clicked.connect(self.radio_button_clicked)
        self.radio_button_show.clicked.connect(self.radio_button_clicked)
        self.radio_button_user.clicked.connect(self.radio_button_clicked)
        self.tree_widget.itemChanged.connect(self.current_item_changed)
        self.tree_widget.itemSelectionChanged.connect(self.item_selection_changed)

    def button_add_hda_clicked(self):
        # add nodes and hip from houdini script
        nodes = hou.selectedNodes()
        if not nodes:
            hou.ui.displayMessage(u'No nodes are selected!')
            return

        # set tools Info
        if len(nodes) == 1 and nodes[0].isLockedHDA() and nodes[0].type().definition():
            # add item is HDA
            hda_name = nodes[0].type().definition().nodeType().name()
            # such as  "bfx.nnn::XXXX::1.0 "
            hda_name_list = hda_name.split('::')
            if len(hda_name_list) != 3:
                msg = (u'Please check your HDA Operator Name\n'
                       u'请查看你的HDA Operator name')
                hou.ui.displayMessage(msg)
                return
            node_name = nodes[0].type().definition().description()
            # such as XXXX
            item = self.set_node_info(name=node_name)
            # item type: class
        else:
            # add item is Nodes
            item = self.set_node_info()

        if not item:
            return

        item.tool_type = Names.Nodes
        if len(nodes) == 1 and nodes[0].isLockedHDA() and nodes[0].type().definition():
        # add item type is HDA
            item.tool_type = Names.HDA
            hda_path = nodes[0].type().definition().libraryFilePath()
            hda_name = nodes[0].type().definition().nodeType().name()
            hda_name_list = hda_name.split('::')
            namespace = hda_name_list[0]
            node_name = hda_name_list[1]
            vernum = hda_name_list[2]

            # check namespace
            if namespace == Names.bfx:
                pass
            elif namespace[:3] == Names.bfx and len(namespace) > 3:
                checked_namespace = self.check_namespace(namespace[4:])
                if not checked_namespace or namespace[3] not in ['.', '_']:
                    msg = (
                        u'The namespace of HDA has some problem,please check it!'
                        u'Current namespace is {0}\n'
                        u'HDA 的 namespace 命名有问题，请检查！当前的namespace是{0}'
                            .format(namespace)
                    )
                    hou.ui.displayMessage(msg)
                    return
            else:
                msg = (
                    u'The begining of the namespace is not "bfx",'
                    u'please check it!Current namespace is {0}\n'
                    u'HDA的namespace不是以"bfx"开头的，请检查！'
                    u'当前的namespace是{0}'.format(namespace)
                )
                hou.ui.displayMessage(msg)
                return

            # change upload path or not
            current_ratiobutton = self.current_radioButton()
            current_project_cbbox = self.project_cbbox.currentText()
            if namespace == Names.bfx:
                if current_ratiobutton != Names.base:
                    msg = (
                        u'The upload path of HDA is base by default,' 
                        u'but current upload path of HDA is {0}\'s {1},'
                        u'please choose upload path\n' 
                        u'默认HDA的上传路径是base,当前HDA的上传路径是{0}下的{1},' 
                        u'请选择上传路径！'
                            .format(current_ratiobutton, current_project_cbbox)
                    )
                    result = hou.ui.displayMessage(msg, buttons=(
                        'Default path:(base)', 'Current path:({0}-{1})'
                        .format(current_ratiobutton, current_project_cbbox),
                        'Cancel'))
                    if result == 0:
                        self.set_radioButton(current_ratiobutton, Names.base)
                        self.set_project_cbbox(Names.bfx)
                        self.update_ui(self.project_cbbox.currentText())
                    elif result == 1:
                        pass
                    else:
                        return
            else:
                if (namespace[4:].upper() != current_project_cbbox.upper() or
                        checked_namespace != current_ratiobutton):
                    msg = (
                        u'The upload path of HDA is {0}\'s {1} by default,' 
                        u'but current upload path of HDA is {2}\'s {3},'
                        u'please choose upload path\n'
                        u'默认HDA的上传路径是{0}下的{1},当前HDA的上传路径是{2}下的{3},' 
                        u'请选择上传路径！'
                        .format(checked_namespace, namespace[4:],
                                current_ratiobutton, current_project_cbbox)
                    )
                    result = hou.ui.displayMessage(msg, buttons=(
                        'Default path:({0}-{1})'
                        .format(checked_namespace, namespace[4:]),
                        'Current path:({0}-{1})'
                        .format(current_ratiobutton, current_project_cbbox),
                        'Cancel'))
                    if result == 0:
                        self.set_radioButton(current_ratiobutton, checked_namespace)
                        self.set_project_cbbox(namespace[4:])
                        self.update_ui(self.project_cbbox.currentText())
                    elif result == 1:
                        pass
                    else:
                        return

            item.version = ''
            item.path = os.path.basename(hda_path)
            item.item_data.path = item.path
            item.hda_name = hda_name
            item.hda_path = nodes[0].type().definition().nodeTypeCategory().name()
            config_path = set_config_path(item=item)

            # check HDA path
            if not hda_path or not os.path.isfile(hda_path):
                msg = (
                    u'Constructor for HDA failed, path to this HDA not exists!\n' 
                    u'HDA 初始化失败, 该HDA路径不存在！'
                )
                hou.ui.displayMessage(msg)
                return

        else:
        # add item type is Node
            basename = item.name
            version_name = '{}_{}.{}'.format(basename, item.version, 'cpio')
            item.path = os.path.join(basename, version_name)
            item.item_data.path = item.path     # item.item_data就相当于是一个字典类
            item.hda_name = nodes[0].parent().path()
            item.hda_path = self.get_node_path(nodes[0].parent())
            nodes_parent = nodes[0].parent()
            config_path = set_config_path(item=item)
            item.hou_version = ".".join(str(e) for e in list(hou.applicationVersion()))
            if not item.hda_path:
                return

        path = os.path.join(self.config_path, config_path, item.path)

        check_backup = False
        # add item path is exist
        if os.path.exists(path):
            if item.tool_type == Names.HDA:
                # save hou_version
                new_hda = hou.hda.definitionsInFile(os.path.join(hda_path))
                old_hda = hou.hda.definitionsInFile(path)
                self.save_hou_version(new_hda=new_hda, old_hda=old_hda)

            # add item is HDA
                msg = (
                    u'HDA you want to add already exists, '
                    u'do you want to overwrite?\n' 
                    u'待添加的HDA已存在,是否想覆盖?'
                )
                result = hou.ui.displayMessage(msg, buttons=('Yes', 'No'))
                if result == 0:
                    check_backup = True
                    # delete source dictory
                    self.delete_function(path)

                    # delete backup file
                    self.delete_function(
                        os.path.join(self.config_path, Names.backup, config_path,
                        os.path.basename(path))
                    )

                    # delete the item have the same item path
                    item_samepath = []
                    for index in range(self.tree_widget.topLevelItemCount()):
                        top = self.tree_widget.topLevelItem(index)
                        if isinstance(top, ToolItem):
                            if top.path == item.path:
                                item_samepath.append(top)
                        elif isinstance(top, MenuItem):
                            for tool in top.get_all_tools():
                                if tool.path == item.path:
                                    item_samepath.append(tool)
                    for t in item_samepath:
                        if t.parent():
                            index = t.parent().indexOfChild(t)
                            t.parent().takeChild(index)
                        else:
                            index = self.tree_widget.indexOfTopLevelItem(t)
                            self.tree_widget.takeTopLevelItem(index)
                else:
                    return
            else:
            # add item is node
                msg = (
                    u'{0} Node(s) you want to add already exists, ' 
                    u'do you want to add version number?\n' 
                    u'待添加的 {0} 节点已存在,是否想升一个版本号？'.format(item.name)
                )
                result = hou.ui.displayMessage(msg, buttons=('Yes', 'No'))
                if result == 0:
                    check_backup = True
                    vernum = get_last_version(os.path.dirname(path))
                    item.version = 'v{}'.format(vernum + 1)
                    ext = os.path.basename(path).split('.')[-1]
                    version_name = '{}_{}.{}'.format(basename, item.version, ext)
                    item.path = os.path.join(basename, version_name)
                    item.item_data.path = item.path
                    path = os.path.join(
                        self.config_path, config_path, basename, version_name
                    )
                else:
                    return

        # judge if there has same name in backup file
        if os.path.exists(os.path.join(self.config_path, Names.backup, config_path,
                                       item.path)) and not check_backup:
            msg = (
                u'{0} Node(s) you want to add already exists in backup files, ' 
                u'do you want to overwrite?\n' 
                u'待添加的 {0} 节点已存在于备份文集中,是否覆盖？'.format(item.name)
            )
            result = hou.ui.displayMessage(msg, buttons=('Yes', 'No'))
            if result == 0:
                self.delete_function(
                    os.path.join(self.config_path, Names.backup,
                    config_path, item.path)
                )
            else:
                return

        brpc.change_path_permission(
            self.config_path, username="publisher", password="gae6deeX", mode="777", og='ple', recursive=True
        )
        path_dir = os.path.dirname(path)
        if not os.path.exists(path_dir):
            os.makedirs(path_dir)

        if item.tool_type == Names.HDA:
            # save hou_version
            self.save_hou_version()
            # copy hda file
            shutil.copy2(hda_path, path)
        else:
            # use "cpio" to up nodes
            cpio_path = path_dir + "/" + version_name
            nodes_parent.saveItemsToFile(nodes, cpio_path, save_hda_fallbacks=True)
            path = cpio_path

        # backup file
        backup_path = os.path.join(
            self.config_path, Names.backup, config_path, item.path
        )
        if not os.path.exists(os.path.dirname(backup_path)):
            os.makedirs(os.path.dirname(backup_path))
        self.copy_function(path, backup_path)
        brpc.change_path_permission(
            self.config_path, username="publisher", password="gae6deeX", mode="555", og='ple', recursive=True
        )
        # add tools to tree_widget
        self.add_tree_widget_item([item])
        logger.info("add HDA info: {}".format(item.__dict__))

    def button_upload_hda_clicked(self):
        upload_path = ''
        readfile = hou.ui.selectFile(
            os.environ['HIH'], 'Upload', False, hou.fileType.Otl,
            multiple_select=True
        )
        upload_path = hou.expandString(readfile)
        # judge user had selected files
        if upload_path != '':
            readfiles = [
                file_path.strip(' ') for file_path in upload_path.split(';')
            ]

            # check if the readfile is hip file or hda file
            result = self.check_readfile(readfiles)
            if not result:
                return

            items, is_check = self.set_upload_info(readfiles=readfiles)

            if not items:
                return

            # create a list includes the item will be clean from the treewidget
            # if they has the same path
            item_clean_list = []
            # create a list includes the item will be skip when upload
            item_skip_list = []

            file_number = len(readfiles)
            # loop for each readfiles
            for number in range(file_number):
                items[number].tool_type = Names.HDA
                hda_path = readfiles[number]

                definition = self.get_definition(hda_path)
                if not definition:
                    return
                if definition == 'Skip':
                    item_skip_list.append(items[number])
                    continue

                hda_name = definition.nodeTypeName()
                hda_name_list = hda_name.split('::')

                namespace = hda_name_list[0]
                node_name = hda_name_list[1]

                # check namespace
                if is_check or namespace == Names.bfx:
                    pass
                elif namespace[:3] == Names.bfx and len(namespace) > 3:
                    checked_namespace = self.check_namespace(namespace[4:])
                    if not checked_namespace or namespace[3] not in ['.', '_']:
                        msg = (
                            u'The namespace of HDA has some problem,'
                            u'please check it!{0} namespace is {1}\n' 
                            u'If you want to skip the upload of current node,'
                            u'please click "Skip" button below\n' 
                            u'HDA 的 namespace 命名有问题，请检查！{0} 的namespace是{1}\n' 
                            u'跳过当前节点上传请点击下面的"Skip"按钮'
                                .format(items[number].name, namespace)
                        )
                        result = hou.ui.displayMessage(
                            msg, buttons=('Skip', 'Cancel')
                        )
                        if result == 0:
                            item_skip_list.append(items[number])
                            continue
                        else:
                            return
                else:
                    msg = (
                        u'The begining of the namespace is not "bfx",'
                        u'please check it!{0} namespace is {1}\n' 
                        u'If you want to skip the upload of current node,'
                        u'please click "Skip" button below\n' 
                        u'HDA的namespace不是以"bfx"开头的，请检查！'
                        u'{0} 的namespace是{1}\n' 
                        u'跳过当前节点上传请点击下面的"Skip"按钮'
                            .format(items[number].name, namespace)
                    )
                    result = hou.ui.displayMessage(
                        msg, buttons=('Skip', 'Cancel')
                    )
                    if result == 0:
                        item_skip_list.append(items[number])
                        continue
                    else:
                        return

                items[number].version = ''
                items[number].path = os.path.basename(hda_path)
                items[number].item_data.path = items[number].path    # item.item_data就相当于是一个字典类
                items[number].hda_name = hda_name
                items[number].hda_path = definition.nodeTypeCategory().name()
                config_path = set_config_path(item=items[number])    # 给它的dirpath添加一个叫HDA层级的文件夹
                if not hda_path or not os.path.isfile(hda_path):
                    msg = (
                        u'Constructor for HDA failed, '
                        u'path to this {0} HDA not exists!\n' 
                        u'If you want to skip the upload of current node,'
                        u'please click "Skip" button below\n' 
                        u'{0} HDA 初始化失败, 该HDA路径不存在！\n' 
                        u'跳过当前节点上传请点击下面的"Skip"按钮'
                            .format(items[number].name))
                    result = hou.ui.displayMessage(
                        msg, buttons=('Skip', 'Cancel')
                    )
                    if result == 0:
                        item_skip_list.append(items[number])
                        continue
                    else:
                        return

                path = os.path.join(
                    self.config_path, config_path, items[number].path
                )

                check_backup = False
                if os.path.exists(path):
                    msg = (
                        u'{0} HDA you want to add already exists, '
                        u'do you want to overwrite?\n' 
                        u'If you want to skip the upload of current node,'
                        u'please click "Skip" button below\n' 
                        u'待添加的{0} HDA已存在,是否想覆盖?\n' 
                        u'跳过当前节点上传请点击下面的"Skip"按钮'
                            .format(items[number].name)
                    )
                    result = hou.ui.displayMessage(
                        msg, buttons=('Overwrite', 'Skip', 'Cancel')
                    )
                    if result == 0:
                        check_backup = True
                        # delete source dictory
                        self.delete_function(path)

                        # delete backup file
                        self.delete_function(os.path.join(
                            self.config_path, Names.backup, config_path,
                            os.path.basename(path))
                        )

                        # append delete item to the list
                        item_clean_list.append(items[number])

                    elif result == 1:
                        item_skip_list.append(items[number])
                        continue
                    else:
                        return

                # judge if there has same name in backup file
                if os.path.exists(os.path.join(
                        self.config_path, Names.backup, config_path,
                        items[number].path)) and not check_backup:
                    msg = (
                        u'{0} HDA you want to add already exists in backup files, '
                        u'do you want to overwrite?\n'
                        u'If you want to skip the upload of current node,'
                        u'please click "Skip" button below\n'
                        u'待添加的{0} HDA已存在于备份文集中,是否覆盖？\n'
                        u'跳过当前节点上传请点击下面的"Skip"按钮'
                           .format(items[number].name)
                    )
                    result = hou.ui.displayMessage(
                        msg, buttons=('Overwrite', 'Skip', 'Cancel')
                    )
                    if result == 0:
                        self.delete_function(os.path.join(
                            self.config_path, Names.backup,
                            config_path, items[number].path)
                        )

                    elif result == 1:
                        item_skip_list.append(items[number])
                        continue
                    else:
                        return

                path_dir = os.path.dirname(path)
                brpc.change_path_permission(
                    self.config_path, username="publisher", password="gae6deeX", mode="777", og='ple', recursive=True
                )
                if not os.path.exists(path_dir):
                    os.makedirs(path_dir)
                # copy hda file
                shutil.copy2(hda_path, path)

                # backup file
                backup_path = os.path.join(
                    self.config_path, Names.backup, config_path, items[number].path
                )
                if not os.path.exists(os.path.dirname(backup_path)):
                    os.makedirs(os.path.dirname(backup_path))
                self.copy_function(path, backup_path)
                brpc.change_path_permission(
                    self.config_path, username="publisher", password="gae6deeX", mode="555", og='ple', recursive=True
                )

            # delete the item have the same item path
            for clean_item in item_clean_list:
                item_samepath = []
                for index in range(self.tree_widget.topLevelItemCount()):
                    top = self.tree_widget.topLevelItem(index)
                    if isinstance(top, ToolItem):
                        if top.path == clean_item.path:
                            item_samepath.append(top)
                    elif isinstance(top, MenuItem):
                        for tool in top.get_all_tools():
                            if tool.path == clean_item.path:
                                item_samepath.append(tool)
                for t in item_samepath:
                    if t.parent():
                        index = t.parent().indexOfChild(t)
                        t.parent().takeChild(index)
                    else:
                        index = self.tree_widget.indexOfTopLevelItem(t)
                        self.tree_widget.takeTopLevelItem(index)

            # remove skip item from items
            for skip_item in item_skip_list:
                items.remove(skip_item)

            # add tools to tree_widget
            if items:
                self.add_tree_widget_item(items)

    def button_add_menu_clicked(self):
        msg = (u'Give a name to your menu(no chinese word)\n' 
               u'It will be the name of the subMenu:\n' 
               u'请给子文件夹取个名字(不要有中文):')
        name, result = QtWidgets.QInputDialog.getText(
            self, 'menu Name', msg, QtWidgets.QLineEdit.Normal
        )
        # TODO(chiyr): replace self to hou.qt.mainWindow()

        if not result:
            return

        item = self.tree_widget.currentItem()

        # create menu item
        if item and isinstance(item, MenuItem):
            m = MenuItem(parent=item)
        else:
            m = MenuItem(parent=self.tree_widget)

        m.name = name
        self.tree_widget.expandAll()
        self.is_dirty = True
        self.label_save.setText(self.translate('Save') + '*')

    def button_delete_clicked(self):

        for item in self.tree_widget.selectedItems():
            is_delete = True

            # add item to self.delete_file list
            if isinstance(item, MenuItem):
                msg = (
                    u'Do you want to delete menu {0}\n'
                    u'Menu {0} and all the tools and '
                    u'sub-menus in it will be deleted!\n'
                    u'你确定想要删除文件夹 {0} 吗?\n'
                    u'文件夹 {0} 下的所有东西和子文件夹都会被删除'
                       .format(item.name)
                )
                result = QtWidgets.QMessageBox.warning(
                    self, 'ToolSet Manager', msg,
                    QtWidgets.QMessageBox.Yes |
                    QtWidgets.QMessageBox.Cancel,
                    QtWidgets.QMessageBox.Cancel
                )
                if result == QtWidgets.QMessageBox.Cancel:
                    is_delete = False
                else:
                    for tool in item.get_all_tools():
                        if tool.tool_type in [Names.HDA, Names.Nodes, Names.hip,
                                              Names.hiplc, Names.hipnc]:
                            config_path = set_config_path(item=tool)
                            path = os.path.join(
                                self.config_path, config_path, tool.path
                            )
                            self.delete_file.append({'path': path, 'item': tool})
            else:
                config_path = set_config_path(item=item)
                path = os.path.join(self.config_path, config_path, item.path)
                msg = (u'Do you want to delete {0}?\n'
                       u'你确定想要删除 {0} 吗?'.format(item.name))
                result = QtWidgets.QMessageBox.warning(
                    self, 'ToolSet Manager', msg,
                    QtWidgets.QMessageBox.Yes |
                    QtWidgets.QMessageBox.Cancel,
                    QtWidgets.QMessageBox.Cancel)
                if result == QtWidgets.QMessageBox.Cancel:
                    is_delete = False
                else:
                    self.delete_file.append({'path': path, 'item': item})

            if is_delete:
                # delete item from treewidget
                if item.parent():
                    index = item.parent().indexOfChild(item)
                    item.parent().takeChild(index)
                else:
                    index = self.tree_widget.indexOfTopLevelItem(item)
                    self.tree_widget.takeTopLevelItem(index)

                self.label_save.setText(self.translate('Save') + '*')

    def button_save_clicked(self, newitems=None):
        # set config.json
        tool_list = []
        for index in range(self.tree_widget.topLevelItemCount()):
            top = self.tree_widget.topLevelItem(index)
            if isinstance(top, ToolItem):
                # save to config.json
                tool = ToolSet(name=top.name,
                               type=top.tool_type,
                               path=top.path,
                               menu='/',
                               author=top.author,
                               about=top.about,
                               version=top.version,
                               hda_name=top.hda_name,
                               hda_path=top.hda_path,
                               hou_version=top.hou_version,
                               definition=top.definition)
                tool_list.append({'tool': tool, 'item': top})
            elif isinstance(top, MenuItem):
                for tool in top.get_all_tools():
                    menu = tool.get_full_name().rstrip(tool.name).rstrip('/')
                    t = ToolSet(name=tool.name,
                                type=tool.tool_type,
                                menu=menu,
                                path=tool.path,
                                author=tool.author,
                                about=tool.about,
                                version=tool.version,
                                hda_name=tool.hda_name,
                                hda_path=tool.hda_path,
                                hou_version=tool.hou_version,
                                definition=tool.definition)
                    tool_list.append({'tool': t, 'item': tool})

        # backup config and skip HDA for now
        # TODO(chiyr): add hda config
        if newitems:
            for newitem in newitems:
                if newitem.tool_type != Names.HDA:
                    for tool_dir in tool_list:
                        tool = tool_dir['tool']
                        if newitem.path == tool['path']:
                            backup_configpath = set_config_path(newitem)
                            brpc.change_path_permission(
                                self.config_path, username="publisher", password="gae6deeX", mode="777", og='ple',
                                recursive=True
                            )
                            backup_path = os.path.join(
                                self.config_path, Names.backup,
                                backup_configpath, newitem.name
                            )
                            if os.path.exists(os.path.join(
                                    backup_path, 'config.json')):
                                existed_config = ConfigJson()
                                existed_config.load_from_json(backup_path)
                                # delete the old data from config with same version
                                for old_tool in existed_config.get_all_tools():
                                    if (old_tool['version'] == tool['version'] and
                                            old_tool['path'] == tool['path']):
                                        existed_config.delete_tools(old_tool)
                                existed_config.add_tool(tool)
                                existed_config.write_to_json(backup_path)
                            else:
                                if not os.path.exists(backup_path):
                                    os.makedirs(backup_path)
                                backup_config = ConfigJson()
                                backup_config.add_tool(tool)
                                backup_config.write_to_json(backup_path)

                            brpc.change_path_permission(
                                self.config_path, username="publisher", password="gae6deeX", mode="555", og='ple',
                                recursive=True
                            )
                            break

        config = self.merge_config(tool_list=tool_list)

        # delete file
        if len(self.delete_file) > 0:
            for file in self.delete_file:
                if os.path.exists(file['path']):
                    if file['path'].split('.')[-1] in constants.OTL_TYPE:
                        logger.info ('Delete file {0}'.format(file['path']))

                        try:
                            self.delete_function(file['path'])
                        except:
                            logger.info (
                                'Delete error,delete path:{0} failed'
                                .format(file['path'])
                            )

                    else:
                        logger.info (
                            'Delete folder {0}'
                            .format(os.path.dirname(file['path']))
                        )

                        try:
                            self.delete_function(os.path.dirname(file['path']))
                        except:
                            logger.info (
                                'Delete error,delete path:{0} failed'
                                .format(os.path.dirname(file['path']))
                            )

            self.delete_file = []

        # write into json
        config.write_to_json(self.config_path)
        self.is_dirty = False
        self.label_save.setText(self.translate('Save'))
        logger.info("write_to_json:{}".format(config))

        toast = ToastWidget(parent=self)
        toast.showText(u'Save succeed\n保存成功!')

        # update
        project = str(self.project_cbbox.currentText())
        if self.preference_mode == Names.shows:
            self.load_project_data(
                name=project, obj_data=self.preference_mode, location=True
            )
        elif self.preference_mode == Names.base:
            self.load_project_data(
                obj_data=self.preference_mode, location=True
            )
        else:
            self.load_project_data(
                name=project, obj_data=self.preference_mode
            )

        # # sync
        package = create_package(src_root=self.config_path, src_location=constants.CurrentLocation,
                                 dst_location="ALL", priority=5, label='HDA_shop sync')
        logger.info(' - package created: {id}'.format(id=package))

    def save_hou_version(self, new_hda = None, old_hda = None):
        '''
        when add new hda and definitions, save current houdini version
          suce as 18.5.532
        if user change a definition and add another definiton
          according to the modification time of definition
            change this two definiton`s houdini version
        Args:
            new_hda: the new hda in current user otls folder
            old_hda: the old hda in hda_shop otls folder

        Returns:

        '''
        nodes = hou.selectedNodes()
        hou_version = ".".join(str(e) for e in list(hou.applicationVersion()))
        if new_hda and old_hda:
            old_definition_l = []
            new_definition_l = []
            for (definition_new, definition_old) in zip(new_hda, old_hda):
                old_definition_time = time.ctime(definition_old.modificationTime())
                old_definition_l.append(old_definition_time)

                new_definition_time = time.ctime(definition_new.modificationTime())
                new_definition_l.append(new_definition_time)

                dif = set(new_definition_l).difference(set(old_definition_l))
                current_definition = time.ctime(nodes[0].type().definition().modificationTime())

                if current_definition in dif:
                    dif.remove(current_definition)
                if len(dif) != 0:
                    for definition in new_hda:
                        if time.ctime(definition.modificationTime()) in dif:
                            set_version = definition.setExtraFileOption(
                                definition.nodeTypeName(), hou_version
                            )
        else:
            definition = nodes[0].type().definition()
            set_version = definition.setExtraFileOption(definition.nodeTypeName(), hou_version)

    def button_help_clicked(self):
        msg = u'作者应该忘了写wiki，你可以通过请他吃一次的牛排来提醒一下他'
        result = hou.ui.displayMessage(msg)
        if result == 0:
            webbrowser.open_new("https://wiki.base-fx.com/display/PLE/HDA+Shop")

    def button_update_clicked(self):
        self.update_ui(self.project_cbbox.currentText())
        self.delete_file = []
        self.label_save.setText(self.translate('Save'))

        toast = ToastWidget(parent=self)
        toast.showText(u'Update succeed\n刷新成功!')

    def button_shelf_backup_clicked(self):

        self.shelf_backup_tool = Shelf_Backup_Tool(parent=self)
        self.shelf_backup_tool.show()


    def update_city_cbbox(self, project=None, type=None, show_folder=True):
        '''
        set default city cbbox = current locations
        if update, city cbbox = CITY_MEMBER list

        :param project: current selected show
        :param type: base or shows
        :param show_folder:
        :return:
        '''
        # default city cbboc
        self.city_cbbox.clear()
        self.city_cbbox.setEnabled(False)
        self.city_cbbox.addItems([self.current_city])

        if self.preference_mode == Names.users:
            return
        # get CITY_MEMBER
        if show_folder:
            # current selected show path
            show_folder = os.path.join(
                get_config_path(project=project,type=type)
            )
            try:
                CITY_MEMBER = get_folder_files_names_list(show_folder, filter_type="dir")
            except:
                logger.info("current show:{} has no HDA".format(project))
                return

            # set current location at first in list
            locations = sorted(CITY_MEMBER)
            current_location = constants.CurrentLocation
            if current_location in locations:
                locations.remove(current_location)
            locations.insert(0, current_location)

            self.city_cbbox.clear()
            self.city_cbbox.setEnabled(True)
            self.city_cbbox.addItems(locations)
        else:
            logger.info("show_folder is none")
            return

    def project_cbbox_activated(self, index):
        if self.preference_mode == Names.shows:
            project = str(self.project_cbbox.currentText())
            self.update_city_cbbox(
                project=str(self.project_cbbox.currentText()),
                type=self.preference_mode
            )
            self.load_project_data(project, self.preference_mode, location=True)

        if self.preference_mode == Names.users:
            project = str(self.project_cbbox.currentText())

            self.load_project_data(project, self.preference_mode)

    def city_cbbox_activated(self, index):
        if self.preference_mode == Names.shows:
            project = str(self.project_cbbox.currentText())

            self.load_project_data(project, self.preference_mode, location=True)
        if self.preference_mode == Names.base:

            self.load_project_data(obj_data=self.preference_mode, location=True)

    def radio_button_clicked(self):
        if self.radio_button_base.isChecked():
            self.preference_mode = Names.base
        if self.radio_button_show.isChecked():
            self.preference_mode = Names.shows
        if self.radio_button_user.isChecked():
            self.preference_mode = Names.users
        self.update_ui()

    def current_item_changed(self, item):
        if self.tree_widget.isItemSelected(item):
            self.is_dirty = True
            self.label_save.setText(self.translate("Save") + "*")

    def item_selection_changed(self):
        item = self.tree_widget.currentItem()
        self.set_permission(item)
        self.tree_widget.closePersistentEditor(item, 0)

    def tree_drop_event(self, event):
        # set permission
        if (self.preference_mode == Names.base and
                self.getuser not in constants.PERMISSION_MEMBERS and
                self.getuser not in constants.PLE_MEMBERS):
            return

        if (self.preference_mode == Names.shows and
                self.getuser not in constants.PERMISSION_MEMBERS and
                self.getuser not in constants.PLE_MEMBERS):
            return

        if (self.preference_mode == Names.users and
                self.getuser != self.project_cbbox.currentText() and
                self.getuser not in constants.PLE_MEMBERS):
            return

        self.is_ditry = True
        self.label_save.setText(self.translate('Save') + '*')
        QtWidgets.QTreeWidget.dropEvent(self.tree_widget, event)

        self.tree_widget.expandAll()
        for index in range(self.tree_widget.columnCount()):
            self.tree_widget.resizeColumnToContents(index)

    def _create_version_tree_context_menu(self):
        self._menu = QtWidgets.QMenu(self)

        # import tools
        self._show_import_action = QtWidgets.QAction(
            get_icon(constants.Icons.IMPORT), '     Import', self
        )
        self._menu.addAction(self._show_import_action)
        self._show_import_action.triggered.connect(self.import_tool_triggered)

    def contextMenuEvent(self, event):
        self._menu.move(event.globalPos())
        currentitem = self.tree_widget.currentItem()
        if currentitem and isinstance(currentitem, ToolItem):
            self._menu.show()

    def tree_mouse_press_event(self, event):
        self.tree_widget.clearSelection()
        self.tree_widget.clearFocus()
        QtWidgets.QTreeWidget.mousePressEvent(self.tree_widget, event)

    def edit_tools(self, event):
        # popup the edit window
        item = self.tree_widget.currentItem()

        # set permission
        if (item and
            self.getuser != item.author and
            self.getuser not in constants.PERMISSION_MEMBERS and
            self.getuser not in constants.PLE_MEMBERS
        ):
            self.text.show()
            self.button_add_menu.setDisabled(True)
            self.button_delete.setDisabled(True)
            self.button_save.setDisabled(True)
            return

        # item is not menu treewidgetitem
        if isinstance(item, ToolItem):
            # double press item and change item info
            new_item = self.set_node_info(item=item)
            if not new_item:
                return
            else:
                if item.parent():
                    item.parent().addChild(new_item)
                else:
                    index = self.tree_widget.indexOfTopLevelItem(item)
                    self.tree_widget.takeTopLevelItem(index)
                    self.tree_widget.addTopLevelItem(new_item)
                self.is_dirty = True
                self.button_save_clicked()
        elif isinstance(item, MenuItem):
            # double press menu and change menu name
            column = self.tree_widget.currentColumn()
            if column == 0:
                self.tree_widget.openPersistentEditor(item, column)
                self.label_save.setText(self.translate('Save') + '*')

    def import_tool_triggered(self):
        current_item = self.tree_widget.currentItem()

        self.import_widget = ShowImport(
            item=current_item, config_path=self.config_path, parent=self
        )
        # self.import_widget.setParent(self, QtCore.Qt.Window)
        self.import_widget.show()
        logger.info("import HDA name: {}".format(current_item.text(0)))
        logger.info("import HDA type: {}".format(current_item.text(1)))
        logger.info("import HDA author: {}".format(current_item.text(2)))

    # ==================================== Method ========================================= #
    def add_tree_widget_item(self, items):

        for item in items:
            # find the node of the same name and delete from tree widget
            item_list = self.tree_widget.findItems(
                item.name, QtCore.Qt.MatchRecursive, 0
            )

            for t in item_list:

                if isinstance(t, ToolItem) and t.tool_type != item.tool_type:
                    continue
                # delete same name item from treewidget
                if t.parent():
                    index = t.parent().indexOfChild(t)
                    t.parent().takeChild(index)
                else:
                    index = self.tree_widget.indexOfTopLevelItem(t)
                    self.tree_widget.takeTopLevelItem(index)

                # find the old item and save to config.json and skip HDA
                if (isinstance(t, ToolItem) and
                        t.tool_type == item.tool_type and
                        t.tool_type != Names.HDA):
                    tool = ToolSet(name=t.name,
                                   type=t.tool_type,
                                   path=t.path,
                                   menu=t.menu,
                                   author=t.author,
                                   about=t.about,
                                   version=t.version,
                                   hda_name=t.hda_name,
                                   hda_path=t.hda_path,
                                   hou_version=t.hou_version,
                                   definition=t.definition
                                   )
                    config_tool = tool
                    config_path = set_config_path(tool=tool)
                    config_path = os.path.dirname(os.path.join(
                        self.config_path, config_path, tool.path)
                    )
                    if os.path.exists(os.path.join(config_path, 'config.json')):
                        old_config = ConfigJson()
                        old_config.load_from_json(config_path)
                        old_config.add_tool(config_tool)
                        old_config.write_to_json(config_path)
                    else:
                        new_config = ConfigJson()
                        new_config.add_tool(config_tool)
                        new_config.write_to_json(config_path)

            # treewidget add item
            current_item = self.tree_widget.currentItem()
            if isinstance(current_item, MenuItem):
                current_item.addChild(item)
            elif isinstance(current_item, ToolItem):
                if current_item.parent():
                    current_item.parent().addChild(item)
                else:
                    self.tree_widget.addTopLevelItem(item)
            else:
                self.tree_widget.addTopLevelItem(item)

            self.is_dirty = True

        self.button_save_clicked(items)
        self.tree_widget.expandAll()
        for index in range(self.tree_widget.columnCount()):
            self.tree_widget.resizeColumnToContents(index)

    def set_node_info(self, item=None, name=None):
        p = AddNodes()
        p.setParent(self, QtCore.Qt.Window)
        # TODO(chiyr): set parent as houdini
        # modify tool info
        if item:
            p.node_name = item.name
            p.about = item.about.replace('  ', '\n')
            p.author = item.author
            p.definition = item.definition
        else:
            # add new tool
            if name:
                p.node_name = name
            p.author = self.getuser

        # judge addnode execute or not
        if p.exec_():
            name = p.node_name
            about = p.about
            author = p.author
            definition = p.definition
        else:
            return None

        if item:
            item.name = name
            item.about = about
            item.author = author
            item.definition = definition
            return item

        # so item not exist
        tool = ToolSet(name=name, author=author, about=about, definition=definition)
        new_item = ToolItem(tool=tool)
        new_item.version = 'v1'
        return new_item

    def set_upload_info(self, readfiles):
        p = Uploadfiles(readfiles)
        p.setParent(self, QtCore.Qt.Window)
        # TODO(chiyr): set parent as houdini

        getnames = []
        # get hda description info
        for file_path in readfiles:
            # judge whether file type is hda
            if file_path.split('.')[-1] in constants.OTL_TYPE:
                file_path= hou.expandString(file_path)
                for definition in hou.hda.definitionsInFile(file_path):
                    try:
                        getnames.append(definition.description())
                        break
                    except :
                        msg = (
                            u'There has some problem with HDA importing,'
                            u'maybe the version is too old\n' 
                            u'导入的HDA有问题,可能是版本太老了'
                        )
                        hou.ui.displayMessage(msg)
                        return None

        p.names = getnames
        p.authors = self.getuser

        # judge whether upload is execute
        if p.exec_():
            names = [p_name.text() for p_name in p.names]
            authors = [p_author.text() for p_author in p.authors]
            abouts = [p_about.text() for p_about in p.abouts]
        else:
            return None

        items = []
        files_number = len(readfiles)
        for number in range(files_number):
            tool = ToolSet(
                name=names[number], author=authors[number],
                about=abouts[number]
            )
            new_item = ToolItem(tool=tool)
            items.append(new_item)
        return items, p.is_check

    def set_edit_permission(self, permission=True):
        self.tree_widget.setDisabled(False)
        if permission:
            self.text.show()
        else:
            self.text.hide()
        self.button_add_HDA.setDisabled(permission)
        self.button_add_menu.setDisabled(permission)
        self.button_delete.setDisabled(permission)
        self.button_save.setDisabled(permission)
        self.button_upload_HDA.setDisabled(permission)

    def merge_config(self, tool_list):
        # write tool to config.json
        config = ConfigJson()
        new_config = ConfigJson()
        try:
            config.load_from_json(self.config_path)    # 把目标path中的json文件读取到config中
            toolsets = config.get_all_tools()
            for tool_dir in tool_list:
                tool = tool_dir['tool']
                new_config.add_tool(tool)

            # no change
            if toolsets == self.toolsets_data:
                return new_config
            else:
                # add new tool
                for tool in toolsets:
                    if tool not in self.toolsets_data:
                        new_config.add_tool(tool)

            # someone change tool
            for tool_dir in tool_list:
                tool = tool_dir['tool']
                item = tool_dir['item']

                # judge current treewidget data is the same as local config data,
                # tool is stand for current treewidget data
                # item.item_data is stand for local config data
                if tool != item.item_data:
                    for t in toolsets:
                        # match the correspondent local item
                        if t.path == item.item_data.path:
                            # change info such Author, About
                            if t == item.item_data:
                                new_config.delete_tools(t)
                                continue
                            msg = (
                                u'Someone changed node{0}, '
                                u'do you want to overwrite and ignore the changes?\n'
                                u'{0}节点已被其他人更改，'
                                u'是否覆盖并忽略别人已更改的内容？'
                                    .format(t.name)
                            )
                            result = hou.ui.displayMessage(
                                msg, buttons=('Yes', 'No')
                            )

                            # choose which will be deleted from new_config
                            if result == 0:
                            # delete local item from new_config
                                new_config.delete_tools(t)
                                continue
                            else:
                            # delete current treewidget item from new_config
                                new_config.delete_tools(tool)
                                continue

            # if new tool path not exist, delete
            new_toolsets = new_config.get_all_tools()
            for new_tool in new_toolsets:
                config_path = set_config_path(tool=new_tool)
                path = os.path.join(self.config_path, config_path, new_tool.path)
                if not os.path.exists(path):
                    new_config.delete_tools(new_tool)

        except ConfigNotExists:
            for tool_dir in tool_list:
                tool = tool_dir['tool']
                new_config.add_tool(tool)

        return new_config

    def check_namespace(self, namespace):
        show_name = [show.name for show in Entity.get_all_roots()]
        if not namespace:
            return False
        if namespace.lower() == Names.bfx:
            return Names.base
        elif namespace.upper() in show_name:
            return Names.shows
        elif namespace.lower() in constants.BFX_MEMBERS :
            return Names.users
        else:
            return False

    def check_readfile(self, readfiles):
        for file_path in readfiles:
            # if file_path.split('.')[-1] in constants.OTL_TYPE or file_path.split('.')[-1] in constants.HIP_TYPE:
            if file_path.split('.')[-1] in constants.OTL_TYPE:
                pass
            else:
                msg = (u'The upload files includes some files are non-hip files or '
                       u'non-otl files,please check it out\n'
                       u'上传的文件有不是otl类型的文件，请检查！')
                hou.ui.displayMessage(msg)
                return False
        return True

    def set_radioButton(self, disable_button, enable_button):
        if disable_button == Names.base:
            self.radio_button_base.setChecked(False)
        elif disable_button == Names.shows:
            self.radio_button_show.setChecked(False)
        elif disable_button == Names.users:
            self.radio_button_user.setChecked(False)

        if enable_button == Names.base:
            self.radio_button_base.setChecked(True)
        elif enable_button == Names.shows:
            self.radio_button_show.setChecked(True)
        elif enable_button == Names.users:
            self.radio_button_user.setChecked(True)

    def set_project_cbbox(self, currentText):
        current_radioButton = self.current_radioButton()
        if current_radioButton == Names.base:
            self.preference_mode = Names.base
            self.project_cbbox.setCurrentIndex(
                self.project_cbbox.findText(str(currentText.upper()))
            )
        elif current_radioButton == Names.shows:
            self.preference_mode = Names.shows
            self.project_cbbox.setCurrentIndex(
                self.project_cbbox.findText(str(currentText.upper()))
            )
        elif current_radioButton == Names.users:
            self.preference_mode = Names.users
            self.project_cbbox.setCurrentIndex(
                self.project_cbbox.findText(str(currentText.lower()))
            )

    def current_radioButton(self):
        if self.radio_button_base.isChecked():
            return Names.base
        if self.radio_button_show.isChecked():
            return Names.shows
        if self.radio_button_user.isChecked():
            return Names.users

    def delete_function(self, delete_path):
        brpc.change_path_permission(
            os.path.dirname(delete_path),
            username="publisher", password="gae6deeX",
            mode="777", og='ple', recursive=True
        )
        if os.path.isfile(delete_path):
            os.remove(delete_path)
        else:
            shutil.rmtree(delete_path)
        brpc.change_path_permission(
            os.path.dirname(delete_path),
            username="publisher", password="gae6deeX",
            mode="555", og='ple', recursive=True
        )

    def copy_function(self, src, dst):
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    def get_definition(self, hda_path):
        """
        this function is only get the max version definition
        :param hda_path:
        :return:
        """
        definition_dict = {}
        version_list = []
        for definition in hou.hda.definitionsInFile(hda_path):
            hda_name = definition.nodeTypeName()
            hda_name_list = hda_name.split('::')
            # check name is correct or not
            if len(hda_name_list) != 3:
                msg = (
                    u'Your {0} HDA\'s Operator Nameis {1},'
                    u'please check it out\n'
                    u'你的{0} HDA\'s Operator name为 {1},请检查'.
                        format(hda_path.split('/')[-1].rstrip('.hda'), hda_name)
                )
                result = hou.ui.displayMessage(msg, buttons=('Skip', 'Cancel'))
                if result == 0:
                    return 'Skip'
                else:
                    return False

            definition_dict[hda_name.split('::')[-1]] = definition
            version_list.append(hda_name.split('::')[-1])

        max_version = max(version_list)
        return definition_dict[max_version]

    def get_node_path(self, node):
        path = node.path()
        path_split = path.lstrip('/').split('/')
        node_path = ''
        return_path = ''
        for element in path_split:
            node_path += '/' + element
            return_path += '/' + hou.node(node_path).type().name()
            if hou.node(node_path).type().definition():
                msg = u'please do not upload nodes in HDA\n请不要在HDA中上传节点'
                hou.ui.displayMessage(msg)
                return
        return return_path

def main_window():
    hou.session.win = HDAShopMainWindow()
    hou.session.win.setMinimumHeight(700)
    # hou.session.win.setStyleSheet(hou.ui.qtStyleSheet())
    hou.session.win.show()


