
import os
from bfx.util.path import PathConverter


TOOLFILES_PATH = PathConverter.to_current('/sw/PLE/shared/Houdini/toolbar/users/BJ')

SHELF_DIR = os.path.join(os.getenv("HOUDINI_USER_PREF_DIR"), "toolbar")

