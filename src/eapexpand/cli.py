import sys
import os
from .unpkt import load, generate

def main():

    source = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    name = os.path.basename(source)
    objects, attributes, connectors = load(source_dir=source)
    generate(name, objects, attributes, connectors, output_dir=output_dir)
    print(f"Done generating {output_dir}{os.sep}{name}.xlsx")

