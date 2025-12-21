"""
WOEplanet Spelunker: common package; paths module.
"""

import os
from pathlib import Path


def get_root_path() -> Path:
    """
    Return the root path of the project.
    """

    # check if running inside a container?
    if root_path := os.getenv('PROJECT_ROOT_PATH'):
        return Path(root_path)

    return Path(__file__).parent.parent.parent.parent
