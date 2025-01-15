# Imports
import traceback
import requests

# Attributes
API_ENDPOINT = 'http://hawk-backup_app:5000/api'

# Main
def api_get(url):
    try:
        print(f'Testing {url}...')
        r = requests.get(url)
        if r.status_code == 200:
            print(f'Testing {url}...SUCCESS!')
            return True, r.json()
        else:
            print(f'Testing {url}...FAILED! Reason: {r.text}')
            return False, None
    except Exception as ex:
        print(f'ERROR: Unexpected exception threw when trying to make a GET API call! Reason: {str(ex)}\n{traceback.format_exc()}')
    return False, None

def main():
    # Health Check
    success, data = api_get(f'{API_ENDPOINT}/health')

    # Alerts
    success, alerts = api_get(f'{API_ENDPOINT}/alerts')
    # TODO: Test each alert - http://localhost:5000/api/alerts/<name>/test

    # Jobs
    success, jobs = api_get(f'{API_ENDPOINT}/jobs')
    # TODO: Test each job - http://localhost:5000/api/jobs/<name>/start
    # TODO: Test each job - http://localhost:5000/api/jobs/<name>/status

    print(f'::set-output name=results::{'success' if success else 'failure'}')

# Start Tests
main()
