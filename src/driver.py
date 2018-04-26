import json

from cloudshell.core.context.error_handling_context import ErrorHandlingContext
from cloudshell.devices.driver_helper import get_api
from cloudshell.devices.driver_helper import get_cli
from cloudshell.devices.driver_helper import get_logger_with_thread_id
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.shell.core.driver_utils import GlobalLock


from vyos.cli.handler import VyOSCliHandler
from vyos.configuration_attributes_structure import VyOSResource
from vyos.runners.configuration import VyOSConfigurationRunner
from vyos.runners.autoload import VyOSAutoloadRunner

from cloudshell.cp.vcenter.common.vcenter.vmomi_service import pyVmomiService
from pyVim.connect import SmartConnect, Disconnect
import pyVmomi


SHELL_TYPE = "CS_GenericDeployedApp"
SHELL_NAME = "Vyos"
VCENTER_RESOURCE_USER_ATTR = "User"
VCENTER_RESOURCE_PASSWORD_ATTR = "Password"



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

    @staticmethod
    def _get_resource_attribute_value(resource, attribute_name):
        """

        :param resource cloudshell.api.cloudshell_api.ResourceInfo:
        :param str attribute_name:
        """
        for attribute in resource.ResourceAttributes:
            if attribute.Name == attribute_name:
                return attribute.Value

    def _enable_ssh_on_vm(self, context, resource_config, cs_api, logger):
        """

        :param context:
        :param resource_config:
        :param cs_api:
        :param logger:
        :return:
        """
        # get VM uuid of the Deployed App
        deployed_vm_resource = cs_api.GetResourceDetails(resource_config.fullname)
        vmuid = deployed_vm_resource.VmDetails.UID
        logger.info("Deployed TVM Module App uuid: {}".format(vmuid))

        # get vCenter name
        app_request_data = json.loads(context.resource.app_context.app_request_json)
        vcenter_name = app_request_data["deploymentService"]["cloudProviderName"]
        logger.info("vCenter shell resource name: {}".format(vcenter_name))

        vsphere = pyVmomiService(SmartConnect, Disconnect, task_waiter=None)

        # get vCenter credentials
        vcenter_resource = cs_api.GetResourceDetails(resourceFullPath=vcenter_name)
        user = self._get_resource_attribute_value(resource=vcenter_resource,
                                                  attribute_name=VCENTER_RESOURCE_USER_ATTR)

        encrypted_password = self._get_resource_attribute_value(resource=vcenter_resource,
                                                                attribute_name=VCENTER_RESOURCE_PASSWORD_ATTR)

        password = cs_api.DecryptPassword(encrypted_password).Value

        logger.info("Connecting to the vCenter: {}".format(vcenter_name))
        si = vsphere.connect(address=vcenter_resource.Address, user=user, password=password)

        # find Deployed App VM on the vCenter
        vm = vsphere.get_vm_by_uuid(si, vmuid)

        creds = pyVmomi.vim.vm.guest.NamePasswordAuthentication(
            username=resource_config.user,
            password=cs_api.DecryptPassword(resource_config.password).Value)

        logger.info("Enabling SSH service on the Deployed VyOS VM")
        enable_ssh_command = ("#!/bin/vbash\n"
                              "source /opt/vyatta/etc/functions/script-template\n"
                              "configure\n"
                              "set service ssh port 22\n"
                              "commit\n"
                              "save\n"
                              "exit")

        cmdspec = pyVmomi.vim.vm.guest.ProcessManager.ProgramSpec(arguments=enable_ssh_command,
                                                                  programPath="/bin/bash")

        si.content.guestOperationsManager.processManager.StartProgramInGuest(vm=vm, auth=creds, spec=cmdspec)

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

            if not resource_config.address or resource_config.address.upper() == "NA":
                logger.info("No IP configured, skipping Autoload")
                return AutoLoadDetails([], [])

            cs_api = get_api(context)

            if resource_config.enable_ssh:
                self._enable_ssh_on_vm(context=context,
                                       resource_config=resource_config,
                                       cs_api=cs_api,
                                       logger=logger)

            cli_handler = VyOSCliHandler(cli=self._cli,
                                         resource_config=resource_config,
                                         api=cs_api,
                                         logger=logger)

            if resource_config.config_file:
                configuration_operations = VyOSConfigurationRunner(cli_handler=cli_handler,
                                                                   logger=logger,
                                                                   resource_config=resource_config,
                                                                   api=cs_api)
                logger.info('Load configuration flow started')
                configuration_operations.restore(path=resource_config.config_file)
                logger.info('Load configuration flow completed')

            autoload_runner = VyOSAutoloadRunner(cli_handler=cli_handler,
                                                 logger=logger,
                                                 resource_config=resource_config)
            logger.info("Autoload flow started")
            autoload_details = autoload_runner.discover()
            logger.info("Autoload command completed")
            logger.info("Autoload details {}".format(autoload_details))

            return autoload_details

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
    context.resource.name = 'tvm_m_2_fec7-7c42'
    context.resource.fullname = 'tvm_m_2_fec7-7c42'
    context.reservation = ReservationContextDetails(*(None,)*7)
    context.reservation.reservation_id = '0cc17f8c-75ba-495f-aeb5-df5f0f9a0e97'
    context.resource.attributes = {}
    context.resource.attributes['{}.User'.format(SHELL_NAME)] = user
    context.resource.attributes['{}.Password'.format(SHELL_NAME)] = password
    context.resource.attributes['{}.Configuration File'.format(SHELL_NAME)] = "ftp://ftp.uconn.edu/48_hour/tvm_m_2_fec7-7c42-running-260418-163606"
    context.resource.address = address
    context.resource.app_context = mock.MagicMock(app_request_json=json.dumps(
        {
            "deploymentService": {
                "cloudProviderName": "vCenter"
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
        folder_path = "ftp://ftp.uconn.edu/48_hour/"  # good

        path = "ftp://speedtest.tele2.net/vyos-test.config.boot"  # fail
        path = "scp://vyos:vyos@192.168.42.157/copied_file_11.boot"  # fail
        path = "ftp://speedtest.tele2.net/2MB.zip" # good upload/fail commit
        path = "scp://root:Password1@192.168.42.252/root/copied_file_11.boot"  # good
        path = "ftp://ftp.uconn.edu/48_hour/tvm_m_2_fec7-7c42-running-260418-163606"

        print dr.get_inventory(context=context)
        # dr.save(context=context,
        #         folder_path=folder_path)

        # dr.restore(context=context,
        #            path=path)

