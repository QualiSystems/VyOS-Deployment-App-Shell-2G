from cloudshell.cli.command_mode import CommandMode


class DefaultCommandMode(CommandMode):
    PROMPT = r'\$'
    ENTER_COMMAND = ''
    EXIT_COMMAND = '\x03'

    def __init__(self):
        super(DefaultCommandMode, self).__init__(DefaultCommandMode.PROMPT,
                                                 DefaultCommandMode.ENTER_COMMAND,
                                                 DefaultCommandMode.EXIT_COMMAND)


class ConfigCommandMode(CommandMode):
    PROMPT = r'#'
    ENTER_COMMAND = 'configure'
    EXIT_COMMAND = 'exit'

    def __init__(self):
        super(ConfigCommandMode, self).__init__(ConfigCommandMode.PROMPT,
                                                ConfigCommandMode.ENTER_COMMAND,
                                                ConfigCommandMode.EXIT_COMMAND)


CommandMode.RELATIONS_DICT = {
    DefaultCommandMode: {
        ConfigCommandMode: {}
    }
}
