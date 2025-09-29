"""
E2E Tests for Stress Testing Domain Endpoints

Tests memory bombs, CPU burns, click storms, and chaos testing
for breaking point discovery and structural assault.
"""

import requests
import time
from typing import Dict, Any
from .base_test import CDPNinjaE2ETest


class TestStressTestingDomain(CDPNinjaE2ETest):
    """Test Stress Testing domain endpoints for chaos engineering"""

    def test_memory_bomb_basic(self):
        """Test basic memory bomb stress testing"""
        # Navigate to memory bomb test target
        self.navigate_to(f"{self.demo_base}/stress-memory-bomb-target.html")
        self.wait_for_events()

        # Trigger memory bomb (small scale for testing)
        response = requests.post(f"{self.cdp_base}/cdp/stress/memory_bomb",
                               json={
                                   "size_mb": 50,  # Small for testing
                                   "duration": 3,   # Short duration
                                   "pattern": "linear"
                               })
        self.assertEqual(response.status_code, 200)

        bomb_data = response.json()
        self.assertIn('memory_bomb', bomb_data)

        bomb = bomb_data['memory_bomb']
        self.assertIn('allocated_memory', bomb)
        self.assertIn('peak_usage', bomb)
        self.assertIn('duration', bomb)

    def test_cpu_burn_stress(self):
        """Test CPU burn stress testing"""
        # Navigate to CPU burn test target
        self.navigate_to(f"{self.demo_base}/stress-cpu-burn-target.html")
        self.wait_for_events()

        # Trigger CPU burn (limited for testing)
        response = requests.post(f"{self.cdp_base}/cdp/stress/cpu_burn",
                               json={
                                   "intensity": 50,  # 50% intensity
                                   "duration": 3,    # 3 seconds
                                   "threads": 2      # Limited threads
                               })
        self.assertEqual(response.status_code, 200)

        burn_data = response.json()
        self.assertIn('cpu_burn', burn_data)

        burn = burn_data['cpu_burn']
        self.assertIn('cpu_usage_peak', burn)
        self.assertIn('duration_actual', burn)
        self.assertIn('threads_used', burn)

    def test_click_storm_advanced(self):
        """Test click storm stress testing"""
        # Navigate to click storm target
        self.navigate_to(f"{self.demo_base}/stress-click-storm-target.html")
        self.wait_for_events()

        # Trigger click storm
        response = requests.post(f"{self.cdp_base}/cdp/stress/click_storm",
                               json={
                                   "target_selector": "#stress-button",
                                   "clicks_per_second": 10,  # Moderate rate
                                   "duration": 2,            # Short duration
                                   "randomize_timing": True
                               })
        self.assertEqual(response.status_code, 200)

        storm_data = response.json()
        self.assertIn('click_storm', storm_data)

        storm = storm_data['click_storm']
        self.assertIn('total_clicks', storm)
        self.assertIn('successful_clicks', storm)
        self.assertIn('click_rate_actual', storm)

    def test_input_overflow_stress(self):
        """Test input overflow stress testing"""
        # Navigate to input overflow target
        self.navigate_to(f"{self.demo_base}/stress-input-overflow-target.html")
        self.wait_for_events()

        # Trigger input overflow
        response = requests.post(f"{self.cdp_base}/cdp/stress/input_overflow",
                               json={
                                   "target_selector": "#stress-input",
                                   "input_size": 1000,    # 1KB input
                                   "input_pattern": "random",
                                   "flood_rate": 5        # 5 inputs per second
                               })
        self.assertEqual(response.status_code, 200)

        overflow_data = response.json()
        self.assertIn('input_overflow', overflow_data)

        overflow = overflow_data['input_overflow']
        self.assertIn('inputs_sent', overflow)
        self.assertIn('overflow_detected', overflow)

    def test_storage_flood_stress(self):
        """Test storage flood stress testing"""
        # Navigate to storage flood target
        self.navigate_to(f"{self.demo_base}/stress-storage-flood-target.html")
        self.wait_for_events()

        # Trigger storage flood
        response = requests.post(f"{self.cdp_base}/cdp/stress/storage_flood",
                               json={
                                   "storage_type": "localStorage",
                                   "data_size_kb": 100,  # 100KB total
                                   "chunk_size": 10,     # 10KB chunks
                                   "flood_rate": 2       # 2 chunks per second
                               })
        self.assertEqual(response.status_code, 200)

        flood_data = response.json()
        self.assertIn('storage_flood', flood_data)

        flood = flood_data['storage_flood']
        self.assertIn('storage_used', flood)
        self.assertIn('chunks_written', flood)
        self.assertIn('storage_limit_reached', flood)

    def test_chaos_monkey_testing(self):
        """Test chaos monkey random stress testing"""
        # Navigate to chaos monkey target
        self.navigate_to(f"{self.demo_base}/stress-chaos-monkey-target.html")
        self.wait_for_events()

        # Trigger chaos monkey (limited chaos for testing)
        response = requests.post(f"{self.cdp_base}/cdp/stress/chaos_monkey",
                               json={
                                   "chaos_level": "low",     # Low chaos for testing
                                   "duration": 5,            # 5 seconds
                                   "target_elements": ["button", "input", "form"],
                                   "chaos_types": ["clicks", "inputs", "navigation"]
                               })
        self.assertEqual(response.status_code, 200)

        chaos_data = response.json()
        self.assertIn('chaos_monkey', chaos_data)

        chaos = chaos_data['chaos_monkey']
        self.assertIn('chaos_actions', chaos)
        self.assertIn('successful_actions', chaos)
        self.assertIn('errors_triggered', chaos)

    def test_race_conditions_stress(self):
        """Test race condition stress testing"""
        # Navigate to race condition target
        self.navigate_to(f"{self.demo_base}/stress-race-conditions-target.html")
        self.wait_for_events()

        # Trigger race condition testing
        response = requests.post(f"{self.cdp_base}/cdp/stress/race_conditions",
                               json={
                                   "concurrent_operations": 5,    # 5 concurrent ops
                                   "operation_type": "form_submit",
                                   "timing_variance": 100,        # 100ms variance
                                   "repetitions": 3               # 3 repetitions
                               })
        self.assertEqual(response.status_code, 200)

        race_data = response.json()
        self.assertIn('race_conditions', race_data)

        race = race_data['race_conditions']
        self.assertIn('race_attempts', race)
        self.assertIn('race_conditions_detected', race)
        self.assertIn('timing_analysis', race)

    def test_full_assault_stress(self):
        """Test full assault combined stress testing"""
        # Navigate to full assault target
        self.navigate_to(f"{self.demo_base}/stress-full-assault-target.html")
        self.wait_for_events()

        # Trigger full assault (reduced intensity for testing)
        response = requests.post(f"{self.cdp_base}/cdp/stress/full_assault",
                               json={
                                   "assault_level": "light",     # Light assault for testing
                                   "duration": 5,                # 5 seconds
                                   "components": ["memory", "cpu", "clicks", "inputs"],
                                   "intensity_ramp": True        # Gradually increase intensity
                               })
        self.assertEqual(response.status_code, 200)

        assault_data = response.json()
        self.assertIn('full_assault', assault_data)

        assault = assault_data['full_assault']
        self.assertIn('assault_components', assault)
        self.assertIn('peak_stress_level', assault)
        self.assertIn('breaking_points', assault)
        self.assertIn('recovery_analysis', assault)

    def test_memory_bomb_advanced(self):
        """Test advanced memory bomb with pattern analysis"""
        # Navigate to advanced memory bomb target
        self.navigate_to(f"{self.demo_base}/stress-memory-bomb-advanced.html")
        self.wait_for_events()

        # Test different memory patterns
        patterns = ["linear", "exponential", "spike", "sustained"]

        for pattern in patterns:
            with self.subTest(pattern=pattern):
                response = requests.post(f"{self.cdp_base}/cdp/stress/memory_bomb",
                                       json={
                                           "size_mb": 30,        # Small for testing
                                           "duration": 2,        # Short duration
                                           "pattern": pattern,
                                           "monitor_gc": True    # Monitor garbage collection
                                       })
                self.assertEqual(response.status_code, 200)

                bomb_data = response.json()
                self.assertIn('memory_bomb', bomb_data)

                bomb = bomb_data['memory_bomb']
                self.assertIn('pattern_used', bomb)
                self.assertEqual(bomb['pattern_used'], pattern)

    def test_stress_recovery_validation(self):
        """Test system recovery after stress testing"""
        # Run a stress test first
        self.navigate_to(f"{self.demo_base}/stress-recovery-test.html")
        self.wait_for_events()

        # Apply stress
        stress_response = requests.post(f"{self.cdp_base}/cdp/stress/cpu_burn",
                                      json={"intensity": 30, "duration": 2})
        self.assertEqual(stress_response.status_code, 200)

        # Wait for recovery
        self.wait_for_events(3)

        # Check system recovery
        recovery_response = requests.get(f"{self.cdp_base}/cdp/performance/metrics")
        self.assertEqual(recovery_response.status_code, 200)

        metrics_data = recovery_response.json()
        self.assertIn('metrics', metrics_data)

        # Verify system has recovered (basic check)
        metrics = metrics_data['metrics']
        memory_metrics = [m for m in metrics if 'Memory' in m.get('name', '')]
        self.assertGreater(len(memory_metrics), 0, "Should have memory metrics after stress test")