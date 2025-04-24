import os
from dotenv import load_dotenv
from ..constants import DEFAULT_CPLN_API_URL
load_dotenv()

def kwargs_from_env(environment=None):
    if not environment:
        environment = os.environ

    base_url = DEFAULT_CPLN_API_URL
    token = environment.get('CPLN_TOKEN')
    org = environment.get('CPLN_ORG')

    params = {}
    if base_url:
        params['base_url'] = base_url

    if token:
        params['token'] = token
    else:
        raise ValueError('CPLN_TOKEN is not set')

    if org:
        params['org'] = org
    else:
        raise ValueError('CPLN_ORG is not set')

    return params
