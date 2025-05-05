# Imports
import requests

# Attributes
IP_ADDRESS = requests.get('https://ipinfo.potatolab.dev/json').json()['ip']
BASE_URL = f'http://{IP_ADDRESS}:5000'

# Functions
def get(endpoint):
    return requests.get(f'{BASE_URL}{endpoint}')

def main():
    success = True

    GET_ENDPOINTS = {
        '/metrics': { 'http': 200, 'output': 'text' },
        '/api/health': { 'http': 200, 'output': 'json' },
        '/api': { 'http': 200, 'output': 'text' },
        '/api/alerts': { 'http': 200, 'output': 'json' },
        '/api/destinations': { 'http': 200, 'output': 'json' },
        '/api/jobs': { 'http': 200, 'output': 'json' }
    }

    print('==========[TESTING]==========')

    for endpoint in GET_ENDPOINTS:
        try:
            r = get(endpoint)
            assert r.status_code == GET_ENDPOINTS[endpoint]['http']
            if GET_ENDPOINTS[endpoint]['output'] == 'text':
                assert r.text is not None
                print(f'[{endpoint}] Output: {r.text}')
            elif GET_ENDPOINTS[endpoint]['output'] == 'json':
                assert r.json() is not None
                print(f'[{endpoint}] Output: {r.json()}')

            assert r.status_code == 200
            assert r.text is not None

        except Exception as ex:
            success = False
            print(f'[{endpoint}] ERROR: {str(ex)}')
        except AssertionError as ex:
            success = False
            print(f'[{endpoint}] ERROR: {str(ex)}')

    if success:
        print('==========[SUCCESS]==========')
        print(f'::set-output name=results::success')
    else:
        print('==========[FAILURE]==========')
        print(f'::set-output name=results::failure')

main()
