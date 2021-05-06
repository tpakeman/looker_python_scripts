import looker_sdk
from looker_sdk.error import SDKError
from datetime import datetime as dt

COLOURS = {'HEADER': '\033[95m',
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

def fetch_projects(client):
    """Fetch all available Looker projects by ID"""
    return set([p.id for p in client.all_projects(fields='id')])

def print_projects(client):
    projects = fetch_projects(client)
    print(f"{COLOURS['OKBLUE']}Available Projects:")
    for p in projects:
        print(f"\t{p}")
    print(f"{COLOURS['END']}")

def run_target_tests(client, targets=None):
    validation_set = fetch_projects(client)
    results = []
    error_ct = 0
    test_ct = 0
    if targets is None:
        targets = validation_set
    else:
        misses = [t for t in targets if t not in validation_set]
        targets = [t for t in targets if t in validation_set]
        if misses != []:
            print(
                f"{COLOURS['WARNING']}Could not find the following projects:{COLOURS['END']}")
            for m in misses:
                print(f"{COLOURS['WARNING']}\t{m}{COLOURS['END']}")
        if targets == []:
            print(f'No valid projects to test against. Try one of the following:')
            for project in validation_set:
                print(f"{COLOURS['OKBLUE']}\t{project}{COLOURS['END']}")
            exit()
    for project in targets:
        test_start = dt.now()
        print(
            f"{COLOURS['BOLD']}\n\nRunning tests for project {project}...{COLOURS['END']}")
        print('_' * 79)
        results = client.run_lookml_test(project)
        if len(results) == 0:
            print(f"{COLOURS['FAIL']}No tests set up.{COLOURS['END']}")
        else:
            for result in results:
                test_name = result.test_name
                if len(test_name) > 69:
                    test_name = test_name[:66] + '...'
                test_ct += 1
                if len(result.errors) == 0:
                    print(
                        f"{COLOURS['OKGREEN']}  {test_name:<72} PASS{COLOURS['END']}")
                else:
                    error_ct += 1
                    print(
                        f"{COLOURS['FAIL']}  {test_name:<72} FAIL{COLOURS['END']}")
                    error = result.errors[0]
                    other_errors = len(result.errors) - 1
                    message = str(error.sanitized_message).splitlines()[0]
                    print(f'\t({message})')
                    if other_errors > 0:
                        print(f'\tand {other_errors} other errors.')
            test_end = dt.now()
            test_duration = (test_end - test_start).total_seconds()
            print(
                f'\nTests for {project} completed in {test_duration:.02f} seconds')
    if test_ct > 0:
        success_rate = 1 - (error_ct / test_ct)
        print(f'\n{error_ct} / {test_ct} failed')
        print(f'{success_rate:.1%} success rate')
