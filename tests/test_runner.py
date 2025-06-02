"""
Test runner script for the unicef-geospatial project.
Provides utilities to run all tests with various configurations.
"""

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath("unicef_geospatial"))

from utils.initialize import initialize_earth_engine

load_dotenv(override=True)


class TestRunner:
    """Test runner for the unicef-geospatial project."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent / "unicef_geospatial"
        self.test_dir = Path(__file__).parent

        initialize_earth_engine(os.environ["PATH_TO_EE_AUTH"])

    def run_all_tests(self):
        """Run all tests with optional coverage reporting."""
        args = [
            "-v",
            "--tb=short",
            "--maxfail=5",
        ]

        # Filter out empty strings
        args = [arg for arg in args if arg]

        return pytest.main(args + [str(self.test_dir)])


def main():
    """Main entry point for the test runner."""

    runner = TestRunner()
    runner.run_all_tests()


if __name__ == "__main__":
    main()
