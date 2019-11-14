import os
from looker_sdk import client, models, error
from looker_sdk.rtl.transport import TransportSettings
from looker_sdk.error import SDKError
import argparse
import re

looker_client = client.setup('looker.ini')
try:
    user = looker_client.me()
    print(f"Authenticated as {user.display_name} (User ID {user.id})")
except SDKError:
    print("Could not authenticate. Check `looker.ini` file")


def get_models():
    """Return a list of models"""
    return [model.name for model in looker_client.all_lookml_models(fields='name')]


def get_explores_from_model(model_name):
    """Return a list of explores for a given model."""
    try:
        return [explore.name for explore in looker_client.lookml_model(model_name, fields='explores').explores]
    except SDKError:
        print(f"ERROR:\tModel {model_name} not found.")
        exit()


def get_fields_from_model_explore(model_name, explore_name):
    """Return a list of fields from a given model and explore"""
    try:
        explore = looker_client.lookml_model_explore(model_name, explore_name)
        dims = [dim.name for dim in explore.fields.dimensions]
        mes = [mes.name for mes in explore.fields.measures]
        return dims, mes
    except SDKError:
        print(f"ERROR:\tExplore {explore_name} not found.")
        exit()


def create_query_from_fields(model_name, explore_name, excludes):
    """Creates a Looker query containing all fields in an explore for a given model.
    Optionally a list of fields to exclude can be passed.
    Returns the query.id, the number of fields and the share_url of the query."""
    dims, mes = get_fields_from_model_explore(model_name, explore_name)
    field_set = dims + mes
    field_set = [field for field in field_set if field not in excludes]
    num_fields = len(field_set)
    body = {"model": model_name, 'view': explore_name, 'fields': field_set}
    query = looker_client.create_query(body)
    del query.client_id
    return query.id, num_fields, query.share_url


def check_fields(model_name, explore_name, print_data=False, continue_on_errors=False, excludes=[]):
    """Runs a query containing all of the fields in a given model and explore to see if there are any SQL errors.
    Can choose to print some helpful output, and to continue if you find an error."""
    query_id, num_fields, query_url = create_query_from_fields(model_name, explore_name, excludes)
    result = looker_client.run_query(query_id, 'csv', limit=1)
    sql = looker_client.run_query(query_id, 'sql')
    if result.startswith('SQL Error'):
        if not continue_on_errors:
            if 'The query is too large' in result: # This error may be specific to BigQuery.
                print(result.splitlines()[-1])
            else:
                print(result)
        if 'at [' in result:
            error_location = result.split(' at [')[1][:-1].split(':')
            error_line = sql.splitlines()[int(error_location[0]) - 2]
            if not continue_on_errors:
                print(f"Error line in SQL: {error_line}")
                if print_data:
                    print(query_url)
            else:
                if excludes == []:
                    print("Errors found, continuing...")
                search_pattern = r'AS ([\w_]*),'
                matches = [m.lower() for m in re.findall(search_pattern, error_line)]
                if len(matches) > 1:
                    print("Multiple possible fields found. Please type a number to exclude, or enter '0' to cancel.")
                    for i in range(len(matches)):
                        print(f"{i + 1}\t{matches[i]}")
                    ans = int(input(""))
                    if ans == 0:
                        return result, num_fields, sql, query_url
                    elif ans <= len(matches):
                        match = matches[ans - 1]
                        field = explore_name + '.' + match[len(explore_name) + 1:]
                        excludes.append(field)
                elif len(matches) == 1:
                    match = matches[0]
                    field = explore_name + '.' + match[len(explore_name) + 1:]
                    excludes.append(field)
                else:
                    return result, num_fields, sql, query_url
                return check_fields(model_name, explore_name, print_data, continue_on_errors, excludes)
    elif result is not None:       
        if print_data:
            print(f"Success for {num_fields} fields:\t{query_url}")
        else:
            print(f"Success for {num_fields} fields.")
        if excludes != []:
            excludes = list(set(excludes))
            excludes.sort()
            print("Failures:")
            for e in excludes:
                print('\t', e)
    else:
        print(result)
    return result, num_fields, sql, query_url


def check_fields_in_model(models=None, explores=None, print_data=False, continue_on_errors=False, excludes=None):
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
            print(f"\nChecking fields for explore: {explore} in model: {model}")
            print("_" * 79)
            if excludes is None:
                excludes = []
            _, _, _, _ = check_fields(model, explore, print_data, continue_on_errors, excludes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Put in the name of a model and a list of explores to check, or omit to check all explores.")
    parser.add_argument('--models', '-m', nargs='+', help='Pass in the name of a model or a space separated list of models')
    parser.add_argument('--explores', '-e', nargs='+', help='Pass in the name of an explore or a space separated list of explores')
    parser.add_argument('--print', '-p', action='store_true', help='Print additional information for further debugging')
    parser.add_argument('--continue', '-c', action='store_true', help='Add this to continue on errors and surface a list. If excluded this will stop on the first error for each explore.')
    parser.add_argument('--dev', '-d', action='store_true', help='Include to compare to dev branch. Omit to use production.')
    parser.add_argument('--excludes', '-x',  nargs='+', help='Include a space separated list of fully-scoped (view.field) fields to ignore.')
    args = parser.parse_args()
    if args.dev:
        looker_client.update_session({'workspace_id': 'dev'})
        print("Comparing to dev branch")
    else:
        print("Comparing to prod branch")
    check_fields_in_model(models=args.models,
                          explores=args.explores,
                          print_data=args.print,
                          continue_on_errors=getattr(args, 'continue'),
                          excludes=args.excludes)
