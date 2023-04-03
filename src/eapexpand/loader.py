from .models.eap import load_attributes, load_connectors, load_objects, load_packages
import os

def load_expanded_dir(source_dir: str):
    # load the key entities
    packages = load_packages(os.path.join(source_dir, "t_package.json"))
    print(f"Loaded {len(packages)} packages")
    for package in packages.values():
        print(f"Package: {package.name} -> {package.path}")
    objects = load_objects(os.path.join(source_dir, "t_object.json"))
    print(f"Loaded {len(objects)} objects")
    for _object in objects.values():
        if _object.package_id in packages:
            _object.package = packages.get(_object.package_id)
            packages.get(_object.package_id).objects.append(_object)
    attributes = load_attributes(os.path.join(source_dir, "t_attribute.json"))
    # add the classifier
    for attrib in attributes.values():
        if attrib.classifier_id in objects:
            attrib.attribute_classifier = objects.get(attrib.classifier_id)
    connectors = load_connectors(os.path.join(source_dir, "t_connector.json"))
    _connectors = {x.dest_role: x for x in connectors.values()}
    for _id, _attr in attributes.items():
        if _attr.name in _connectors:
            _attr.connector = _connectors.get(_attr.name)
    # Generalizations
    for connector in connectors.values():
        if connector.connector_type == "Generalization":
            print(f"Generalization: {connector.start_object_id} -> {connector.end_object_id}")
            if connector.start_object_id in objects:
                objects[connector.start_object_id].generalizations.append(
                    objects[connector.end_object_id]
                )
            if connector.end_object_id in objects:
                objects[connector.end_object_id].specializations.append(
                    objects[connector.start_object_id]
                )
    # Coalesce the attributes into the objects
    for object_id, _object in objects.items():
        _object.attributes = [
            attributes[attr_id]
            for attr_id in attributes
            if attributes[attr_id].object_id == object_id
        ]
        _object.attributes.sort()
    for object_id, _object in objects.items():
        if _object.generalizations:
            for _generality in _object.generalizations:
                for _attr in _generality.attributes:
                    print(f"Adding attribute: {_attr.name} to {_object.name}")
                    _object.attributes.append(_attr) if _attr not in _object.attributes else None
    # link the connectors to the objects
    return objects, attributes, connectors
