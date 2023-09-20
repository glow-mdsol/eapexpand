from pathlib import Path
from typing import Dict, List
from .eap import (
    Artifact,
    Boundary,
    DataType,
    Document,
    Note,
    Object,
    Attribute,
    Connector,
    ObjectProperty,
    Package,
    Class,
    Enumeration,
    State,
    StateNode,
    Text,
)
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_packages(path: str) -> Dict[int, Package]:
    """
    Loads the packages from the EAP file
    """
    data = {}
    assert Path(path).exists(), f"Input Path does not exist: {path}"
    assert (Path(path) / "t_package.json").exists(), f"Path is not a file: {path}"
    with open((Path(path) / "t_package.json"), "r") as f:
        for line in f:
            _package = Package.from_json(line)
            data[_package.id] = _package
    # bind parent packages
    _by_id = {x.package_id: x for x in data.values()}
    for _package in data.values():
        if _package.parent_id in _by_id:
            _parent = _by_id.get(_package.parent_id)
            _package.parent = _parent
    return data


def load_objects(path: str) -> Document:
    """
    Loads the objects from the EAP file
    - note, includes Packages, Classes, Enumerations, etc
    """
    data = {}
    assert Path(path).exists(), f"Input Path does not exist: {path}"
    assert (Path(path) / "t_object.json").exists(), f"Path is not a file: {path}"
    # pull the package metadata
    _package_metadata = load_packages(path)
   
    data_types = {}
    with open((Path(path) / "t_datatypes.json"), "r") as f:
        for line in f:
            if line:
                _datatype = DataType.from_json(line)
                data_types[_datatype.id] = _datatype

    _packages = {}
    with open((Path(path) / "t_object.json"), "r") as f:
        for line in f:
            _line = json.loads(line)
            if _line["Object_Type"] == "Class":
                _object = Class.from_json(line)
            elif _line["Object_Type"] == "Enumeration":
                _object = Enumeration.from_json(line)
            elif _line["Object_Type"] == "Artifact":
                _object = Artifact.from_json(line)
            elif _line["Object_Type"] == "Boundary":
                _object = Boundary.from_json(line)
            elif _line["Object_Type"] == "Text":
                _object = Text.from_json(line)
            elif _line["Object_Type"] == "State":
                _object = State.from_json(line)
            elif _line["Object_Type"] == "StateNode":
                _object = StateNode.from_json(line)
            elif _line["Object_Type"] == "Note":
                _object = Note.from_json(line)
            elif _line["Object_Type"] == "Package":
                # extract the package object metadata
                _object = Package.from_json(line)
                _pkg = _package_metadata.get(_object.ea_guid)
                # merge the package metadata
                if _pkg:
                    _object.merge(_pkg)
                _packages[_object.package_id] = _object
            else:
                logger.warning("Unknown Object Type: %s" % _line["Object_Type"])
                continue
            # add/update to data
            data[_object.object_id] = _object
    # assign objectproperties to objects
    if (Path(path) / "t_objectproperties.json").exists():
        with open((Path(path) / "t_objectproperties.json"), "r") as f:
            for line in f:
                _object = ObjectProperty.from_json(line)
                data[_object.object_id].properties.append(_object)
    # assign attributes to objects
    if (Path(path) / "t_attribute.json").exists():
        with open((Path(path) / "t_attribute.json"), "r") as f:
            for line in f:
                _attribute = Attribute.from_json(line)
                data[_attribute.object_id].attributes.append(_attribute)
                if _attribute.classifier_id:
                    data[_attribute.classifier_id].classifies.append(_attribute)

    if (Path(path) / "t_connector.json").exists():
        with open((Path(path) / "t_connector.json"), "r") as f:
            for line in f:
                _connector = Connector.from_json(line)
                data[_connector.start_object_id].connectors.append(_connector)
                if _connector.connector_type == "Generalization":
                    if _connector.start_object_id in data:
                        data[_connector.start_object_id].generalizations.append(
                            data[_connector.end_object_id]
                        )
                if _connector.end_object_id in data:
                    data[_connector.end_object_id].specializations.append(
                        data[_connector.start_object_id]
                    )
    # fix packages
    _packages = {x.package_id: x for x in data.values() if x.object_type == "Package"}
    for pkg_id, _package in _packages.items():
        # bind the objects
        _objects = [x for x in data.values() if x.package_id == pkg_id]
        print("Package %s (%s) has %s objects" % (_package.name, _package.package_id, len(_objects)))
        _package.objects = _objects
        # bind the parent
        _package.parent = _packages.get(_package.parent_id)
    document = Document(name=os.path.basename(path),
                        data_types=data_types, 
                        packages=_packages, 
                        objects=data.values())
    return document


# def load_attributes(path: str) -> Dict[int, Attribute]:
#     """
#     Loads the attributes from the EAP file
#     """
#     data = {}
#     assert Path(path).exists(), f"Path does not exist: {path}"
#     assert (Path(path) / "t_attribute.json").exists() , f"Path is not a file: {path}"
#     with open((Path(path) / "t_attribute.json"), "r") as f:
#         for line in f:
#             # object id -> classifier
#             try:
#                 _attr = Attribute.from_json(line)
#                 if _attr.id in data:
#                     logger.warning(f"Warning - duplicated object id: {_attr.id}")
#                 data[_attr.id] = _attr
#             except (AttributeError, KeyError, TypeError) as exc:
#                 logger.error(f"Error Loading Attributes: {exc}", line)
#     return data


# def load_connectors(path: str) -> Dict[int, Connector]:
#     """
#     Loads the connectors from the EAP file
#     """
#     data = {}
#     assert Path(path).exists(), f"Path does not exist: {path}"
#     assert (Path(path) / "t_connector.json").exists() , f"Path is not a file: {path}"
#     with open((Path(path) / "t_connector.json"), "r") as f:
#         for line in f:
#             _connector = Connector.from_json(line)
#             data[_connector.connector_id] = _connector
#     return data
