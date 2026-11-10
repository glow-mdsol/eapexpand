import os
import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ..report import get_report
from .eap import (
    Connector,
    Document,
    ModelObject,
    Attribute,
    Class,
    Enumeration,
    Boundary,
    DataType,
    Note,
    Artifact,
    ModelObjectProperty,
    ModelPackage,
    State,
    StateNode,
    Text,
    Diagram,
)


_IRREGULAR_PLURALS = {"children": "child", "criteria": "criterion"}


def _singularize(name: str) -> str:
    if name in _IRREGULAR_PLURALS:
        return _IRREGULAR_PLURALS[name]
    if name.endswith("ies"):
        return name[:-3] + "y"
    if name.endswith("s") and not name.endswith("ss"):
        return name[:-1]
    return name


def _pluralize(name: str) -> str:
    if name.endswith("y"):
        return name[:-1] + "ies"
    if name.endswith("s"):
        return name
    return name + "s"


def _openapi_id_props(api_metadata: dict, class_name: str) -> set[str]:
    openapi_data = api_metadata.get("openapi", {})
    return set(openapi_data.get("idPropertiesByClass", {}).get(class_name, []))


def _resolve_api_attr_from_openapi(
    api_metadata: dict, class_name: str, connector_name: str, multivalued: bool
) -> str | None:
    id_props = _openapi_id_props(api_metadata, class_name)
    if not id_props:
        return None

    singular = _singularize(connector_name)
    plural = _pluralize(singular)
    ordered_candidates = []

    if multivalued:
        ordered_candidates.extend(
            [
                f"{connector_name}Ids",
                f"{plural}Ids",
                f"{singular}Ids",
                f"{connector_name}Id",
                f"{singular}Id",
            ]
        )
    else:
        ordered_candidates.extend(
            [
                f"{connector_name}Id",
                f"{singular}Id",
                f"{connector_name}Ids",
                f"{singular}Ids",
                f"{plural}Ids",
            ]
        )

    for candidate in ordered_candidates:
        if candidate in id_props:
            return candidate
    return None


def _resolve_map_type_from_openapi(
    api_metadata: dict, class_name: str, connector_name: str
) -> str | None:
    openapi_data = api_metadata.get("openapi", {})
    class_map = openapi_data.get("aliasCodePropsByClass", {}).get(class_name, {})
    return class_map.get(connector_name)


_OPENAPI_CLASS_MAPS = ("idPropertiesByClass", "aliasCodePropsByClass", "refPropsByClass")


def _with_inherited_openapi_metadata(
    api_metadata: dict, connectors: list[Connector], data: dict
) -> dict:
    """
    Abstract UML classes (e.g. StudyDesign) have no OpenAPI schema of their own; the
    spec only carries their concrete subtypes. Give each such class the OpenAPI
    properties common to all of its subtypes, so connectors declared on the abstract
    class resolve the same way as on a concrete one.
    """
    openapi = api_metadata.get("openapi")
    if not openapi:
        return api_metadata
    subtypes: dict[str, list[str]] = {}
    for conn in connectors:
        if conn.connector_type != "Generalization":
            continue
        child, parent = data.get(conn.start_object_id), data.get(conn.end_object_id)
        if child is not None and parent is not None:
            subtypes.setdefault(parent.name, []).append(child.name)

    def effective(class_map: dict, class_name: str):
        if class_name in class_map:
            return class_map[class_name]
        child_values = [effective(class_map, c) for c in subtypes.get(class_name, [])]
        child_values = [v for v in child_values if v is not None]
        if not child_values:
            return None
        if isinstance(child_values[0], dict):
            common = set.intersection(*(set(v) for v in child_values))
            return {k: child_values[0][k] for k in child_values[0] if k in common}
        common = set.intersection(*(set(v) for v in child_values))
        return sorted(common)

    augmented = dict(openapi)
    for map_name in _OPENAPI_CLASS_MAPS:
        class_map = dict(openapi.get(map_name, {}))
        for parent in subtypes:
            if parent not in class_map:
                value = effective(class_map, parent)
                if value:
                    class_map[parent] = value
        augmented[map_name] = class_map
    return {**api_metadata, "openapi": augmented}


# Properties every renderer adds through the Base mixin.
_RENDERER_PROVIDED_PROPS = {"id", "instanceType", "extensionAttributes"}


def _related(obj: ModelObject, links: str, end: str) -> list[ModelObject]:
    """Transitive closure over ``generalizations`` (ancestors) or ``specializations`` (descendants)."""
    result: list[ModelObject] = []
    pending = [getattr(c, end) for c in getattr(obj, links) or [] if getattr(c, end)]
    while pending:
        other = pending.pop()
        if other in result:
            continue
        result.append(other)
        pending.extend(getattr(c, end) for c in getattr(other, links) or [] if getattr(c, end))
    return result


