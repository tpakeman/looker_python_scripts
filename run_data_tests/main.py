from helpers import ignore_insecure_requests
import run_data_tests
import argparse

def main():
    parser = argparse.ArgumentParser('Pass the name of a project or omit to check all projects.')
    parser.add_argument('--projects', '-p', nargs='+', help='Pass in the name of a project or a space separated list of projects')
    parser.add_argument('--list', '-l', action='store_true', help='List all available Looker projects')
    parser.add_argument('--dev', '-d', action='store_true', help='Include to compare to dev branch. Omit to use production.')
    parser.add_argument('--silent', '-s', action='store_true', help='Surpress insecure request warnings.')
    args = parser.parse_args()
    if args.silent:
        ignore_insecure_requests()
    try:
        client = run_data_tests.auth(section='Personal Sandbox')
    except Exception:
        exit()
    if args.dev:
        client = run_data_tests.toggle_dev(client, True)
    if args.list:
        run_data_tests.print_projects(client)
    else:
        run_data_tests.run_target_tests(client, targets=args.projects)

if __name__ == '__main__':
    main()
