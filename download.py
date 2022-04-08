import json
import os
import shutil
import tarfile
import traceback
import zipfile
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union, cast
from urllib.request import Request, urlopen, urlretrieve

PYPI_INSTANCE = "https://pypi.org/pypi"
PYPI_TOP_PACKAGES = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json"

ArchiveKind = Union[tarfile.TarFile, zipfile.ZipFile]


def get_package_source(package: str, version: Optional[str] = None) -> str:
    with urlopen(PYPI_INSTANCE + f"/{package}/json") as page:
        metadata = json.load(page)

    if version is None:
        sources = metadata["urls"]
    else:
        if version in metadata["releases"]:
            sources = metadata["releases"][version]
        else:
            raise ValueError(
                f"No releases found with given version ('{version}') tag. "
                f"Found releases: {metadata['releases'].keys()}"
            )

    for source in sources:
        if source["python_version"] == "source":
            break
    else:
        raise ValueError(f"Couldn't find any sources for {package}")

    return cast(str, source["url"])


def get_archive_manager(local_file: str) -> ArchiveKind:
    if tarfile.is_tarfile(local_file):
        return tarfile.open(local_file)
    elif zipfile.is_zipfile(local_file):
        return zipfile.ZipFile(local_file)
    else:
        raise ValueError("Unknown archive kind.")


def get_first_archive_member(archive: ArchiveKind) -> str:
    if isinstance(archive, tarfile.TarFile):
        return archive.getnames()[0]
    elif isinstance(archive, zipfile.ZipFile):
        return archive.namelist()[0]


def download_and_extract(
    package: str, directory: Path, version: Optional[str] = None
) -> Path:
    try:
        source = get_package_source(package, version)
    except ValueError:
        return None

    print(f"Downloading {package}.")
    local_file, _ = urlretrieve(source, directory / f"{package}-src")
    with get_archive_manager(local_file) as archive:
        print(f"Extracting {package}")
        archive.extractall(path=directory)
        result_dir = get_first_archive_member(archive)
    os.remove(local_file)
    return directory / result_dir


def get_package(
    package: str, directory: Path, version: Optional[str] = None
) -> Tuple[str, Optional[Path]]:
    try:
        return package, download_and_extract(package, directory, version)
    except Exception as e:
        print(f"Caught an exception while downloading {package}.")
        traceback.print_exc()
        return package, None


def get_top_packages() -> List[str]:
    with urlopen(PYPI_TOP_PACKAGES.format()) as page:
        result = json.load(page)

    return [package["project"] for package in result["rows"]]


def dump_config(directory: Path, values: List[str]):
    with open(directory / "info.json", "w") as f:
        json.dump(values, f)


def read_config(directory: Path) -> List[str]:
    if (pkg_config := directory / "info.json").exists():
        with open(pkg_config) as f:
            cache = json.load(f)
        return cache
    else:
        return []


def filter_already_downloaded(
    directory: Path, packages: List[str]
) -> List[str]:
    cache = read_config(directory)
    return [package for package in packages if package not in cache]


def download_top_packages(
    directory: Path,
    workers: int = 24,
    limit: slice = slice(None),
) -> Generator[Path, None, None]:
    assert directory.exists()
    if not (directory / "info.json").exists():
        dump_config(directory, [])

    packages = get_top_packages()[limit]
    packages = filter_already_downloaded(directory, packages)
    caches = []
    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            bound_downloader = partial(get_package, directory=directory)
            for package, package_directory in executor.map(
                bound_downloader, packages
            ):
                if package_directory is not None:
                    caches.append(package)
                    print(
                        f"Package {package_directory} is created for {package}."
                    )
    finally:
        dump_config(directory, read_config(directory) + caches)


def main():
    parser = ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument(
        "--limit",
        type=lambda limit: slice(*map(int, limit.split(":"))),
        default=slice(0, 10),
    )
    options = parser.parse_args()
    download_top_packages(**vars(options))


if __name__ == "__main__":
    main()
