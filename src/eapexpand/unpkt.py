from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path

from typing import Dict, Optional, List

from .models.sqlite_loader import load_from_file

from .loader import load_expanded_dir


def main(source_dir_or_file: str, output_dir: str, gen: dict):
    """
    Main entry point
    """
    if Path(source_dir_or_file).is_file():
        document = load_from_file(source_dir_or_file)
    else:
        name = (
            os.path.basename(os.path.dirname(source_dir_or_file))
            if source_dir_or_file.endswith("/")
            else os.path.basename(source_dir_or_file)
        )
        document = load_expanded_dir(source_dir_or_file)
    for aspect, genflag in gen.items():
        if genflag:
            if aspect == "prisma":
                from .render.render_prisma import generate as generate_prisma

                generate_prisma(document.name, document, output_dir)
            elif aspect == "linkml":
                from .render.render_linkml import generate as generate_linkml

                generate_linkml(document.name, document=document, output_dir=output_dir)
            elif aspect == "shapes":
                from .render.render_shapes import generate as generate_shapes

                generate_shapes(document.name, document, output_dir)
            else:
                raise ValueError(f"Unknown aspect: {aspect}")
    else:
        # always generate the workbook
        from .render.render_workbook import generate as generate_workbook

        generate_workbook(document.name, document, output_dir=output_dir)
