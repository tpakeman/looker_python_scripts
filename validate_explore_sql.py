import looker_sdk
from looker_sdk.error import SDKError
from helpers.logging import cprint, setup_log
from helpers import sdk
import argparse, re

LOGGER = setup_log('validate_sql')

def get_models(client):
    """Return a list of models"""
    return [model.name for model in client.all_lookml_models(fields='name')]


def get_explores_from_model(client, model_name, log=LOGGER):
    """Return a list of explores for a given model."""
    try:
        return [explore.name for explore in client.lookml_model(model_name, fields='explores').explores]
    except SDKError:
        cprint(f"ERROR:\tModel {model_name} not found.", "FAIL", log)
        exit()


def get_fields_from_model_explore(client, model_name, explore_name, log=LOGGER):
    """Return a list of fields from a given model and explore"""
    try:
        explore = client.lookml_model_explore(model_name, explore_name)
        dims = [dim.name for dim in explore.fields.dimensions]
        mes = [mes.name for mes in explore.fields.measures]
        return dims, mes
    except SDKError:
        cprint(f"ERROR:\tExplore {explore_name} not found.", "FAIL", log)
        exit()


def create_query_from_fields(client, model_name, explore_name, excludes):
    """Creates a Looker query containing all fields in an explore for a given model.
    Optionally a list of fields to exclude can be passed.
    Returns the query.id, the number of fields and the share_url of the query."""
    dims, mes = get_fields_from_model_explore(client, model_name, explore_name)
    field_set = dims + mes
    field_set = [field for field in field_set if field not in excludes]
    body = looker_sdk.models.WriteQuery(model=model_name, view=explore_name, fields=field_set)
    query = client.create_query(body)
    del query.client_id
    return query.id, field_set, query.share_url


# TO DO - refine logic here
def has_error(sql_string):
    """Check if returned SQL text contains an error"""
    patt = re.compile(r'.*(?:error)')
    return re.match(patt, sql_string.strip().lower()) is not None

### TO DO - check logic here
def check_fields(client, model_name, explore_name, continue_on_errors=False, excludes=[], ix=None, log=LOGGER):
    """Runs a query containing all of the fields in a given model and explore to see if there are any SQL errors.
    Can choose to print some helpful output, and to continue if you find an error.
    
    Continuation logic looks like this:
        Try all fields and if one causes an error, exclude it and try again
        Continue this process until all remaining fields run without errors. 
    """
    query_id, field_set, query_url = create_query_from_fields(client, model_name, explore_name, excludes)
    num_fields = len(field_set)
    result = client.run_query(query_id, 'csv', limit=1)
    # sql = client.run_query(query_id, 'sql') # What is this for?
    if has_error(result):
        if not continue_on_errors:
            cprint(f"{result}:\t",'FAIL', log)
            cprint(f"{query_url}\n", 'UNDERLINE', log)
            return result, num_fields, query_url
        else:
            for field in field_set:
                if '.'.join(field.split('.')[1:]) in result:
                    if excludes == []:
                        cprint(f"Errors found, continuing...", "WARNING", log)
                    excludes.append(field)
                    return check_fields(client, model_name, explore_name, continue_on_errors, excludes, ix, log)
            return check_fields(client, model_name, explore_name, False, excludes, ix, log)
    else:
        cprint(f"Success for {num_fields} fields:\t", 'OKGREEN', log, end='')
        cprint(f"{query_url}\n", 'UNDERLINE', log)
        if excludes != []:
            excludes = sorted(list(set(excludes)))
            cprint(f"Failures:", "FAIL", log)
            for e in excludes:
                cprint(f"\t{e}", "FAIL", log)
    return result, num_fields, query_url


def check_fields_in_model(client, models=None, explores=None, continue_on_errors=False, excludes=None, log=LOGGER):
    """Input the name of a model, and optionally, a list of explores to check against.
    If explores is None this will check the fields for all explores"""
    if models is None:
        models = get_models(client)
    elif isinstance(models, str):
        models = [models]
    for model in models:
        if explores is None:
            explores = get_explores_from_model(client, model)
        elif isinstance(explores, str):
            explores = [explores]
        for explore in explores:
            cprint(f"\nChecking fields for explore: ", "BOLD", log, end='')
            cprint(f"{explore}", "OKBLUE", log, end='')
            cprint(" in model: ", "BOLD", log, end='')
            cprint(f"{model}", "OKBLUE", log)
            print("_" * 79)
            if excludes is None:
                excludes = []
            _ = check_fields(client, model, explore, continue_on_errors, excludes)

def main():
    parser = argparse.ArgumentParser("Put in the name of a model and a list of explores to check, or omit to check all explores.")
    parser.add_argument('--models', '-m', nargs='+', help='Pass in the name of a model or a space separated list of models')
    parser.add_argument('--explores', '-e', nargs='+', help='Pass in the name of an explore or a space separated list of explores')
    parser.add_argument('--continue', '-c', action='store_true', help='Add this to continue on errors and surface a list. If excluded this will stop on the first error for each explore.')
    parser.add_argument('--dev', '-d', action='store_true', help='Include to compare to dev branch. Omit to use production.')
    parser.add_argument('--excludes', '-x',  nargs='+', help='Include a space separated list of fully-scoped (view.field) fields to ignore.')
    parser.add_argument('--silent', '-s', action='store_true', help='Surpress insecure request warnings.')
    args = parser.parse_args()
    if args.silent:
        sdk.ignore_insecure_requests()
    try:
        client = sdk.auth(LOGGER, section='Personal Sandbox')
    except Exception:
        exit()
    if args.dev:
        client = sdk.toggle_dev(client, LOGGER, True)
    check_fields_in_model(client,
                          models=args.models,
                          explores=args.explores,
                          continue_on_errors=getattr(args, 'continue'),
                          excludes=args.excludes)

if __name__ == '__main__':
    main()
