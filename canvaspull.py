import requests
import datetime
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build



COURSE_TO_TAG_MAPPING = {
    "COMPUTER NETWORKS": "Class 3",
    "INTRO TO MACHINE LEARNING": "Class 2",
    "APPLIED DISCRETE MATHEMATICS": "Class 1",
    "EMBEDDED SYSTEMS DESIGN": "Class 4",
    "INTRO TO KOREA THROUGH FILMS": "Class 5",  # Note: This is a partial name, so you'll need to check if "KOREAN" is in the course name
    "ALGORITHMIC THINKING": "Class 6"
}

# Authenticate and build the Google Tasks service
def get_google_tasks_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')

    # If there are no (valid) credentials available, prompt the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/home/peter/Notionsync/client_secret_139386008790-8qci4i09ek46b80vps9tm2dn2205r0v8.apps.googleusercontent.com.json', ['https://www.googleapis.com/auth/tasks'])
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

    service = build('tasks', 'v1', credentials=creds)
    return service

# Add a task to Google Tasks
def add_task_to_google_tasks(service, title, due_date=None):
    task = {
        'title': title
    }
    if due_date:
        task['due'] = due_date
    tasklist_id = '@default'  # Default list
    result = service.tasks().insert(tasklist=tasklist_id, body=task).execute()
    return result

def extract_tag_from_course_name(course_name):
    """Extract the tag from the course name, using the portion after the 'SEC' code."""
    try:
        tag = course_name.split('SEC')[1].strip().split(' ', 1)[1]
        return tag
    except IndexError:
        return None

def assignment_exists_in_notion(course_name, assignment_name):
    """Check if an assignment exists in the Notion database."""
    query_payload = {
        "filter": {
            "and": [
                {
                    "property": "Content",
                    "text": {
                        "equals": assignment_name
                    }
                },
                {
                    "property": "Course",
                    "text": {
                        "equals": course_name  # Assuming you have a Course property in Notion
                    }
                }
            ]
        }
    }
    response = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=NOTION_HEADERS, json=query_payload)
    results = response.json().get('results', [])
    return len(results) > 0

def add_assignment_to_notion(course_name, assignment_name, due_date):
    """Add the assignment to Notion."""
    tag = None
    for course, class_tag in COURSE_TO_TAG_MAPPING.items():
        if course in course_name.upper():
            tag = class_tag
            break

    if not tag:
        print(f"Couldn't determine tag for course name: {course_name}")
        return

    # Prepare the data
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Content": {  # Use "Content" instead of "Title"
                "title": [
                    {
                        "text": {
                            "content": assignment_name
                        }
                    }
                ]
            },
            "Date": {
                "date": {
                    "start": due_date
                }
            },
            "Tags": {
                "multi_select": [{"name": tag}]
            }
        }
    }

    response = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=data)
    if response.status_code == 200:
        print(f"Added to Notion: {assignment_name} ({course_name})")
    else:
        print(f"Failed to add to Notion: {assignment_name} ({course_name}) - {response.text}")
# ... [Rest of your code]
def mark_completed_tasks_in_google_tasks(service):
    """Marks tasks as completed in Google Tasks based on Notion's status."""
    # Fetch all entries from the Notion database
    response = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=NOTION_HEADERS)
    notion_entries = response.json().get('results', [])

    # Filter for entries marked as completed
    completed_entries = [entry for entry in notion_entries if entry['properties']['Completed']['checkbox']]

    # Loop through each completed entry and mark the corresponding task as completed in Google Tasks
    for entry in completed_entries:
        title = entry['properties']['Content']['title'][0]['text']['content']

        # Check if a task with the same title exists in Google Tasks and is not already marked as completed
        tasklist_id = '@default'
        tasks = service.tasks().list(tasklist=tasklist_id).execute()

        for task in tasks.get('items', []):
            if task['title'] == title and task.get('status') != 'completed':
                task['status'] = 'completed'
                updated_task = service.tasks().update(tasklist=tasklist_id, task=task['id'], body=task).execute()
                print(f"Marked '{title}' as completed in Google Tasks.")

def task_exists(service, title):
    tasklist_id = '@default'
    tasks = service.tasks().list(tasklist=tasklist_id).execute()
    for task in tasks.get('items', []):
        if task['title'] == title:
            return True
    return False


