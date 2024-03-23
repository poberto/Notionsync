from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime
import requests

class debugerror(Exception):
    """A custom exception for demonstration purposes."""
    pass

def archive_notion_page(page_id, headers):
    """Archive a Notion page."""
    ARCHIVE_URL = f"https://api.notion.com/v1/pages/{page_id}"
    data = {
        "archived": True
    }
    response = requests.patch(ARCHIVE_URL, headers=headers, json=data)
    return response

def refresh_google_token(client_id, client_secret, refresh_token):
    """Refresh the Google access token."""
    refresh_request = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    response = requests.post("https://oauth2.googleapis.com/token", data=refresh_request).json()
    return response.get("access_token")

# Set your client_id, client_secret, access_token, and refresh_token
client_id = ''
client_secret = ''
access_token = ''
refresh_token = ''

# Create Google credentials using the provided access and refresh tokens
# Try to build the Google Calendar API client
try:
    credentials = Credentials(token=access_token, refresh_token=refresh_token, client_id=client_id, client_secret=client_secret, token_uri="https://oauth2.googleapis.com/token")
    service = build('calendar', 'v3', credentials=credentials)
except:
    # If the access_token is expired, refresh it
    access_token = refresh_google_token(client_id, client_secret, refresh_token)
    credentials = Credentials(token=access_token, refresh_token=refresh_token, client_id=client_id, client_secret=client_secret, token_uri="https://oauth2.googleapis.com/token")
    service = build('calendar', 'v3', credentials=credentials)

# Fetch the next 10 events from the primary Google Calendar
now = datetime.datetime.utcnow().isoformat() + 'Z'
events_result = service.events().list(calendarId='primary', timeMin=now, singleEvents=True, orderBy='startTime').execute()
events = events_result.get('items', [])

# Notion setup
NOTION_TOKEN = ""
ENDPOINT_URL = ""
DATABASE_ID = ""

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Fetch all entries from the Notion database with pagination
notion_entries = []
next_cursor = None
while True:
    params = {}
    if next_cursor:
        params["start_cursor"] = next_cursor
    response = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=params)
    current_results = response.json().get('results', [])
    notion_entries.extend(current_results)
    next_cursor = response.json().get('next_cursor')
    if not next_cursor:
        break



for entry in notion_entries:
    notion_title = entry['properties']['Content']['title'][0]['text']['content']
    notion_date = entry['properties']['Date']['date']['start']
    
    exists_in_gcal = any(event['summary'] == notion_title and event['start'].get('dateTime', event['start'].get('date')).split('T')[0] == notion_date for event in events)

    if not exists_in_gcal:
        # Create this event in Google Calendar
        event_body = {
            "summary": notion_title,
            "start": {
                "date": notion_date
            },
            "end": {
                "date": notion_date
            }
        }

        service.events().insert(calendarId='primary', body=event_body).execute()


# # Remove events from Notion if they're no longer in Google Calendar
# for entry in notion_entries:
#     if 'Content' in entry['properties'] and 'title' in entry['properties']['Content'] and entry['properties']['Content']['title']:
#         notion_title = entry['properties']['Content']['title'][0]['text']['content']
#         notion_date = None

#         if entry and 'properties' in entry:
#             properties = entry['properties']
#             if 'Date' in properties:
#                 date_prop = properties['Date']
#                 if date_prop and 'date' in date_prop:
#                     date_dict = date_prop['date']
#                     if date_dict:
#                         notion_date = date_dict.get('start')

#         if not notion_date:
#             raise(debugerror("No date found for this entry in Notion"))


#         exists_in_gcal = any(event['summary'] == notion_title and event['start'].get('dateTime', event['start'].get('date')).split('T')[0] == notion_date for event in events)

#         if not exists_in_gcal:
#             # Archive this entry in Notion
#             page_id = entry['id']
#             print(f"Attempting to archive page with ID: {page_id}")
#             response = archive_notion_page(page_id, headers)
#             if response.status_code == 200:
#                 print(f"Successfully archived page with ID: {page_id}")
#             else:
#                 print(f"Failed to archive page with ID: {page_id}. Response: {response.text}")
#         response.raise_for_status()



# Check and add new events to Notion
for event in events:
    title = event['summary']
    start_time = event['start'].get('dateTime', event['start'].get('date'))
    start_time = datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    
    # Check if the year is beyond 2025
    if start_time.year > 2025:
        continue
    
    # Extract the event description
    description = event.get('description', "").lower()

    tags = []
    # Check for specific keywords in the description
    if "class" in description and "exam" not in description:
        tags.append("Classes")
    if "1" in description:
        tags.append("Class 1")
    if "2" in description:
        tags.append("Class 2")
    if "3" in description:
        tags.append("Class 3")
    if "4" in description:
        tags.append("Class 4")
    if "5" in description:
        tags.append("Class 5")
    if "6" in description:
        tags.append("Class 6")
    if "exam" in description:
        tags.append("Exams")

    
    # Check if this event exists in Notion
    exists = False
    for entry in notion_entries:
        if 'Content' in entry['properties'] and 'title' in entry['properties']['Content'] and entry['properties']['Content']['title']:
            notion_title = entry['properties']['Content']['title'][0]['text']['content']
            notion_date = None

            if entry and 'properties' in entry:
                properties = entry['properties']
                if 'Date' in properties:
                    date_prop = properties['Date']
                    if date_prop and 'date' in date_prop:
                        date_dict = date_prop['date']
                        if date_dict:
                            notion_date = date_dict.get('start')

            if not notion_date:
                continue


            
            
            
            if notion_title == title and notion_date == start_time.strftime("%Y-%m-%d"):
                exists = True
                break

    # If not, add it
    if not exists:
        data = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "Content": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "Date": {
                    "date": {
                        "start": start_time.strftime("%Y-%m-%d"),
                        "end": (start_time + datetime.timedelta(hours=1)).strftime("%Y-%m-%d")
                    }
                }
            }
        }
        
        # Add tags only if there are any for the event
        if tags:
            data["properties"]["Tags"] = {
                "multi_select": [{"name": tag} for tag in tags]
            }
    
    # Send the event to Notion (whether it has tags or not)
        response = requests.post(ENDPOINT_URL, headers=headers, json=data)
        response.raise_for_status()



print("Events added to Notion!")
