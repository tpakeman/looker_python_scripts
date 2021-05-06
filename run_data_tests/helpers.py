import urllib3

def ignore_insecure_requests():
    """Disable annoying warnings when using a Looker environment with no certificate"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
