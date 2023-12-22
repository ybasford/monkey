# To get the version from shell, run `python ./version.py` (see `python ./version.py -h` for
# details).
import argparse
from pathlib import Path

MAJOR = "2"
MINOR = "3"
PATCH = "0"

build_file_path = Path(__file__).parent.joinpath("BUILD")
with open(build_file_path, "r") as build_file:
    BUILD = build_file.read().strip()


def get_version(build=BUILD):
    if build:
        return f"{MAJOR}.{MINOR}.{PATCH}+{build}"
    else:
        return f"{MAJOR}.{MINOR}.{PATCH}"


def print_version():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b", "--build", default=BUILD, help="Choose the build string for this version.", type=str
    )
    args = parser.parse_args()
    print(get_version(args.build))


if __name__ == "__main__":
    print_version()
