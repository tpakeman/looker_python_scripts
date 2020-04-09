# Import libraries
import os
import looker_sdk
from looker_sdk.error import SDKError
from datetime import datetime as dt
import urllib3
import argparse

# For colour-coding the output
colours = {'HEADER': '\033[95m',
           'OKBLUE': '\033[94m',
           'OKGREEN': '\033[92m',
           'WARNING': '\033[93m',
           'FAIL': '\033[91m',
           'END': '\033[0m',
           'BOLD': '\033[1m',
           'UNDERLINE': '\033[4m'}

looker_client = looker_sdk.init31('looker.ini')
try:
    # Use this if testing locally or on a server without a certificate
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    user = looker_client.me()
    print(
        f"{colours['HEADER']}Authenticated as {user.display_name} (User ID {user.id}){colours['END']}")
except SDKError as e:
    print(
        f"{colours['FAIL']}Could not authenticate. Check `looker.ini` file{colours['END']}")

# Fetch all projects and run all tests


def run_target_tests(targets=None):
    validation_set = [project.id for project in looker_client.all_projects()]
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
                f"{colours['WARNING']}Could not find the following projects:{colours['END']}")
            for m in misses:
                print(f"{colours['WARNING']}\t{m}{colours['END']}")
        if targets == []:
            print(f'No valid projects to test against. Try one of the following:')
            for project in validation_set:
                print(f"{colours['OKBLUE']}\t{project}{colours['END']}")
            exit()
    for project in targets:
        test_start = dt.now()
        print(
            f"{colours['BOLD']}\n\nRunning tests for project {project}...{colours['END']}")
        print('_' * 79)
        results = looker_client.run_lookml_test(project)
        if len(results) == 0:
            print(f"{colours['FAIL']}No tests set up.{colours['END']}")
        else:
            for result in results:
                test_name = result.test_name
                if len(test_name) > 69:
                    test_name = test_name[:66] + '...'
                test_ct += 1
                if len(result.errors) == 0:
                    print(
                        f"{colours['OKGREEN']}  {test_name:<72} PASS{colours['END']}")
                else:
                    error_ct += 1
                    print(
                        f"{colours['FAIL']}  {test_name:<72} FAIL{colours['END']}")
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'Put in the name of a project or omit to check all projects.')
    parser.add_argument('--projects', '-p', nargs='+',
                        help='Pass in the name of a project or a space separated list of projects')
    parser.add_argument('--dev', '-d', action='store_true',
                        help='Include to compare to dev branch. Omit to use production.')
    args = parser.parse_args()
    if args.dev:
        looker_client.update_session(looker_sdk.models.WriteApiSession(workspace_id='dev'))
        print(f"{colours['WARNING']}Comparing to dev branch{colours['END']}")
    else:
        print(f"{colours['HEADER']}Comparing to prod branch{colours['END']}")
    run_target_tests(targets=args.projects)
