# -*- coding: utf-8 -*-
import sys
import os
import re
import shutil
import time
import bfx.rpc.client as brpc
from BQt import QtWidgets, uic, QtCore
from bfx.util.log import bfx_get_logger
from bfx.ui.component.toast import ToastWidget
from bfx.util.path import PathConverter
from .core import ConfigJson, get_last_version, set_config_path
from .constants import Names

try:
    import hou
except ImportError:
    pass

try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

logger = bfx_get_logger(__name__)
logger.debug("loading module {0} at {1}".format(__name__, __file__))


class ShowImport(QtWidgets.QMainWindow):
    def __init__(self, item=None, config_path=None, parent=None):
        super(ShowImport, self).__init__(parent=parent)

        # setup UI ----------------------------------------------- #
        ui_file = os.path.join(
            os.path.dirname(__file__), 'designer', 'importWindow.ui'
        )
        uic.loadUi(ui_file, self)

        self.type = item.tool_type
        self.name = item.name
        self.path = item.path
        self.version = item.version
        self.date = item.date
        self.about = item.about
        self.hda_path = item.hda_path
        self.hda_name = item.hda_name
        self.label_type.setText(self.type)
        self.label_name.setText(self.name)
        self.config_path = config_path
        self.type_path = set_config_path(item=item)
        self.definition = item.definition


        self.set_history_item()
        self.create_connect()

    def set_history_item(self):
        """
        display items in the views
        :return:
        """
        if self.type == Names.HDA:
            try:
                definition_tuple = hou.hda.definitionsInFile(
                    os.path.join(self.config_path, self.type_path, self.path)
                )
            except hou.OperationFailed as e:
                msg = (
                    u"Load hda failed,please check this hda under this path {0}\n"
                    u"加载hda 失败,请检查这个hda {0} 是否正常".format(
                        os.path.join(self.config_path, self.type_path, self.path)
                    )
                )
                hou.ui.displayMessage(msg)
                return

            for definition in definition_tuple:
                version = definition.nodeTypeName()
                try:
                    hou_version = definition.extraFileOptions()[version]
                except KeyError as e:
                    hou_version = None
                    logger.info("This {} definition has no hou_version".format(e))
                hda_time = time.ctime(definition.modificationTime())
                self.tree_widget.addTopLevelItem(
                    QtWidgets.QTreeWidgetItem([version, hou_version, hda_time, self.definition])
                )
        else:
            max_vernum = get_last_version(
                os.path.join(self.config_path, self.type_path, self.name)
            )
            path = os.path.join(
                self.config_path, self.type_path, self.name,
                self.path.split('/')[-1]
            )
            nodes_time = time.ctime(os.path.getctime(path))
            try:
                node_hou_version = self.hou_version
            except:
                node_hou_version = None
                logger.info("This {} nodes has no hou_version".format(self.name))
            if max_vernum == 1:
                self.tree_widget.addTopLevelItem(
                    QtWidgets.QTreeWidgetItem([self.name + '_' + self.version, node_hou_version,
                                               nodes_time, self.definition])
                )
            else:
                old_config = ConfigJson()
                old_config.load_from_json(
                    os.path.join(self.config_path, self.type_path, self.name)
                )
                old_tools = old_config.get_all_tools()
                for tool in old_tools:
                    try:
                        node_hou_version = tool.hou_version
                    except:
                        node_hou_version = None
                        logger.info("This {} nodes has no hou_version".format(self.name))
                    self.tree_widget.addTopLevelItem(
                        QtWidgets.QTreeWidgetItem([tool.name + '_' + tool.version,
                                                   node_hou_version, nodes_time, tool.definition])
                    )
                self.tree_widget.addTopLevelItem(
                    QtWidgets.QTreeWidgetItem([self.name + '_' + self.version, node_hou_version,
                                               nodes_time, self.definition])
                )

    def get_item_path(self):
        """
        get the history item path
        :return: item path
        """
        item = self.tree_widget.currentItem()
        if not item:
            return ''
        if self.type == Names.HDA:
            path = os.path.join(self.config_path, self.type_path, self.path)
            self.hda_name = '{}::{}::{}'.format(
                self.hda_name.split('::')[0], self.hda_name.split('::')[1],
                item.text(0).split('::')[-1]
            )
        else:
            path = os.path.join(
                self.config_path, self.type_path, self.path
            )
        return path


    # ======================================== Event ======================================= #
    def create_connect(self):
        self.load_button.clicked.connect(self.load_button_clicked)

    def loadedFiles(self):
        """

        :return: a list of hda files loaded into this Houdini session
        """
        result = []
        for category in hou.nodeTypeCategories().values():
            for node_type in category.nodeTypes().values():
                definition = node_type.definition()
                if definition is None:
                    continue
                if definition.libraryFilePath() not in result:
                    result.append(definition.libraryFilePath())
        return result

    def check_nodes(self):
        '''
        check import nodes path has one level or multiple levels
        if .cpio nodes and .py nodes has multiple levels create parent node
        if .cpio nodes has one level ,create parent node

        :return: parent_node
        '''
        # create parent nodes
        hda_path_split = self.hda_path.lstrip('/').split('/')
        hda_name_split = self.hda_name.lstrip('/').split('/')
        len_number = len(hda_name_split)
        node_path = ''

        source_path = self.get_item_path()
        nodes_type = Path(source_path).suffix

        if len_number > 1:
            for number in range(len_number - 1):
                node_path += '/' + hda_name_split[number]
                node_child_path = node_path + '/' + hda_name_split[number + 1]
                if not hou.node(node_child_path):
                    parent_node = hou.node(node_path).createNode(
                        hda_path_split[number + 1], hda_name_split[number + 1]
                    )
                    parent_node.moveToGoodPosition()
                    return parent_node
                else:
                    msg = (
                        u'you want to add has existed already,import failed\n'
                        u'待添加的节点(\'{0}\')已经存在,导入失败\n'
                            .format(node_child_path + "/" + self.path)
                    )
                    hou.ui.displayMessage(msg)
                    return

        elif nodes_type == ".cpio":
            parent_node = hou.node("{}".format(self.hda_name))
            parent_node.moveToGoodPosition()
            return parent_node

    def load_button_clicked(self):
        '''
        import HDA, .cpio nodes and .py nodes
        .cpio will gradually replace .py in the future

        :return:
        '''
        self.load_button.setDisabled(True)
        self.load_button.setText('Loading.....')
        source_path = self.get_item_path()

        # load
        if self.type == Names.HDA:

            # copy hda to local otls folder
            otls_path = os.path.join(os.environ['HIH'], Names.otls)
            if not os.path.exists(otls_path):
                os.makedirs(otls_path)
            target_path = os.path.join(otls_path, os.path.basename(source_path))
            if os.path.exists(target_path):
                msg = (
                    u'There already has a same name HDA in otls folder in local HOME,'
                    u'do you want to overwrite?\n'
                    u'(IF YOU WANT TO OVERWRITE THIS HDA,'
                    u'PLEASE MAKE SURE THAT HDA IS NOT IN USING)\n' 
                    u'在本地主文件夹的otls文件里,已经存在一个相同名字的HDA {0},是否替换?\n'
                    u'(如果要替换该HDA,请确保该HDA没有用于当前的制作中)'
                    .format(os.path.basename(source_path).split('.')[0])
                )
                result = hou.ui.displayMessage(msg, buttons=('Yes', 'No'))
                if result == 0:
                    os.remove(target_path)
                else:
                    self.load_button.setDisabled(False)
                    self.load_button.setText(Names.Load)
                    return

            brpc.change_path_permission(
                source_path, username="publisher", password="gae6deeX", mode="777", og='ple', recursive=True
            )
            shutil.copy2(source_path, target_path)
            brpc.change_path_permission(
                source_path, username="publisher", password="gae6deeX", mode="555", og='ple', recursive=True
            )

            # create hda node in current houdini
            hou.hda.installFile(target_path)
            parent_node = self.create_parent(self.name, self.hda_path)
            if not parent_node:
                self.load_button.setDisabled(False)
                self.load_button.setText(Names.Load)
                return
            try:
                hda_node = parent_node.createNode(self.hda_name)
            except:
                msg = (u'Import hda failed!\n导入hda失败！')
                hou.ui.displayMessage(msg)
                self.load_button.setDisabled(False)
                self.load_button.setText(Names.Load)
                return

            # move to good position
            hda_node.moveToGoodPosition()
            hda_node.setSelected(True, clear_all_selected=True)

        else:
            # check if temp file path is exist or not
            temp_path = os.path.join(os.environ['HIH'], 'temp')
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)

            # delete old file in temp folder
            for old_file in os.listdir(temp_path):
                delete_path = os.path.join(temp_path, os.path.basename(old_file))
                self.delete_function(delete_path)

            # copy node python file to temp folder
            target_path = os.path.join(temp_path, os.path.basename(source_path))
            if os.path.exists(target_path):
                os.remove(target_path)

            brpc.change_path_permission(
                source_path, username="publisher", password="gae6deeX", mode="777", og='ple', recursive=True
            )
            shutil.copy2(source_path, target_path)
            brpc.change_path_permission(
                source_path, username="publisher", password="gae6deeX", mode="555", og='ple', recursive=True
            )

            # check import nodes type is "py" or "cpio"
            nodes_type = Path(source_path).suffix
            if nodes_type == ".cpio":
                # check_node
                new_node = self.check_nodes()
                if new_node:
                    new_node.loadItemsFromFile(source_path, ignore_load_warnings=False)
            else:
                #modify hda path or hda name to right
                #if selected item's version is not correct
                pattern = re.compile(r'v([0-9]+)\Wpy', re.I)
                select_version = pattern.search(source_path).group(1)
                if select_version != self.version.lstrip('v'):
                    select_item_config = ConfigJson()
                    select_item_config.load_from_json(
                        os.path.join(self.config_path, self.type_path, self.name)
                    )
                    tools = select_item_config.get_all_tools()
                    for tool in tools:
                        if tool.version.lstrip('v') == select_version:
                            self.hda_name = tool.hda_name
                            self.hda_path = tool.hda_path

                # check nodes
                self.check_nodes()

                # execute python file to create nodes
                #TODO: use load cpio instead of exec py file
                try:
                    exec(open(target_path).read())
                except AttributeError as e:
                    msg = (u'Import node failed!\n导入node失败！')
                    logger.info('AttributeError: ')
                    logger.info(str(e))
                    hou.ui.displayMessage(msg)
                    self.load_button.setDisabled(False)
                    self.load_button.setText(Names.Load)
                    return
                except ImportError:
                    self.load_button.setDisabled(False)
                    self.load_button.setText(Names.Load)
                    return

            # move to good position
            for node in hou.selectedNodes():
                node.moveToGoodPosition()

        # layout selected nodes
        items = hou.selectedItems()
        items[0].parent().layoutChildren(items)

        # to zoom the created nodes
        editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        editor.homeToSelection()

        toast = ToastWidget(parent=self)
        toast.showText(u'Load succeed\n加载成功!')

        self.load_button.setDisabled(False)
        self.load_button.setText(Names.Load)

    # ======================================== Method ======================================= #
    def create_parent(self, name, hda_path):
        name = name.replace(' ', '_')
        name = name.replace(':', "_")
        if hda_path == 'Sop':
            parent_node = hou.node('/obj/').createNode('geo', name)

            node_clildren = parent_node.children()
            if len(node_clildren) != 0:
                for node in node_clildren:
                    node.destroy()

        elif hda_path in ['Dop', 'Pop']:
            parent_node = hou.node('/obj/').createNode('dopnet', name)

            node_clildren = parent_node.children()
            if len(node_clildren) != 0:
                for node in node_clildren:
                    node.destroy()

        elif hda_path == 'Object':
            parent_node = hou.node('/obj/')

        elif hda_path == 'Lop':
            parent_node = hou.node('/stage/')

        elif hda_path == 'Driver':
            parent_node = hou.node('/out/')

        elif hda_path == 'Shop':
            parent_node = hou.node('/obj/').createNode('shopnet', name)

        elif hda_path == 'Vop':
            parent_node = hou.node('/obj/').createNode('vopnet', name)

        else:
            msg = (u"Sooooory,can't load {} type hda yet,"
                   u"if you need this function,please tell ple".format(hda_path))
            # TODO(chiyr):add node type
            hou.ui.displayMessage(msg)
            return False

        parent_node.moveToGoodPosition()
        return parent_node

    def delete_function(self, delete_path):
        if os.path.isfile(delete_path):
            os.remove(delete_path)
        else:
            shutil.rmtree(delete_path)

def main():
    """main function that's run when the script is run as a standalone script."""


    app = QtWidgets.QApplication(sys.argv)
    window = ShowImport(config_path=PathConverter.to_current('/sw/PLE/shared/Houdini/hda_shop/users/chiyr'))
    window.show()
    # print
    print(window.tree_widget.findItems('v1', QtCore.Qt.MatchRecursive, 0))
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()