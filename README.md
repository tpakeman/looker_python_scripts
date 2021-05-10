# looker_python_scripts
A selection of Python 3 scripts to achieve various tasks in Looker
Each script is saved as a single self contained python file in the root directory. Some shared functions are in the `helpers/` directory.

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
* `--help` or `-h` to print help
* `--silent` or `-s` to surpress insecure request warnings
* `--list` or `-l` to list all available looker projects on environment
* `--projects` or `-p` followed by a space-separated list of projects to test against. Omitting this will run against all projects
* `--dev` or `-d` to run against the current state of the user's development branch. Omitting this will run against production

#### Sample usage
* `python run_data_tests.py -p foo` Will run all tests in project `foo`, in production mode
* `python run_data_tests.py -d -p bar baz` Will run all tests in projects `bar` and `baz`, in development mode

---

## Select fields in explore
This is a CLI that runs a query containing all of the fields in an explore and surfaces any errors.
* By default, this will return on the first error discovered
* Use the `-c` or `--continue` argument to attempt to iteratively find all errors. This uses many more API queries
* **NOTE** Error checking is very simplistic - Looker does not surface error codes for failed queries, so we are literally looking for the string 'error' to appear in the results

#### Arguments
* `-explores` or `-e` followed by a space-separated list of explores to test against. Omitting this will run against all explores
* `-models` or `-m` followed by a space-separated list of models to test against. Omitting this will run against all models
* `--dev` or `-d` to run against the current state of the user's development branch. Omitting this will run against production
* `--continue` or `-c` will continue on errors. Omitting this will stop on the first error. *Caution* this is a recursive function that removes the fields causing problems and re-runs the query, so it can lead to very many API calls in cases with lots of errors

#### Sample usage
* `python validate_explore_sql.py -dc -e foo` Will run all fields in explore `foo` for all models, in development mode, continuing on errors
* `python validate_explore_sql.py -m bar` Will run all explores in model `bar`, in production mode.
* `python validate_explore_sql.py -m bar -e baz bat` Will run the `baz` and `bat` explores in model `bar`, in production mode.

---

### TO DO
* validate_sql.py
  * Batch mode for validating explore fields in chunks
  * Validate fields by name
  * Improve error finding and continuation logic