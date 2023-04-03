import sys
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--usdm", help="Source is USDM", action="store_true", default=False)
    parser.add_argument("--usdm-ct", type=str, help="Path to Controlled Terms file")
    parser.add_argument("--output", type=str, help="Output directory", default="output")
    parser.add_argument("source", type=str, help="Source directory")
    opts = parser.parse_args()
    source = opts.source
    output_dir = opts.output
    if opts.usdm:
        if opts.usdm_ct is None:
            print("USDM Controlled Terms file is required")
            sys.exit(1)
        from .usdm_unpkt import main_usdm
        main_usdm(opts.source, opts.usdm_ct, output_dir)
    else:
        from .unpkt import main
        main(source, output_dir)

