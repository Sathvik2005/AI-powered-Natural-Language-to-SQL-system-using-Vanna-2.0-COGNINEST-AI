import requests
import json

# Test to see what components are actually being returned
try:
    response = requests.post(
        'http://localhost:8000/chat',
        json={'question': 'How many patients do we have?'},
        timeout=30
    )
    print(f'Status Code: {response.status_code}')
    data = response.json()
    print(f'Response Keys: {list(data.keys())}')
    print(f'\nFull Response:')
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f'Error: {type(e).__name__}: {str(e)}')
