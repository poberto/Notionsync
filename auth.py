import requests
import json

# Load the client secrets
with open('', 'r') as f:
    client_data = json.load(f)
    client_id = client_data['installed']['client_id']
    client_secret = client_data['installed']['client_secret']

# Define the token endpoint and the data payload
token_url = 
data_payload = {
    'code': 
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
    'grant_type': 'authorization_code'
}

response = requests.post(token_url, data=data_payload)
token_data = response.json()

print("Response:", token_data)
print("Access Token:", token_data.get('access_token'))
print("Refresh Token:", token_data.get('refresh_token'))