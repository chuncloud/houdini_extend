# -*- coding: utf-8 -*-
"""
该模块提供用于处理节点创建，修改，查询，连接，选中等和节点相关函数

===============================================================================

This module provides functions for node creation, modification,
querying, connection, selection and other node-related operations.


"""

# Standard library imports
# -----------------------
import hou
import os
import toolutils
import logging
import functools
from datetime import datetime
# Related third party imports
# ---------------------------



def focus_network_editor_to(node):
    """
    Focuses the network editor view on the specified node
    This function will select the target node and center the network editor view on it
    Args:
        node (hou.Node): The Houdini node object to focus on
    将网络编辑器视图聚焦到指定节点
    该函数会选中指定节点并将网络编辑器视图居中显示该节点
    Args:
        node (hou.Node): 需要聚焦的Houdini节点对象
    """
    hou.clearAllSelected()
    try:
        node.setSelected(True)
    except hou.ObjectWasDeleted as error:
        return
    for ui in hou.ui.currentPaneTabs():
        if ui.type() == hou.paneTabType.NetworkEditor:
            ui.homeToSelection()
            break


def get_node_type_name(node):  # todo: remove
    """
    get the type name of the input node
    the namespace of node should be like this,'bfx::bfx_cache::4.0' or 'filecache'
    then the type name is 'bfx_cache' or 'filecache'

    :param node: it can be the houdini node or the path of the houdini node
    :return: (string) the type name of the input node
    """
    if isinstance(node, str):
        node_path = node
        node = hou.node(node_path)

    if isinstance(node, hou.Node):
        node_type_name = node.type().nameComponents()[-2]
        return node_type_name
    else:
        raise ValueError("unknown input:{}".format(node))


def get_node_type_version(node):
    """
    get the type version of the input node
    the namespace of node should be like this,'bfx::bfx_cache::4.0' or 'filecache'
    then the type name is '4.0' or ''

    :param node: it can be the houdini node or the path of the houdini node
    :return: (string) the type version of the input node
    """
    if isinstance(node, str):
        node_path = node
        node = hou.node(node_path)

    if isinstance(node, hou.Node):
        node_type_version = node.type().nameComponents()[-1]
        return node_type_version
    else:
        raise ValueError("unknown input:{}".format(node))


def get_node_network(node):
    """
    Retrieves the network type (context) of the given Houdini node.

    This function determines the network context (e.g., 'Object', 'SOP', 'DOP')
    in which the specified node resides. It accepts either a hou.Node object
    or a string path to a node.

    :param node: The node or its path for which to retrieve the network type.
    :type node: hou.Node or str

    :return: The name of the network type/category the node belongs to.
    :rtype: str

    :raises ValueError: If the input is neither a valid hou.Node nor a string path.
    """
    if isinstance(node, str):
        node_path = node
        node = hou.node(node_path)

    if isinstance(node, hou.Node):
        node_net_work = node.childTypeCategory().name()
        return node_net_work
    else:
        raise ValueError("unknown input:{}".format(node))


def log_to_file(func):  # todo: will remove to bfx_core/scrc/py/bfx_core/log.py
    """
    A decorator that enables logging functionality for the decorated function by writing logs to a file.

    This decorator allows the decorated function to automatically generate a log file to record execution details.
    The log file path can either be customized through parameters or default to a temporary directory.
    Additionally, it ensures proper setup and cleanup of logging handlers to avoid memory leaks.

    :param func: The function to be decorated with logging capabilities.
    :type func: function

    :return: The wrapped function with added logging behavior.
    :rtype: function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        Wrapper function that configures the logger, executes the target function,
        and cleans up resources after execution.

        Accepts an optional 'custom_logger_path' parameter in kwargs to define where the log file is saved.
        If not provided, defaults to '/tmp/hou_traverse_nodes/' with a timestamped filename.
        """
        # Check if a custom log file path is provided
        custom_logger_path = kwargs.pop("custom_logger_path", None)

        if custom_logger_path:
            # Create necessary directories if they don't exist
            if not os.path.exists(custom_logger_path):
                os.makedirs(os.path.dirname(custom_logger_path))
            log_file = custom_logger_path
        else:
            # Set default log directory
            log_dir = "/tmp/hou_traverse_nodes/"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Generate timestamped log filename based on function name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S.%f')
            log_file = os.path.join(
                log_dir, "{}_{}.log".format(func.__name__, timestamp)
            )

        # Configure logger
        logger_name = func.__name__
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        # Setup file handler for logging
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Inject logger into function's kwargs
        kwargs['logger'] = logger

        # Execute the decorated function
        result = func(*args, **kwargs)

        # Clean up logging resources
        logger.removeHandler(file_handler)
        file_handler.close()

        return result

    return wrapper


