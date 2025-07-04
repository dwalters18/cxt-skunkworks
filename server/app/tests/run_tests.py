#!/usr/bin/env python3
"""
TMS PRD Alignment Test Runner

This script provides a comprehensive test runner for all TMS validation tests,
including PRD alignment, schema validation, API compatibility, and integration tests.

Usage:
    python run_tests.py [options]
    python run_tests.py --suite prd
    python run_tests.py --suite all --coverage
    python run_tests.py --integration --verbose
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional, Dict
import json
from datetime import datetime


class TMSTestRunner:
    """Comprehensive test runner for TMS PRD alignment validation"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.app_dir = self.test_dir.parent  # server/app
        self.project_root = self.app_dir.parent.parent  # cxt-skunkworks root
        self.results = {}
        
        # Set up Python path for imports
        if str(self.app_dir) not in sys.path:
            sys.path.insert(0, str(self.app_dir))
        
    def run_command(self, cmd: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result"""
        print(f"Running: {' '.join(cmd)}")
        
        # Set up environment with correct Python path
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.app_dir) + ':' + env.get('PYTHONPATH', '')
        
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  cwd=self.app_dir, env=env)
        else:
            result = subprocess.run(cmd, cwd=self.app_dir, env=env)
            
        return result

    def install_test_dependencies(self) -> bool:
        """Install test dependencies from test_requirements.txt"""
        requirements_file = self.test_dir / "test_requirements.txt"

        if not requirements_file.exists():
            print("Warning: test_requirements.txt not found. Skipping dependency installation.")
            return True

        print("Installing test dependencies...")
        result = self.run_command([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])

        if result.returncode != 0:
            print(f"Failed to install test dependencies: {result.stderr}")
            return False

        print("Test dependencies installed successfully.")
        return True

    def run_prd_alignment_tests(self, verbose: bool = False, coverage: bool = False) -> bool:
        """Run PRD alignment validation tests"""
        print("\n=== Running PRD Alignment Tests ===")

        cmd = ['python', '-m', 'pytest', '-m', 'prd']
        if verbose:
            cmd.append('-v')
        if coverage:
            cmd.extend(['--cov=../models', '--cov-report=term-missing'])
        
        result = self.run_command(cmd)
        success = result.returncode == 0
        self.results['prd_alignment'] = {
            'status': 'PASSED' if success else 'FAILED',
            'output': result.stdout,
            'errors': result.stderr
        }
        return success

    def run_schema_validation_tests(self, verbose: bool = False, coverage: bool = False) -> bool:
        """Run database schema validation tests"""
        print("\n=== Running Schema Validation Tests ===")

        cmd = ['python', '-m', 'pytest', '-m', 'schema']
        if verbose:
            cmd.append('-v')
        if coverage:
            cmd.extend(['--cov=../models', '--cov-report=term-missing'])
        
        result = self.run_command(cmd)
        success = result.returncode == 0
        self.results['schema_validation'] = {
            'status': 'PASSED' if success else 'FAILED',
            'output': result.stdout,
            'errors': result.stderr
        }
        return success

    def run_api_compatibility_tests(self, verbose: bool = False, coverage: bool = False) -> bool:
        """Run API compatibility tests"""
        print("\n=== Running API Compatibility Tests ===")

        cmd = ['python', '-m', 'pytest', '-m', 'api']
        if verbose:
            cmd.append('-v')
        if coverage:
            cmd.extend(['--cov=../models', '--cov-report=term-missing'])
        
        result = self.run_command(cmd)
        success = result.returncode == 0
        self.results['api_compatibility'] = {
            'status': 'PASSED' if success else 'FAILED',
            'output': result.stdout,
            'errors': result.stderr
        }
        return success

    def run_smoke_tests(self, verbose: bool = False) -> bool:
        """Run quick smoke tests"""
        print("\n=== Running Smoke Tests ===")

        cmd = ['python', '-m', 'pytest', '-m', 'smoke', '--tb=line']
        if verbose:
            cmd.append('-v')
        
        result = self.run_command(cmd)
        success = result.returncode == 0
        self.results['smoke'] = {
            'status': 'PASSED' if success else 'FAILED',
            'output': result.stdout,
            'errors': result.stderr
        }
        return success

    def run_integration_tests(self, verbose: bool = False) -> Dict:
        """Run integration tests (requires external services)"""
        print("\n=== Running Integration Tests ===")
        print("Warning: Integration tests require external services (PostgreSQL, Kafka, etc.)")

        cmd = [sys.executable, "-m", "pytest", "-m", "integration"]

        if verbose:
            cmd.append("-v")

        result = self.run_command(cmd)

        return {
            "suite": "integration",
            "passed": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    def run_all_tests(self, verbose: bool = False, coverage: bool = False,
                     include_integration: bool = False) -> Dict:
        """Run all test suites"""
        print("\n=== Running All Test Suites ===")

        cmd = [sys.executable, "-m", "pytest"]

        if verbose:
            cmd.append("-v")
        if coverage:
            cmd.extend([
                "--cov=server/app/models",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-fail-under=80"
            ])

        if not include_integration:
            cmd.extend(["-m", "not integration"])

        result = self.run_command(cmd)

        return {
            "suite": "all",
            "passed": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    def generate_report(self, results: List[Dict]) -> str:
        """Generate a test report"""
        report = []
        report.append("TMS PRD Alignment Test Report")
        report.append("=" * 40)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        total_suites = len(results)
        passed_suites = sum(1 for r in results if r["passed"])

        report.append(f"Test Suites: {passed_suites}/{total_suites} passed")
        report.append("")

        for result in results:
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            report.append(f"{result['suite']}: {status}")

            if not result["passed"] and result.get("stderr"):
                report.append(f"  Error: {result['stderr'][:200]}...")

        report.append("")

        if passed_suites == total_suites:
            report.append("🎉 All tests passed! TMS data models are aligned with PRDs.")
        else:
            report.append("⚠️  Some tests failed. Please review and fix alignment issues.")

        return "\n".join(report)

    def save_results(self, results: List[Dict], output_file: str = "test_results.json"):
        """Save test results to a JSON file"""
        output_path = self.test_dir / output_file

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "total_suites": len(results),
                "passed_suites": sum(1 for r in results if r["passed"]),
                "failed_suites": sum(1 for r in results if not r["passed"])
            }
        }

        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"Test results saved to: {output_path}")


def main():
    """Main entry point for the test runner"""
    parser = argparse.ArgumentParser(
        description="TMS PRD Alignment Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --suite prd
  python run_tests.py --suite all --coverage
  python run_tests.py --integration --verbose
  python run_tests.py --smoke
        """
    )

    parser.add_argument(
        "--suite",
        choices=["prd", "schema", "api", "integration", "smoke", "all"],
        default="all",
        help="Test suite to run (default: all)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Enable coverage reporting"
    )

    parser.add_argument(
        "--integration", "-i",
        action="store_true",
        help="Include integration tests (requires external services)"
    )

    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running tests"
    )

    parser.add_argument(
        "--output", "-o",
        default="test_results.json",
        help="Output file for test results (default: test_results.json)"
    )

    args = parser.parse_args()

    runner = TMSTestRunner()
    results = []

    # Install dependencies if requested
    if args.install_deps:
        if not runner.install_test_dependencies():
            sys.exit(1)

    try:
        # Run specified test suites
        if args.suite == "prd":
            results.append(runner.run_prd_alignment_tests(args.verbose, args.coverage))
        elif args.suite == "schema":
            results.append(runner.run_schema_validation_tests(args.verbose, args.coverage))
        elif args.suite == "api":
            results.append(runner.run_api_compatibility_tests(args.verbose, args.coverage))
        elif args.suite == "integration":
            results.append(runner.run_integration_tests(args.verbose))
        elif args.suite == "smoke":
            results.append(runner.run_smoke_tests(args.verbose))
        elif args.suite == "all":
            results.append(runner.run_prd_alignment_tests(args.verbose, args.coverage))
            results.append(runner.run_schema_validation_tests(args.verbose, args.coverage))
            results.append(runner.run_api_compatibility_tests(args.verbose, args.coverage))
            results.append(runner.run_smoke_tests(args.verbose))

            if args.integration:
                results.append(runner.run_integration_tests(args.verbose))

        # Generate and display report
        report = runner.generate_report(results)
        print("\n" + report)

        # Save results
        runner.save_results(results, args.output)

        # Exit with failure if any tests failed
        if not all(r["passed"] for r in results):
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nTest run interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
