"""
Model Generator for OpenSees ~ load case
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
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
import numpy as np
import numpy.typing as npt
from . import transformations
from .collections import NodePointLoadCollection
from .collections import NodeMassCollection
from .collections import LineElementUDLCollection

if TYPE_CHECKING:
    from .model import Model
    from .ops.element import elasticBeamColumn

nparr = npt.NDArray[np.float64]


@dataclass
class PointLoad:
    """
    Point load object. Global coordinate system.
    Attributes:
        other (list[float])
        floor (list[float])
    """
    other: list[float] = field(init=False, repr=False)
    floor: list[float] = field(init=False, repr=False)

    def __post_init__(self):
        self.other = [0.00]*6
        self.floor = [0.00]*6

    def add(self, load: list[float], kind='other'):
        """
        Adds a load to the existing load
        """
        assert hasattr(self, kind)
        assert(len(load) == len(self.other))
        current = getattr(self, kind)
        new = [c + o for c, o in zip(current, load)]
        setattr(self, kind, new)

    def total(self):
        """
        Returns the total load
        """
        return [o + f for o, f in zip(self.other, self.floor)]


@dataclass
class PointMass:
    """
    Point mass object. Global coordinate system.
    Attributes:
        mself (list[float])
        floor (list[float])
    """
    mself: list[float] = field(init=False, repr=False)
    floor: list[float] = field(init=False, repr=False)

    def __post_init__(self):
        self.mself = [0.00]*6
        self.floor = [0.00]*6

    def add(self, mass: list[float], kind='other'):
        """
        Adds a mass to the existing mass
        """
        assert hasattr(self, kind)
        assert(len(mass) == len(self.mself))
        current = getattr(self, kind)
        current = [c + o for c, o in zip(current, mass)]

    def total(self):
        """
        Returns the total mass
        """
        return [o + f for o, f in zip(self.mself, self.floor)]





@dataclass(repr=False)
class LineElementUDL:
    """

    """
    parent_line_element: elasticBeamColumn
    self_weight: nparr = field(
        default_factory=lambda: np.zeros(shape=3))
    floor_weight: nparr = field(
        default_factory=lambda: np.zeros(shape=3))
    floor_massless_load: nparr = field(
        default_factory=lambda: np.zeros(shape=3))
    other_load: nparr = field(
        default_factory=lambda: np.zeros(shape=3))

    def total(self):
        return (self.self_weight
                + self.floor_weight
                + self.floor_massless_load
                + self.other_load)

    def copy(self, other_parent_line_element) -> 'LineElementUDL':
        other = LineElementUDL(other_parent_line_element)
        other.self_weight = self.self_weight.copy()
        other.floor_weight = self.floor_weight.copy()
        other.floor_massless_load = self.floor_massless_load.copy()
        other.other_load = self.other_load.copy()
        return other

    def add_glob(self, udl: nparr, ltype='other_load'):
        """
        Adds a uniformly distributed load
        to the existing udl
        The load is defined
        with respect to the global coordinate system
        of the building, and it is converted to the
        local coordinate system prior to adding it.
        Args:
            udl (nparr): Array of size 3 containing
                components of the uniformly distributed load that is
                applied to the clear length of the element, acting on
                the global x, y, and z directions, in the direction of
                the global axes.
        """
        assert hasattr(self, ltype)
        T_mat = transformations.transformation_matrix(
            self.parent_line_element.geomtransf.x_axis,
            self.parent_line_element.geomtransf.y_axis,
            self.parent_line_element.geomtransf.z_axis)
        udl_local = T_mat @ udl
        attr = getattr(self, ltype)
        attr += udl_local

    def get_udl_self_other_glob(self):
        """

        """
        udl = self.self_weight + self.other_load
        T_mat = transformations.transformation_matrix(
            self.parent_line_element.geomtransf.x_axis,
            self.parent_line_element.geomtransf.y_axis,
            self.parent_line_element.geomtransf.z_axis)
        return T_mat.T @ udl


@dataclass(repr=False)
class LoadCase:
    """
    """
    name: str
    parent_model: Model
    node_loads: NodePointLoadCollection = field(init=False)
    node_mass: NodeMassCollection = field(init=False)
    line_element_udl: LineElementUDLCollection = field(init=False)

    def __post_init__(self):
        self.node_loads = NodePointLoadCollection(self)
        self.node_mass = NodeMassCollection(self)
        self.line_element_udl = LineElementUDLCollection(self)
        # initialize loads and mass
        for node in self.parent_model.list_of_all_nodes():
            self.node_loads.registry[node.uid] = PointLoad()
            self.node_mass.registry[node.uid] = PointLoad()
        for line_element in (self.parent_model
                             .list_of_beamcolumn_elements()):
            self.line_element_udl.registry[line_element.uid] = \
                LineElementUDL(line_element)