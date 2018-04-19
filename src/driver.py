from cloudshell.core.context.error_handling_context import ErrorHandlingContext
from cloudshell.devices.autoload.autoload_builder import AutoloadDetailsBuilder
from cloudshell.devices.driver_helper import get_api
from cloudshell.devices.driver_helper import get_cli
from cloudshell.devices.driver_helper import get_logger_with_thread_id
from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_utils import GlobalLock


from vyos.autoload import models
from vyos.cli.handler import VyOSCliHandler
from vyos.configuration_attributes_structure import VyOSResource
from vyos.runners.configuration import VyOSConfigurationRunner


SHELL_TYPE = "CS_GenericDeployedApp"
SHELL_NAME = "Vyos"


class VyosDriver(ResourceDriverInterface, GlobalLock):
    def __init__(self):
        """Constructor must be without arguments, it is created with reflection at run time"""
        super(VyosDriver, self).__init__()
        self._cli = None

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        resource_config = VyOSResource.from_context(context=context,
                                                    shell_type=SHELL_TYPE,
                                                    shell_name=SHELL_NAME)

        self._cli = get_cli(resource_config.sessions_concurrency_limit)
        return "Finished initializing"

    def cleanup(self):
        """Destroy the driver session, this function is called everytime a driver instance is destroyed

        This is a good place to close any open sessions, finish writing to log files
        """
        pass

    @GlobalLock.lock
    def get_inventory(self, context):
        """Discovers the resource structure and attributes.

        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """
        logger = get_logger_with_thread_id(context)
        logger.info("Autoload")

        with ErrorHandlingContext(logger):
            resource_config = VyOSResource.from_context(context=context,
                                                        shell_type=SHELL_TYPE,
                                                        shell_name=SHELL_NAME)

            if resource_config.config_file:
                api = get_api(context)
                cli_handler = VyOSCliHandler(cli=self._cli,
                                             resource_config=resource_config,
                                             api=api,
                                             logger=logger)

                configuration_operations = VyOSConfigurationRunner(cli_handler=cli_handler,
                                                                   logger=logger,
                                                                   resource_config=resource_config,
                                                                   api=api)
                logger.info('Load configuration started')
                configuration_operations.restore(path=path)
                logger.info('Load configuration completed')

            root_resource = models.GenericDeployedApp(shell_name=resource_config.shell_name,
                                                      name="VyOS Deployed App",
                                                      unique_id=100500)
            port1 = models.GenericVPort(shell_name=resource_config.shell_name,
                                        name="VyOS Port 1",
                                        unique_id=100600)
            port1.mac_address = "02:42:7a:e0:8f:6f"
            port1.requested_vnic_name = "2"

            root_resource.add_sub_resource(100600, port1)
            logger.info("Autoload completed")

            return AutoloadDetailsBuilder(root_resource).autoload_details()

    def save(self, context, folder_path):
        """Save selected file to the provided destination

        :param ResourceCommandContext context: ResourceCommandContext object with all Resource Attributes inside
        :param folder_path: destination path where file will be saved
        :return str saved configuration file name:
        """

        logger = get_logger_with_thread_id(context)
        logger.info("Save configuration")

        with ErrorHandlingContext(logger):

            resource_config = VyOSResource.from_context(context=context,
                                                        shell_type=SHELL_TYPE,
                                                        shell_name=SHELL_NAME)

            api = get_api(context)
            cli_handler = VyOSCliHandler(cli=self._cli,
                                         resource_config=resource_config,
                                         api=api,
                                         logger=logger)

            configuration_operations = VyOSConfigurationRunner(cli_handler=cli_handler,
                                                               logger=logger,
                                                               resource_config=resource_config,
                                                               api=api)
            logger.info("Save started")
            response = configuration_operations.save(folder_path=folder_path)
            logger.info("Save completed")
            return response

    @GlobalLock.lock
    def restore(self, context, path):
        """Restore selected file to the provided destination

        :param ResourceCommandContext context: ResourceCommandContext object with all Resource Attributes inside
        :param path: source config file
        """

        logger = get_logger_with_thread_id(context)
        logger.info("Restore configuration")

        with ErrorHandlingContext(logger):

            resource_config = VyOSResource.from_context(context=context,
                                                        shell_type=SHELL_TYPE,
                                                        shell_name=SHELL_NAME)

            api = get_api(context)
            cli_handler = VyOSCliHandler(cli=self._cli,
                                         resource_config=resource_config,
                                         api=api,
                                         logger=logger)

            configuration_operations = VyOSConfigurationRunner(cli_handler=cli_handler,
                                                               logger=logger,
                                                               resource_config=resource_config,
                                                               api=api)
            logger.info('Restore started')
            configuration_operations.restore(path=path)
            logger.info('Restore completed')


if __name__ == "__main__":
    import mock, json
    from cloudshell.shell.core.driver_context import ResourceCommandContext, ResourceContextDetails, \
        ReservationContextDetails

    address = '192.168.42.157'

    user = 'vyos'
    password = 'vyos'
    port = 443
    scheme = "https"
    auth_key = 'h8WRxvHoWkmH8rLQz+Z/pg=='
    api_port = 8029

    context = ResourceCommandContext(*(None,)*4)
    context.resource = ResourceContextDetails(*(None,)*13)
    context.resource.name = 'tvm_m_2_fec7-7c42'
    context.resource.fullname = 'tvm_m_2_fec7-7c42'
    context.reservation = ReservationContextDetails(*(None,)*7)
    context.reservation.reservation_id = '0cc17f8c-75ba-495f-aeb5-df5f0f9a0e97'
    context.resource.attributes = {}
    context.resource.attributes['{}.User'.format(SHELL_NAME)] = user
    context.resource.attributes['{}.Password'.format(SHELL_NAME)] = password
    context.resource.attributes['{}.Configuration File'.format(SHELL_NAME)] = "scp://root:Password1@192.168.42.252/root/copied_file_11.boot"
    context.resource.address = address
    context.resource.app_context = mock.MagicMock(app_request_json=json.dumps(
        {
            "deploymentService": {
                "cloudProviderName": "vcenter_333"
            }
        }))

    context.connectivity = mock.MagicMock()
    context.connectivity.server_address = "192.168.85.23"

    dr = VyosDriver()
    dr.initialize(context)

    # result = dr.get_inventory(context)
    #
    # for res in result.resources:
    #     print res.__dict__

    with mock.patch('__main__.get_api') as get_api:
        get_api.return_value = type('api', (object,), {
            'DecryptPassword': lambda self, pw: type('Password', (object,), {'Value': pw})()})()

        folder_path = "scp://vyos:vyos@192.168.42.157/copied_file_11.boot"  # fail
        folder_path = "ftp://speedtest.tele2.net/vyos-test.config.boot"  # fail
        folder_path = "ftp://speedtest.tele2.net/upload"  # good

        path = "ftp://speedtest.tele2.net/vyos-test.config.boot"  # fail
        path = "scp://vyos:vyos@192.168.42.157/copied_file_11.boot"  # fail
        path = "ftp://speedtest.tele2.net/2MB.zip" # good upload/fail commit
        path = "scp://root:Password1@192.168.42.252/root/copied_file_11.boot"  # good

        # dr.save(context=context,
        #         folder_path=folder_path,
        #         configuration_type=None,
        #         vrf_management_name=None)

        dr.restore(context=context,
                   path=path,
                   restore_method=None,
                   configuration_type=None,
                   vrf_management_name=None)
