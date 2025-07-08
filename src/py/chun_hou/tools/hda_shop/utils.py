class CommonHelper:
    """ the helper to read qss file"""
    def __init__(self):
        pass

    @staticmethod
    def readqss(style):
        with open(style, 'r') as f:
            return f.read()


def create_xmlfile(workspace):
    '''
    create a temp xml file under houdinix.x/toolbar folder
    :param workspace:current user's workspace
    :return:
    '''
    import os
    from xml.dom.minidom import Document
    from . import core
    from . import constants

    current_show = workspace.split('/')[2]
    config_path = os.path.join(
        constants.TOOLFILES_PATH, 'shows', current_show, constants.CurrentLocation
    )

    # delete xml file first
    if os.path.exists(os.path.join(os.environ['HIH'], 'toolbar/temp.shelf')):
        os.remove(os.path.join(os.environ['HIH'], 'toolbar/temp.shelf'))

    # create xml file
    if os.path.exists(os.path.join(config_path, 'config.json')):
        try:
            doc = Document()
            shelf_doc = doc.createElement('shelfDocument')
            doc.appendChild(shelf_doc)

            config_menu = core.ConfigJson()
            config_menu.load_from_json(config_path)
            toolsets = config_menu.get_all_tools()
            for tool in toolsets:
                if tool['type'] == 'HDA':
                    tool_name = doc.createElement('tool')
                    shelf_doc.appendChild(tool_name)

                    tool_level = tool['hda_path']
                    if tool_level == 'Object':
                        tool_level = 'Obj'
                    tool_name.setAttribute('icon', 'SOP_cache')
                    tool_name.setAttribute('label', tool['name'])
                    tool_name.setAttribute('name', tool['hda_name'])
                    tool_submenu = os.path.join(
                        current_show, tool['menu'].lstrip('/')
                    )

                    # add to scene view
                    toolMenuContext_viewer = doc.createElement('toolMenuContext')
                    toolMenuContext_viewer.setAttribute('name', 'viewer')
                    contextNetType_viewer = doc.createElement('contextNetType')
                    contextNetType_viewer_text = doc.createTextNode(
                        str(tool_level).upper()
                    )
                    tool_name.appendChild(toolMenuContext_viewer)
                    toolMenuContext_viewer.appendChild(contextNetType_viewer)
                    contextNetType_viewer.appendChild(contextNetType_viewer_text)

                    # add to network editor view
                    toolMenuContext_network = doc.createElement('toolMenuContext')
                    toolMenuContext_network.setAttribute('name', 'network')
                    contextNetType_network = doc.createElement('contextNetType')
                    contextNetType_network_text = doc.createTextNode(
                        str(tool_level).upper()
                    )
                    tool_name.appendChild(toolMenuContext_network)
                    toolMenuContext_network.appendChild(contextNetType_network)
                    contextNetType_network.appendChild(contextNetType_network_text)

                    # add level in tab menu
                    toolSubmenu = doc.createElement('toolSubmenu')
                    toolSubmenu_text = doc.createTextNode(
                        str(tool_submenu).rstrip('/')
                    )
                    tool_name.appendChild(toolSubmenu)
                    toolSubmenu.appendChild(toolSubmenu_text)

                    code = (
                        'networkeditor = hou.ui.paneTabOfType'
                        '(hou.paneTabType.NetworkEditor)\n'
                        'select_nodes = hou.selectedNodes()\n'
                        'current_level = networkeditor.pwd().path()\n'
                        'current_node = hou.node(current_level).createNode("{0}")\n'
                        'current_node.moveToGoodPosition()')\
                        .format(tool['hda_name'])
                    script = doc.createElement('script')
                    script.setAttribute('scriptType', 'python')
                    script_text = doc.createCDATASection(str(code))
                    tool_name.appendChild(script)
                    script.appendChild(script_text)

            xmlfile = open(os.path.join(
                os.environ['HIH'], 'toolbar/temp.shelf'), 'w+'
            )
            doc.writexml(xmlfile, newl='\n', addindent='  ', encoding='UTF-8')
            xmlfile.close()
        except ValueError as e:
            print("create temp.shelf failed\nError:" + str(e))
        except IOError as e:
            print("create temp.shelf failed\nError:" + str(e))

def get_filtered_directory_contents(root_dir, filter_type=None):
    """
    Retrieve a list of folder names or file names under the specified directory based on the given filter.

    This function fetches either the names of directories or files within a specified root directory.
    Hidden directories (those starting with '.') are excluded from the results. If an error occurs,
    it prints the exception and returns ["None"] as a fallback.

    :param str root_dir: Path to the root directory where folders or files will be listed.
                         Must be a valid directory path for expected behavior.
    :param filter_type: Optional parameter indicating the filtering criteria:
                        - If set to "dir", only subdirectories are returned.
                        - If set to a file extension (e.g., ".txt"), only matching files are returned.
                        - If not provided, all non-hidden files and directories are returned.

    :return: A list of strings representing folder or file names based on the filter.
             Returns ["None"] in case of an OSError.
    :rtype: list[str]
    """
    from bfx_core.compat import Path
    if filter_type == "dir":
        try:
            name_list = [dir.name for dir in Path(root_dir).iterdir() if not dir.name.startswith('.')]
        except OSError as e:
            print(e)
            name_list = ["None"]
    else:
        try:
            name_list = [file.name for file in Path(root_dir).iterdir() if file.name.endswith(filter_type)]
        except OSError as e:
            name_list = ["None"]

    return name_list