#!/usr/bin/env python
""" pyexos """

import difflib
import re

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

    def is_alive(self):
        """
        Check if the SSH connection is still alive.

        :return: Boolean
        """
        if self.device:
            is_alive = self.device.remote_conn.transport.is_active()
        else:
            is_alive = False
        return {'is_alive': is_alive}

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
            with open(filename) as file:
                self.candidate_config = file.read().splitlines()
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
            commands = list(set(self.candidate_config))
            commands.append('save')
            for command in commands:
                output = self.device.send_command_timing(command)
                if 'Invalid input detected' in output:
                    raise EXOSException("Error while sending the '{0}' command:"
                                        "\n{1}".format(command, output))
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
            output = self.device.send_command('show configuration', delay_factor=20)
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
        Generate replace diff to be used to build delete commands

        :return: config diff
        :raises: EXOSException
        """
        if self.candidate_config is None:
            raise EXOSException("Candidate config not loaded")

        # make sure we have the running_config
        self.get_running_config()

        replace_diff = difflib.unified_diff([x.strip() for x in self.running_config],
                                            [x.strip() for x in self.candidate_config],
                                            fromfile='running_config.conf',
                                            tofile='candidate_config.conf',
                                            lineterm='')

        replace_diff = '\n'.join(replace_diff)
        return replace_diff

    def commit_replace_config(self):
        """
        Commit candidate_config to the device, by replaceing the previous
        running configuration.

        :return: None
        :raises: EXOSException, ValueError, NetMikoTimeoutException
        """
        if self.candidate_config is None:
            raise EXOSException("Candidate config not loaded")

        try:
            # fetch running_config to generate delete commands for it
            self.get_running_config()

            # generate delta commands
            self.candidate_config = self._generate_commands()

            # commit new candidate_config
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

    def _generate_commands(self):  # noqa
        """
        Generate a list of delete statements for the candidate config

        :return: (list) delete statements
        """
        replace_diff = self.compare_replace_config()
        commands = []
        acl_commands = []
        unconfigure_acl_commands = []
        command = None
        for line in replace_diff.splitlines():
            if line.startswith('+') and ('configure access-list' in line and 'ports' in line):
                direction = line.split()[-1]
                if direction not in ['ingress', 'egress']:
                    direction = 'ingress'
                ports = line.split()[4]
                if ',' in line:
                    delimiter = ','
                else:
                    delimiter = ':'
                for port in ports.split(delimiter):
                    acl_command = '{0} {1} {2}'.format(' '.join(line.split()[:4]), port, direction)
                    acl_commands.append(acl_command[1::])
                    if acl_command[1::] not in self.running_config:
                        commands.append(acl_command[1::])
            elif line.startswith('+'):
                command = line[1::]
            elif line.startswith('-') and 'running_config.conf' not in line:
                if ('create vlan' in line or
                    'create eaps' in line or
                    'create meter' in line):
                    command = line[1::].replace('create', 'delete')
                elif ('fdbentry' in line or
                      'fdb' in line):
                    command = line[1::].replace('create', 'delete').split('port')[0].strip()
                elif 'configure iproute' in line:
                    command = line[1::].replace('add', 'delete')
                elif ('disable iproute ipv4 compression' in line or
                      'disable iproute ipv6 compression' in line or
                      'disable igmp snooping vlan' in line or
                      'disable igmp proxy-query vlan' in line or
                      'disable tacacs' in line or
                      'disable tacacs-authorization' in line or
                      'disable idletimeout' in line or
                      'disable edp ports' in line or
                      'disable lldp ports' in line or
                      'disable learning port' in line or
                      'disable snmp access vr' in line):
                    command = line[1::].replace('disable', 'enable')
                elif ('enable log target' in line or
                      'enable sntp-client' in line or
                      'enable tacacs' in line or
                      'enable tacacs-authorization' in line or
                      'enable iproute ipv4 compression' in line or
                      'enable iproute ipv6 compression' in line or
                      'enable stpd' in line):
                    command = line[1::].replace('enable', 'disable')
                elif 'enable eaps' == line[1::]:
                    command = line[1::].replace('enable', 'disable') + "\ny"
                elif 'enable sflow' in line:
                    if len(line.split()) > 3:
                        line_parts = line.split()
                        command = ' '.join(line_parts[:-1])[1::].replace('enable', 'disable')
                    else:
                        command = line[1::].replace('enable', 'disable')
                elif 'configure tacacs primary' in line:
                    command = 'unconfigure tacacs server primary'
                elif 'configure tacacs secondary' in line:
                    command = 'unconfigure tacacs server secondary'
                elif 'configure access-list' in line and 'ports' in line:
                    unconfigure_acl_commands.append(line[1::])
                elif 'configure access-list zone' in line:
                    acl_zone_parts = line.split('application')
                    application = acl_zone_parts[1].split()[0]
                    command = '{0} {1} {2}'.format(''.join(acl_zone_parts[0])[1::],
                                                   'delete application', application)
                elif 'enable sharing' in line:
                    line_part = line.split('grouping')
                    command = line_part[0][1::].replace('enable', 'disable')
                elif ('configure eaps' in line and
                      'port' in line or
                      'configure mstp region' in line):
                    command = ' '.join(line.split()[:-1])[1::].replace('configure', 'unconfigure')
                elif 'configure pim register-checksum-to include-data' in line:
                    command = 'configure pim register-checksum-to exclude-data'
                elif ('configure eaps shared-port' in line or
                      'configure sflow collector' in line or
                      'configure pim' in line):
                    command = line[1::].replace('configure', 'unconfigure')
                elif ('configure syslog' in line or
                      'configure dns-client' in line):
                    command = line[1::].replace('add', 'delete')
                elif 'configure snmpv3 add community' in line:
                    command = ' '.join(line.split()[:5])[1::].replace('add', 'delete')
                elif 'configure sflow agent' in line:
                    command = line[1::].split('ipaddress')[0].replace('configure', 'unconfigure')
                elif 'configure sflow ports' in line:
                    command = line[1::].split('sample-rate')[0].replace('configure', 'unconfigure')
                elif 'configure sflow' in line:
                    command = "unconfigure sflow"
                elif 'create ldap domain' in line:
                    if 'default' in line:
                        command = ' '.join(line.split()[:-1])[1::].replace('create', 'delete')
                    else:
                        command = line[1::].replace('create', 'delete')
                elif 'configure ldap domain' in line:
                    command = ' '.join(line.split()[:-2])[1::].replace('configure', 'delete')
                elif 'configure sntp-client primary' in line:
                    command = 'unconfigure sntp-client primary'
                elif 'configure sntp-client secondary' in line:
                    command = 'unconfigure sntp-client secondary'
                elif ('configure snmpv3 add target-addr' in line or
                      'configure snmpv3 add target-params' in line):
                    command = ' '.join(line.split()[:5])[1::]
                    command = re.sub('\sadd', ' delete', command)
                elif 'configure vlan' in line and 'untagged' in line:
                    command = ' '.join(line.split()[:-1])[1::].replace('add', 'delete')
                elif 'configure vlan' in line and 'tagged' in line:
                    command = ' '.join(line.split()[:-1])[1::].replace('add', 'delete')
                elif 'description-string' in line:
                    command = ' '.join(line.split()[:-1])[1::].replace('configure', 'unconfigure')
                elif 'configure vlan' in line and 'ipaddress' in line:
                    command = ' '.join(line.split()[:-2])[1::].replace('configure', 'unconfigure')
                elif 'configure snmp sysName' in line:
                    command = "configure snmp sysName \"''\""
                elif 'configure snmp sysLocation' in line:
                    command = "configure snmp sysLocation \"''\""
                elif 'configure snmp sysContact' in line:
                    command = 'configure snmp sysContact "support@extremenetworks.com, +1 888 257 3000"'
                elif 'configure timezone' in line:
                    command = 'configure timezone 0'
            if command:
                if command not in commands:
                    commands.append(command)
        for line in list(set(unconfigure_acl_commands)):
            if line not in list(set(acl_commands)):
                direction = line.split()[-1]
                acl_command = '{0} {1}'.format(' '.join(line.split()[:3]), direction)
                commands.append(acl_command.replace('configure', 'unconfigure'))

        commands = [x for x in commands if not x.startswith('#') and not x.startswith('+')]
        commands = [x for x in commands if not x == '']
        return commands
