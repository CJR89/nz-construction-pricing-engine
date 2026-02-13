"""Test runner script"""

import subprocess
import sys

def run_tests():
    """Run all tests"""
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-v"],
        cwd="/home/runner/work/nz-construction-pricing-engine/nz-construction-pricing-engine"
    )
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
