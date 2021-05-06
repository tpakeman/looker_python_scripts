# looker_python_scripts
A selection of Python 3 scripts to achieve various tasks in Looker
Each script is saved in a self-contained subfolder of this repo: navigate to the subdirectory and run `main.py` following the instructions below

### Requirements
* Python 3.7+
* [looker_sdk](https://pypi.org/project/looker-sdk/) available on PyPI
* `looker.ini` file stored (usually in the same directory as the scripts) and containing Looker API credentials as explained in docs on [PyPI](https://pypi.org/project/looker-sdk/)
  * See `looker.ini.example` for sample format
* Run `pipenv shell && pipenv install` to install required modules using pipenv (recommended) or use `pip install -r requirements.txt`
---

## Run data tests
This CLI runs all of the Looker data tests against a Looker project and displays a pass/fail result and the total % success rate.

#### Arguments
* `-projects` or `-p` followed by a space-separated list of projects to test against. Omitting this will run against all projects
* `--dev` or `-d` to run against the current state of the user's development branch. Omitting this will run against production

#### Sample usage
* `python path/to/file.py -p foo` Will run all tests in project `foo`, in production mode
* `python path/to/file.py -d -p bar baz` Will run all tests in projects `bar` and `baz`, in development mode
---
## Select fields in explore
This is a CLI that runs a query containing all of the fields in an explore and surfaces any errors.

#### Arguments
* `-explores` or `-e` followed by a space-separated list of explores to test against. Omitting this will run against all explores
* `-models` or `-m` followed by a space-separated list of models to test against. Omitting this will run against all models
* `--dev` or `-d` to run against the current state of the user's development branch. Omitting this will run against production
* `--continue` or `-c` will continue on errors. Omitting this will stop on the first error. *Caution* this is a recursive function that removes the fields causing problems and re-runs the query, so it can lead to very many API calls in cases with lots of errors

#### Sample usage
* `python path/to/file.py -dc -e foo` Will run all fields in explore `foo` for all models, in development mode, continuing on errors
* `python path/to/file.py -m bar` Will run all explores in model `bar`, in production mode.
* `python path/to/file.py -m bar -e baz bat` Will run the `baz` and `bat` explores in model `bar`, in production mode.