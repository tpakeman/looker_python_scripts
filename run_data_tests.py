# Import libraries
import os
from looker_sdk import client, models, error
from looker_sdk.error import SDKError
from datetime import datetime as dt
import urllib3
import argparse

looker_client = client.setup('looker.ini')
try:
    looker_client.me()
except SDKError as e:
    print("Could not authenticate. Check `looker.ini` file")

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
            print("Could not find the following projects:")
            for m in misses:
                print(f"\t{m}")
        if targets == []:
            print("No valid projects to test against. Try one of the following:")
            for project in validation_set:
                print(f"\t{project}")
            exit()
    for project in targets:
        test_start = dt.now()
        print(f"\n\nRunning tests for project {project}...")
        print('_' * 79)
        results = looker_client.run_lookml_test(project)
        if len(results) == 0:
            print("No tests set up.")
        else:
            for result in results:
                test_name = result.test_name
                if len(test_name) > 69:
                    test_name = test_name[:66] + '...'
                test_ct += 1
                if len(result.errors) == 0:
                    print(f"  {test_name:<72} PASS")
                else:
                    error_ct += 1
                    print(f"  {test_name:<72} FAIL")
                    error = result.errors[0]
                    other_errors = len(result.errors) - 1
                    message = str(error.sanitized_message).splitlines()[0]
                    print(f"\t({message})")
                    if other_errors > 0:
                        print(f"\tand {other_errors} other errors.")
            test_end = dt.now()
            test_duration = (test_end - test_start).total_seconds()
            print(f"\nTests for {project} completed in {test_duration:.02f} seconds")
    success_rate = 1 - (error_ct / test_ct)
    print(f"\n{error_ct} / {test_ct} failed")
    print(f"{success_rate:.1%} success rate")



if __name__ == '__main__':
    parser = argparse.ArgumentParser("Put in the name of a project or omit to check all projects.")
    parser.add_argument('--projects', '-p', nargs='+', help='Pass in the name of a project or a space separated list of projects')
    parser.add_argument('--dev', '-d', action='store_true', help='Include to compare to dev branch. Omit to use production.')
    args = parser.parse_args()
    if args.dev:
        looker_client.update_session({'workspace_id': 'dev'})
        print("Comparing to dev branch")
    else:
        print("Comparing to prod branch")
    run_target_tests(targets=args.projects)
