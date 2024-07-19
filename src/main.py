"""
Modules used for this program, self explanatory...
"""
import sys
from pathlib import Path
# import json
from datetime import date, datetime, timedelta
from dateutil.rrule import rrulestr
# from dateutil.parser import parse as parse_dt

from icalendar import Calendar  # type: ignore # pylint: disable=E0401


def generate_recurring_events(rrule_str: str, start: datetime,
                              end: datetime,
                              original_duration: timedelta) -> list[dict]:
    """
    Generate recurring events based on the RRULE string and return them
    as a list of event dictionaries.
    """
    recurring_events = []

    # Create an rrule object
    rrule_obj = rrulestr(rrule_str, dtstart=start)

    # Generate occurrences
    occurrences = list(rrule_obj)

    # Filter occurrences within the event's time range
    for occurrence in occurrences:
        if start <= occurrence <= end:
            event = {  # pylint: disable=W0621
                'summary': 'Recurring Event',  # Modify as needed
                'dtstart': occurrence,
                'dtend': occurrence + original_duration,
                'duration': str(original_duration),
            }
            recurring_events.append(event)

    return recurring_events


def parse_ics(file_path):
    """
    Parse the calendar file to extract events, handling both single
    occurrences and recurrence rules, and return them as a list
    of event dictionaries.
    """
    with open(file_path, 'rb') as f:
        calendar = Calendar.from_ical(f.read())

    events_list = []
    for component in calendar.walk():
        if component.name == "VEVENT":
            dtstart = component.get('dtstart').dt
            dtend = component.get('dtend').dt
            summary = str(component.get('summary'))

            # Don't care about timezones, convert to offest-naive
            if dtstart.tzinfo:
                dtstart = dtstart.replace(tzinfo=None)
            if dtend.tzinfo:
                dtend = dtend.replace(tzinfo=None)

            duration = dtend - dtstart

            # Handle recurrence
            rule = component.get('rrule')
            if rule:
                rrule_str = str(rule)
                # Generate recurring events
                recurring_events = generate_recurring_events(
                    rrule_str, dtstart, dtend, duration)
                events_list.extend(recurring_events)
            else:
                # Single occurrence event
                event = {  # pylint: disable=W0621
                    'summary': summary,
                    'dtstart': dtstart,
                    'dtend': dtend,
                    'duration': str(dtend - dtstart),
                }
                events_list.append(event)

    return events_list


def get_cal_path(calendar_file: str = "testing"):
    """
    Get's the calendar file and returns the path. Defaults to test calendar if
    no other calendar file is provided
    """
    calendars_path = (Path(__file__).parent / "calendars/").resolve()
    return str(calendars_path) + f"/{calendar_file}.ics"


try:
    cal_file = input(
        "Enter the calendar file's name (without extension): ")
    events = parse_ics(get_cal_path(cal_file))
except FileNotFoundError:
    FILE_STRUCT = """
  Calendar-Parser/
    └─ src/
        ├─ calendars/
        │   ├─ Calendar1.ics
        │   ├─ Calendar2.ics
        │   └─ ...
        └─ main.py
"""
    print("File not found. Check if file exists and also the spelling. " +
          f"File structure should be:\n{FILE_STRUCT}")
    sys.exit(1)

# events_json = json.dumps(events, indent=4)  # used for better pretty output
# print(events_json)


def get_start_day() -> date:
    """
    Gets the starting date
    """
    while True:
        try:
            start_date = input("Enter starting date in MM-DD-YYYY format: ")
            start_datetime = datetime.strptime(start_date, "%m-%d-%Y")
            break
        except ValueError as err:
            if str(err) == "day is out of range for month":
                print("Enter a valid date.")
                continue
            print("Must be a valid date in the correct format, MM-DD-YYYY.")
            continue

    return start_datetime


def get_end_day() -> date:
    """
    Gets the end date
    """
    while True:
        try:
            end_date = input("Enter ending date in M-D-YYYY format: ")
            end_datetime = datetime.strptime(end_date, "%m-%d-%Y")
            break
        except ValueError as err:
            if str(err) == "day is out of range for month":
                print("Enter a valid date.")
                continue
            print("Must be a valid date in the correct format, M-D-YYYY.")
            continue

    return end_datetime


date_obj1 = get_start_day()
date_obj2 = get_end_day()


def get_events_between(start: date, end: date) -> tuple[int, list[dict]]:
    """
    Get's a list of the events between two dates.
    """
    events_between = []  # pylint: disable=W0621

    for event in events:  # pylint: disable=W0621
        event_start = event['dtstart']
        event_end = event['dtend']
        if start <= event_start <= end and start <= event_end <= end:
            # print(f"Event {num_events}: {event}, {event['duration']}")
            events_between.append(event)

    return (len(events_between), events_between)


def format_datetime(dt: datetime) -> str:
    """
    Format a datetime object to a string in '%Y-%m-%d %H:%M:%S' format.
    """
    return dt.strftime('%Y-%m-%d %H:%M:%S')


num_events, events_between = get_events_between(date_obj1, date_obj2)
print(f"{events}\n\n\n")
print(f"There are {num_events} events. They are:\n{events_between}\n")
for event in events_between:
    print(f"Summary: {event['summary']}")
    print(f"Start: {format_datetime(event['dtstart'])}")
    print(f"End: {format_datetime(event['dtend'])}")
    print(f"Duration: {event['duration']}\n")
