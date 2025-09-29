"""
E2E Tests for System Domain Endpoints

Tests system command execution, system info retrieval,
process monitoring, and Chrome instance management.
"""

import requests
import time
import platform
from typing import Dict, Any
from .base_test import CDPNinjaE2ETest


class TestSystemDomain(CDPNinjaE2ETest):
    """Test System domain endpoints for system management"""

    def test_system_execute_command(self):
        """Test system command execution"""
        # Test safe system commands based on platform
        if platform.system() == "Windows":
            test_commands = [
                {"command": "echo", "args": ["Hello World"]},
                {"command": "dir", "args": ["/B"]},
                {"command": "ver", "args": []}
            ]
        else:
            test_commands = [
                {"command": "echo", "args": ["Hello World"]},
                {"command": "ls", "args": ["-la"]},
                {"command": "uname", "args": ["-a"]}
            ]

        for cmd_test in test_commands:
            with self.subTest(command=cmd_test["command"]):
                response = requests.post(f"{self.cdp_base}/system/execute",
                                       json={
                                           "command": cmd_test["command"],
                                           "args": cmd_test["args"],
                                           "timeout": 10
                                       })
                self.assertEqual(response.status_code, 200)

                exec_data = response.json()
                self.assertIn('execution_result', exec_data)

                result = exec_data['execution_result']
                self.assertIn('stdout', result)
                self.assertIn('stderr', result)
                self.assertIn('return_code', result)

                # Verify successful execution for basic commands
                if cmd_test["command"] in ["echo", "uname", "ver"]:
                    self.assertEqual(result['return_code'], 0)

        # Test command with working directory
        workdir_response = requests.post(f"{self.cdp_base}/system/execute",
                                       json={
                                           "command": "pwd" if platform.system() != "Windows" else "cd",
                                           "working_directory": "/tmp" if platform.system() != "Windows" else "C:\\"
                                       })
        self.assertEqual(workdir_response.status_code, 200)

        # Test command with environment variables
        env_response = requests.post(f"{self.cdp_base}/system/execute",
                                   json={
                                       "command": "echo",
                                       "args": ["$TEST_VAR"] if platform.system() != "Windows" else ["%TEST_VAR%"],
                                       "environment": {"TEST_VAR": "test_value"}
                                   })
        self.assertEqual(env_response.status_code, 200)

    def test_system_info_retrieval(self):
        """Test system information retrieval"""
        response = requests.get(f"{self.cdp_base}/system/info")
        self.assertEqual(response.status_code, 200)

        info_data = response.json()
        self.assertIn('system_info', info_data)

        system_info = info_data['system_info']
        expected_fields = ['platform', 'cpu_count', 'memory_total', 'disk_usage']

        for field in expected_fields:
            self.assertIn(field, system_info)

        # Verify data types and reasonable values
        self.assertIsInstance(system_info['cpu_count'], int)
        self.assertGreater(system_info['cpu_count'], 0)

        self.assertIsInstance(system_info['memory_total'], (int, float))
        self.assertGreater(system_info['memory_total'], 0)

        self.assertIn('platform', system_info)
        self.assertIn(system_info['platform'], ['Windows', 'Linux', 'Darwin'])

        # Test detailed system info
        detailed_response = requests.get(f"{self.cdp_base}/system/info",
                                       params={"detailed": True})
        self.assertEqual(detailed_response.status_code, 200)

        detailed_data = detailed_response.json()
        detailed_info = detailed_data['system_info']

        # Should have additional details
        additional_fields = ['cpu_usage', 'memory_available', 'network_interfaces']
        for field in additional_fields:
            if field in detailed_info:
                self.assertIsNotNone(detailed_info[field])

    def test_process_monitoring(self):
        """Test system process monitoring"""
        response = requests.get(f"{self.cdp_base}/system/processes")
        self.assertEqual(response.status_code, 200)

        process_data = response.json()
        self.assertIn('processes', process_data)

        processes = process_data['processes']
        self.assertIsInstance(processes, list)
        self.assertGreater(len(processes), 0, "Should find system processes")

        # Verify process data structure
        if len(processes) > 0:
            process = processes[0]
            expected_fields = ['pid', 'name', 'cpu_percent', 'memory_percent']

            for field in expected_fields:
                if field in process:
                    self.assertIsNotNone(process[field])

        # Test filtered process monitoring
        filter_response = requests.get(f"{self.cdp_base}/system/processes",
                                     params={"filter": "chrome"})
        self.assertEqual(filter_response.status_code, 200)

        filtered_data = filter_response.json()
        filtered_processes = filtered_data['processes']

        # Should find Chrome processes (or none if not running)
        for process in filtered_processes:
            self.assertIn('chrome', process['name'].lower())

        # Test process monitoring with stats
        stats_response = requests.get(f"{self.cdp_base}/system/processes",
                                    params={"include_stats": True})
        self.assertEqual(stats_response.status_code, 200)

        stats_data = stats_response.json()
        if 'process_stats' in stats_data:
            stats = stats_data['process_stats']
            self.assertIn('total_processes', stats)
            self.assertIn('total_memory_usage', stats)

    def test_chrome_info_monitoring(self):
        """Test Chrome instance information and monitoring"""
        response = requests.get(f"{self.cdp_base}/system/chrome/info")
        self.assertEqual(response.status_code, 200)

        chrome_data = response.json()
        self.assertIn('chrome_info', chrome_data)

        chrome_info = chrome_data['chrome_info']
        expected_fields = ['version', 'debugging_enabled', 'tabs_count']

        for field in expected_fields:
            if field in chrome_info:
                self.assertIsNotNone(chrome_info[field])

        # If Chrome is running with debugging
        if chrome_info.get('debugging_enabled'):
            self.assertIn('debugging_port', chrome_info)
            self.assertIsInstance(chrome_info['debugging_port'], int)
            self.assertGreater(chrome_info['debugging_port'], 0)

            if 'tabs_count' in chrome_info:
                self.assertIsInstance(chrome_info['tabs_count'], int)
                self.assertGreaterEqual(chrome_info['tabs_count'], 0)

        # Test Chrome process monitoring
        chrome_processes_response = requests.get(f"{self.cdp_base}/system/chrome/info",
                                                params={"include_processes": True})
        self.assertEqual(chrome_processes_response.status_code, 200)

        chrome_proc_data = chrome_processes_response.json()
        if 'chrome_processes' in chrome_proc_data['chrome_info']:
            processes = chrome_proc_data['chrome_info']['chrome_processes']
            self.assertIsInstance(processes, list)

    def test_system_command_security(self):
        """Test system command security and restrictions"""
        # Test potentially dangerous commands that should be restricted
        dangerous_commands = [
            {"command": "rm", "args": ["-rf", "/"]},
            {"command": "del", "args": ["/F", "/S", "/Q", "C:\\"]},
            {"command": "format", "args": ["C:"]},
            {"command": "shutdown", "args": ["-h", "now"]},
        ]

        for dangerous_cmd in dangerous_commands:
            with self.subTest(command=dangerous_cmd["command"]):
                response = requests.post(f"{self.cdp_base}/system/execute",
                                       json=dangerous_cmd)

                # Should either reject the command or handle it safely
                if response.status_code == 200:
                    exec_data = response.json()
                    if 'execution_result' in exec_data:
                        result = exec_data['execution_result']
                        # Should not succeed with dangerous operations
                        self.assertNotEqual(result.get('return_code'), 0,
                                          f"Dangerous command {dangerous_cmd['command']} should not succeed")
                else:
                    # Command was rejected, which is appropriate
                    self.assertIn(response.status_code, [400, 403, 405])

    def test_system_performance_monitoring(self):
        """Test system performance monitoring during operations"""
        # Get baseline system info
        baseline_response = requests.get(f"{self.cdp_base}/system/info",
                                       params={"detailed": True})
        self.assertEqual(baseline_response.status_code, 200)

        baseline_data = baseline_response.json()['system_info']

        # Perform some system operations
        operations = [
            {"command": "echo", "args": ["test1"]},
            {"command": "echo", "args": ["test2"]},
            {"command": "echo", "args": ["test3"]}
        ]

        for op in operations:
            requests.post(f"{self.cdp_base}/system/execute", json=op)
            time.sleep(0.1)  # Brief pause

        # Get post-operation system info
        post_op_response = requests.get(f"{self.cdp_base}/system/info",
                                      params={"detailed": True})
        self.assertEqual(post_op_response.status_code, 200)

        post_op_data = post_op_response.json()['system_info']

        # Verify system is still stable
        if 'cpu_usage' in baseline_data and 'cpu_usage' in post_op_data:
            # CPU usage should be reasonable
            self.assertLess(post_op_data['cpu_usage'], 90,
                          "CPU usage should not spike excessively")

        if 'memory_available' in baseline_data and 'memory_available' in post_op_data:
            # Memory should not have dropped dramatically
            memory_change = baseline_data['memory_available'] - post_op_data['memory_available']
            self.assertLess(abs(memory_change), baseline_data['memory_available'] * 0.1,
                          "Memory usage should not change dramatically")

    def test_system_error_handling(self):
        """Test system command error handling"""
        # Test non-existent command
        nonexistent_response = requests.post(f"{self.cdp_base}/system/execute",
                                           json={"command": "nonexistent_command_12345"})

        if nonexistent_response.status_code == 200:
            exec_data = nonexistent_response.json()
            if 'execution_result' in exec_data:
                result = exec_data['execution_result']
                # Should have non-zero return code for non-existent command
                self.assertNotEqual(result['return_code'], 0)
        else:
            # Command was rejected, which is also acceptable
            self.assertIn(nonexistent_response.status_code, [400, 404])

        # Test command with invalid arguments
        invalid_args_response = requests.post(f"{self.cdp_base}/system/execute",
                                            json={
                                                "command": "ls" if platform.system() != "Windows" else "dir",
                                                "args": ["--invalid-flag-that-does-not-exist"]
                                            })

        if invalid_args_response.status_code == 200:
            exec_data = invalid_args_response.json()
            if 'execution_result' in exec_data:
                result = exec_data['execution_result']
                # Should have error output or non-zero return code
                self.assertTrue(
                    result['return_code'] != 0 or len(result['stderr']) > 0,
                    "Invalid arguments should produce error"
                )

        # Test command timeout
        timeout_response = requests.post(f"{self.cdp_base}/system/execute",
                                       json={
                                           "command": "sleep" if platform.system() != "Windows" else "timeout",
                                           "args": ["10"] if platform.system() != "Windows" else ["/T", "10"],
                                           "timeout": 1  # 1 second timeout
                                       })

        if timeout_response.status_code == 200:
            exec_data = timeout_response.json()
            if 'execution_result' in exec_data:
                result = exec_data['execution_result']
                # Should indicate timeout occurred
                self.assertTrue(
                    'timeout' in result or result['return_code'] != 0,
                    "Command timeout should be handled"
                )