def get_topmost_upstream_nodes(start_node,
                               is_search_lockedHDA=False,
                               valid_node_types=None,
                               stop_by_loadfromdisk=False):
    """
    The underlying function calls get_valid_upstream_nodes,
    Finds all nodes that meet the criteria.
    Nodes without upstream connections are considered top-level nodes
    Returns the topmost valid nodes in the node network:
    底层调用get_valid_upstream_nodes,
    查找所有的符合条件的节点，如果节点没有上游节点则算是最上层节点
    返回节点网络里最上层（topmost）的那些有效节点：
    :param start_node: The node that starts to traverse
    :param is_search_lockedHDA: default False if True search lockedHDA.
    :param valid_node_types: Node type list, to filter invalid nodes,
                            if node_types == None, return all upstream nodes
    :param stop_by_loadfromdisk: to control if need to search upstream nodes of loadfromdisk node,
                                 default value is False,if u want to stop search, need like this
                                 stop_by_loadfromdisk=True
    :return: topmost: set() return the topmost nodes
    """
    # 第一步：拿到所有符合条件的上游节点
    valid_nodes = get_valid_upstream_nodes(start_node,
                                           is_search_lockedHDA=is_search_lockedHDA,
                                           valid_node_types=valid_node_types,
                                           stop_by_loadfromdisk=stop_by_loadfromdisk,
                                           return_node_object=True)

    topmost = set()
    for node_obj in valid_nodes:
        # 如果根本没有 inputs，就肯定是顶层节点
        if not node_obj.inputs():
            topmost.add(node_obj)

    return topmost


