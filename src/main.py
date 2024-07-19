"""
Modules used for this program, self explanatory...
"""
from pathlib import Path
import json
from datetime import date, datetime
from icalendar import Calendar  # type: ignore # pylint: disable=import-error


def parse_ics(file_path):
    """
    Parses calendar file and outputs events in dicts to an array
    """
    with open(file_path, 'rb') as f:
        calendar = Calendar.from_ical(f.read())

    events_list = []
    for component in calendar.walk():
        if component.name == "VEVENT":
            dtstart = component.get('dtstart').dt
            dtstart_str = (
                dtstart.strftime('%Y-%m-%d %H:%M:%S')
                if isinstance(dtstart, datetime)
                else str(dtstart)
            )

            dtend = component.get('dtend').dt
            dtend_str = (
                dtend.strftime('%Y-%m-%d %H:%M:%S')
                if isinstance(dtend, datetime)
                else str(dtend)
            )

            duration = None
            if isinstance(dtstart, datetime) and isinstance(dtend, datetime):
                duration = dtend - dtstart

            # dtstart_unix = int(dtstart.timestamp()) if isinstance(
            #     dtstart, datetime) else None

            # dtend = component.get('dtend').dt
            # dtend_unix = int(dtend.timestamp()) if isinstance(
            #     dtend, datetime) else None

            event = {
                'summary': str(component.get('summary')),
                'dtstart': dtstart_str,
                'dtend': dtend_str,
                'duration': str(duration),
                # 'description': str(component.get('description')),  # No need
                # 'location': str(component.get('location'))  # No need
            }

            events_list.append(event)

    return events_list


calendars_path = (Path(__file__).parent / "calendars/").resolve()
ICS_FILE_PATH = str(calendars_path) + "/cal1.ics"

events = parse_ics(ICS_FILE_PATH)
events_json = json.dumps(events, indent=4)  # remove later
# print(events_json)


def get_start_day() -> date:
    """
    Gets the starting date
    """
    while True:
        try:
            start_date = input("Enter starting date in MM-DD-YYYY format: ")
            start_date = datetime.strptime(start_date, "%m-%d-%Y")
            break
        except ValueError as err:
            if str(err) == "day is out of range for month":
                print("Enter a valid date.")
                continue
            print("Must be a valid date in the correct format, MM-DD-YYYY.")
            continue

    return start_date


def get_end_day() -> date:
    """
    Gets the end date
    """
    while True:
        try:
            end_date = input("Enter ending date in M-D-YYYY format: ")
            end_date = datetime.strptime(end_date, "%m-%d-%Y")
            break
        except ValueError as err:
            if str(err) == "day is out of range for month":
                print("Enter a valid date.")
                continue
            print("Must be a valid date in the correct format, M-D-YYYY.")
            continue

    return end_date


date_obj1 = get_start_day()
date_obj2 = get_end_day()

# print(f"Start:\n{type(date_obj1)} {date_obj1}\n")
# print(f"End:\n{type(date_obj2)} {date_obj2}")


def get_events_between(start: datetime = None, end: datetime = None) -> list[dict]:
    """
    Get's a list of the events between two dates.
    """
    for event in events:
        print(event)

    return None


get_events_between()
