from cloudshell.devices.runners.configuration_runner import ConfigurationRunner

from vyos.flows.restore import VyOSRestoreFlow
from vyos.flows.save import VyOSSaveFlow


class VyOSConfigurationRunner(ConfigurationRunner):
    @property
    def restore_flow(self):
        return VyOSRestoreFlow(cli_handler=self.cli_handler, logger=self._logger)

    @property
    def save_flow(self):
        return VyOSSaveFlow(cli_handler=self.cli_handler, logger=self._logger)

    @property
    def file_system(self):
        return ""
