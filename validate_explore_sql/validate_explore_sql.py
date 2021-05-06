import looker_sdk
from looker_sdk.error import SDKError

COLOURS = {'HEADER':'\033[95m',
           'OKBLUE': '\033[94m',
           'OKGREEN': '\033[92m',
           'WARNING': '\033[93m',
           'FAIL': '\033[91m',
           'END': '\033[0m',
           'BOLD': '\033[1m',
           'UNDERLINE': '\033[4m'}

def auth(ini_path='looker.ini', section=None):
    """Attempt to log in to Looker API with specified ini file and section"""
    try:
        client = looker_sdk.init31(ini_path, section)
        user = client.me()
        print(f"{COLOURS['HEADER']}Authenticated as {user.display_name} (User ID {user.id}){COLOURS['END']}")
    except SDKError:
        print(f"{COLOURS['FAIL']}Could not authenticate. Check `looker.ini` file at {ini_path} and section name {section}{COLOURS['END']}")
        raise SDKError
    return client


def toggle_dev(client, on=True):
    """Explicitly toggle between dev and prod.
        on=True for Dev
        on=False for Prod
    """
    if on:
        client.update_session(looker_sdk.models.WriteApiSession(workspace_id='dev'))
        print(f"{COLOURS['WARNING']}Comparing to dev branch{COLOURS['END']}")
    else:
        client.update_session(looker_sdk.models.WriteApiSession(workspace_id='prod'))
        print(f"{COLOURS['HEADER']}Comparing to prod branch{COLOURS['END']}")
    return client


def get_models(client):
    """Return a list of models"""
    return [model.name for model in client.all_lookml_models(fields='name')]


def get_explores_from_model(client, model_name):
    """Return a list of explores for a given model."""
    try:
        return [explore.name for explore in client.lookml_model(model_name, fields='explores').explores]
    except SDKError:
        print(f"{COLOURS['FAIL']}ERROR:\tModel {model_name} not found.{COLOURS['END']}")
        exit()


def get_fields_from_model_explore(client, model_name, explore_name):
    """Return a list of fields from a given model and explore"""
    try:
        explore = client.lookml_model_explore(model_name, explore_name)
        dims = [dim.name for dim in explore.fields.dimensions]
        mes = [mes.name for mes in explore.fields.measures]
        return dims, mes
    except SDKError:
        print(f"{COLOURS['FAIL']}ERROR:\tExplore {explore_name} not found.{COLOURS['END']}")
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


def check_fields(client, model_name, explore_name, continue_on_errors=False, excludes=[]):
    """Runs a query containing all of the fields in a given model and explore to see if there are any SQL errors.
    Can choose to print some helpful output, and to continue if you find an error."""
    query_id, field_set, query_url = create_query_from_fields(client, model_name, explore_name, excludes)
    num_fields = len(field_set)
    result = client.run_query(query_id, 'csv', limit=1)
    sql = client.run_query(query_id, 'sql')
    if result.strip().startswith('SQL Error'):
        if continue_on_errors:
            for field in field_set:
                if field in result:
                    if excludes == []:
                        print(f"{COLOURS['WARNING']}Errors found, continuing...{COLOURS['END']}")
                    excludes.append(field)
                    return check_fields(client, model_name, explore_name, continue_on_errors, excludes)
        else:
            print(f"{COLOURS['FAIL']}{result}:\t{COLOURS['END']}{COLOURS['UNDERLINE']}{query_url}{COLOURS['END']}")
            return result, num_fields, sql, query_url
    elif result is not None:       
        print(f"{COLOURS['OKGREEN']}Success for {num_fields} fields:\t{COLOURS['END']}{COLOURS['UNDERLINE']}{query_url}{COLOURS['END']}\n")
        if excludes != []:
            excludes = list(set(excludes))
            excludes.sort()
            print(f"{COLOURS['FAIL']}Failures:{COLOURS['END']}")
            for e in excludes:
                print(f"{COLOURS['FAIL']}\t{e}{COLOURS['END']}")
    else:
        print(result)
    return result, num_fields, sql, query_url


def check_fields_in_model(client, models=None, explores=None, continue_on_errors=False, excludes=None):
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
            print(f"{COLOURS['BOLD']}\nChecking fields for explore: {COLOURS['END']}{COLOURS['OKBLUE']}{explore}{COLOURS['END']}{COLOURS['BOLD']} in model: {COLOURS['END']}{COLOURS['OKBLUE']}{model}{COLOURS['END']}")
            print("_" * 79)
            if excludes is None:
                excludes = []
            _, _, _, _ = check_fields(client, model, explore, continue_on_errors, excludes)

