from cloudshell.cli.command_mode_helper import CommandModeHelper
from cloudshell.devices.cli_handler_impl import CliHandlerImpl

from vyos.cli.command_modes import ConfigCommandMode
from vyos.cli.command_modes import DefaultCommandMode


class VyOSCliHandler(CliHandlerImpl):
    def __init__(self, cli, resource_config, logger, api):
        """

        :param cloudshell.cli.cli.CLI cli: CLI object
        :param traffic.teravm.controller.configuration_attributes_structure.TrafficGeneratorControllerResource resource_config:
        :param logging.Logger logger:
        :param cloudshell.api.cloudshell_api.CloudShellAPISession api: cloudshell API object
        """
        super(VyOSCliHandler, self).__init__(cli, resource_config, logger, api)
        self._modes = CommandModeHelper.create_command_mode()

    @property
    def default_mode(self):
        return self._modes[DefaultCommandMode]

    @property
    def config_mode(self):
        return self._modes[ConfigCommandMode]

    @property
    def enable_mode(self):
        return self.default_mode
