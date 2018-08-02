from datetime import datetime
from datetime import timedelta
from functools import wraps
import json
import os
import time

from cloudshell.cli.session_manager_impl import SessionManagerException
from cloudshell.core.context.error_handling_context import ErrorHandlingContext
from cloudshell.devices.driver_helper import get_api
from cloudshell.devices.driver_helper import get_cli
from cloudshell.devices.driver_helper import get_logger_with_thread_id
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.shell.core.driver_utils import GlobalLock

from vyos.cli.handler import VyOSCliHandler
from vyos.configuration_attributes_structure import VyOSResource
from vyos.deployment.post_boot_vm_configure import PostBootVMConfigureOperation
from vyos.runners.configuration import VyOSConfigurationRunner
from vyos.runners.autoload import VyOSAutoloadRunner


SHELL_TYPE = "CS_GenericDeployedApp"
SHELL_NAME = "Vyos"

SSH_WAITING_TIMEOUT = 20 * 60
SSH_WAITING_INTERVAL = 5 * 60

CLEAR_NIC_HW_ID_SCRIPT_PATH = "vyos/vm_scripts/clear-nic-hw-id.pl"


def unstable_ssh(f, timeout=SSH_WAITING_TIMEOUT, interval=SSH_WAITING_INTERVAL):
    @wraps(f)
    def wrapper(*args, **kwargs):
        timeout_time = datetime.now() + timedelta(seconds=timeout)
        logger = kwargs["logger"]

        while True:
            logger.info("Trying to execute operation with CLI command(s)...")

            try:
                return f(*args, **kwargs)
            except SessionManagerException:  # note: it may catch CLI errors, unrelated to the connectivity
                logger.info("Unable to get CLI session", exc_info=True)

                if datetime.now() > timeout_time:
                    raise Exception("Unable to get CLI session within {} minute(s)"
                                    .format(timeout / 60))
            time.sleep(interval)

    return wrapper


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

    @unstable_ssh
    def _execute_load_config_flow(self, resource_config, cli_handler, cs_api, logger):
        """

        :param resource_config:
        :param cli_handler:
        :param cs_api:
        :param logger:
        :return:
        """
        configuration_operations = VyOSConfigurationRunner(cli_handler=cli_handler,
                                                           logger=logger,
                                                           resource_config=resource_config,
                                                           api=cs_api)
        logger.info('Load configuration flow started')
        configuration_operations.restore(path=resource_config.config_file)
        logger.info('Load configuration flow completed')

    @unstable_ssh
    def _execute_autoload_flow(self, resource_config, cli_handler, logger):
        """

        :param resource_config:
        :param cli_handler:
        :param logger:
        :return:
        """
        autoload_runner = VyOSAutoloadRunner(cli_handler=cli_handler,
                                             logger=logger,
                                             resource_config=resource_config)
        logger.info("Autoload flow started")
        autoload_details = autoload_runner.discover()
        logger.info("Autoload flow completed. Discovered details {}".format(autoload_details))

        return autoload_details

    @GlobalLock.lock
    def get_inventory(self, context):
        """Discovers the resource structure and attributes.

        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """
        logger = get_logger_with_thread_id(context)
        logger.info("Autoload command started")

        with ErrorHandlingContext(logger):
            resource_config = VyOSResource.from_context(context=context,
                                                        shell_type=SHELL_TYPE,
                                                        shell_name=SHELL_NAME)
            cs_api = get_api(context)

            if not resource_config.address or resource_config.address.upper() == "NA":
                logger.info("No IP configured, skipping Autoload")
                return AutoLoadDetails([], [])

            cli_handler = VyOSCliHandler(cli=self._cli,
                                         resource_config=resource_config,
                                         api=cs_api,
                                         logger=logger)

            if resource_config.config_file:
                self._execute_load_config_flow(resource_config=resource_config,
                                               cli_handler=cli_handler,
                                               cs_api=cs_api,
                                               logger=logger)

            return self._execute_autoload_flow(resource_config=resource_config,
                                               cli_handler=cli_handler,
                                               logger=logger)

    def vm_post_boot_configure(self, context):
        """Command that will be executed after VM cloning and powering on

        Removes hard-coded MAC addresses in the configuration file
        :param ResourceCommandContext context: the context the command runs on
        """
        logger = get_logger_with_thread_id(context)
        logger.info("Post command started")

        with ErrorHandlingContext(logger):
            resource_config = VyOSResource.from_context(context=context,
                                                        shell_type=SHELL_TYPE,
                                                        shell_name=SHELL_NAME)

            cs_api = get_api(context)
            app_request_data = json.loads(context.resource.app_context.app_request_json)
            vcenter_name = app_request_data["deploymentService"]["cloudProviderName"]

            vm_configure_operation = PostBootVMConfigureOperation(cs_api=cs_api,
                                                                  resource_config=resource_config,
                                                                  vcenter_name=vcenter_name,
                                                                  logger=logger)

            vm_configure_operation.wait_for_vm()

            dirname = os.path.dirname(__file__)
            filename = os.path.join(dirname, CLEAR_NIC_HW_ID_SCRIPT_PATH)

            vm_configure_operation.apply_clear_nic_hw_id_script(script_path=filename)
            vm_configure_operation.reboot_vm()

            if resource_config.enable_ssh:
                vm_configure_operation.enable_ssh()

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
    import mock
    from cloudshell.shell.core.driver_context import ResourceCommandContext, ResourceContextDetails, \
        ReservationContextDetails

    # address = '192.168.42.231'
    address = "192.168.41.85"

    user = 'vyos'
    password = 'vyos'
    port = 443
    scheme = "https"
    auth_key = 'h8WRxvHoWkmH8rLQz+Z/pg=='
    api_port = 8029

    context = ResourceCommandContext(*(None,)*4)
    context.resource = ResourceContextDetails(*(None,)*13)
    context.resource.name = 'vcenter_fresh_9ffc-e5ba'
    context.resource.fullname = 'vcenter_fresh_9ffc-e5ba'
    context.reservation = ReservationContextDetails(*(None,)*7)
    context.reservation.reservation_id = 'c6ba183e-b70d-447d-95f5-4a07521ee5ba'
    context.resource.attributes = {}
    context.resource.attributes['{}.Enable SSH'.format(SHELL_NAME)] = "False"
    context.resource.attributes['{}.User'.format(SHELL_NAME)] = user
    context.resource.attributes['{}.Password'.format(SHELL_NAME)] = password
    # context.resource.attributes['{}.Configuration File'.format(SHELL_NAME)] = "ftp://ftp.uconn.edu/48_hour/tvm_m_2_fec7-7c42-running-260418-163606"
    context.resource.attributes['{}.Configuration File'.format(SHELL_NAME)] = ""
    context.resource.address = address
    context.resource.app_context = mock.MagicMock(app_request_json=json.dumps(
        {
            "deploymentService": {
                "cloudProviderName": "vCenter"
            }
        }))

    context.connectivity = mock.MagicMock()
    context.connectivity.server_address = "192.168.85.28"

    dr = VyosDriver()
    dr.initialize(context)

    # result = dr.get_inventory(context)
    #
    # for res in result.resources:
    #     print res.__dict__

    # with mock.patch('__main__.get_api') as get_api:
    #     get_api.return_value = type('api', (object,), {
    #         'DecryptPassword': lambda self, pw: type('Password', (object,), {'Value': pw})()})()

    folder_path = "scp://vyos:vyos@192.168.42.157/copied_file_11.boot"  # fail
    folder_path = "ftp://speedtest.tele2.net/vyos-test.config.boot"  # fail
    folder_path = "ftp://speedtest.tele2.net/upload"  # good
    folder_path = "ftp://ftp.uconn.edu/48_hour/"  # good
    folder_path = "ftp://ftp.uconn.edu/"

    path = "ftp://speedtest.tele2.net/vyos-test.config.boot"  # fail
    path = "scp://vyos:vyos@192.168.42.157/copied_file_11.boot"  # fail
    path = "ftp://speedtest.tele2.net/2MB.zip" # good upload/fail commit
    path = "scp://root:Password1@192.168.42.252/root/copied_file_11.boot"  # good
    path = "http://192.168.41.65/vyosconfig.txt"

    # print dr.get_inventory(context=context)
    print dr.vm_post_boot_configure(context=context)
        # dr.save(context=context,
        #         folder_path=folder_path)

        # dr.restore(context=context,
        #            path=path)
#

