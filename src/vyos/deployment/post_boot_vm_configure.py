from datetime import datetime
from datetime import timedelta
from functools import wraps
import time

from cloudshell.cp.vcenter.common.vcenter.vmomi_service import pyVmomiService
import pyVmomi
from pyVim.connect import SmartConnect
from pyVim.connect import Disconnect
import requests


VYOS_CLEAR_VNIC_ID_SCRIPT_PATH = "/config/scripts/clear-nic-hw-id.pl"
PERL_PROGRAM_PATH = "/usr/bin/perl"

VCENTER_RESOURCE_USER_ATTR = "User"
VCENTER_RESOURCE_PASSWORD_ATTR = "Password"

VM_TOOLS_WAITING_TIMEOUT = 20 * 60
VM_TOOLS_WAITING_INTERVAL = 10

GUEST_OPERATIONS_WAITING_TIMEOUT = 20 * 60
GUEST_OPERATIONS_WAITING_INTERVAL = 20


def wait_for_guest_operations(f, timeout=GUEST_OPERATIONS_WAITING_TIMEOUT, interval=GUEST_OPERATIONS_WAITING_INTERVAL):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        timeout_time = datetime.now() + timedelta(seconds=timeout)

        while True:
            try:
                return f(self, *args, **kwargs)
            except pyVmomi.vim.fault.GuestOperationsUnavailable:
                self._logger.info("Unable to perform operation due to GuestOperationsUnavailable Exception",
                                  exc_info=True)

                if datetime.now() > timeout_time:
                    raise Exception("Unable to perform operation due to GuestOperationsUnavailable Exception "
                                    "within {} minute(s)".format(timeout / 60))
            time.sleep(interval)

    return wrapper


