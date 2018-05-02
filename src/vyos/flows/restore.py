from cloudshell.devices.flows.action_flows import RestoreConfigurationFlow

from vyos.command_actions.system_actions import SystemActions


class VyOSRestoreFlow(RestoreConfigurationFlow):
    def __init__(self, cli_handler, logger):
        super(VyOSRestoreFlow, self).__init__(cli_handler, logger)

    def execute_flow(self, path, configuration_type, restore_method, vrf_management_name):
        """Execute flow which save selected file to the provided destination

        :param path: the path to the configuration file, including the configuration file name
        :param restore_method: the restore method to use when restoring the configuration file.
                               Possible Values are append and override
        :param configuration_type: the configuration type to restore. Possible values are startup and running
        :param vrf_management_name: Virtual Routing and Forwarding Name
        """
        with self._cli_handler.get_cli_service(self._cli_handler.config_mode) as config_session:
            sys_actions = SystemActions(config_session, self._logger)
            load_action_map = sys_actions.prepare_action_map(path, configuration_type)
            sys_actions.load(path=path,
                             action_map=load_action_map)
            sys_actions.commit()
            sys_actions.save(destination="")
