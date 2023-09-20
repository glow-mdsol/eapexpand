from __future__ import annotations

from dataclasses import dataclass, field
import os

from typing import Dict, Optional, List

from .loader import load_expanded_dir


def main(source_dir: str, output_dir: str, gen: dict):
    """
    Main entry point
    """
    name = (
        os.path.basename(os.path.dirname(source_dir))
        if source_dir.endswith("/")
        else os.path.basename(source_dir)
    )
    document = load_expanded_dir(source_dir)
    for aspect, genflag in gen.items():
        if genflag:
            if aspect == "prisma":
                from .render.prisma import generate as generate_prisma
                generate_prisma(name, document, output_dir)
            elif aspect == "linkml":
                from .render.linkml import generate as generate_linkml
                generate_linkml(name, document=document, output_dir=output_dir)
            elif aspect == "shapes":
                from .render.shapes import generate as generate_shapes
                generate_shapes(name, document, output_dir)
            else:
                raise ValueError(f"Unknown aspect: {aspect}")
    else:
        # always generate the workbook
        from .render.workbook import generate as generate_workbook
        generate_workbook(name, document, output_dir=output_dir)
    
