from random import randint
import re


from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor
from cloudshell.devices.autoload.autoload_builder import AutoloadDetailsBuilder

from vyos.autoload import models
from vyos.cli import command_templates


class VyOSAutoloadFlow(object):
    def __init__(self, cli_handler, resource_config, logger):
        """

        :param cli_handler:
        :param resource_config:
        :param logger:
        """
        self._cli_handler = cli_handler
        self._resource_config = resource_config
        self._logger = logger

    def execute_flow(self):
        """

        :return:
        """
        with self._cli_handler.get_cli_service(self._cli_handler.default_mode) as session:
            output = CommandTemplateExecutor(session,
                                             command_templates.SHOW_INTERFACES,
                                             ).execute_command()

            root_resource = models.GenericDeployedApp(shell_name=self._resource_config.shell_name,
                                                      name="VyOS Deployed App",
                                                      unique_id=randint(1000, 9999))  # todo: get unique id somehow

            interfaces_data = re.search(r".*[-]{2,}(.*)lo", output,
                                        re.DOTALL).groups()[0].split("\n")

            for interface_data in interfaces_data:
                interface_name_match = re.search(r"(?P<interface_name>[a-zA-Z0-9.]+?)[ ]{2,}.*", interface_data)
                if interface_name_match:
                    interface_name = interface_name_match.group("interface_name")
                    unique_id = hash(interface_name)
                    port = models.GenericVPort(shell_name=self._resource_config.shell_name,
                                               name=interface_name,
                                               unique_id=unique_id)

                    root_resource.add_sub_resource(unique_id, port)

            return AutoloadDetailsBuilder(root_resource).autoload_details()
