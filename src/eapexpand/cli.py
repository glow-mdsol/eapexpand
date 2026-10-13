import sys
import argparse
from pathlib import Path
import yaml
from .helpers.openapi_metadata import load_openapi_api_metadata


def _merge_api_metadata(base: dict, overlay: dict) -> dict:
    merged = dict(base or {})
    for key, value in (overlay or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--usdm", help="Source is USDM", action="store_true", default=False
    )
    parser.add_argument("--usdm-ct", type=str, help="Path to Controlled Terms file")
    parser.add_argument("--output", type=str, help="Output directory", default="output")
    parser.add_argument("--api-metadata", type=str, help="API Metadata file")
    parser.add_argument("--openapi-spec", type=str, help="OpenAPI specification file")
    parser.add_argument("--internal-enums", help="Use internal enumerations for code lists", action="store_true", default=False)
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

        openapi_spec_file = Path(opts.openapi_spec) if opts.openapi_spec else Path(opts.source).parent / "USDM_API.json"
        if openapi_spec_file.is_file():
            api_metadata = _merge_api_metadata(
                api_metadata, load_openapi_api_metadata(openapi_spec_file)
            )

        main_usdm(
            source_dir_or_file=opts.source,
            controlled_term=opts.usdm_ct,
            output_dir=output_dir,
            gen=gen,
            api_metadata=api_metadata,
            internal_enums=opts.internal_enums
        )
    else:
        from .unpkt import main

        main(source, output_dir, gen)


def load_usdm():
    """
    Process the USDM file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "version", help="USDM version", action="store", default=None
    )
    parser.add_argument("--output", type=str, help="Output directory", default="output")
    opts = parser.parse_args()
    assert opts.version is not None, "USDM version is required"
    source_version = opts.version
    gen=dict(linkml=True)
    output_dir = opts.output
    usdm_ct = Path.cwd() / "input" / source_version / f"{source_version}_USDM_CT.xlsx"
    assert usdm_ct.is_file(), "USDM Controlled Terms file not found"
    source = Path.cwd() / "input" / source_version / f"{source_version}_USDM_UML.qea"
    assert source.is_file(), "USDM file not found"
    api_metadata_file = Path.cwd() / "docs" / "api_attributes.yaml" 
    if api_metadata_file.is_file():
        with open(api_metadata_file, "r") as f:
            api_metadata = yaml.safe_load(f.read())
    else:
        api_metadata = {}

    openapi_spec_file = Path.cwd() / "input" / source_version / "USDM_API.json"
    if openapi_spec_file.is_file():
        api_metadata = _merge_api_metadata(
            api_metadata, load_openapi_api_metadata(openapi_spec_file)
        )

    from .usdm_unpkt import main_usdm
    main_usdm(
        source_dir_or_file=source,
        controlled_term=usdm_ct,
        output_dir=output_dir,
        gen=gen,
        api_metadata=api_metadata,
    )
