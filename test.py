import ast
import sys
import tokenize
import traceback
import warnings
from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple


def ast_unparse_c(source):
    ann = {}
    exec(f"from __future__ import annotations; a: {source}", ann, ann)
    return ann["__annotations__"]["a"]


@dataclass
class Report:
    filename: Path
    report: Any


def test_package_impl(file: Path) -> List[Any]:
    reports = []
    # IMPLEMENT HERE
    return reports


def test_package_files(directory: Path) -> List[Report]:
    reports = []
    for file in directory.glob("**/*.py"):
        # do whatever you want
        for report in test_package_impl(file):
            reports.append(Report(directory / file, report))
    return reports


def test_package(directory: Path) -> Tuple[str, List[Report], Optional[str]]:
    name = directory.name.split("-", -1)[0]
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        try:
            reports = test_package_files(directory)
        except Exception:
            return (name, [], traceback.format_exc(limit=2))

    return name, reports, None


def test_all(directory: Path, workers: int = 20):
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(test_package, d) for d in directory.iterdir()}
        for future in as_completed(futures):
            package, reports, errors = future.result()
            if reports or errors:
                print("=" * 50)
                print("Package:", package)
                for report in reports:
                    print(report)
                if errors:
                    print(f"While testing an exception caught: ", errors)


def main():
    parser = ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--workers", type=int)
    options = parser.parse_args()
    test_all(**vars(options))


if __name__ == "__main__":
    main()
