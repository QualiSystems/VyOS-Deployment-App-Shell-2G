from collections import OrderedDict

from cloudshell.cli.command_template.command_template import CommandTemplate


DEFAULT_ERROR_MAP = OrderedDict((("error:", "Error happens while executing CLI command"),))


def prepare_error_map(error_map=None):
    """

    :param collections.OrderedDict error_map:
    :rtype: collections.OrderedDict
    """
    if error_map is None:
        error_map = OrderedDict()

    error_map.update(DEFAULT_ERROR_MAP)
    return error_map


SAVE_CONFIGURATION = CommandTemplate("save {destination_file_path}", error_map=prepare_error_map(
    error_map=OrderedDict((("[Ee]rror saving", "Failed to save configuration file"),))))

LOAD_CONFIGURATION = CommandTemplate("load {source_file_path}", error_map=prepare_error_map(
    error_map=OrderedDict((("[Cc]an not open", "Unable to open remote configuration file. "
                                               "Please check that config file link is correct"),))))

COMMIT = CommandTemplate("commit", error_map=prepare_error_map())

SHOW_INTERFACES = CommandTemplate("show interfaces", error_map=prepare_error_map())
