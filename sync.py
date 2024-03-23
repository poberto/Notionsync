from notion.client import NotionClient
from datetime import datetime

# Set up the Notion client with your integration token
client = NotionClient(token_v2="")

# Access the database
database_url = "https://www.notion.so/47a751804e084c129a4f6b4ce1d3de15"
database = client.get_block(database_url)

# For each event fetched from Google Calendar, add it to the Notion database
for event in events:
    title = event['summary']
    start_time = event['start'].get('dateTime', event['start'].get('date'))
    
    # Convert the start_time to a format that Notion accepts
    start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    
    # Add the event to the Notion database
    new_row = database.collection.add_row()
    new_row.name = title
    new_row.date = start_time

print("Events added to Notion!")
