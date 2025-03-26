# Imports
import traceback
import requests

# Attributes
IP_ADDRESS = requests.get('https://ipinfo.potatolab.dev/json').json()['ip']
BASE_URL = f'http://{IP_ADDRESS}:5000'

# Main
def api_get(url, json=True):
    try:
        print(f'Testing {url}...')
        r = requests.get(url)
        if r.status_code == 200:
            print(f'Testing {url}...SUCCESS!')
            if json:
                return True, r.json()
            else:
                return True, None
        else:
            print(f'Testing {url}...FAILED! Reason: {r.text}')
            return False, None
    except Exception as ex:
        print(f'ERROR: Unexpected exception threw when trying to make a GET API call! Reason: {str(ex)}\n{traceback.format_exc()}')
    return False, None

def main():
    # Test Prometheus endpoint
    success, data = api_get(f'{BASE_URL}/metrics', json=False)

    # Health Check
    success, data = api_get(f'{BASE_URL}/api/health')

    # Alerts
    success, alerts = api_get(f'{BASE_URL}/api/alerts')
    # TODO: Test each alert - http://localhost:5000/api/alerts/<name>/test

    # Jobs
    success, jobs = api_get(f'{BASE_URL}/api/jobs')
    # TODO: Test each job - http://localhost:5000/api/jobs/<name>/start
    # TODO: Test each job - http://localhost:5000/api/jobs/<name>/status

    print(f'::set-output name=results::{'success' if success else 'failure'}')

# Start Tests
main()
