# Syntax Test Suite

This is a test suite project that is for scraping most common pypi packages and run syntax based analysis over them.

## Usage
- First go to `test.py` and fill a `test_package_impl`.
- Then download pypi packages by `python download.py [directory to download]`
- and finally run your `test_package_impl` by `python test.py [directory where downloads are]`

You can specify worker process/thread count by `--workers`

## Example
Example implementation of `test_packages_impl`
```py
def test_package_impl(file: Path) -> List[Any]:
    reports = []
    try:
        with tokenize.open(file) as f:
            source = f.read()

        source = ast.parse(source)
    except SyntaxError:
        return reports
      
    for node in ast.walk(source):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Constant):
            for comparator in node.comparators:
                if isinstance(comparator, (ast.Tuple, ast.List, ast.Set)) and all(isinstance(elt, ast.Constant) for elt in comparator.elts):
                    break
            else:
                continue
            reports.append({"lineno": node.lineno, "source": ast.unparse(node)})

    return reports
```
And run
```
 $ python test.py packages --workers 8
==================================================
Package: pytest
Report(filename=PosixPath('packages/pytest-5.3.5/packages/pytest-5.3.5/doc/en/example/assertion/failure_demo.py'), report={'lineno': 81, 'source': '1 in [0, 2, 3, 4, 5]'})
```

