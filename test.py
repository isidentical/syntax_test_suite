import ast
import sys
import traceback
import warnings
from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Tuple


def ast_unparse_c(source):
    ann = {}
    exec(f"from __future__ import annotations; a: {source}", ann, ann)
    return ann["__annotations__"]["a"]


def test_package_impl(directory: Path) -> List[Path]:
    checks = []
    for file in directory.glob("**/*.py"):
        # do whatever you want
        pass

    return checks


def test_package(directory: Path) -> Tuple[str, List[Path]]:
    name = directory.name.split("-", -1)[0]
    print(f"Parsing {name}")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        try:
            checks = test_package_impl(directory)
        except Exception:
            return (name, [], traceback.format_exc(limit=2))

    return name, checks, None


def test_all(directory: Path, workers: int = 20):
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for package, checks, errors in executor.map(
            test_package, directory.iterdir()
        ):
            if checks:
                print(f"{package} couldn't unparse these files: ", *checks)
            if errors:
                print(f"While parsing {package} an exception caught: ", errors)


def main():
    parser = ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--workers", type=int)
    options = parser.parse_args()
    test_all(**vars(options))


if __name__ == "__main__":
    main()
