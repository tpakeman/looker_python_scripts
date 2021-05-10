import argparse
from datetime import datetime as dt
from helpers import sdk
from helpers.logging import cprint, setup_log

LOGGER = setup_log('run_data_tests')

def fetch_projects(client):
    """Fetch all available Looker projects by ID"""
    return set([p.id for p in client.all_projects(fields='id')])

def print_projects(client, log=LOGGER):
    projects = fetch_projects(client)
    cprint(f"Available Projects:", 'OKBLUE', log)
    for p in projects:
        cprint(f"\t{p}", 'OKBLUE', log)

def run_target_tests(client, targets=None, log=LOGGER):
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
            cprint("Could not find the following projects:", 'WARNING', log)
            for m in misses:
                cprint(f"\t{m}", 'WARNING', log)
        if targets == []:
            print(f'No valid projects to test against. Try one of the following:')
            for project in validation_set:
                cprint(f"\t{project}", 'OKBLUE', log)
            exit()
    for project in targets:
        test_start = dt.now()
        cprint, log(
            f"\n\nRunning tests for project {project}...", 'BOLD')
        print('_' * 79)
        results = client.run_lookml_test(project)
        if len(results) == 0:
            cprint(f"No tests set up.", 'FAIL', log)
        else:
            for result in results:
                test_name = result.test_name
                if len(test_name) > 69:
                    test_name = test_name[:66] + '...'
                test_ct += 1
                if len(result.errors) == 0:
                    cprint(f"{test_name:<72} PASS", 'OKGREEN', log)
                else:
                    error_ct += 1
                    cprint(f"  {test_name:<72} ", 'FAIL', log)
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


def main():
    parser = argparse.ArgumentParser('Pass the name of a project or omit to check all projects.')
    parser.add_argument('--projects', '-p', nargs='+', help='Pass in the name of a project or a space separated list of projects')
    parser.add_argument('--list', '-l', action='store_true', help='List all available Looker projects')
    parser.add_argument('--dev', '-d', action='store_true', help='Include to compare to dev branch. Omit to use production.')
    parser.add_argument('--silent', '-s', action='store_true', help='Surpress insecure request warnings.')
    args = parser.parse_args()
    if args.silent:
        sdk.ignore_insecure_requests()
    try:
        client = sdk.auth(LOGGER, section='Personal Sandbox')
    except Exception: # Auth function handles logging here
        exit()
    if args.dev:
        client = sdk.toggle_dev(client, LOGGER, True)
    if args.list:
        print_projects(client)
    else:
        run_target_tests(client, targets=args.projects)

if __name__ == '__main__':
    main()
