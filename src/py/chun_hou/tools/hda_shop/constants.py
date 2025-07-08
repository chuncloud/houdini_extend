from bfx_resources.icons import ICON_DIR
from bfx.env.constants import LocationInfo
from bfx.data.prod.shotgun.production2 import Person
from bfx.util.path import PathConverter
from bfx_hou.tools.hda_shop.utils import get_filtered_directory_contents
import os.path
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path


class Icons:
    """
    this class can provide icons
    """
    ADD_NODE = os.path.join(ICON_DIR, "file", "svg", "ic_file_upload_48px.svg")
    ADD_MENU = os.path.join(ICON_DIR, "file", "svg", "ic_create_new_folder_48px.svg")
    SAVE = os.path.join(ICON_DIR, "content", "svg", "ic_save_48px.svg")
    DELETE = os.path.join(ICON_DIR, "content", "svg", "ic_remove_circle_outline_48px.svg")
    USER = os.path.join(ICON_DIR, 'social', '2x_web', 'ic_group_white_48dp.png')
    HELP = os.path.join(ICON_DIR, 'action', '2x_web', 'ic_help_outline_black_48dp.png')
    UNDO = os.path.join(ICON_DIR, 'content', '2x_web', 'ic_reply_black_48dp.png')
    IMPORT = os.path.join(ICON_DIR, 'action', '2x_web', 'ic_system_update_alt_black_48dp.png')
    UPDATE = os.path.join(ICON_DIR, 'action', '2x_web', 'ic_cached_black_48dp.png')
    SHELF_BACKUP = os.path.join(ICON_DIR, 'file', 'svg', 'ic_folder_open_48px.svg')


class Names:
    """
    this class can provide some common name
    """
    shows = 'shows'
    users = 'users'
    base = 'base'
    bfx = 'bfx'
    backup = 'backup'
    Nodes = 'Nodes'
    HDA = 'HDA'
    hda = 'hda'
    hdalc = 'hdalc'
    hdanc = 'hdanc'
    otls = 'otls'
    otl = 'otl'
    otllc = 'otllc'
    otlnc = 'otlnc'
    Hip = 'Hip'
    hip = 'hip'
    hiplc = 'hiplc'
    hipnc = 'hipnc'
    Shelf = 'Shelf'
    Load = 'Load'


CurrentLocation = LocationInfo.code # BJ

TOOLFILES_PATH = PathConverter.to_current('/sw/PLE/shared/Houdini/hda_shop/')

USER_MEMBER = get_filtered_directory_contents("/sw/PLE/shared/Houdini/hda_shop/users/", filter_type="dir")
SHOW_MEMBER = get_filtered_directory_contents("/sw/PLE/shared/Houdini/hda_shop/shows/", filter_type="dir")

# for now, no use
# EFX_MEMBERS_ACTIVE = [efx_user.login for efx_user in Person.select().where(
#                     ((Person.department == 83) |
#                     (Person.department == 106)),
#                     (Person.status == 'act'),
#                     (Person.location == CurrentLocation))]

BFX_MEMBERS = [user.login for user in Person]
PLE_MEMBERS = [ple_user.login for ple_user in Person.select().where(Person.department == 88)]

PERMISSION_MEMBERS = [permission_user.login for permission_user in Person.select().where(Person.permission_group_id != 8)]

OTL_TYPE = [Names.hda, Names.hdalc, Names.hdanc, Names.otl, Names.otllc, Names.otlnc]
HIP_TYPE = [Names.hip, Names.hiplc, Names.hipnc]

