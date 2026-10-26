[![License](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/MIT) [![Publish site](https://github.com/ukaea/fair-mast/actions/workflows/deploy_pages.yml/badge.svg?branch=main)](https://github.com/ukaea/fair-mast/actions/workflows/deploy_pages.yml)

# FAIR MAST Documentation

Source for the [FAIR MAST documentation](https://ukaea.github.io/fair-mast/): notebooks and guides for loading MAST data and metadata from the public S3 bucket (`s3://mast`, endpoint `https://s3.echo.stfc.ac.uk`).

## Building the documentation

The documentation is built with [Jupyter Book](https://jupyterbook.org/). From the repository root:

```bash
uv venv .docs-venv --python 3.12
source .docs-venv/bin/activate
uv pip install -r docs-requirements.txt
jb build docs --path-output docs/built_docs
```

Then open `docs/built_docs/_build/html/index.html` in a browser.

Executed notebooks are cached in `docs/built_docs/_build/.jupyter_cache`, so later builds only re-run notebooks whose code has changed. Delete that directory to re-run everything.

## Publishing the documentation

The `Publish site` workflow (`.github/workflows/deploy_pages.yml`) builds the book on every push and pull request to `main`, and deploys it to GitHub Pages from `main`.

- **Notebook cache.** The build restores the execution cache from `s3://mast/fairmast-docs/jupyter_cache/` and, on `main`, saves it back. Only notebooks with changed code are executed. This needs the `STFC_ACCESS_KEY` and `STFC_SECRET_ACCESS_KEY` repository secrets.
- **Re-running everything.** Code changes are the only trigger, so after the data changes, delete the cache prefix to re-execute every notebook.
- **Failed notebooks.** A notebook that fails to execute doesn't fail the build. It shows up as a warning annotation on the run, with its traceback under `reports/` in the built site. Check these before merging.

## Publishing metadata to S3

The metadata Parquet files under `s3://mast/fairmast-meta/` are generated and uploaded outside this repository. Objects in the `mast` bucket are only publicly readable if they are uploaded with a public-read ACL; the bucket policy does not grant it. Always upload with `--acl public-read`, for example:

```bash
s5cmd --endpoint-url https://s3.echo.stfc.ac.uk cp --acl public-read "./fairmast-meta/*" s3://mast/fairmast-meta/
```

Check that an object is public with `curl -I https://s3.echo.stfc.ac.uk/mast/fairmast-meta/l2_shots.parquet`, which should return `200`, not `403`.

## Supported data formats

| Format  | Version | MIME Type            | Spec URL                                                            |
|---------|---------|----------------------|---------------------------------------------------------------------|
| Parquet | 1.0+    | application/parquet  | https://parquet.apache.org/docs/overview                           |
| Zarr    | v2      | application/zarr     | https://zarr.readthedocs.io/en/stable/spec/v2.html                 |

The Zarr files use a chunked and compressed layout suitable for large-scale analysis workflows.

## Citation

If you would like to reference this work, please cite the following publications:

***Samuel Jackson, Saiful Khan, Nathan Cummings, James Hodson, Shaun de Witt, Stanislas Pamela, Rob Akers, Jeyan Thiyagalingam***, _An Open Data Service for Supporting Research in Machine Learning on Tokamak Data_, IEEE Transactions on Plasma Science, 2025;1–10. 

***Samuel Jackson, Saiful Khan, Nathan Cummings, James Hodson, Shaun de Witt, Stanislas Pamela, Rob Akers, Jeyan Thiyagalingam***, _FAIR-MAST: A fusion device data management system_, SoftwareX, Volume 27, 2024,101869, ISSN 2352-7110, [https://doi.org/10.1016/j.softx.2024.101869](https://doi.org/10.1016/j.softx.2024.101869).

In BibTex format:
```
@article{jackson_open_2025,
    title = {An {Open} {Data} {Service} for {Supporting} {Research} in {Machine} {Learning} on {Tokamak} {Data}},
    issn = {1939-9375},
    url = {https://ieeexplore.ieee.org/document/11128905},
    doi = {10.1109/TPS.2025.3583419},
    urldate = {2025-08-19},
    journal = {IEEE Transactions on Plasma Science},
    author = {Jackson, Samuel and Khan, Saiful and Cummings, Nathan and Hodson, James and de Witt, Shaun and Pamela, Stanislas and Akers, Rob and Thiyagalingam, Jeyan},
    year = {2025},
}

@article{jackson_fair-mast_2024,
	title = {{FAIR}-{MAST}: {A} fusion device data management system},
	volume = {27},
	issn = {23527110},
	shorttitle = {{FAIR}-{MAST}},
	url = {https://linkinghub.elsevier.com/retrieve/pii/S2352711024002395},
	doi = {10.1016/j.softx.2024.101869},
	language = {en},
	urldate = {2025-01-17},
	journal = {SoftwareX},
	author = {Jackson, Samuel and Khan, Saiful and Cummings, Nathan and Hodson, James and De Witt, Shaun and Pamela, Stanislas and Akers, Rob and Thiyagalingam, Jeyan},
	month = sep,
	year = {2024},
	pages = {101869},
}
```
