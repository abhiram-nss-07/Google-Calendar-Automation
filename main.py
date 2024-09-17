from __future__ import print_function
import datetime
import os.path
import re
from sys import argv
import pytz  
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
#Add Your Google Calendar ID
YOUR_CALENDAR_ID = ''
YOUR_TIMEZONE = 'Asia/Kolkata'  


def main():
    """Shows basic usage of the Google Calendar API. Allows the user to input details in a single line."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Ask the user for the meeting or lecture input
    user_input = input(
        "Enter meeting/lecture details (e.g., 'Schedule a lecture CSET 201 at Room 101 from 11:30 am to 12:30 pm' \n 'Schedule a meeting on AI research with Dr. Jane at 2:00 pm'): "
    )

    # Parse the user input for meetings or lectures
    event_details = parseInput(user_input)

    if event_details:
        addEvent(creds, *event_details)
    else:
        print("Failed to parse input.")


def parseInput(user_input):
    """
    Parse the user input for meetings and lectures, returning relevant event details.
    Supports both lectures and meetings with different formats.
    """
    lecture_pattern = re.compile(
        r"Schedule a lecture (?P<lecture>.+?) at (?P<venue>.+?) from (?P<start_time>.+?) to (?P<end_time>.+)"
    )
    meeting_pattern = re.compile(
        r"Schedule a meeting on (?P<topic>.+?) with (?P<person>.+?) at (?P<time>.+)"
    )
    
    # Add other patterns here as needed
    lecture_time_place_pattern = re.compile(
        r"Schedule a lecture at (?P<venue>.+?) from (?P<start_time>.+?) to (?P<end_time>.+)"
    )

    # Try to match lecture, meeting, or other patterns
    lecture_match = lecture_pattern.match(user_input)
    meeting_match = meeting_pattern.match(user_input)
    lecture_time_place_match = lecture_time_place_pattern.match(user_input)

    if lecture_match:
        lecture = lecture_match.group("lecture")
        venue = lecture_match.group("venue")
        start_time = lecture_match.group("start_time")
        end_time = lecture_match.group("end_time")
        return lecture, "Lecture", venue, start_time, end_time

    elif meeting_match:
        topic = meeting_match.group("topic")
        person = meeting_match.group("person")
        time = meeting_match.group("time")
        return topic, f"Meeting with {person}", "Online", time, None  # Only start time for meetings

    elif lecture_time_place_match:
        venue = lecture_time_place_match.group("venue")
        start_time = lecture_time_place_match.group("start_time")
        end_time = lecture_time_place_match.group("end_time")
        return "Lecture", "Lecture", venue, start_time, end_time

    return None


# Add calendar event from current time for length of 'duration'
def addEvent(creds, title, description, venue, start_time, end_time=None):
    try:
        # Convert start_time and end_time to datetime objects
        start = datetime.datetime.strptime(start_time, "%I:%M %p")
        if end_time:
            end = datetime.datetime.strptime(end_time, "%I:%M %p")
        else:
            end = start + datetime.timedelta(hours=1)  # Assume 1-hour meeting if no end time provided

        # Use Asia/Kolkata timezone
        timezone = pytz.timezone(YOUR_TIMEZONE)
        today = datetime.date.today()
        start_with_tz = timezone.localize(datetime.datetime.combine(today, start.time()))
        end_with_tz = timezone.localize(datetime.datetime.combine(today, end.time()))

        # Prepare the event details
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_with_tz.isoformat(),
                'timeZone': YOUR_TIMEZONE,
            },
            'end': {
                'dateTime': end_with_tz.isoformat(),
                'timeZone': YOUR_TIMEZONE,
            },
            'location': venue
        }

        # Add event to Google Calendar
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().insert(calendarId=YOUR_CALENDAR_ID, body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))

    except HttpError as error:
        print('An error occurred: %s' % error)


if __name__ == '__main__':
    main()
