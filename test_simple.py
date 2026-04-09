import requests
import json

# Test basic connectivity first
try:
    response = requests.post(
        'http://localhost:8000/chat',
        json={'question': 'How many patients do we have?'},
        timeout=10
    )
    print(f'Status Code: {response.status_code}')
    print(f'Response Text: {response.text}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {str(e)}')
