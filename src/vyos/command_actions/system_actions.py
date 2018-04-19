import re
from collections import OrderedDict

from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor
from cloudshell.devices.networking_utils import UrlParser

from vyos.cli import command_templates


class SystemActions(object):
    def __init__(self, cli_service, logger):
        """
        Reboot actions
        :param cli_service: default mode cli_service
        :type cli_service: CliService
        :param logger:
        :type logger: Logger
        :return:
        """
        self._cli_service = cli_service
        self._logger = logger

    @staticmethod
    def prepare_action_map(source_file, destination_file):
        action_map = OrderedDict()
        if "://" in destination_file:
            url = UrlParser.parse_url(destination_file)
            dst_file_name = url.get(UrlParser.FILENAME)
            source_file_name = UrlParser.parse_url(source_file).get(UrlParser.FILENAME)
            action_map[r"[\[\(].*{}[\)\]]".format(
                dst_file_name)] = lambda session, logger: session.send_line("", logger)

            action_map[r"[\[\(]{}[\)\]]".format(source_file_name)] = lambda session, logger: session.send_line("",
                                                                                                               logger)
        else:
            destination_file_name = UrlParser.parse_url(destination_file).get(UrlParser.FILENAME)
            url = UrlParser.parse_url(source_file)

            source_file_name = url.get(UrlParser.FILENAME)
            action_map[r"(?!/)[\[\(]{}[\)\]]".format(
                destination_file_name)] = lambda session, logger: session.send_line("", logger)
            action_map[r"(?!/)[\[\(]{}[\)\]]".format(
                source_file_name)] = lambda session, logger: session.send_line("", logger)
        host = url.get(UrlParser.HOSTNAME)
        if host:
            action_map[r"(?!/){}(?!/)".format(host)] = lambda session, logger: session.send_line("", logger)
        password = url.get(UrlParser.PASSWORD)
        if password:
            action_map[r"[Pp]assword:".format(
                source_file)] = lambda session, logger: session.send_line(password, logger)
        return action_map

    def save(self, destination, action_map=None, error_map=None, timeout=180):
        """Copy file from device to tftp or vice versa, as well as copying inside devices filesystem.

        :param destination: destination file
        :param action_map: actions will be taken during executing commands, i.e. handles yes/no prompts
        :param error_map: errors will be raised during executing commands, i.e. handles Invalid Commands errors
        :param timeout: session timeout
        :raise Exception:
        """
        output = CommandTemplateExecutor(self._cli_service,
                                         command_templates.SAVE_CONFIGURATION,
                                         action_map=action_map,
                                         error_map=error_map,
                                         timeout=timeout).execute_command(destination_file_path=destination)

        if not re.search(r"[Dd]one", output, re.IGNORECASE):
            error_match = re.search(r"error.*\n|failed.*\n", output, re.IGNORECASE)

            if error_match:
                self._logger.error(output)
                raise Exception("Copy command failed. See logs for the details")

    def load(self, path, action_map=None, error_map=None, timeout=300):
        """Load configuration file

        :param path: relative path to the file on the remote host tftp://server/sourcefile
        :param action_map: actions will be taken during executing commands, i.e. handles yes/no prompts
        :param error_map: errors will be raised during executing commands, i.e. handles Invalid Commands errors
        :param timeout: session timeout
        :raise Exception:
        """
        output = CommandTemplateExecutor(self._cli_service,
                                         command_templates.LOAD_CONFIGURATION,
                                         action_map=action_map,
                                         error_map=error_map,
                                         timeout=timeout,
                                         check_action_loop_detector=False).execute_command(source_file_path=path)

        if re.search(r'[Ee]rror.*', output, flags=re.DOTALL):
            self._logger.error(output)
            raise Exception("Copy command failed. See logs for the details")

    def commit(self):
        """

        :return:
        """
        command = CommandTemplateExecutor(cli_service=self._cli_service,
                                          command_template=command_templates.COMMIT)

        command.execute_command()
