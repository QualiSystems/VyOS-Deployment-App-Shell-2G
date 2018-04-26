class VyOSResource(object):
    def __init__(self, address=None, family=None, shell_type=None, shell_name=None,
                 fullname=None, name=None, attributes=None):
        """

        :param str address: IP address of the resource
        :param str family: resource family
        :param str shell_name: shell name
        :param str fullname: full name of the resource
        :param str name: name of the resource
        :param dict[str, str] attributes: attributes of the resource
        """
        self.address = address
        self.family = family
        self.shell_name = shell_name
        self.fullname = fullname
        self.name = name
        self.attributes = attributes or {}

        # todo: move it somewhere else !
        self.vrf_management_name = ""

        if shell_name:
            self.namespace_prefix = "{}.".format(self.shell_name)
            self.shell_type = "{}.".format(shell_type)
        else:
            self.namespace_prefix = ""
            self.shell_type = ""

    @property
    def config_file(self):
        """

        :rtype: str
        """
        return self.attributes.get("{}Configuration File".format(self.namespace_prefix), None)

    @property
    def enable_ssh(self):
        """

        :rtype: str
        """
        enable_ssh = self.attributes.get("{}Enable SSH".format(self.namespace_prefix), "")

        if enable_ssh.lower() == "true":
            return True

        return False

    @property
    def user(self):
        """

        :rtype: str
        """
        return self.attributes.get("{}User".format(self.namespace_prefix), None)

    @property
    def password(self):
        """

        :rtype: string
        """
        return self.attributes.get("{}Password".format(self.namespace_prefix), None)

    @property
    def cli_connection_type(self):
        """

        :rtype: str
        """
        return self.attributes.get("{}CLI Connection Type".format(self.namespace_prefix), "SSH")

    @property
    def cli_tcp_port(self):
        """

        :rtype: str
        """
        return self.attributes.get("{}CLI TCP Port".format(self.namespace_prefix), 22)

    @property
    def sessions_concurrency_limit(self):
        """

        :rtype: float
        """
        return self.attributes.get("{}Sessions Concurrency Limit".format(self.namespace_prefix), 1)


    @classmethod
    def from_context(cls, context, shell_type=None, shell_name=None):
        """Create an instance of TrafficGeneratorVBladeResource from the given context

        :param cloudshell.shell.core.driver_context.ResourceCommandContext context:
        :param str shell_type: shell type
        :param str shell_name: shell name
        :rtype: TrafficGeneratorVChassisResource
        """
        return cls(address=context.resource.address,
                   family=context.resource.family,
                   shell_type=shell_type,
                   shell_name=shell_name,
                   fullname=context.resource.fullname,
                   attributes=dict(context.resource.attributes),
                   name=context.resource.name)
