import os
import sys

# Add the package source directory (wizard_of_wor/wizard_of_wor) to sys.path
# so that internal imports like 'from constants import ...' work.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../wizard_of_wor"))
)
# Add the package root directory (wizard_of_wor/) to sys.path
# so that test imports like 'from wizard_of_wor.game import ...' work.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
