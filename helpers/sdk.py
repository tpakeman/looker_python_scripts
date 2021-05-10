import urllib3
from looker_sdk.error import SDKError
import looker_sdk
from helpers.logging import cprint

def ignore_insecure_requests():
    """Disable annoying warnings when using a Looker environment with no certificate"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def auth(log, ini_path='looker.ini', section=None):
    """Attempt to log in to Looker API with specified ini file and section"""
    try:
        client = looker_sdk.init31(ini_path, section)
        user = client.me()
        cprint(f"Authenticated as {user.display_name} (User ID {user.id})", 'HEADER', log)
    except SDKError:
        cprint(f"Could not authenticate. Check `looker.ini` file at {ini_path} and section name {section}", "FAIL", log)
        raise SDKError
    return client

def toggle_dev(client, log, on=True):
    """Explicitly toggle between dev and prod.
        on=True for Dev
        on=False for Prod
    """
    if on:
        client.update_session(looker_sdk.models.WriteApiSession(workspace_id='dev'))
        cprint("Comparing to dev branch", 'WARNING', log)
    else:
        client.update_session(looker_sdk.models.WriteApiSession(workspace_id='prod'))
        cprint("Comparing to prod branch", 'HEADER', log)
    return client
