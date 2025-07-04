"""
TMS Test Package

This package contains comprehensive validation tests for the Transportation
Management System (TMS) to ensure PRD alignment and data integrity.
"""
import sys
import os

# Add the parent directory to the Python path for imports
_current_dir = os.path.dirname(__file__)
_app_dir = os.path.join(_current_dir, '..')
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)