# NOTION SETUP
NOTION_TOKEN = ""
DATABASE_ID = "47a751804e084c129a4f6b4ce1d3de15"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Check if a task with the same title already exists in Google Tasks
BASE_URL = "https://canvas.instructure.com/api/v1/"
TOKEN = ''

headers = {
    "Authorization": f"Bearer {TOKEN}"
}
response = requests.get(BASE_URL + "courses?enrollment_type=student&state=active", headers=headers, verify=False)

# Handle pagination
courses = []
current_date = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
while response.status_code == 200:
    courses.extend(response.json())
    links = response.headers.get('Link', '')
    next_link = [l.split(';')[0] for l in links.split(',') if 'rel="next"' in l]
    if next_link:
        response = requests.get(next_link[0][1:-1], headers=headers, verify=False)  # [1:-1] to remove < >
    else:
        break

# # Filter for current courses
# current_courses = [
#     course for course in courses 
#     if 'end_at' not in course or 
#     (course['end_at'] and datetime.datetime.fromisoformat(course['end_at'].replace('Z', '+00:00')) > current_date)
# ]
# Print the current courses
# Print all courses and their end dates
# List of class IDs you want to select
selected_courses_ids = [
    139970000000220635,
    139970000000220641,
    139970000000220645,
    139970000000220650,
    139970000000220709,
    139970000000220745,
    139970000000222690,
    139970000000223736
]

# Filter for the selected courses
selected_courses = [course for course in courses if course['id'] in selected_courses_ids]

# Print the selected courses
for course in selected_courses:
    print(course['id'], course.get('name', 'N/A'))
    

# Fetch and print assignments for each selected course
for course in selected_courses:
    print(f"\nAssignments for {course.get('name', 'N/A')} (ID: {course['id']}):")
    
    # Get assignments for this course
    assignments_endpoint = f"{BASE_URL}courses/{course['id']}/assignments"
    assignments_response = requests.get(assignments_endpoint, headers=headers, verify=False)
    
    # Check for valid response
    if assignments_response.status_code == 200:
        assignments = assignments_response.json()
        for assignment in assignments:
            print(f"- {assignment.get('name', 'N/A')} (Due: {assignment.get('due_at', 'No due date')})")
    else:
        print(f"Failed to retrieve assignments for course ID {course['id']}.")

# Main part of the script
service = get_google_tasks_service()
# Main part of the script

for course in selected_courses:
    course_name = course.get('name', 'N/A')
    print(f"\nProcessing assignments for {course_name}:")

    # Start with the initial endpoint for assignments
    assignments_endpoint = f"{BASE_URL}courses/{course['id']}/assignments?include[]=submission"
    
    while assignments_endpoint:
        assignments_response = requests.get(assignments_endpoint, headers=headers, verify=False)

        if assignments_response.status_code == 200:
            assignments = assignments_response.json()
            for assignment in assignments:
                submission_state = assignment.get('submission', {}).get('workflow_state', 'unsubmitted')

                # Skip the assignment if it's submitted or graded
                if submission_state in ['submitted', 'graded', 'pending_review']:
                    continue

                assignment_name = assignment.get('name', 'N/A')
                task_title = f"{assignment_name} ({course_name})"
                
                # Add to Google Tasks
                if not task_exists(service, task_title):
                    due_date = assignment.get('due_at')
                    add_task_to_google_tasks(service, task_title, due_date)
                    print(f"- Added to Google Tasks: {task_title} (Due: {due_date})")
                else:
                    print(f"- Skipped Google Tasks (already exists): {task_title}")

                # Add to Notion
                if not assignment_exists_in_notion(course_name, assignment_name):
                    due_date = assignment.get('due_at')
                    add_assignment_to_notion(course_name, assignment_name, due_date)
                    print(f"- Added to Notion: {assignment_name} (Due: {due_date})")
                else:
                    print(f"- Skipped Notion (already exists): {assignment_name}")

            # Check for 'next' link in headers for pagination
            links = assignments_response.headers.get('Link', '')
            next_link = [link.split(';')[0].strip('<>') for link in links.split(',') if 'rel="next"' in link]
            assignments_endpoint = next_link[0] if next_link else None
        else:
            print(f"Failed to retrieve assignments for course ID {course['id']}")
            break

    # Refresh Google Tasks Service
    service = get_google_tasks_service()
    mark_completed_tasks_in_google_tasks(service)
