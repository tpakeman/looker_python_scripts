# looker_python_scripts
A selection of Python 3 scripts to achieve various tasks in Looker

## Select fields in explore
This is a CLI that runs a query containing all of the fields in an explore and surfaces any errors.

### Requirements
* Python 3.7+
* [looker_sdk](https://pypi.org/project/looker-sdk/) available on PyPI
* `looker.ini` file stored in the same directory and containing Looker API credentials as explained in docs on PyPI

### Arguments
* `-explores` or `-e` followed by a list of explores to test against. Ommitting this will run against all explores
* `-models` or `-m` followed by a list of models to test against. Ommitting this will run against all models
* `--dev` or `-d` to run against the current state of the user's development branch. Ommitting this will run against production
* `--continue` or `-c` will continue on errors. Ommitting this will stop on the first error. *Caution* this is a recursive function that removes the fields causing problems and re-runs the query, so it can lead to very many API calls in cases with lots of errors
* `--print` or `-p` to print the link to the explore containing all of the fields

### Sample usage
* `python path/to/file.py -dc -e foo` Will run all fields in explore `foo` for all models, in development mode, continuing on errors
* `python path/to/file.py -m bar` Will run all explores in model `bar`, in production mode.
* `python path/to/file.py -m bar -e baz bat -p` Will run the `baz` and `bat` explores in model `bar`, in production mode, and print the links to the explore queries used.