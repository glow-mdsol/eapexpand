import re
import sys
import argparse
from pathlib import Path
import yaml
from .helpers.openapi_metadata import load_openapi_api_metadata
from .report import display_path, get_report, start_report

# API attributes (``*Id``/``*Ids`` references, API-only relationships, AliasCode
# typing) are derived from the DDF-RA OpenAPI specification.
DEFAULT_OPENAPI_SPEC = Path(__file__).resolve().parents[2] / "docs" / "ddf_ra" / "USDM_API.yaml"


# USDM v3 and earlier are no longer supported: the API attributes come from the
# v4 DDF-RA OpenAPI specification and there is no equivalent for older releases.
MIN_USDM_MAJOR_VERSION = 4
_VERSION_PATTERN = re.compile(r"v?(\d+)\.\d+\.\d+")


def _require_supported_version(version_source: str) -> None:
    """Exit if ``version_source`` (a version or file name) names a USDM release before v4."""
    match = _VERSION_PATTERN.search(version_source)
    if match and int(match.group(1)) < MIN_USDM_MAJOR_VERSION:
        print(
            f"USDM {match.group(0)} is not supported; "
            f"only USDM v{MIN_USDM_MAJOR_VERSION}.x and later can be generated"
        )
        sys.exit(1)


def _spec_version(openapi_spec_file: Path) -> str | None:
    with openapi_spec_file.open("r") as fh:
        return str(yaml.safe_load(fh).get("info", {}).get("version"))


def _load_api_metadata(openapi_spec_file: Path, usdm_version: str | None = None) -> dict:
    """
    Load API metadata from the OpenAPI spec; when the USDM version is known, the
    spec is only applied if its ``info.version`` matches.
    """
    report = get_report()
    report.set_path("OpenAPI specification", openapi_spec_file)
    if not openapi_spec_file.is_file():
        print(f"OpenAPI specification not found ({openapi_spec_file}); no API attributes added")
        report.warning("OpenAPI", f"Specification not found ({display_path(openapi_spec_file)}); no API attributes added")
        return {}
    if usdm_version is not None:
        spec_version = _spec_version(openapi_spec_file)
        if spec_version != usdm_version.lstrip("v"):
            message = (
                f"OpenAPI specification {display_path(openapi_spec_file)} is version {spec_version}, "
                f"not {usdm_version}; no API attributes added"
            )
            print(message)
            report.warning("OpenAPI", message)
            return {}
    return load_openapi_api_metadata(openapi_spec_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--usdm", help="Source is USDM", action="store_true", default=False
    )
    parser.add_argument("--usdm-ct", type=str, help="Path to Controlled Terms file")
    parser.add_argument("--output", type=str, help="Output directory", default="output")
    parser.add_argument(
        "--openapi-spec",
        type=str,
        help=f"OpenAPI specification file (YAML or JSON) for API attributes (default: {DEFAULT_OPENAPI_SPEC})",
    )
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
        _require_supported_version(Path(opts.source).name)
        from .usdm_unpkt import main_usdm

        start_report()
        openapi_spec_file = Path(opts.openapi_spec) if opts.openapi_spec else DEFAULT_OPENAPI_SPEC
        api_metadata = _load_api_metadata(openapi_spec_file)

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
    _require_supported_version(source_version)
    gen=dict(linkml=True)
    output_dir = opts.output
    usdm_ct = Path.cwd() / "input" / source_version / f"{source_version}_USDM_CT.xlsx"
    assert usdm_ct.is_file(), "USDM Controlled Terms file not found"
    source = Path.cwd() / "input" / source_version / f"{source_version}_USDM_UML.qea"
    assert source.is_file(), "USDM file not found"
    start_report()
    api_metadata = _load_api_metadata(DEFAULT_OPENAPI_SPEC, usdm_version=source_version)

    from .usdm_unpkt import main_usdm
    main_usdm(
        source_dir_or_file=source,
        controlled_term=usdm_ct,
        output_dir=output_dir,
        gen=gen,
        api_metadata=api_metadata,
    )
