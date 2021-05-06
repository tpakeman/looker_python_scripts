from helpers import ignore_insecure_requests
import validate_explore_sql
import argparse

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
        ignore_insecure_requests()
    try:
        client = validate_explore_sql.auth(section='Personal Sandbox')
    except Exception:
        exit()
    if args.dev:
        client = validate_explore_sql.toggle_dev(client, True)
    validate_explore_sql.check_fields_in_model(client,
                                               models=args.models,
                                               explores=args.explores,
                                               continue_on_errors=getattr(args, 'continue'),
                                               excludes=args.excludes)

if __name__ == '__main__':
    main()
