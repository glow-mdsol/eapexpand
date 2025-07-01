import pprint
import yaml
from pathlib import Path
from dictdiffer import diff, patch, swap, revert
import argparse
import pprint

"""
Compare two linkml files
"""

def compare(this: str, that: str):
    assert Path(this).exists(), f"Input Path does not exist: {this}"
    assert Path(that).exists(), f"Input Path does not exist: {that}"
    with open(this, "r") as f:
        this_data = yaml.safe_load(f)
    with open(that, "r") as f:
        that_data = yaml.safe_load(f)
    delta = diff(this_data, that_data)
    return delta

def main():
    parser = argparse.ArgumentParser(description="Compare two linkml files")
    parser.add_argument("this", help="The first file to compare")
    parser.add_argument("that", help="The second file to compare")
    args = parser.parse_args()
    delta = compare(args.this, args.that)
    print(pprint.pprint(list(delta)))


