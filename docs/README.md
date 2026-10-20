# FAIR MAST Documentation

Example notebooks and documentation for using the MAST data archive. See the [live documentation](https://ukaea.github.io/fair-mast/).

To build the documentation locally, create its dedicated virtual environment (kept separate from the application's dependencies) and run Jupyter Book from the repository root:

```bash
uv venv .docs-venv --python 3.12
source .docs-venv/bin/activate
uv pip install -r docs-requirements.txt
jb build docs --path-output docs/built_docs
```

Then open `docs/built_docs/_build/html/index.html` in a browser.
