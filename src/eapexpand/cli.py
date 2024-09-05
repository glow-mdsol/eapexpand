import sys
import argparse
from pathlib import Path
import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--usdm", help="Source is USDM", action="store_true", default=False
    )
    parser.add_argument("--usdm-ct", type=str, help="Path to Controlled Terms file")
    parser.add_argument("--output", type=str, help="Output directory", default="output")
    parser.add_argument("--api-metadata", type=str, help="API Metadata file")
    parser.add_argument("source", type=str, help="Source directory or file")
    parser.add_argument(
        "--prisma", help="Generate Prisma Schema", action="store_true", default=False
    )
    parser.add_argument(
        "--linkml", help="Generate LinkML Schema", action="store_true", default=False
    )
    parser.add_argument(
        "--shapes", help="Generate SHACL Schema", action="store_true", default=False
    )
    opts = parser.parse_args()
    gen = dict(prisma=opts.prisma, linkml=opts.linkml, shapes=opts.shapes)
    source = opts.source
    output_dir = opts.output
    if opts.usdm:
        if opts.usdm_ct is None:
            print("USDM Controlled Terms file is required")
            sys.exit(1)
        if not Path(opts.usdm_ct).is_file():
            print("USDM Controlled Terms file not found")
            sys.exit(1)
        if not Path(opts.source).is_file():
            print("USDM file not found")
            sys.exit(1)
        from .usdm_unpkt import main_usdm

        if opts.api_metadata:
            assert Path(opts.api_metadata).is_file(), "API Metadata file not found"
            with open(opts.api_metadata, "r") as f:
                api_metadata = yaml.safe_load(f.read())
        else:
            api_metadata = {}
        main_usdm(
            source_dir_or_file=opts.source,
            controlled_term=opts.usdm_ct,
            output_dir=output_dir,
            gen=gen,
            api_metadata=api_metadata,
        )
    else:
        from .unpkt import main

        main(source, output_dir, gen)