class PostBootVMConfigureOperation(object):
    def __init__(self, resource_config, cs_api, vcenter_name, logger):
        """

        :param resource_config:
        :param cs_api:
        :param vcenter_name:
        :param logger:
        """
        self._resource_config = resource_config
        self._cs_api = cs_api
        self._logger = logger
        self._vcenter_service = pyVmomiService(SmartConnect,
                                               Disconnect,
                                               task_waiter=None)

        self._vcenter_si = self._get_vcenter_si(vcenter_service=self._vcenter_service,
                                                cs_api=cs_api,
                                                vcenter_name=vcenter_name)

        vm_uid = self._get_vm_uid(resource_config=resource_config,
                                  cs_api=cs_api,
                                  logger=logger)

        self._vm = self._get_vm(vcenter_service=self._vcenter_service,
                                vm_uid=vm_uid)

        self._vm_creds = self._get_vm_creds(resource_config=resource_config, cs_api=cs_api)

    @staticmethod
    def _get_cs_resource_attribute_value(resource, attribute_name):
        """

        :param resource cloudshell.api.cloudshell_api.ResourceInfo:
        :param str attribute_name:
        """
        for attribute in resource.ResourceAttributes:
            if attribute.Name == attribute_name:
                return attribute.Value

    def _get_vm_uid(self, resource_config, cs_api, logger):
        """

        :param resource_config:
        :param cs_api:
        :param logger:
        :return:
        """
        deployed_vm_resource = cs_api.GetResourceDetails(resource_config.fullname)
        vm_uid = deployed_vm_resource.VmDetails.UID
        logger.info("Deployed App VM uuid: {}".format(vm_uid))

        return vm_uid

    def _get_vm(self, vcenter_service, vm_uid):
        """

        :param vcenter_service:
        :param vm_uid:
        :return:
        """
        return vcenter_service.get_vm_by_uuid(self._vcenter_si, vm_uid)

    def _get_vcenter_si(self, cs_api, vcenter_service, vcenter_name):
        """

        :param cs_api:
        :param vcenter_service:
        :param vcenter_name:
        :return:
        """
        vcenter_resource = cs_api.GetResourceDetails(resourceFullPath=vcenter_name)
        user = self._get_cs_resource_attribute_value(resource=vcenter_resource,
                                                     attribute_name=VCENTER_RESOURCE_USER_ATTR)

        encrypted_password = self._get_cs_resource_attribute_value(resource=vcenter_resource,
                                                                   attribute_name=VCENTER_RESOURCE_PASSWORD_ATTR)

        password = cs_api.DecryptPassword(encrypted_password).Value

        return vcenter_service.connect(address=vcenter_resource.Address, user=user, password=password)

    def _get_vm_creds(self, resource_config, cs_api):
        """

        :param resource_config:
        :param cs_api:
        :rtype: pyVmomi.vim.vm.guest.NamePasswordAuthentication
        """
        password = cs_api.DecryptPassword(resource_config.password).Value

        return pyVmomi.vim.vm.guest.NamePasswordAuthentication(
            username=resource_config.user,
            password=password)

    @wait_for_guest_operations
    def enable_ssh(self):
        """

        :return:
        """
        self._logger.info("Enabling SSH service on the Deployed VyOS VM")
        enable_ssh_command = ("#!/bin/vbash\n"
                              "source /opt/vyatta/etc/functions/script-template\n"
                              "configure\n"
                              "set service ssh port 22\n"
                              "commit\n"
                              "save\n"
                              "exit")

        cmdspec = pyVmomi.vim.vm.guest.ProcessManager.ProgramSpec(arguments=enable_ssh_command,
                                                                  programPath="/bin/bash")

        self._vcenter_si.content.guestOperationsManager.processManager.StartProgramInGuest(vm=self._vm,
                                                                                           auth=self._vm_creds,
                                                                                           spec=cmdspec)
        self._logger.info("Enabling SSH service on the Deployed VyOS VM command triggered")

    def _get_vm_power_state(self):
        """

        :return:
        """
        vm_power_state = self._vm.summary.runtime.powerState
        self._logger.info("Checking VM Power state: {}".format(vm_power_state))

        return vm_power_state

    @property
    def is_vm_powered_on(self):
        """

        :return:
        """
        vm_power_state = self._get_vm_power_state()

        return vm_power_state == pyVmomi.vim.VirtualMachine.PowerState.poweredOn

    def wait_for_vm(self, timeout=VM_TOOLS_WAITING_TIMEOUT, interval=VM_TOOLS_WAITING_INTERVAL):
        """

        :param int timeout:
        :param int interval:
        :return:
        """
        self._logger.info("Waiting for Virtual Machine Tools to be ready")
        timeout_time = datetime.now() + timedelta(seconds=timeout)

        while self._vm.summary.runtime.powerState != pyVmomi.vim.VirtualMachine.PowerState.poweredOn \
                or self._vm.guest.toolsStatus not in [pyVmomi.vim.VirtualMachineToolsStatus.toolsOk,
                                                      pyVmomi.vim.VirtualMachineToolsStatus.toolsOld]\
                or self._vm.guest.guestId is None:

            self._logger.info("Waiting for Virtual Machine Tools. Current VM status is : {}. Tools status is {}"
                              .format(self._vm.summary.runtime.powerState, self._vm.guest.toolsStatus))

            if datetime.now() > timeout_time:
                raise Exception("VM aren't ready within {} minute(s). Power state: {}. Tools status: {}"
                                .format(timeout / 60,
                                        self._vm.summary.runtime.powerState,
                                        self._vm.guest.toolsStatus))

            time.sleep(interval)

        self._logger.info("Virtual Machine Tools are ready. Power state: {}. Tools status: {}".format(
            self._vm.summary.runtime.powerState,
            self._vm.guest.toolsStatus))

    @wait_for_guest_operations
    def _upload_custom_script(self, local_script_path, remote_script_path):
        """

        :param str local_script_path:
        :param str remote_script_path:
        :return:
        """
        self._logger.info("Trying to upload script '{}' to VM as '{}'".format(local_script_path, remote_script_path))

        with open(local_script_path, 'rb') as script_file:
            script_content = script_file.read()

        file_attribute = pyVmomi.vim.vm.guest.FileManager.FileAttributes()
        si_content = self._vcenter_si.RetrieveContent()

        try:
            url = si_content.guestOperationsManager.fileManager.InitiateFileTransferToGuest(
                self._vm, self._vm_creds, VYOS_CLEAR_VNIC_ID_SCRIPT_PATH, file_attribute, len(script_content), True)
        except Exception as e:
            self._logger.exception("Unable to upload script file '{}' due to: {}".format(local_script_path, e))
            raise

        resp = requests.put(url=url, data=script_content, verify=False)
        resp.raise_for_status()

        self._logger.info("Changing permissions to 755 for script '{}'".format(remote_script_path))

        cmdspec = pyVmomi.vim.vm.guest.ProcessManager.ProgramSpec(
            arguments="755 {}".format(VYOS_CLEAR_VNIC_ID_SCRIPT_PATH),
            programPath="/bin/chmod")

        self._vcenter_si.content.guestOperationsManager.processManager.StartProgramInGuest(vm=self._vm,
                                                                                           auth=self._vm_creds,
                                                                                           spec=cmdspec)

        self._logger.info("Script '{}' was uploaded as '{}'".format(local_script_path, remote_script_path))

    @wait_for_guest_operations
    def _execute_custom_script(self, remote_script_path, program_path):
        """

        :param str remote_script_path:
        :return:
        """
        self._logger.info("Trying to start script '{} {}'".format(program_path, remote_script_path))

        cmdspec = pyVmomi.vim.vm.guest.ProcessManager.ProgramSpec(
            arguments=remote_script_path,
            programPath=program_path)

        self._vcenter_si.content.guestOperationsManager.processManager.StartProgramInGuest(vm=self._vm,
                                                                                           auth=self._vm_creds,
                                                                                           spec=cmdspec)

        self._logger.info("Script '{} {}' was started".format(program_path, remote_script_path))

    def apply_clear_nic_hw_id_script(self, script_path):
        """

        :param str script_path:
        :return:
        """
        self._upload_custom_script(local_script_path=script_path,
                                   remote_script_path=VYOS_CLEAR_VNIC_ID_SCRIPT_PATH)

        self._execute_custom_script(remote_script_path=VYOS_CLEAR_VNIC_ID_SCRIPT_PATH,
                                    program_path=PERL_PROGRAM_PATH)

    def reboot_vm(self, wait_for_vm=True):
        """

        :param bool wait_for_vm:
        :return:
        """
        self._logger.info("Rebooting VM...")
        self._vm.RebootGuest()

        if wait_for_vm:
            self.wait_for_vm()

        self._logger.info("VM was successfully rebooted")