def _known_names(objects: list[ModelObject]) -> set[str]:
    return {
        name
        for o in objects
        for name in [a.name for a in o.object_attributes or []]
        + [c.name for c in o.outgoing_connections or []]
        if name
    }


def cardinality_text(spec: dict) -> str:
    return ("0" if spec["optional"] else "1") + ".." + ("*" if spec["multivalued"] else "1")


def _add_openapi_only_relationships(api_metadata: dict, data: dict) -> None:
    """
    Add relationships the API exposes but the UML model does not (e.g. the
    StudyVersion-level collections of BiomedicalConcepts, Organizations, ...).
    """
    ref_props = api_metadata.get("openapi", {}).get("refPropsByClass", {})
    by_name = {o.name: o for o in data.values() if isinstance(o, ModelObject)}
    for obj in list(by_name.values()):
        props = ref_props.get(obj.name)
        if not props:
            continue
        ancestors = _related(obj, "generalizations", "target_object")
        # already modelled on the class, a supertype, or a subtype (abstract
        # classes pick up their subtypes' common OpenAPI properties)
        known = _known_names([obj, *ancestors, *_related(obj, "specializations", "source_object")])
        # leave properties shared by all subtypes to the supertype
        inherited = {name for parent in ancestors for name in ref_props.get(parent.name, {})}
        for prop_name, spec in props.items():
            if prop_name in _RENDERER_PROVIDED_PROPS or prop_name in known or prop_name in inherited:
                continue
            target = by_name.get(spec["type"])
            if target is None:
                logger.warning(f"OpenAPI {obj.name}.{prop_name}: no UML class {spec['type']}")
                get_report().warning(
                    "OpenAPI: properties without a UML class", f"{obj.name}.{prop_name} -> {spec['type']}"
                )
                continue
            logger.info(f"Adding API relationship {obj.name}.{prop_name} -> {target.name}")
            get_report().info(
                "API-only relationships added from the OpenAPI specification",
                f"{obj.name}.{prop_name} -> {target.name} ({cardinality_text(spec)})",
            )
            cardinality = ("0" if spec["optional"] else "1") + ".." + ("*" if spec["multivalued"] else "1")
            connector = Connector(
                connector_type="Association",
                name=prop_name,
                start_object_id=obj.object_id,
                end_object_id=target.object_id,
                definition=f"The {target.name} instances of the {obj.name} (API relationship).",
                dest_card=cardinality,
                source_object=obj,
                target_object=target,
                api_only=True,
            )
            obj.outgoing_connections.append(connector)


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row) if value is not None}


