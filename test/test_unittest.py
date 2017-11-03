#!/usr/bin/env python
""" Interact with Extreme Networks devices running EXOS """

import unittest
import mock

from pyEXOS import EXOS

from pyEXOS.exceptions import EXOSException
from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.ssh_exception import NetMikoAuthenticationException


class TestEXOSDevice(unittest.TestCase):

    """
    Tests EXOS module.
    """

    def setUp(self):
        self.device = EXOS('hostname', 'username', 'password')

    # test init

    def test_pyexos_init(self):
        """ testing pyEXOS object init """
        self.assertIsInstance(self.device, EXOS)

    # test open

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_open(self, mock_con):
        """ testing pyEXOS open """
        self.assertIsNone(self.device.open())

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_open_raises_NetMikoTimeoutException(self, mock_con):
        """ testing pyEXOS open NetMikoTimeoutException """
        mock_con.side_effect = NetMikoTimeoutException
        self.assertRaises(NetMikoTimeoutException, self.device.open)

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_open_raises_NetMikoAuthenticationException(self, mock_con):
        """ testing pyEXOS open NetMikoAuthenticationException """
        mock_con.side_effect = NetMikoAuthenticationException
        self.assertRaises(NetMikoAuthenticationException, self.device.open)

    # test close

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_close(self, mock_con):
        """ testing pyEXOS close """
        self.device.open()
        self.assertIsNone(self.device.close())

    # test load_candidate_config

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_load_candidate_config_exception(self, mock_con):
        """ testing pyEXOS load_candidate_config EXOSException """
        self.device.open()
        self.assertRaises(EXOSException, self.device.load_candidate_config)

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_load_candidate_config_from_file(self, mock_con):
        """ testing pyEXOS load_candidate_config """
        self.device.open()
        filename = 'test/config_merge.txt'
        self.device.load_candidate_config(filename=filename)
        self.assertIsInstance(self.device.candidate_config, list)

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_load_candidate_config_from_str(self, mock_con):
        """ testing pyEXOS load_candidate_config """
        self.device.open()
        config = 'config'
        self.device.load_candidate_config(config=config)
        self.assertIsInstance(self.device.candidate_config, list)

    # test commit_config

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_commit_config(self, mock_con):
        """ testing pyEXOS commit_config """
        self.device.open()
        config = 'config'
        self.device.load_candidate_config(config=config)
        self.assertIsNone(self.device.commit_config())

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_commit_config_exception_no_candidate(self, mock_con):
        """ testing pyEXOS commit_config EXOSException """
        self.device.open()
        self.assertRaises(EXOSException, self.device.commit_config)

    def test_pyexos_commit_config_exception(self):
        """ testing pyEXOS commit_config Error """
        with mock.patch('pyEXOS.exos.ConnectHandler') as class_con:
            for error in [ValueError, EXOSException]:
                instance = class_con.return_value
                instance.send_command_timing.side_effect = error
                self.device.open()
                config = 'config'
                self.device.load_candidate_config(config=config)
                self.assertRaises(error, self.device.commit_config)

    def test_pyexos_commit_config_invalid(self):
        """ testing pyEXOS commit_config Invalid Command """
        with mock.patch('pyEXOS.exos.ConnectHandler') as class_con:
            instance = class_con.return_value
            instance.send_command_timing.return_value = "Invalid input detected"
            self.device.open()
            config = 'config'
            self.device.load_candidate_config(config=config)
            self.assertRaises(EXOSException, self.device.commit_config)

    # test discard_config

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_discard_config(self, mock_con):
        """ testing pyEXOS discard_config """
        self.device.open()
        config = 'config'
        self.device.load_candidate_config(config=config)
        self.device.discard_config()
        self.assertIsNone(self.device.candidate_config)

    # test get_running_config

    def test_pyexos_get_running_config(self):
        """ testing pyEXOS get_running_config """
        with mock.patch('pyEXOS.exos.ConnectHandler') as class_con:
            instance = class_con.return_value
            instance.send_command.return_value = 'running_config'
            self.device.open()
            self.device.get_running_config()
            self.assertIsInstance(self.device.running_config, list)

    def test_pyexos_get_running_config_exception(self):
        """ testing pyEXOS get_running_config Exception """
        with mock.patch('pyEXOS.exos.ConnectHandler') as class_con:
            instance = class_con.return_value
            instance.send_command.side_effect = ValueError
            self.device.open()
            self.assertRaises(ValueError, self.device.get_running_config)

    # test compare_merge_config

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_compare_merge_config(self, mock_con):
        """ testing pyEXOS compare_merge_config """
        self.device.open()
        config = 'config'
        self.device.load_candidate_config(config=config)
        diff = self.device.compare_merge_config()
        self.assertIsInstance(diff, str)

    # test is_alive

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_is_alive(self, mock_con):
        """ testing pyEXOS is_alive """
        self.device.open()
        self.assertTrue(self.device.is_alive())

    def test_pyexos_is_alive_false(self):
        """ testing pyEXOS is_alive """
        self.assertTrue(self.device.is_alive())

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_compare_merge_config_exception(self, mock_con):
        """ testing pyEXOS compare_merge_config exception """
        self.device.open()
        self.assertRaises(EXOSException, self.device.compare_merge_config)

    # test compare_replace_config

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_compare_replace_config(self, mock_con):
        """ testing pyEXOS compare_replace_config """
        self.device.open()
        config = 'config'
        self.device.load_candidate_config(config=config)
        diff = self.device.compare_replace_config()
        self.assertIsInstance(diff, str)

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_compare_replace_config_exception(self, mock_con):
        """ testing pyEXOS compare_replace_config exception """
        self.device.open()
        self.assertRaises(EXOSException, self.device.compare_replace_config)

    # test commit_replace_config

    def test_pyexos_commit_replace_config(self):
        """ testing pyEXOS load_replace_candidate_config """
        running_config = open('test/config_running.txt').read()
        with mock.patch('pyEXOS.exos.ConnectHandler') as class_con:
            instance = class_con.return_value
            instance.send_command.return_value = running_config
            self.device.open()
            filename = 'test/config_replace.txt'
            self.device.load_candidate_config(filename=filename)
            self.assertIsNone(self.device.commit_replace_config())

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_commit_replace_config_exception(self, mock_con):
        """ testing pyEXOS load_replace_candidate_config EXOSException """
        with mock.patch.object(EXOS, 'commit_config') as mock_commit:
            mock_commit.side_effect = EXOSException('error')
            self.device.open()
            config = 'config'
            self.device.load_candidate_config(config=config)
            self.assertRaises(EXOSException, self.device.commit_replace_config)

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_commit_replace_config_exception_no_candidate(self, mock_con):
        """ testing pyEXOS load_replace_candidate_config EXOSException """
        self.device.open()
        self.assertRaises(EXOSException, self.device.commit_replace_config)

    # test rollback

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_rollback(self, mock_con):
        """ testing pyEXOS rollback """
        self.device.open()
        config = 'config'
        self.device.load_candidate_config(config=config)
        self.device.commit_config()
        self.assertIsNone(self.device.rollback())

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_rollback_exception(self, mock_con):
        """ testing pyEXOS rollback EXOSException """
        with mock.patch.object(EXOS, 'commit_replace_config') as mock_commit:
            mock_commit.side_effect = EXOSException('error')
            self.device.open()
            config = 'config'
            self.device.load_candidate_config(config=config)
            self.device.commit_config()
            self.assertRaises(EXOSException, self.device.rollback)

    @mock.patch('pyEXOS.exos.ConnectHandler')
    def test_pyexos_rollback_exception_no_running(self, mock_con):
        """ testing pyEXOS rollback EXOSException """
        self.device.open()
        self.assertRaises(EXOSException, self.device.rollback)


if __name__ == '__main__':
    unittest.main()
