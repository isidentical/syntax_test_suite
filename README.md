# Syntax Test Suite

This is a test suite project that is for scraping most common pypi packages and run syntax based analysis over them.

## Usage
- First go to `test.py` and fill a `test_package_impl`.
- Then download pypi packages by `python download.py [directory to download]`
- and finally run your `test_package_impl` by `python test.py [directory where downloads are]`

You can specify worker process/thread count by `--workers`
