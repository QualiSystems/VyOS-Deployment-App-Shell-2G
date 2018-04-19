from cloudshell.devices.standards.base import AbstractResource
from cloudshell.devices.standards.validators import attr_length_validator


AVAILABLE_SHELL_TYPES = ["CS_GenericDeployedApp", "CS_GenericVPort"]


class GenericDeployedApp(AbstractResource):
    RESOURCE_MODEL = "Generic Deployed App"
    RELATIVE_PATH_TEMPLATE = "DA"

    def __init__(self, shell_name, name, unique_id, shell_type="CS_GenericDeployedApp"):
        super(GenericDeployedApp, self).__init__(shell_name, name, unique_id)

        if shell_name:
            self.shell_name = "{}.".format(shell_name)
            if shell_type in AVAILABLE_SHELL_TYPES:
                self.shell_type = "{}.".format(shell_type)
            else:
                raise Exception(self.__class__.__name__, "Unavailable shell type {shell_type}."
                                                         "Shell type should be one of: {avail}"
                                .format(shell_type=shell_type, avail=", ".join(AVAILABLE_SHELL_TYPES)))
        else:
            self.shell_name = ""
            self.shell_type = ""


class GenericVPort(AbstractResource):
    RESOURCE_MODEL = "Generic V Port"
    RELATIVE_PATH_TEMPLATE = "P"

    def __init__(self, shell_name, name, unique_id, shell_type="CS_GenericVPort"):
        super(GenericVPort, self).__init__(shell_name, name, unique_id)

        if shell_name:
            if shell_type in AVAILABLE_SHELL_TYPES:
                self.shell_type = "{}.".format(shell_type)
            else:
                raise Exception(self.__class__.__name__, "Unavailable shell type {shell_type}."
                                                         "Shell type should be one of: {avail}"
                                .format(shell_type=shell_type, avail=", ".join(AVAILABLE_SHELL_TYPES)))
        else:
            self.shell_name = ""
            self.shell_type = ""

    @property
    def logical_name(self):
        return self.attributes.get("{}Logical Name".format(self.namespace), None)

    @logical_name.setter
    @attr_length_validator
    def logical_name(self, value):
        """

        :param value:
        :return:
        """
        self.attributes["{}Logical Name".format(self.namespace)] = value

    @property
    def mac_address(self):
        """

        :return:
        """
        return self.attributes.get("{}MAC Address".format(self.namespace), None)

    @mac_address.setter
    @attr_length_validator
    def mac_address(self, value):
        """

        :param value:
        :return:
        """
        self.attributes["{}MAC Address".format(self.namespace)] = value

    @property
    def requested_vnic_name(self):
        return self.attributes.get("{}Requested vNIC Name".format(self.namespace), None)

    @requested_vnic_name.setter
    @attr_length_validator
    def requested_vnic_name(self, value):
        """

        :param value:
        :return:
        """
        self.attributes["{}Requested vNIC Name".format(self.namespace)] = value