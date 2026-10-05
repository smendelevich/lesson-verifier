"""Lesson verifier: compares a source lesson with a loaded lesson. See SPEC.md."""

import argparse
import sys


def build_parser():
    parser = argparse.ArgumentParser(
        prog="verify.py",
        description="Verify that a Hebrew lesson was loaded correctly.",
    )
    parser.add_argument("source", help="path to source.json (the expected lesson)")
    parser.add_argument("loaded", help="path to loaded.json (what the system holds)")
    parser.add_argument(
        "--assets-dir",
        help="directory to look up audio_file and image_file names in",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="output format (default: text)",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    parser.parse_args(argv)
    # No checks yet.
    return 0


if __name__ == "__main__":
    sys.exit(main())
