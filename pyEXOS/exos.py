#!/usr/bin/env python
""" pyexos """

import difflib

from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.ssh_exception import NetMikoAuthenticationException

from pyEXOS.exceptions import EXOSException


class EXOS(object):
    """
    Establishes a connection with the ESOX device via SSH and provides a number of
    config manipulation methods.
    """

    def __init__(self, hostname, username, password, port=22, timeout=60, ssh_config_file=None):
        """
        EXOS device constructor.

        :param hostname:  (str) IP or FQDN of the target device
        :param username:  (str) Username
        :param password:  (str) Password
        :param port:      (int) SSH Port (default: 22)
        :param timeout:   (int) Timeout (default: 60 sec)
        :param ssh_config_file: (file) Path to SSH config file
        :return: (obj) EXOS object
        """
        self.hostname = str(hostname)
        self.username = str(username)
        self.password = str(password)
        self.port = int(port)
        self.timeout = int(timeout)
        self.ssh_config_file = str(ssh_config_file)

        self.device = None
        self.candidate_config = None
        self.running_config = None

    def open(self):
        """
        Open a connection to an EXOS device using SSH.

        :return: None
        :raises: NetMikoTimeoutException, NetMikoAuthenticationException
        """
        try:
            self.device = ConnectHandler(device_type='extreme',
                                         ip=self.hostname,
                                         port=self.port,
                                         username=self.username,
                                         password=self.password,
                                         ssh_config_file=self.ssh_config_file)
            self.device.timeout = self.timeout
        except (NetMikoTimeoutException, NetMikoAuthenticationException):
            raise

    def close(self):
        """
        Close the SSH connection to the EXOS device.

        :return: None
        """
        if hasattr(self.device, 'remote_conn'):
            self.device.remote_conn.close()

    def load_candidate_config(self, filename=None, config=None):
        """
        Populate candidate_config from str or file as a list of commands.

        :param filename:  Path to the file containing the desired
                          configuration. Default: None.
        :param config:    String containing the desired configuration.
                          Default: None.

        :return: None
        :raises: EXOSException
        """

        # scp to device in the future candidate.xsf

        if filename is None and config is None:
            raise EXOSException("at least one of the following attributes has to be \
                provided: 'filename' or 'confg'")

        self.candidate_config = ''

        if filename is not None:
            with open(filename) as f:
                self.candidate_config = f.read().splitlines()
        else:
            self.candidate_config = config.splitlines()

    def commit_config(self):
        """
        Commit candidate_config to the device.

        :return: None
        :raises: EXOSException, ValueError, NetMikoTimeoutException
        """

        # load file in the future
        # save configuration as-script backup
        # load script configuration candidate

        if self.candidate_config is None:
            raise EXOSException("Candidate config not loaded")

        try:
            # make a backup of the running_config
            self.get_running_config()
            # send candidate_config
            self.candidate_config.append('save')
            self.device.send_config_set(self.candidate_config)
            self.candidate_config = None
        except (EXOSException, ValueError, NetMikoTimeoutException):
            raise

    def discard_config(self):
        """
        Clear previously loaded candidate_config without committing it.

        :return: None
        """
        # remove file on device in the future
        # rm candidate.xsf

        self.candidate_config = None

    def get_running_config(self):
        """
        Populate running_config from remote deviceas a list of commands.

        :return: None
        :raises: ValueError, IndexError, IOError
        """
        try:
            output = self.device.send_command('show configuration')
            self.running_config = output.splitlines()
        except (ValueError, IndexError, IOError):
            raise

    def compare_merge_config(self):
        """
        Compare configuration to be merged, with the one on the device.

        Compare executed candidate config with the running config and
        return a diff, assuming the loaded config will be merged with the
        existing one.

        :return: config diff
        :raises: EXOSException
        """
        if self.candidate_config is None:
            raise EXOSException("Candidate config not loaded")

        # make sure we have the running_config
        self.get_running_config()

        old_conf = list(set(self.running_config))
        new_conf = self.running_config + self.candidate_config
        new_conf = list(set(new_conf))

        diff = difflib.unified_diff(old_conf,
                                    new_conf,
                                    fromfile='running_config.conf',
                                    tofile='candidate_config.conf',
                                    n=0,
                                    lineterm='')
        return '\n'.join(list(diff))

    def compare_replace_config(self):
        """
        Compare configuration to be replaced, with the one on the device.

        The running_config will be deleted prior to loading the candidate_config,
        the result applied on the router is the candidate_config only.

        :return: config diff
        """
        if self.candidate_config is None:
            raise EXOSException("Candidate config not loaded")

        diff = difflib.unified_diff('',
                                    self.candidate_config,
                                    fromfile='running_config.conf',
                                    tofile='candidate_config.conf',
                                    lineterm='')
        return '\n'.join(list(diff))

    def commit_replace_config(self):
        """
        Commit candidate_config to the device, by replaceing the previous
        running configuration.

        The current running_configuration is inspected and commands generated
        to delete all current config statements from the device, prior to
        loading the candidate_config.

        :return: None
        :raises: EXOSException, ValueError, NetMikoTimeoutException
        """
        if self.candidate_config is None:
            raise EXOSException("Candidate config not loaded")

        try:
            # fetch running_config to generate delete commands for it
            self.get_running_config()

            # generate delete commands for current running_config
            delete_commands = self._generate_delete_statements(self.running_config)

            # merge loaded candidate_config with delete_commands
            self.candidate_config = delete_commands + self.candidate_config

            # commit new combined candidate_config
            self.commit_config()
        except (EXOSException, ValueError, NetMikoTimeoutException):
            raise

    def rollback(self):
        """
        Rollback the last committed configuration.

        :return: None
        :raises: EXOSException, ValueError, NetMikoTimeoutException
        """
        if self.running_config is None:
            raise EXOSException("No previous running_config to roll back to present")

        try:
            # load the previous running_config to get back to the previous state
            self.candidate_config = self.running_config

            # remove all comments and empty lines
            self.candidate_config = [x for x in self.candidate_config if not x.startswith('#')]
            self.candidate_config = [x for x in self.candidate_config if not x == '']

            # commit_replace the config
            self.commit_replace_config()
        except (EXOSException, ValueError, NetMikoTimeoutException):
            raise

    def _generate_delete_statements(self, config):
        """
        Generate a list of delete statements for the passed config

        :param config: (list) list of config statements to be deleted
        :return: (list) delete statements
        """
        delete_statements = []
        return delete_statements
