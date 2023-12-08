import os
import sqlite3
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


def load_from_file(filename: str) -> Document:
    """
    Loads the SQLite file
    """
    assert os.path.exists(filename), f"File does not exist: {filename}"
    conn = sqlite3.connect(filename)
    conn.row_factory = dict_factory
    cur = conn.cursor()
    _packages = {}
    data = {}
    print("Loading packages")
    for package in cur.execute("SELECT * FROM t_package").fetchall():
        _package = Package.from_dict(package)
        _packages[_package.id] = _package

    for _package in _packages.values():
        if _package.parent_id and _package.parent_id != 0:
            _package.parent = _packages.get(_package.parent_id)
    print("Loading objects")
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
            _object.attributes.append(_attr)
        # load the outgoing connectors
        for connector in cur.execute(
            "SELECT * FROM t_connector tc " "WHERE tc.start_object_id = ?",
            (_object.object_id,),
        ).fetchall():
            _conn = Connector.from_dict(connector)
            if _conn.connector_type == "Association":
                # eg protocolStatus: Code
                _object.outgoing_connections.append(_conn)
            elif _conn.connector_type == "Generalization":
                _object.generalizations.append(_conn)
        # load the incoming connectors
        for connector in cur.execute(
            "SELECT * FROM t_connector tc " "WHERE tc.end_object_id = ?",
            (_object.object_id,),
        ).fetchall():
            _conn = Connector.from_dict(connector)
            _object.incoming_connections.append(_conn)
        _packages.get(_object.package_id).objects.append(_object)
        data[_object.object_id] = _object
    diagrams = []
    print("Loading diagrams")
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
    #     _packages = {x.package_id: x for x in data.values() if x.object_type == "Package"}
    # for pkg_id, _package in _packages.items():
    #     # bind the objects
    #     _objects = [x for x in data.values() if x.package_id == pkg_id]
    #     print("Package %s (%s) has %s objects" % (_package.name, _package.package_id, len(_objects)))
    #     _package.objects = _objects
    #     # bind the parent
    #     _package.parent = _packages.get(_package.parent_id)
    _name = os.path.splitext(os.path.basename(filename))[0]
    document = Document(
        name=_name,
        packages=list(_packages.values()),
        objects=list(data.values()),
        diagrams=diagrams,
    )

    return document
