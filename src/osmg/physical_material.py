"""
Model Generator for OpenSees ~ physical material
"""

#                          __
#   ____  ____ ___  ____ _/ /
#  / __ \/ __ `__ \/ __ `/ /
# / /_/ / / / / / / /_/ /_/
# \____/_/ /_/ /_/\__, (_)
#                /____/
#
# https://github.com/ioannis-vm/OpenSees_Model_Generator

from __future__ import annotations
from dataclasses import dataclass
from . import common


@dataclass
class PhysicalMaterial:
    """
    Physical material.
    We use this for self-weight, plotting enhancements etc.
    """
    uid: int
    name: str
    variety: str
    density: float
    E: float
    G: float