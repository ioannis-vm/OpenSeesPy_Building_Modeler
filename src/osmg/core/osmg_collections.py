"""Collections are designated containers of objects of a particular type."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar

import numpy as np
import numpy.typing as npt

from osmg.analysis.common import UDL
from osmg.core import common
from osmg.core.uid_object import UIDObject
from osmg.geometry.transformations import (
    transformation_matrix,
    transformation_matrix_2d,
)
from osmg.model_objects.element import BeamColumnElement, Element
from osmg.model_objects.node import Node

nparr = npt.NDArray[np.float64]

TV = TypeVar('TV')

if TYPE_CHECKING:
    from osmg.model_objects import element


@dataclass(repr=False)
class Collection(dict[int, TV]):
    """Collection of objects."""

    def add(self, obj: TV) -> None:
        """
        Add an object to the collection.

        The object needs to have a unique id attribute, `uid`.

        Arguments:
          obj: Object to be added.

        Raises:
          ValueError: If the object does not have a uid attribute.
          ValueError: If the object already exists.
        """
        assert hasattr(obj, 'uid')
        if obj.uid in self:
            msg = f'uid {obj.uid} already exists'
            raise ValueError(msg)
        self[obj.uid] = obj

    def retrieve_by_attr(self, attr: str, val: object) -> TV:
        """
        Retrieve object by attribute value.

        Retrieve an object from the collection based on an attribute
        value. If more than one instances satisfy the criterion, the
        function returns the first occurrence.

        Arguments:
          attr: The name of the attribute.
          val: The value that the attribute should have.

        Returns:
          The retrieved object.

        Raises:
          ValueError: If the object is not found.
        """
        res = None
        for thing in self.values():
            found = False
            if hasattr(thing, attr):
                other_val = getattr(thing, attr)
                if other_val == val:
                    res = thing
                    found = True
                    break
            if found:
                break
        if res is None:
            msg = (
                f'Item having the value "{val}" '
                f'in the attribute "{attr}" not found in collection.'
            )
            raise ValueError(msg)
        return res

    def __repr__(self) -> str:
        """
        Get string representation.

        Returns:
          The string representation of the object.
        """
        res = ''
        res += 'Collection Object\n'
        res += f'ID: {id(self)}\n'
        res += f'Number of objects: {len(self)}\n'
        return res


@dataclass(repr=False)
class NamedCollection(Collection[TV], Generic[TV]):
    """
    A collection that allows assigning and retrieving objects by name.

    Attributes:
    ----------
    named_contents : dict[str, TV]
        A mapping of names to objects for easy retrieval.
    """

    named_contents: dict[str, TV] = field(default_factory=dict)

    def add(self, obj: TV, name: str | None = None) -> None:
        """
        Add a named object to the collection.

        The Node needs to have a unique id attribute, `uid`.
        Parameters
        ----------
        obj : TV
            Object to be added.
        name : str
            The name to assign to the object.

        """
        super().add(obj)
        if name:
            self.named_contents[name] = obj

    def retrieve_by_name(self, name: str) -> TV:
        """
        Retrieve an object by its name.

        Params:
          name: The name of the object to retrieve.

        Returns:
            The object associated with the given name.

        Raises:
          KeyError: If no object is found with the given name.
        """
        if name not in self.named_contents:
            msg = f"No object found with the name '{name}'."
            raise KeyError(msg)
        return self.named_contents[name]

    def __repr__(self) -> str:
        """
        Get string representation.

        Returns:
        -------
        str
            The string representation of the object.
        """
        res = ''
        res += 'NamedCollection Object\n'
        res += f'ID: {id(self)}\n'
        res += f'Number of objects: {len(self)}\n'
        res += f'Named objects: {list(self.named_contents.keys())}\n'
        return res


@dataclass(repr=False)
class ElementCollection(Collection[Element]):
    """Collection of elements."""

    def add(self, obj: Element) -> None:
        """
        Add an element to the collection.

        Arguments:
          obj: Object to be added.
        """
        super().add(obj)


@dataclass(repr=False)
class NodeCollection(NamedCollection[Node]):
    """
    A collection specifically for managing named Nodes.

    Methods:
    -------
    search_by_coordinates:
        Search for a node at the specified coordinates.
    """

    def search_by_coordinates(
        self, coordinates: tuple[float, ...], radius: float = common.EPSILON
    ) -> Node | None:
        """
        Obtain the node that occupies a given point if it exists.

        Params:
          coordinates: The coordinates to search at.

        Returns:
          Node: The node at the given coordinates, or None if no node is found.
        """
        candidate_pt: nparr = np.array(coordinates)
        for other_node in self.values():
            other_pt: nparr = np.array(other_node.coordinates)
            if np.linalg.norm(candidate_pt - other_pt) < radius:
                return other_node
        return None

    def search_by_coordinates_or_raise(
        self, coordinates: tuple[float, ...], radius: float = common.EPSILON
    ) -> Node:
        """
        Obtain the node that occupies a given point if it exists.

        Raise an error if it does not exist.

        Params:
          coordinates: The coordinates to search at.

        Returns:
          The node at the given coordinates, or None if no node is found.

        Raises:
          ValueError: If a node is not found.
        """
        node = self.search_by_coordinates(coordinates=coordinates, radius=radius)
        if node is None:
            msg = f'No node found at given coordinates: {coordinates}.'
            raise ValueError(msg)
        return node


@dataclass
class ComponentAssembly(UIDObject):
    """
    Component assembly object.

    A component assembly represents some part of a structure and holds
    various lower-level elements such as nodes and beam-column
    elements.

    Attributes:
        uid: Unique identifier of the component assembly.
        tags: List of tags, used to filter component assemblies if
            needed.
        external_nodes: The external nodes to which the component
            assembly is connected.
        internal_nodes: Internal nodes that are required for the
            connectivity of the elements within the component
            assembly. These nodes only exist as part of the component
            assembly.
        elements: Collection containing the elements that are part of
            the component assembly.
    """

    tags: set[str]
    external_nodes: NodeCollection = field(default_factory=NodeCollection)
    internal_nodes: NodeCollection = field(default_factory=NodeCollection)
    elements: ElementCollection = field(default_factory=ElementCollection)

    def __repr__(self) -> str:
        """
        Get string representation.

        Returns:
          The string representation of the object.
        """
        res = ''
        res += 'Component assembly object\n'
        res += f'uid: {self.uid}\n'
        res += 'External Nodes\n'
        for node in self.external_nodes.values():
            res += f'  {node.uid}, {node.coordinates}'
        return res

    def element_connectivity(
        self,
    ) -> dict[tuple[int, ...], element.Element]:
        """
        Element connectivity.

        Returns:
          The connectivity of all elements. Elements are connected to
          external nodes. Each component assembly can be represented
          by a tuple of node uids of its connected nodes in ascending
          order. This method returns a dictionary having these tuples
          as keys, and the associated components as values.
        """
        res = {}
        elms = self.elements.values()
        for elm in elms:
            uids = [x.uid for x in elm.nodes]
            uids.sort()
            uids_tuple = (*uids,)
            res[uids_tuple] = elm
        return res


@dataclass
class BeamColumnAssembly(ComponentAssembly):
    """
    Beamcolumn assembly object.

    A beamcolumn assembly is a collection meant to represent beams and
    columns. It is modeled with beamcolumn elements connected in
    series, with optional zerolength elements at certain
    locations. All beamcolumn elements in the collection need to be
    colinear, since parts of osmg rely on this assumption.
    """

    def calculate_element_udl(self, udl: UDL) -> dict[int, UDL]:
        """
        Distribute the given UDL to the beamcolumn elements.

        Given a UDL, determine the elements meant to take the load and
        return what is necessary to define the load in OpenSees: The
        tags of the elements and the load expressed in the local
        coordinate system of each element.

        Returns:
          Dictionary mapping the UID of the beamcolumn elements with
          UDL values expressed in the members' local coordinate
          system.
        """
        local_udls: dict[int, UDL] = {}
        for beamcolumn_element in self.elements.values():
            if not isinstance(beamcolumn_element, BeamColumnElement):
                continue
            if beamcolumn_element.geomtransf.y_axis is None:
                transformation_mat = transformation_matrix_2d(
                    beamcolumn_element.geomtransf.x_axis,
                    beamcolumn_element.geomtransf.z_axis,
                )
            else:
                transformation_mat = transformation_matrix(
                    beamcolumn_element.geomtransf.x_axis,
                    beamcolumn_element.geomtransf.y_axis,
                    beamcolumn_element.geomtransf.z_axis,
                )
            udl_local = UDL(transformation_mat @ np.array(udl))
            local_udls[beamcolumn_element.uid] = udl_local
        return local_udls


@dataclass(repr=False)
class ComponentAssemblyCollection(Collection[ComponentAssembly]):
    """
    Collection of component assemblies with connectivity tracking.

    Attributes:
    ----------
    connectivity_map : dict[tuple[int, ...], int]
        A dictionary where the keys are sorted tuples of external node uids,
        and the values are the uids of the corresponding component assemblies.
    """

    connectivity_map: dict[tuple[int, ...], int] = field(default_factory=dict)

    def add(self, obj: ComponentAssembly) -> None:
        """
        Add a component to the collection and update connectivity information.

        Arguments:
          obj: ComponentAssembly to be added.

        Raises:
          ValueError: If the object is missing required attributes or
                      if connectivity information conflicts.
        """
        super().add(obj)

        # Ensure external nodes have unique IDs
        if not obj.external_nodes:
            msg = (
                'ComponentAssembly must have external nodes to update connectivity.'
            )
            raise ValueError(msg)

        # Extract external node uids
        external_uids = [node.uid for node in obj.external_nodes.values()]
        if not external_uids:
            msg = 'External nodes must have valid unique IDs.'
            raise ValueError(msg)

        # Create a sorted tuple of external node uids
        sorted_uids = tuple(sorted(external_uids))

        # Update connectivity map
        if sorted_uids in self.connectivity_map:
            msg = (
                f'Connectivity information for nodes {sorted_uids} '
                f'already exists for ComponentAssembly {self.connectivity_map[sorted_uids]}.'
            )
            raise ValueError(msg)

        self.connectivity_map[sorted_uids] = obj.uid

    def search_by_nodes(self, nodes: list[Node]) -> ComponentAssembly | None:
        """
        Search and return a component assembly connected to the given nodes.

        Arguments:
          nodes: List of Node objects to check for connectivity.

        Returns:
          The connected ComponentAssembly if found, else None.
        """
        # Extract sorted uids from the given nodes
        node_uids = tuple(sorted(node.uid for node in nodes))

        # Check if the connectivity map contains the sorted uids
        if node_uids in self.connectivity_map:
            assembly_uid = self.connectivity_map[node_uids]
            return self[assembly_uid]

        return None

    def search_by_nodes_or_raise(self, nodes: list[Node]) -> ComponentAssembly:
        """
        Search and return a component assembly connected to the given nodes.

        Raise an error if not found.

        Arguments:
          nodes: List of Node objects to check for connectivity.

        Returns:
          The connected ComponentAssembly.

        Raises:
          ValueError: If not found
        """
        component = self.search_by_nodes(nodes)
        if component is None:
            msg = 'Component not found.'
            raise ValueError(msg)
        return component

    def __repr__(self) -> str:
        """
        Get string representation.

        Returns:
          The string representation of the object.
        """
        res = ''
        res += 'ComponentAssemblyCollection Object\n'
        res += f'ID: {id(self)}\n'
        res += f'Number of assemblies: {len(self)}\n'
        res += f'Connectivity map: {self.connectivity_map}\n'
        return res