@log_to_file
def get_valid_upstream_nodes(start_node, is_search_lockedHDA=False, valid_node_types=None,
                             logger=None, return_node_object=False, stop_by_loadfromdisk=False,
                             ignore_stop_by_loadfromdisk_nodes=None):
    """
    It will generate a log file to record loop upstream nodes history auto,
    the log file will under this folder, /tmp/hou_traverse_nodes/
    and the log file name is the time when we start to run this function.
    If you want to custom logger file path at "/xxxxx/xxxx.log", can do like this:
        get_valid_upstream_nodes(start_node, custom_logger_path="/xxxxx/xxxx.log")

    :param start_node: The node that starts the traversal
    :param is_search_lockedHDA: Default False. If True, search inside locked HDAs
    :param valid_node_types: List of node types to filter valid nodes.
                             If None, returns all upstream nodes.
    :param logger: Logger instance passed by the decorator
    :param return_node_object: Default False. If True, returns hou.Node objects instead of paths
    :param stop_by_loadfromdisk: Default False. If True, stops traversal at nodes with enable "loadfromdisk" parameter
    :param ignore_stop_by_loadfromdisk_nodes: Default None (converted to empty set internally).
                                             List of node paths to exclude from stop-by-loadfromdisk behavior.
    :return: Set of valid nodes (paths if return_node_object=False, hou.Node objects if True)

    Usable Tips:
    1. Get all upstream node paths:
        get_valid_upstream_nodes(start_node)
    2. Get all upstream node objects:
        get_valid_upstream_nodes(start_node, return_node_object=True)
    3. Search locked HDAs:
        get_valid_upstream_nodes(start_node, is_search_lockedHDA=True)
    4. Filter specific node types:
        get_valid_upstream_nodes(start_node, valid_node_types=["filecache", "alembic"])
    5. Stop at loadfromdisk nodes:
        get_valid_upstream_nodes(start_node, stop_by_loadfromdisk=True)
    6. Ignore specific nodes in stop-by-loadfromdisk:
        get_valid_upstream_nodes(start_node, stop_by_loadfromdisk=True,
                                ignore_stop_by_loadfromdisk_nodes=['/obj/geo1/filecache1'])

    Note:
    - Traversal skips visited nodes and nodes inside locked HDAs (when is_search_lockedHDA=False)
    """
    valid_nodes = set()
    traversed_node = set()
    if ignore_stop_by_loadfromdisk_nodes is None:
        ignore_stop_by_loadfromdisk_nodes = set()

    __get_upstream_nodes(start_node, is_search_lockedHDA, traversed_node, valid_nodes,
                         valid_node_types, logger, stop_by_loadfromdisk,
                         ignore_stop_by_loadfromdisk_nodes)
    if return_node_object:
        valid_nodes = {hou.node(node_path) for node_path in valid_nodes}
        traversed_node = {hou.node(node_path) for node_path in traversed_node}

    # TODO: to let traversed_node become the order list
    if logger:
        logger.info("**********************************")
        logger.info("start_node.path():\n{}".format(start_node.path()))
        logger.info("is_search_lockedHDA:\n{}".format(is_search_lockedHDA))
        logger.info("traversed_node:\n{}".format(traversed_node))
        logger.info("valid_nodes:\n{}".format(valid_nodes))
        logger.info("valid_node_types:\n{}".format(str(valid_node_types)))
        logger.info("stop_by_loadfromdisk:\n{}".format(stop_by_loadfromdisk))
        logger.info("ignore_stop_by_loadfromdisk_nodes:\n{}".format(ignore_stop_by_loadfromdisk_nodes))
        logger.info("**********************************")
    else:
        print("**********************************")
        print("start_node.path():\n{}".format(start_node.path()))
        print("is_search_lockedHDA:\n{}".format(is_search_lockedHDA))
        print("traversed_node:\n{}".format(traversed_node))
        print("valid_nodes:\n{}".format(valid_nodes))
        print("valid_node_types:\n{}".format(str(valid_node_types)))
        print("stop_by_loadfromdisk:\n{}".format(stop_by_loadfromdisk))
        print("ignore_stop_by_loadfromdisk_nodes:\n{}".format(ignore_stop_by_loadfromdisk_nodes))
        print("**********************************")
    return valid_nodes


