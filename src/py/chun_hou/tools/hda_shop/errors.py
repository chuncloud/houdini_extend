from bfx.util.error import BFXException


class ConfigNotExists(BFXException):
    def __init__(self, project):

        super(ConfigNotExists, self).__init__(
            u'Config file {} does not exists!'.format(project)
        )
