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

    try:
        print('==========[TESTING]==========')

        # General
        r = get('/metrics')
        assert r.status_code == 200
        assert r.text is not None

        r = get('/api/health')
        assert r.status_code == 200
        assert r.json() is not None

        r = get('/api')
        assert r.status_code == 200
        assert r.json() is not None

        # Test pulling all datasets
        r = get('/api/alerts')
        assert r.status_code == 200
        assert r.json() is not None

        r = get('/api/destinations')
        assert r.status_code == 200
        assert r.json() is not None

        r = get('/api/jobs')
        assert r.status_code == 200
        assert r.json() is not None

        # TODO: Add more tests

        print('==========[SUCCESS]==========')
    
    except AssertionError as ex:
        success = False
        print('==========[FAILURE]==========')
        print(ex)
    
    print(f'::set-output name=results::{'success' if success else 'failure'}')

main()
