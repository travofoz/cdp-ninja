"""
E2E Tests for Performance Domain Endpoints

Tests performance metrics capture and consistency
across server vs pool CDPClient instances.
"""

import requests
import time
from typing import Dict, Any
from .base_test import CDPNinjaE2ETest


class TestPerformanceDomain(CDPNinjaE2ETest):
    """Test Performance domain endpoints for event consistency"""

    def test_performance_metrics_basic(self):
        """Test basic performance metrics capture"""
        # Navigate to performance test page
        self.navigate_to(f"{self.demo_base}/performance-heavy-page.html")
        self.wait_for_events()

        # Get performance metrics
        response = requests.get(f"{self.cdp_base}/cdp/performance/metrics")
        self.assertEqual(response.status_code, 200)

        metrics = response.json()
        self.assertIn('metrics', metrics)

        # Verify basic metrics are present
        metric_names = {m.get('name') for m in metrics['metrics']}
        expected_metrics = {'Timestamp', 'JSHeapUsedSize', 'JSHeapTotalSize'}

        for expected in expected_metrics:
            self.assertIn(expected, metric_names,
                         f"Expected performance metric {expected} not found")

    def test_memory_monitoring(self):
        """Test memory usage monitoring"""
        # Start memory monitoring
        start_response = requests.post(f"{self.cdp_base}/cdp/performance/memory_monitor",
                                     json={"enable": True, "interval": 1000})
        self.assertEqual(start_response.status_code, 200)

        # Navigate to memory-intensive page
        self.navigate_to(f"{self.demo_base}/performance-memory-leak.html")
        self.wait_for_events(3)

        # Get memory data
        response = requests.get(f"{self.cdp_base}/cdp/performance/memory_monitor")
        self.assertEqual(response.status_code, 200)

        memory_data = response.json()
        self.assertIn('memory_usage', memory_data)
        self.assertGreater(len(memory_data['memory_usage']), 0,
                          "Should capture memory usage data")

        # Stop monitoring
        requests.post(f"{self.cdp_base}/cdp/performance/memory_monitor",
                     json={"enable": False})

    def test_rendering_metrics(self):
        """Test rendering performance metrics"""
        # Navigate to page with rendering challenges
        self.navigate_to(f"{self.demo_base}/performance-rendering-heavy.html")
        self.wait_for_events()

        # Get rendering metrics
        response = requests.get(f"{self.cdp_base}/cdp/performance/rendering_metrics")
        self.assertEqual(response.status_code, 200)

        rendering_data = response.json()
        self.assertIn('rendering_metrics', rendering_data)

        # Verify key rendering metrics
        metrics = rendering_data['rendering_metrics']
        expected_fields = ['paint_events', 'layout_events', 'composite_events']

        for field in expected_fields:
            self.assertIn(field, metrics,
                         f"Rendering metrics should include {field}")

    def test_cpu_profiling(self):
        """Test CPU profiling functionality"""
        # Start CPU profiling
        start_response = requests.post(f"{self.cdp_base}/cdp/performance/cpu_profiling",
                                     json={"action": "start", "duration": 3})
        self.assertEqual(start_response.status_code, 200)

        # Navigate to CPU-intensive page
        self.navigate_to(f"{self.demo_base}/performance-cpu-intensive.html")
        self.wait_for_events(4)  # Wait for profiling to complete

        # Get profiling results
        results_response = requests.post(f"{self.cdp_base}/cdp/performance/cpu_profiling",
                                       json={"action": "get_results"})
        self.assertEqual(results_response.status_code, 200)

        profile_data = results_response.json()
        self.assertIn('profile', profile_data)

        # Verify profile contains expected data
        profile = profile_data['profile']
        self.assertIn('nodes', profile)
        self.assertGreater(len(profile['nodes']), 0,
                          "CPU profile should contain execution nodes")

    def test_resource_timing(self):
        """Test resource timing analysis"""
        # Navigate to page with multiple resources
        self.navigate_to(f"{self.demo_base}/performance-multiple-resources.html")
        self.wait_for_events()

        # Get resource timing
        response = requests.get(f"{self.cdp_base}/cdp/performance/resource_timing")
        self.assertEqual(response.status_code, 200)

        timing_data = response.json()
        self.assertIn('resource_timing', timing_data)

        resources = timing_data['resource_timing']
        self.assertGreater(len(resources), 0, "Should capture resource timing data")

        # Verify timing data structure
        for resource in resources:
            self.assertIn('name', resource)
            self.assertIn('duration', resource)
            self.assertIn('transferSize', resource)

    def test_background_tasks_monitoring(self):
        """Test background task monitoring"""
        # Enable background task monitoring
        enable_response = requests.post(f"{self.cdp_base}/cdp/performance/background_tasks",
                                      json={"enable": True})
        self.assertEqual(enable_response.status_code, 200)

        # Navigate to page with background tasks
        self.navigate_to(f"{self.demo_base}/performance-background-tasks.html")
        self.wait_for_events(3)

        # Get background task data
        response = requests.get(f"{self.cdp_base}/cdp/performance/background_tasks")
        self.assertEqual(response.status_code, 200)

        task_data = response.json()
        self.assertIn('background_tasks', task_data)

        # Disable monitoring
        requests.post(f"{self.cdp_base}/cdp/performance/background_tasks",
                     json={"enable": False})

    def test_core_web_vitals(self):
        """Test Core Web Vitals measurement"""
        # Navigate to page for Core Web Vitals testing
        self.navigate_to(f"{self.demo_base}/performance-web-vitals.html")
        self.wait_for_events(3)

        # Get Core Web Vitals
        response = requests.get(f"{self.cdp_base}/cdp/performance/core_web_vitals")
        self.assertEqual(response.status_code, 200)

        vitals_data = response.json()
        self.assertIn('core_web_vitals', vitals_data)

        vitals = vitals_data['core_web_vitals']

        # Check for key Core Web Vitals metrics
        expected_vitals = ['LCP', 'FID', 'CLS']
        for vital in expected_vitals:
            if vital in vitals:
                self.assertIsInstance(vitals[vital], (int, float),
                                    f"{vital} should be a numeric value")

    def test_performance_budget_tracking(self):
        """Test performance budget tracking"""
        # Set performance budgets
        budget_config = {
            "budgets": {
                "loadTime": 3000,  # 3 seconds
                "firstContentfulPaint": 1500,  # 1.5 seconds
                "jsSize": 500000  # 500KB
            }
        }

        budget_response = requests.post(f"{self.cdp_base}/cdp/performance/budget_tracking",
                                      json=budget_config)
        self.assertEqual(budget_response.status_code, 200)

        # Navigate to page that may exceed budgets
        self.navigate_to(f"{self.demo_base}/performance-budget-test.html")
        self.wait_for_events()

        # Get budget tracking results
        response = requests.get(f"{self.cdp_base}/cdp/performance/budget_tracking")
        self.assertEqual(response.status_code, 200)

        budget_data = response.json()
        self.assertIn('budget_results', budget_data)

        results = budget_data['budget_results']
        self.assertIn('violations', results)
        self.assertIn('metrics', results)

    def test_optimization_recommendations(self):
        """Test performance optimization recommendations"""
        # Navigate to page with optimization opportunities
        self.navigate_to(f"{self.demo_base}/performance-optimization-needed.html")
        self.wait_for_events()

        # Get optimization recommendations
        response = requests.get(f"{self.cdp_base}/cdp/performance/optimization_recommendations")
        self.assertEqual(response.status_code, 200)

        recommendations = response.json()
        self.assertIn('recommendations', recommendations)

        # Verify recommendation structure
        if len(recommendations['recommendations']) > 0:
            rec = recommendations['recommendations'][0]
            self.assertIn('category', rec)
            self.assertIn('priority', rec)
            self.assertIn('description', rec)

    def test_optimization_impact_analysis(self):
        """Test optimization impact analysis"""
        # Perform optimization impact analysis
        analysis_config = {
            "baseline_url": f"{self.demo_base}/performance-baseline",
            "optimized_url": f"{self.demo_base}/performance-optimized",
            "metrics": ["loadTime", "firstContentfulPaint", "largestContentfulPaint"]
        }

        response = requests.post(f"{self.cdp_base}/cdp/performance/optimization_impact",
                               json=analysis_config)
        self.assertEqual(response.status_code, 200)

        impact_data = response.json()
        self.assertIn('impact_analysis', impact_data)

        analysis = impact_data['impact_analysis']
        self.assertIn('baseline_metrics', analysis)
        self.assertIn('optimized_metrics', analysis)
        self.assertIn('improvements', analysis)

    def test_performance_cross_instance_consistency(self):
        """Test performance events consistency across CDPClient instances"""
        # Generate performance events
        self.navigate_to(f"{self.demo_base}/performance-events-test.html")
        self.wait_for_events()

        # Test cross-instance consistency for Performance domain
        expected_events = ["Performance.metrics"]
        self.assert_event_consistency("Performance", expected_events)