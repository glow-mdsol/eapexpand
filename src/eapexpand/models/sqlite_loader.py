import os
import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .eap import (
    Connector,
    Document,
    Object,
    Attribute,
    Class,
    Enumeration,
    Boundary,
    DataType,
    Note,
    Artifact,
    ObjectProperty,
    Package,
    State,
    StateNode,
    Text,
    Diagram,
)


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
        _package = Package.from_dict(package)
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
                _object = Object.from_dict(obj)
            case "ObjectProperty":
                _object = ObjectProperty.from_dict(obj)
            case "State":
                _object = State.from_dict(obj)
            case "StateNode":
                _object = StateNode.from_dict(obj)
            case "Text":
                _object = Text.from_dict(obj)
            case "Package":
                _object = Package.from_dict(obj)
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
    for conn in cur.execute("SELECT * FROM t_connector").fetchall():
        _conn = Connector.from_dict(conn)  # type: Connector
        _source_object = data.get(_conn.start_object_id)
        if not _source_object:
            logger.info(f"Skipping {_conn.connector_id} ({_conn.name}): Source object not found: {_conn.start_object_id}")
            continue
        # end
        _target_object = data.get(_conn.end_object_id)
        assert _target_object, f"Connector {_conn.connector_id}: Target object not found: {_conn._target_object_id}"
        if api_metadata:
            if api_metadata.get("apiAttributes", {}).get(_conn.name):
                _api_attr_spec = api_metadata["apiAttributes"][_conn.name]
                
                if "names" in _api_attr_spec:
                    if _conn.multivalued:
                        _name = _api_attr_spec["names"]
                    else:
                        _name = _api_attr_spec["name"]
                else:
                    _name = _api_attr_spec["name"]
                # add an API attribute
                _api_attr = Attribute(
                    name=_name,
                    attribute_type="String",
                    preferred_term="API Attribute for " + _conn.name,
                    definition="An API attribute added for " + _conn.name,
                    lower_bound='0' if _conn.optional else '1',
                    upper_bound='*' if _conn.multivalued else '1',
                    pos=_attr.pos + 1000,
                )
                _conn.optional = True
                # print("Adding API attribute", _api_attr.name, "for", _conn.name, "with cardinality", _conn.dest_card)
                _source_object.object_attributes.append(_api_attr)
            elif api_metadata.get("mapTypes"):
                if _conn.name in api_metadata["mapTypes"]:
                    _conn.aliased_type = api_metadata["mapTypes"][_conn.name]["type"]
                                  
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
    # Add the API attributes
    if api_metadata:
        for obj in data.values():
            if not isinstance(obj, Object):
                continue
            if api_metadata.get("addedAttributes", {}).get(obj.name):
                for attr in api_metadata["addedAttributes"][obj.name]:
                    print(f"Adding API attribute {attr.get('name')} for {obj.name}")
                    _target_id = cur.execute(
                        "SELECT object_id FROM t_object WHERE name = ?", (attr["type"],)
                    ).fetchone()["Object_ID"]
                    assert _target_id, f"Object {attr['type']} not found"
                    assert _target_id in data, f"Object {attr['type']} not found"
                    _connector = Connector(
                        connector_type="Association",
                        name=attr.get("name"),
                        start_object_id=obj.object_id,
                        end_object_id=_target_id,
                        definition=attr.get("description"),
                        dest_card="0..*" if attr.get("multivalued") else "0..1",
                        source_object=obj,
                        target_object=data.get(_target_id),
                    )
                    obj.outgoing_connections.append(_connector)
                    assert _connector in obj.outgoing_connections
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
