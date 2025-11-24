"""
Test runner script for Jarvis Personal Secretary
Run this script to verify all functions are working after code changes.

Usage:
    python scripts/run_tests.py              # Run all tests
    python scripts/run_tests.py --verbose    # Run with verbose output
    python scripts/run_tests.py --coverage   # Run with coverage report
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def run_tests(verbose=False, coverage=False, specific_test=None):
    """Run pytest test suite"""
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")  # Quiet mode for cleaner output
    
    if coverage:
        cmd.extend(["--cov=src", "--cov=jarvis_chat", "--cov-report=term-missing"])
    
    if specific_test:
        cmd.append(str(Path(specific_test)))
    else:
        cmd.append(str(Path("tests")))
    
    # Add color output
    cmd.append("--color=yes")
    
    print("=" * 70)
    print("Running Jarvis Test Suite")
    print("=" * 70)
    print()
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run Jarvis test suite")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "-t", "--test",
        type=str,
        help="Run a specific test file or test function"
    )
    
    args = parser.parse_args()
    
    success = run_tests(
        verbose=args.verbose,
        coverage=args.coverage,
        specific_test=args.test
    )
    
    print()
    print("=" * 70)
    if success:
        print("[SUCCESS] All tests passed!")
    else:
        print("[FAILED] Some tests failed. Please review the output above.")
    print("=" * 70)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

