import os
import sys

# Add the package source directory to sys.path so that imports like
# 'from constants import ...' work. This allows the legacy script-style imports
# to function within the test environment.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../wizard_of_wor"))
)
