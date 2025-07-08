# -*- coding:utf-8 -*-
import os
import json
import bfx.rpc.client as brpc
from collections import OrderedDict
from bfx.util.log import bfx_get_logger
from .errors import ConfigNotExists
from .constants import Names, TOOLFILES_PATH

logger = bfx_get_logger(__name__)
logger.debug('loading module {0} at {1}'.format(__name__, __file__))

def get_toolset_root():
    """
    Currently return the shared toolset path
    Once the toolset should be published into show level,
    use this function to return the root path
    :return:
    """
    return TOOLFILES_PATH

def get_config_path(project=None, type=None):
    """
    return the Tool path for the given project

    :param project:
    :param type:
    :return:
    """
    if type == 'shows':
        path = os.path.join(get_toolset_root(), Names.shows, project)
    elif type == 'users':
        path = os.path.join(get_toolset_root(), Names.users, project)
    elif type == 'base':
        path = os.path.join(get_toolset_root(), Names.base)
    return path

def set_config_path(item=None, tool=None):
    """
    add a corresponding menu name in local folders
    """
    config_path = ''
    if item:
        if item.tool_type == Names.HDA:
            config_path = Names.otls
        elif item.tool_type == Names.Shelf:
            config_path = Names.Shelf
        elif item.tool_type in [Names.hip, Names.hiplc, Names.hipnc]:
            config_path = Names.Hip
        elif item.tool_type == Names.Nodes:
            config_path = Names.Nodes
    elif tool:
        if tool.type == Names.HDA:
            config_path = Names.otls
        elif tool.type == Names.Shelf:
            config_path = Names.Shelf
        elif tool.type in [Names.hip, Names.hiplc, Names.hipnc]:
            config_path = Names.Hip
        elif tool.type == Names.Nodes:
            config_path = Names.Nodes

    return config_path

def get_last_version(backup_path):
    """
    get the last version in backup file
    :param backup_path: backup config json path
    :return: max version number in backup path
    """
    if not os.path.exists(backup_path):
        return 1

    max_version = 1

    for version_name in os.listdir(backup_path):
        if version_name == 'config.json':
            continue
        _version = version_name[version_name.rfind('_') + 2:].split('.')[0]
        if int(max_version) < int(_version):
            max_version = int(_version)

    return max_version


class ConfigJson(OrderedDict):
    '''
    ConfigJson is the helper object to store the config data in json format

    'toolsets':
    [{
        'name': 'tool',
        'type': 'hip',   # hip, py, hda
        'menu': 'efx/key',
        'path': 'tool_name.nk'
    }]

    '''

    def __init__(self):
        super(ConfigJson, self).__init__()

        self.info = {"toolsets": []}

    def add_tool(self, tool):
        '''
        :param tool: instance of Tool
        :return:
        '''

        self.info['toolsets'].append(tool.copy())

    def get_all_tools(self):
        tools = []
        for t in self.info['toolsets']:
            tool = ToolSet()
            for key in t:
                t[key] = t[key]
            tool.update(t)
            tools.append(tool)
        return tools

    def update_json(self, old_tool, new_tool):
        for t in self.info['toolsets']:
            if t == old_tool:
                t.update(new_tool)

    def delete_tools(self, tool):
        if tool in self.info['toolsets']:
            self.info['toolsets'].remove(tool)

    def get_all_user(self):
        path = os.path.join(get_toolset_root(), 'users')
        users = []
        if os.path.exists(path):
            files = os.listdir(path)
            for user in files:
                if user == 'backups':
                    continue
                if os.path.isdir(os.path.join(path, user) and user.find('.') < 0):
                    users.append(user)
        users.sort()
        return users

    def load_from_dict(self, src):
        for keyword in src:
            self.info[keyword] = src[keyword]

    def load_from_json(self, path):
        path = os.path.join(path, 'config.json')
        if not os.path.isfile(path):
            raise ConfigNotExists(path)
        try:
            with open(path) as src:
                dst = json.load(src, object_pairs_hook=OrderedDict)
            self.load_from_dict(dst)
        except ValueError as e:
            print('ValueError:' + str(e))

    def write_to_json(self, path):
        path = os.path.join(path, 'config.json')
        dir_path = os.path.dirname(path)
        brpc.change_path_permission(
            dir_path, username="publisher", password="gae6deeX", mode="777", og='ple', recursive=True
        )
        with open(path, 'w') as dst:
            dst.write(self.write_to_string())
        brpc.change_path_permission(
            dir_path, username="publisher", password="gae6deeX", mode="555", og='ple', recursive=True
        )

    def write_to_string(self):
        return json.dumps(self.info, indent=4)


class ToolSet(dict):
    """
    ToolSet is the helper object to store the item data in dict format
    """

    def __init__(self, name='', path='', type='', menu='/', author='', about='', definition='',
                 version='', date='', hda_path='', hda_name='', hou_version=''):

        super(ToolSet, self).__init__()
        self.__dict__ = self

        self.name = name
        self.type = type
        self.menu = menu
        self.path = path
        self.author = author
        self.about = about
        self.definition = definition
        self.version = version
        self.date = date
        self.hda_path = hda_path
        self.hda_name = hda_name
        self.hou_version = hou_version
