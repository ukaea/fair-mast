# mast-book
Example notebooks and documentation for using the MAST data archive. See a live version of this documentations [here](http://ada-sam-app.oxfordfun.com)

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
jb build .
```

You can see the outputs in the `_build` folder. For more information about building jupyter books [see the docs](https://jupyterbook.org/en/stable/basics/build.html).