"""
E2E Tests for JavaScript Debugging Domain Endpoints

Tests advanced JavaScript debugging, async analysis,
and runtime evaluation capabilities.
"""

import requests
import time
from typing import Dict, Any
from .base_test import CDPNinjaE2ETest


class TestJSDebuggingDomain(CDPNinjaE2ETest):
    """Test JavaScript Debugging domain endpoints for JS analysis"""

    def test_advanced_javascript_debugging(self):
        """Test advanced JavaScript debugging capabilities"""
        # Navigate to JavaScript debugging test page
        self.navigate_to(f"{self.demo_base}/js-debugging-advanced.html")
        self.wait_for_events()

        # Start advanced debugging session
        response = requests.post(f"{self.cdp_base}/cdp/js/advanced_debugging",
                               json={
                                   "debug_mode": "comprehensive",
                                   "track_variables": True,
                                   "monitor_scope": True,
                                   "capture_stack_traces": True
                               })
        self.assertEqual(response.status_code, 200)

        debug_data = response.json()
        self.assertIn('debug_session', debug_data)

        debug_session = debug_data['debug_session']
        expected_fields = ['session_id', 'breakpoints_set', 'scope_monitoring']

        for field in expected_fields:
            self.assertIn(field, debug_session)

        # Test variable inspection
        variables_response = requests.post(f"{self.cdp_base}/cdp/js/advanced_debugging",
                                         json={
                                             "action": "inspect_variables",
                                             "scope": "global"
                                         })
        self.assertEqual(variables_response.status_code, 200)

        var_data = variables_response.json()
        self.assertIn('variable_inspection', var_data)

        # Test breakpoint management
        breakpoint_response = requests.post(f"{self.cdp_base}/cdp/js/advanced_debugging",
                                          json={
                                              "action": "set_breakpoint",
                                              "line": 42,
                                              "condition": "x > 10"
                                          })
        self.assertEqual(breakpoint_response.status_code, 200)

        bp_data = breakpoint_response.json()
        self.assertIn('breakpoint_result', bp_data)

        # Test step debugging
        step_response = requests.post(f"{self.cdp_base}/cdp/js/advanced_debugging",
                                    json={
                                        "action": "step_over",
                                        "step_count": 3
                                    })
        self.assertEqual(step_response.status_code, 200)

        # Test call stack analysis
        stack_response = requests.post(f"{self.cdp_base}/cdp/js/advanced_debugging",
                                     json={
                                         "action": "analyze_call_stack",
                                         "include_source": True
                                     })
        self.assertEqual(stack_response.status_code, 200)

        stack_data = stack_response.json()
        self.assertIn('call_stack_analysis', stack_data)

        # Test exception handling analysis
        exception_response = requests.post(f"{self.cdp_base}/cdp/js/advanced_debugging",
                                         json={
                                             "action": "analyze_exceptions",
                                             "pause_on_exceptions": True
                                         })
        self.assertEqual(exception_response.status_code, 200)

    def test_async_javascript_analysis(self):
        """Test asynchronous JavaScript analysis"""
        # Navigate to async JavaScript test page
        self.navigate_to(f"{self.demo_base}/js-async-analysis.html")
        self.wait_for_events()

        # Start async analysis
        response = requests.post(f"{self.cdp_base}/cdp/js/async_analysis",
                               json={
                                   "analysis_type": "comprehensive",
                                   "track_promises": True,
                                   "monitor_callbacks": True,
                                   "detect_deadlocks": True
                               })
        self.assertEqual(response.status_code, 200)

        async_data = response.json()
        self.assertIn('async_analysis', async_data)

        analysis = async_data['async_analysis']
        expected_components = ['promise_tracking', 'callback_monitoring', 'async_patterns']

        for component in expected_components:
            self.assertIn(component, analysis)

        # Test promise chain analysis
        promise_response = requests.post(f"{self.cdp_base}/cdp/js/async_analysis",
                                       json={
                                           "action": "analyze_promises",
                                           "track_rejections": True,
                                           "monitor_resolution_time": True
                                       })
        self.assertEqual(promise_response.status_code, 200)

        promise_data = promise_response.json()
        self.assertIn('promise_analysis', promise_data)

        promise_analysis = promise_data['promise_analysis']
        self.assertIn('promise_chains', promise_analysis)
        self.assertIn('unhandled_rejections', promise_analysis)

        # Test callback hell detection
        callback_response = requests.post(f"{self.cdp_base}/cdp/js/async_analysis",
                                        json={
                                            "action": "detect_callback_hell",
                                            "nesting_threshold": 3,
                                            "suggest_alternatives": True
                                        })
        self.assertEqual(callback_response.status_code, 200)

        callback_data = callback_response.json()
        self.assertIn('callback_analysis', callback_data)

        # Test async/await pattern analysis
        await_response = requests.post(f"{self.cdp_base}/cdp/js/async_analysis",
                                     json={
                                         "action": "analyze_async_await",
                                         "detect_anti_patterns": True,
                                         "performance_impact": True
                                     })
        self.assertEqual(await_response.status_code, 200)

        await_data = await_response.json()
        self.assertIn('async_await_analysis', await_data)

        # Test event loop monitoring
        event_loop_response = requests.post(f"{self.cdp_base}/cdp/js/async_analysis",
                                          json={
                                              "action": "monitor_event_loop",
                                              "duration": 3,  # 3 seconds
                                              "detect_blocking": True
                                          })
        self.assertEqual(event_loop_response.status_code, 200)

        loop_data = event_loop_response.json()
        self.assertIn('event_loop_analysis', loop_data)

        # Test race condition detection
        race_response = requests.post(f"{self.cdp_base}/cdp/js/async_analysis",
                                    json={
                                        "action": "detect_race_conditions",
                                        "concurrent_operations": True,
                                        "shared_state_access": True
                                    })
        self.assertEqual(race_response.status_code, 200)

        race_data = race_response.json()
        self.assertIn('race_condition_analysis', race_data)

        # Test deadlock detection
        deadlock_response = requests.post(f"{self.cdp_base}/cdp/js/async_analysis",
                                        json={
                                            "action": "detect_deadlocks",
                                            "dependency_analysis": True,
                                            "circular_wait_detection": True
                                        })
        self.assertEqual(deadlock_response.status_code, 200)

        deadlock_data = deadlock_response.json()
        self.assertIn('deadlock_analysis', deadlock_data)

    def test_javascript_error_archaeology(self):
        """Test JavaScript error archaeology and analysis"""
        # Navigate to JavaScript error test page
        self.navigate_to(f"{self.demo_base}/js-error-archaeology.html")
        self.wait_for_events()

        # Trigger JavaScript errors for analysis
        error_response = requests.post(f"{self.cdp_base}/cdp/execute",
                                     json={
                                         "expression": "throw new Error('Test error for archaeology');"
                                     })
        # Error expected
        self.wait_for_events()

        # Analyze JavaScript errors
        archaeology_response = requests.post(f"{self.cdp_base}/cdp/js/advanced_debugging",
                                           json={
                                               "action": "error_archaeology",
                                               "analyze_stack_traces": True,
                                               "correlate_events": True
                                           })
        self.assertEqual(archaeology_response.status_code, 200)

        archaeology_data = archaeology_response.json()
        self.assertIn('error_archaeology', archaeology_data)

        archaeology = archaeology_data['error_archaeology']
        self.assertIn('error_patterns', archaeology)
        self.assertIn('root_cause_analysis', archaeology)

    def test_runtime_evaluation_advanced(self):
        """Test advanced runtime evaluation capabilities"""
        # Navigate to runtime evaluation test page
        self.navigate_to(f"{self.demo_base}/js-runtime-evaluation.html")
        self.wait_for_events()

        # Test complex expression evaluation
        expressions = [
            "Math.max(...Array.from({length: 1000}, (_, i) => i))",
            "Promise.resolve(42).then(x => x * 2)",
            "new Set([1, 2, 3, 2, 1]).size",
            "Object.keys(window).filter(k => k.startsWith('on')).length"
        ]

        for expr in expressions:
            with self.subTest(expression=expr):
                eval_response = requests.post(f"{self.cdp_base}/cdp/execute",
                                            json={"expression": expr})
                self.assertEqual(eval_response.status_code, 200)

                eval_data = eval_response.json()
                self.assertIn('result', eval_data)

        # Test function injection and execution
        function_code = """
        function testFunction(a, b) {
            return a + b + Math.random();
        }
        testFunction(5, 10);
        """

        function_response = requests.post(f"{self.cdp_base}/cdp/execute",
                                        json={"expression": function_code})
        self.assertEqual(function_response.status_code, 200)

        # Test object inspection
        object_code = """
        const testObj = {
            name: 'test',
            value: 42,
            nested: { deep: 'value' },
            method: function() { return 'called'; }
        };
        testObj;
        """

        object_response = requests.post(f"{self.cdp_base}/cdp/execute",
                                      json={"expression": object_code})
        self.assertEqual(object_response.status_code, 200)

    def test_js_cross_instance_consistency(self):
        """Test JavaScript debugging events consistency across CDPClient instances"""
        # Navigate to JS events test page
        self.navigate_to(f"{self.demo_base}/js-events-test.html")
        self.wait_for_events()

        # Execute JavaScript that generates Runtime events
        js_response = requests.post(f"{self.cdp_base}/cdp/execute",
                                  json={"expression": "console.log('Debug test message');"})
        self.assertEqual(js_response.status_code, 200)

        self.wait_for_events()

        # Test cross-instance consistency for Runtime domain
        expected_events = ["Runtime.consoleAPICalled", "Runtime.evaluate"]
        self.assert_event_consistency("Runtime", expected_events)