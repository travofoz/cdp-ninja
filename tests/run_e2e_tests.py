#!/usr/bin/env python3
"""
CDP Ninja E2E Test Runner

Run domain-based tests to validate endpoint consistency and prevent regressions.

Usage:
    # Run all tests
    python tests/run_e2e_tests.py

    # Run specific domain
    python tests/run_e2e_tests.py --domain console

    # Run with verbose output
    python tests/run_e2e_tests.py --verbose

Prerequisites:
    1. Chrome running with --remote-debugging-port=9222
    2. CDP Ninja bridge running on localhost:8888 (via tunnel)
    3. Demo site available at cdp-ninja-test.meatspace.lol
"""

import unittest
import sys
import argparse
import requests
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from e2e.test_console_domain import TestConsoleDomain
from e2e.test_network_domain import TestNetworkDomain
from e2e.test_performance_domain import TestPerformanceDomain
from e2e.test_dom_domain import TestDOMDomain
from e2e.test_security_domain import TestSecurityDomain
from e2e.test_accessibility_domain import TestAccessibilityDomain
from e2e.test_error_handling_domain import TestErrorHandlingDomain
from e2e.test_stress_testing_domain import TestStressTestingDomain
from e2e.test_browser_interaction_domain import TestBrowserInteractionDomain
from e2e.test_navigation_domain import TestNavigationDomain
from e2e.test_js_debugging_domain import TestJSDebuggingDomain
from e2e.test_system_domain import TestSystemDomain


def check_prerequisites():
    """Check that required services are running"""
    errors = []

    # Check CDP Ninja bridge
    try:
        response = requests.get("http://localhost:8888/cdp/status", timeout=5)
        if response.status_code != 200:
            errors.append("CDP Ninja bridge not responding correctly")
    except requests.RequestException:
        errors.append("CDP Ninja bridge not accessible at localhost:8888")

    # Check demo site
    try:
        response = requests.get("http://cdp-ninja-test.meatspace.lol", timeout=5)
        if response.status_code != 200:
            errors.append("Demo site not accessible at cdp-ninja-test.meatspace.lol")
    except requests.RequestException:
        errors.append("Demo site not accessible at cdp-ninja-test.meatspace.lol")

    return errors


def create_test_suite(domain=None):
    """Create test suite for specified domain or all domains"""
    suite = unittest.TestSuite()

    domain_tests = {
        'console': TestConsoleDomain,
        'network': TestNetworkDomain,
        'performance': TestPerformanceDomain,
        'dom': TestDOMDomain,
        'security': TestSecurityDomain,
        'accessibility': TestAccessibilityDomain,
        'error_handling': TestErrorHandlingDomain,
        'stress_testing': TestStressTestingDomain,
        'browser_interaction': TestBrowserInteractionDomain,
        'navigation': TestNavigationDomain,
        'js_debugging': TestJSDebuggingDomain,
        'system': TestSystemDomain,
    }

    if domain:
        if domain.lower() in domain_tests:
            suite.addTest(unittest.TestLoader().loadTestsFromTestCase(
                domain_tests[domain.lower()]
            ))
        else:
            print(f"Unknown domain: {domain}")
            print(f"Available domains: {', '.join(domain_tests.keys())}")
            sys.exit(1)
    else:
        # Add all domain tests
        for test_class in domain_tests.values():
            suite.addTest(unittest.TestLoader().loadTestsFromTestCase(test_class))

    return suite


def main():
    parser = argparse.ArgumentParser(description='Run CDP Ninja E2E tests')
    parser.add_argument('--domain', '-d', help='Run tests for specific domain')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose test output')
    parser.add_argument('--skip-prereq-check', action='store_true',
                       help='Skip prerequisite checks')

    args = parser.parse_args()

    # Check prerequisites unless skipped
    if not args.skip_prereq_check:
        print("Checking prerequisites...")
        errors = check_prerequisites()
        if errors:
            print("❌ Prerequisites not met:")
            for error in errors:
                print(f"  - {error}")
            print("\nSetup instructions:")
            print("1. Start Chrome: chrome --remote-debugging-port=9222")
            print("2. Start CDP Ninja bridge: cdp-ninja --bridge-port 8888")
            print("3. Setup SSH tunnel: ssh -R 8888:localhost:8888 user@server")
            print("4. Create demo site at cdp-ninja-test.meatspace.lol")
            sys.exit(1)
        print("✅ Prerequisites OK")

    # Create and run test suite
    suite = create_test_suite(args.domain)

    # Configure test runner
    verbosity = 2 if args.verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)

    print(f"\nRunning CDP Ninja E2E tests{' for ' + args.domain + ' domain' if args.domain else ''}...")
    result = runner.run(suite)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print(f"\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")

    if not result.failures and not result.errors:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()