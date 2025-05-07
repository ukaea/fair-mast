# FAIR MAST Documentation
Example notebooks and documentation for using the MAST data archive. See a live version of this documentations [here](https://mastapp.site/)

## Setup
To setup the environment for the notebooks we need to create the local conda environment:

```bash
conda env create -f environment.yml
conda activate mast-book
```

They run the notebooks!

## Building the Book Locally

Then build the book locally:

```bash
jb build . --path-output ../src/api/static
```

You can see the outputs in the `./src/api/static/_build` folder. For more information about building jupyter books [see the docs](https://jupyterbook.org/en/stable/basics/build.html).