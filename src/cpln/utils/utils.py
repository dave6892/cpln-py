import os
from dotenv import load_dotenv
load_dotenv()

def kwargs_from_env(environment=None):
    if not environment:
        environment = os.environ
    base_url = environment.get('CPLN_URL')
    token = environment.get('CPLN_TOKEN')
    org = environment.get('CPLN_ORG')

    params = {}
    if base_url:
        params['base_url'] = base_url

    if token:
        params['token'] = token

    if org:
        params['org'] = org

    return params