def __get_upstream_nodes(node, is_search_lockedHDA, traversed_node, valid_nodes,
                         valid_node_types, logger=None, stop_by_loadfromdisk=False,
                         ignore_stop_by_loadfromdisk_nodes=None):
    """
    :param node: the node object
    :param traversed_node: set()  to records node path that have been traversed
    :param valid_nodes: set()  to records node that is valid
    :param valid_node_types: node type list, to filter invalid nodes,
                            if node_types == None, return all upstream nodes
    :param logger: logger, passed in by the decorator
    :param stop_by_loadfromdisk: to control if you need to search upstream nodes of loadfromdisk node
    """
    if not node:
        return

    if node.path() in traversed_node:
        return

    if node.isInsideLockedHDA() and not is_search_lockedHDA:
        # some node in locked HDA do not need to get node parms
        return

    traversed_node.add(node.path())
    if logger:
        logger.info("================================================================")
        logger.info("get_upstream_nodes - node.path():\n{}".format(node.path()))
        logger.info("================================================================")
        logger.info("\n\n")

    node_type = get_node_type_name(node)
    if not valid_node_types:
        valid_nodes.add(node.path())
    else:
        if node_type in valid_node_types:
            valid_nodes.add(node.path())

    if (stop_by_loadfromdisk and
            node.parm("loadfromdisk") and
            node.evalParm("loadfromdisk") and
            os.path.exists(get_filepath_from_node(node))):
        if node.path() not in ignore_stop_by_loadfromdisk_nodes:
            return

    # force to update node references
    for parm in node.parms():
        if parm.parmTemplate().type() != hou.parmTemplateType.String:
            continue
        try:
            parm.pressButton()
        except Exception:
            pass

    if node.references():
        for reference_node in node.references():
            if reference_node == node: continue
            __get_upstream_nodes(reference_node, is_search_lockedHDA, traversed_node, valid_nodes,
                                 valid_node_types, logger, stop_by_loadfromdisk,
                                 ignore_stop_by_loadfromdisk_nodes)

    if node.inputs():
        for upstream_node in node.inputs():
            __get_upstream_nodes(upstream_node, is_search_lockedHDA, traversed_node, valid_nodes,
                                 valid_node_types, logger, stop_by_loadfromdisk,
                                 ignore_stop_by_loadfromdisk_nodes)

    if node_type in ["export_setting", "render_setting"]:
        for output_node in node.outputs():
            __get_upstream_nodes(output_node, is_search_lockedHDA, traversed_node, valid_nodes,
                                 valid_node_types, logger, stop_by_loadfromdisk,
                                 ignore_stop_by_loadfromdisk_nodes)

    if node_type in ["instancer", "subnet", "geo"]:
        output_nodes = get_subnet_output_nodes(node)
        for output_node in output_nodes:
            __get_upstream_nodes(output_node, is_search_lockedHDA, traversed_node, valid_nodes,
                                 valid_node_types, logger, stop_by_loadfromdisk,
                                 ignore_stop_by_loadfromdisk_nodes)

    # Optimize part to cover Houdini Artists:
    if node_type in ["dopio", "dopimportfield", "dopimportrecords"]:
        dop_node = node.parm('doppath').evalAsNode()
        __get_upstream_nodes(dop_node, is_search_lockedHDA, traversed_node, valid_nodes,
                             valid_node_types, logger, stop_by_loadfromdisk,
                             ignore_stop_by_loadfromdisk_nodes)

    if node_type == "object_merge":
        nodes_path = get_multi_parm_list_path(node, "numobj", "objpath")
        for node_path in nodes_path:
            try:
                node_path = get_abs_node_path(node, node_path)
                reference_node = hou.node(node_path)
                if reference_node:
                    if get_node_type_name(reference_node) == 'geo':
                        reference_node = reference_node.renderNode()
                else:
                    reference_node = None
            except AttributeError as e:
                reference_node = None
            __get_upstream_nodes(reference_node, is_search_lockedHDA, traversed_node, valid_nodes,
                                 valid_node_types, logger, stop_by_loadfromdisk,
                                 ignore_stop_by_loadfromdisk_nodes)

    if node_type == "sopimport":
        sop_node = node.parm("soppath").evalAsNode()
        __get_upstream_nodes(sop_node, is_search_lockedHDA, traversed_node, valid_nodes,
                             valid_node_types, logger, stop_by_loadfromdisk,
                             ignore_stop_by_loadfromdisk_nodes)

    if node_type == "sceneimport":
        object_nodes = node.parm("objects").evalAsNodes()
        force_object_nodes = node.parm("forceobjects").evalAsNodes()
        exclude_object_nodes = node.parm("excludeobjects").evalAsNodes()
        all_nodes = object_nodes + force_object_nodes + exclude_object_nodes
        for geo_node in all_nodes:
            start_node = geo_node.renderNode()
            __get_upstream_nodes(start_node, is_search_lockedHDA, traversed_node, valid_nodes,
                                 valid_node_types, logger, stop_by_loadfromdisk,
                                 ignore_stop_by_loadfromdisk_nodes)


def get_subnet_output_nodes(parent_node):
    """
    first, try to get all the output node inside the parent_node
    second, try to get the rendernode
    third, try to get the displaynode
    finally, try to get all the node that not have output nodes

    return: output_nodes = [node1, node2, ...]
    """

    # output_nodes = [] or [node1, node2, ...]
    output_nodes = toolutils.findAllChildNodesOfType(parent_node, "output")
    if output_nodes == []:
        if hasattr(parent_node, "renderNode") and parent_node.renderNode():
            # some node not have render node attribute
            output_nodes.append(parent_node.renderNode())
        elif hasattr(parent_node, "displayNode") and parent_node.displayNode():
            output_nodes.append(parent_node.displayNode())
        else:
            for child_node in parent_node.children():
                if not child_node.outputs():
                    output_nodes.append(child_node)

    return output_nodes
