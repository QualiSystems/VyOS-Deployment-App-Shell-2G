from cloudshell.devices.flows.action_flows import SaveConfigurationFlow

from vyos.command_actions.system_actions import SystemActions


class VyOSSaveFlow(SaveConfigurationFlow):
    def execute_flow(self, folder_path, configuration_type=None, vrf_management_name=None):
        """Execute flow which save selected file to the provided destination

        :param folder_path: destination path where file will be saved
        :param configuration_type: source file, which will be saved
        :param vrf_management_name: Virtual Routing and Forwarding Name
        :return: saved configuration file name
        """

        with self._cli_handler.get_cli_service(self._cli_handler.config_mode) as config_session:
            save_action = SystemActions(config_session, self._logger)
            action_map = save_action.prepare_action_map(configuration_type, folder_path)
            save_action.save(destination=folder_path,
                             action_map=action_map)
