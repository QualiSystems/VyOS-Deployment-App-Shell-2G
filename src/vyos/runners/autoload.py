from cloudshell.devices.runners.autoload_runner import AutoloadRunner

from vyos.flows.autoload import VyOSAutoloadFlow


class VyOSAutoloadRunner(AutoloadRunner):
    def __init__(self, resource_config, cli_handler, logger):
        """

        :param resource_config:
        :param cli_handler:
        :param logger:
        """
        super(VyOSAutoloadRunner, self).__init__(resource_config)
        self._cli_handler = cli_handler
        self._logger = logger

    @property
    def autoload_flow(self):
        return VyOSAutoloadFlow(cli_handler=self._cli_handler,
                                resource_config=self.resource_config,
                                logger=self._logger)

    def discover(self):
        """

        :return: AutoLoadDetails object
        """
        return self.autoload_flow.execute_flow()
