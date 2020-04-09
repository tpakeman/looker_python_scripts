import os
from looker_sdk import models, error, init31
from looker_sdk.rtl.transport import TransportSettings
from looker_sdk.error import SDKError
import argparse
import re
import urllib3

# For colour-coding the output
colours = {'HEADER':'\033[95m',
           'OKBLUE': '\033[94m',
           'OKGREEN': '\033[92m',
           'WARNING': '\033[93m',
           'FAIL': '\033[91m',
           'END': '\033[0m',
           'BOLD': '\033[1m',
           'UNDERLINE': '\033[4m'}


looker_client = init31('looker.ini')
try:
    # Use this if testing locally or on a server without a certificate
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    user = looker_client.me()
    print(f"{colours['HEADER']}Authenticated as {user.display_name} (User ID {user.id}){colours['END']}")
except SDKError:
    print(f"{colours['FAIL']}Could not authenticate. Check `looker.ini` file{colours['END']}")


def get_models():
    """Return a list of models"""
    return [model.name for model in looker_client.all_lookml_models(fields='name')]


def get_explores_from_model(model_name):
    """Return a list of explores for a given model."""
    try:
        return [explore.name for explore in looker_client.lookml_model(model_name, fields='explores').explores]
    except SDKError:
        print(f"{colours['FAIL']}ERROR:\tModel {model_name} not found.{colours['END']}")
        exit()


def get_fields_from_model_explore(model_name, explore_name):
    """Return a list of fields from a given model and explore"""
    try:
        explore = looker_client.lookml_model_explore(model_name, explore_name)
        dims = [dim.name for dim in explore.fields.dimensions]
        mes = [mes.name for mes in explore.fields.measures]
        return dims, mes
    except SDKError:
        print(f"{colours['FAIL']}ERROR:\tExplore {explore_name} not found.{colours['END']}")
        exit()


def create_query_from_fields(model_name, explore_name, excludes):
    """Creates a Looker query containing all fields in an explore for a given model.
    Optionally a list of fields to exclude can be passed.
    Returns the query.id, the number of fields and the share_url of the query."""
    dims, mes = get_fields_from_model_explore(model_name, explore_name)
    field_set = dims + mes
    field_set = [field for field in field_set if field not in excludes]
    body = models.WriteQuery(model=model_name, view=explore_name, fields=field_set)
    query = looker_client.create_query(body)
    del query.client_id
    return query.id, field_set, query.share_url


def check_fields(model_name, explore_name, continue_on_errors=False, excludes=[]):
    """Runs a query containing all of the fields in a given model and explore to see if there are any SQL errors.
    Can choose to print some helpful output, and to continue if you find an error."""
    query_id, field_set, query_url = create_query_from_fields(model_name, explore_name, excludes)
    num_fields = len(field_set)
    result = looker_client.run_query(query_id, 'csv', limit=1)
    sql = looker_client.run_query(query_id, 'sql')
    if result.strip().startswith('SQL Error'):
        if continue_on_errors:
            for field in field_set:
                if field in result:
                    if excludes == []:
                        print(f"{colours['WARNING']}Errors found, continuing...{colours['END']}")
                    excludes.append(field)
                    return check_fields(model_name, explore_name, continue_on_errors, excludes)
        else:
            print(f"{colours['FAIL']}{result}:\t{colours['END']}{colours['UNDERLINE']}{query_url}{colours['END']}")
            return result, num_fields, sql, query_url
    elif result is not None:       
        print(f"{colours['OKGREEN']}Success for {num_fields} fields:\t{colours['END']}{colours['UNDERLINE']}{query_url}{colours['END']}\n")
        if excludes != []:
            excludes = list(set(excludes))
            excludes.sort()
            print(f"{colours['FAIL']}Failures:{colours['END']}")
            for e in excludes:
                print(f"{colours['FAIL']}\t{e}{colours['END']}")
    else:
        print(result)
    return result, num_fields, sql, query_url


def check_fields_in_model(models=None, explores=None, continue_on_errors=False, excludes=None):
    """Input the name of a model, and optionally, a list of explores to check against.
    If explores is None this will check the fields for all explores"""
    if models is None:
        models = get_models()
    elif isinstance(models, str):
        models = [models]
    for model in models:
        if explores is None:
            explores = get_explores_from_model(model)
        elif isinstance(explores, str):
            explores = [explores]
        for explore in explores:
            print(f"{colours['BOLD']}\nChecking fields for explore: {colours['END']}{colours['OKBLUE']}{explore}{colours['END']}{colours['BOLD']} in model: {colours['END']}{colours['OKBLUE']}{model}{colours['END']}")
            print("_" * 79)
            if excludes is None:
                excludes = []
            _, _, _, _ = check_fields(model, explore, continue_on_errors, excludes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Put in the name of a model and a list of explores to check, or omit to check all explores.")
    parser.add_argument('--models', '-m', nargs='+', help='Pass in the name of a model or a space separated list of models')
    parser.add_argument('--explores', '-e', nargs='+', help='Pass in the name of an explore or a space separated list of explores')
    parser.add_argument('--continue', '-c', action='store_true', help='Add this to continue on errors and surface a list. If excluded this will stop on the first error for each explore.')
    parser.add_argument('--dev', '-d', action='store_true', help='Include to compare to dev branch. Omit to use production.')
    parser.add_argument('--excludes', '-x',  nargs='+', help='Include a space separated list of fully-scoped (view.field) fields to ignore.')
    args = parser.parse_args()
    if args.dev:
        looker_client.update_session(models.WriteApiSession(workspace_id='dev'))
        print(f"{colours['WARNING']}Comparing to dev branch{colours['END']}")
    else:
        print(f"{colours['HEADER']}Comparing to prod branch{colours['END']}")
    check_fields_in_model(models=args.models,
                          explores=args.explores,
                          continue_on_errors=getattr(args, 'continue'),
                          excludes=args.excludes)