def load_from_file(
    filename: str,
    prefix: str | None = None,
    name: str | None = None,
    api_metadata: dict | None = None,
) -> Document:
    """
    Loads the SQLite file
    """
    logger.info(f"Loading SQLite Database {filename}")
    assert os.path.exists(filename), f"File does not exist: {filename}"
    conn = sqlite3.connect(filename)
    conn.row_factory = dict_factory
    cur = conn.cursor()
    _packages = {}
    data = {}
    if prefix:
        logger.info(f"Using prefix: {prefix}")
        _prefix = (
            prefix + Path(filename).stem
            if prefix.endswith("/")
            else prefix + "/" + Path(filename).stem
        )
    else:
        logger.info("No prefix provided, using default")
        _prefix = f"http://example.org/{Path(filename).stem}"
    logger.info("Loading packages")
    for package in cur.execute("SELECT * FROM t_package").fetchall():
        _package = ModelPackage.from_dict(package)
        _packages[_package.id] = _package

    for _package in _packages.values():
        if _package.parent_id and _package.parent_id != 0:
            _package.parent = _packages.get(_package.parent_id)
    logger.info("Loading objects")
    for obj in cur.execute("SELECT * FROM t_object").fetchall():
        match obj["Object_Type"]:
            case "Class":
                _object = Class.from_dict(obj)
            case "Enumeration":
                _object = Enumeration.from_dict(obj)
            case "Artifact":
                _object = Artifact.from_dict(obj)
            case "Boundary":
                _object = Boundary.from_dict(obj)
            case "DataType":
                _object = DataType.from_dict(obj)
            case "Note":
                _object = Note.from_dict(obj)
            case "Object":
                _object = ModelObject.from_dict(obj)
            case "ObjectProperty":
                _object = ModelObjectProperty.from_dict(obj)
            case "State":
                _object = State.from_dict(obj)
            case "StateNode":
                _object = StateNode.from_dict(obj)
            case "Text":
                _object = Text.from_dict(obj)
            case "Package":
                _object = ModelPackage.from_dict(obj)
                # Merge the package metadata
                for _, package in _packages.items():
                    if package.ea_guid == _object.ea_guid:
                        _object.merge(package)
                # replace
                _packages[_object.package_id] = _object
            case _:
                raise ValueError(f"Unknown object type: {obj['Object_Type']}")
        # load the attributes
        print(f"Loading attributes for {_object.name} ({obj['Object_Type']})")
        for attr in cur.execute(
            "SELECT * FROM t_attribute WHERE object_id = ?", (_object.object_id,)
        ).fetchall():
            _attr = Attribute.from_dict(attr)
            _object.object_attributes.append(_attr)
        # # load the outgoing connectors
        # for connector in cur.execute(
        #     "SELECT * FROM t_connector tc " "WHERE tc.start_object_id = ?",
        #     (_object.object_id,),
        # ).fetchall():
        #     _conn = Connector.from_dict(connector)
        #     if _conn.connector_type == "Association":
        #         # eg protocolStatus: Code
        #         _object.outgoing_connections.append(_conn)
        #     elif _conn.connector_type == "Generalization":
        #         _object.generalizations.append(_conn)
        # # load the incoming connectors
        # for connector in cur.execute(
        #     "SELECT * FROM t_connector tc " "WHERE tc.end_object_id = ?",
        #     (_object.object_id,),
        # ).fetchall():
        #     _conn = Connector.from_dict(connector)
        #     _object.incoming_connections.append(_conn)
        #     _conn.target_object = _object
        _packages.get(_object.package_id).objects.append(_object)
        data[_object.object_id] = _object
    # load the connectors
    _connectors = [Connector.from_dict(conn) for conn in cur.execute("SELECT * FROM t_connector").fetchall()]
    if api_metadata:
        api_metadata = _with_inherited_openapi_metadata(api_metadata, _connectors, data)
    for _conn in _connectors:
        _source_object = data.get(_conn.start_object_id)
        if not _source_object:
            logger.info(f"Skipping {_conn.connector_id} ({_conn.name}): Source object not found: {_conn.start_object_id}")
            get_report().warning(
                "UML: connectors skipped (source object not found)",
                f"connector {_conn.connector_id} ({_conn.connector_type}{' ' + _conn.name if _conn.name else ''}) "
                f"from object {_conn.start_object_id}",
            )
            continue
        # end
        _target_object = data.get(_conn.end_object_id)
        assert _target_object, f"Connector {_conn.connector_id}: Target object not found: {_conn._target_object_id}"
        if api_metadata and _conn.connector_type == "Association":
            _api_attr_name = _resolve_api_attr_from_openapi(
                api_metadata, _source_object.name, _conn.name, _conn.multivalued
            )
            if _api_attr_name:
                # exchanged by id: the relationship keeps its UML target and
                # cardinality, and is serialised under the API name
                _conn.api_name = _api_attr_name
            else:
                _openapi_type = _resolve_map_type_from_openapi(
                    api_metadata, _source_object.name, _conn.name
                )
                if _openapi_type:
                    _conn.aliased_type = _openapi_type

        if _source_object and _target_object:
            if _conn.connector_type == "Association":
                _source_object.outgoing_connections.append(_conn)
                _target_object.incoming_connections.append(_conn)
                _conn.source_object = _source_object
                _conn.target_object = _target_object
            elif _conn.connector_type == "Generalization":
                _source_object.generalizations.append(_conn)
                _target_object.specializations.append(_conn)
                _conn.source_object = _source_object
                _conn.target_object = _target_object
        else:
            get_report().warning(
                "UML: orphan connectors",
                f"{_conn.connector_type} {_conn.name} from {_conn.start_object_id} to {_conn.end_object_id}",
            )
            print(
                f"Orphan connector ({_conn.connector_type})",
                _conn.name,
                "from",
                _conn.start_object_id,
                "to",
                _conn.end_object_id,
            )
    diagrams = []
    logger.info("Loading diagrams")
    for diagram in cur.execute("SELECT * FROM t_diagram").fetchall():
        diagram = Diagram(
            diagram["Diagram_ID"],
            diagram["Name"],
            diagram["Diagram_Type"],
            diagram["Version"],
        )
        for link in cur.execute(
            "SELECT * FROM t_diagramobjects WHERE Diagram_ID = ? ORDER BY Sequence",
            (diagram.id,),
        ).fetchall():
            _object = data.get(link["Object_ID"])
            if _object:
                diagram.add_object(link["Sequence"], _object)
        diagrams.append(diagram)
    # Add API-only relationships (present in the OpenAPI spec but not the UML model)
    if api_metadata:
        _add_openapi_only_relationships(api_metadata, data)
    #     _packages = {x.package_id: x for x in data.values() if x.object_type == "Package"}
    # for pkg_id, _package in _packages.items():
    #     # bind the objects
    #     _objects = [x for x in data.values() if x.package_id == pkg_id]
    #     print("Package %s (%s) has %s objects" % (_package.name, _package.package_id, len(_objects)))
    #     _package.objects = _objects
    #     # bind the parent
    #     _package.parent = _packages.get(_package.parent_id)
    if name:
        _name = name
    else:
        _name = os.path.splitext(os.path.basename(filename))[0]
    document = Document(
        name=_name,
        prefix=_prefix,
        packages=list(_packages.values()),
        objects=list(data.values()),
        diagrams=diagrams,
    )

    return document
