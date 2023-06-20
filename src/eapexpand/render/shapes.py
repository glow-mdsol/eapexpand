from typing import Optional
from rdflib import Graph, URIRef, Literal, Namespace, SH, SKOS


"""
Generates one or more shapes for the Object
"""


def generate(self, name: str,
             packages: dict, 
             objects: dict, 
             attributes: dict, 
             connectors: dict, 
             output_dir: Optional[str] = "output"):
    """
    Create SHACL models from the EAP model
    """
    graph = Graph()
    graph.bind("sh", SH)
    graph.bind("skos", SKOS)
    
