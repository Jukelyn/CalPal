"""
Modules used for this program, self explanatory...
"""
import os
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
import pytz  # type: ignore # pylint: disable=E0401
from icalendar import Calendar  # type: ignore # pylint: disable=E0401
import recurring_ical_events  # type: ignore # pylint: disable=E0401

EST = pytz.timezone('US/Eastern')
FILE_STRUCT = """
    Calendar-Parser/
        └─ src/
            ├─ calendars/
            │   ├─ Calendar1.ics
            │   ├─ Calendar2.ics
            │   └─ ...
            └─ main.py
"""
MANY_EVENTS = 5


def parse_ics(file_path: str, start: datetime, end: datetime) -> list[dict]:
    """
    Parse the calendar file to extract events, handling both single
    occurrences and recurrence rules, and return them as a list
    of event dictionaries.
    """
    try:
        with open(file_path, 'rb') as f:
            calendar = Calendar.from_ical(f.read())
    except FileNotFoundError:
        print("File not found. Check if file exists and also the spelling. " +
              f"File structure should be:\n{FILE_STRUCT}")
        sys.exit(1)

    events_list = []
    single_occurrence_events = []

    for component in calendar.walk():
        if component.name == "VEVENT":
            dtstart = component.get('dtstart').dt
            dtend = component.get('dtend').dt
            summary = str(component.get('summary'))

            if dtstart.tzinfo:
                dtstart = dtstart.astimezone(EST)
            else:
                dtstart = EST.localize(dtstart)
            if dtend.tzinfo:
                dtend = dtend.astimezone(EST)
            else:
                dtend = EST.localize(dtend)

            duration = dtend - dtstart

            # Handle single occurrence event
            rule = component.get('rrule')
            if not rule:
                event = {  # pylint: disable=W0621
                    'summary': summary,
                    'dtstart': dtstart,
                    'dtend': dtend,
                    'duration': str(duration),
                }
                single_occurrence_events.append(event)

    # Handle recurring events using the recurring_ical_events module
    recurring_events = recurring_ical_events.of(calendar).between(start, end)
    for event in recurring_events:
        dtstart = event["dtstart"].dt
        dtend = event["dtend"].dt if "dtend" in event else dtstart + duration

        # Don't care about timezones, convert to offset-naive
        if dtstart.tzinfo:
            dtstart = dtstart.replace(tzinfo=None)
        if dtend.tzinfo:
            dtend = dtend.replace(tzinfo=None)

        recurring_event = {
            'summary': str(event.get('summary', 'Recurring Event')),
            'dtstart': dtstart,
            'dtend': dtend,
            'duration': str(dtend - dtstart),
        }
        events_list.append(recurring_event)

    return single_occurrence_events + events_list


def get_cal_path(calendar_file: str):
    """
    Get's the calendar file and returns the path. Defaults to test calendar if
    no other calendar file is provided.
    """
    calendars_path = (Path(__file__).parent / "calendars/").resolve()
    return str(calendars_path) + f"/{calendar_file}.ics"


def get_start_day() -> date:
    """
    Gets the starting date.
    """
    while True:
        try:
            start_date_in = input("Enter starting date in MM DD YYYY format: ")
            if start_date_in:
                start_date_arr = start_date_in.split()

                start_date = f"{
                    start_date_arr[0]}-{start_date_arr[1]}-{start_date_arr[2]}"
            else:
                start_date = "07-15-2024"  # left in on purpose

            start_datetime = datetime.strptime(start_date, "%m-%d-%Y")
            start_datetime = EST.localize(start_datetime)  # Localize to EST

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
    Gets the ending date.
    """
    while True:
        try:
            end_date_in = input("Enter ending date in MM DD YYYY format: ")

            if end_date_in:
                end_date_arr = end_date_in.split()

                end_date = f"{
                    end_date_arr[0]}-{end_date_arr[1]}-{end_date_arr[2]}"
            else:
                end_date = "07-19-2024"  # left in on purpose

            end_datetime = datetime.strptime(end_date, "%m-%d-%Y")
            end_datetime = EST.localize(end_datetime)  # Localize to EST
            end_datetime += timedelta(days=1)

            break
        except ValueError as err:
            if str(err) == "day is out of range for month":
                print("Enter a valid date.")
                continue
            print("Must be a valid date in the correct format, M-D-YYYY.")
            continue

    return end_datetime


def get_calendar_file() -> tuple[str, datetime, datetime]:
    """
    Get's the calendar file path, handles errors if not found, asks user for
    the starting date and ending date that they want to focus on and returns
    a tuple containing the data. If no path is found, the testing file will be
    used instead.
    """
    try:
        cal_file = input(
            "Enter the calendar file's name (without extension): ")
        file_pathname = get_cal_path(  # pylint: disable=W0621
            cal_file) if cal_file else get_cal_path("testing")
    except FileNotFoundError:
        print("File not found. Check if file exists and also the spelling. " +
              f"File structure should be:\n{FILE_STRUCT}")
        sys.exit(1)

    start_day = get_start_day()  # pylint: disable=W0621
    end_day = get_end_day()  # pylint: disable=W0621

    return (file_pathname, start_day, end_day)


file_pathname, start_day, end_day = get_calendar_file()
events = parse_ics(file_pathname, start_day, end_day)

# events_json = json.dumps(events, indent=4)  # used for better pretty output
# print(events_json)


def get_events_between(start: date, end: date) -> tuple[int, list[dict]]:
    """
    Get's a list of the events between two dates.
    """
    if start.tzinfo is None:
        start = EST.localize(start)
    if end.tzinfo is None:
        end = EST.localize(end)

    events_between = []  # pylint: disable=W0621

    for event in events:  # pylint: disable=W0621
        event_start = event['dtstart']
        event_end = event['dtend']

        if event_start.tzinfo is None:
            event_start = EST.localize(event_start)
        if event_end.tzinfo is None:
            event_end = EST.localize(event_end)

        if start <= event_start <= end and start <= event_end <= end:
            # print(f"Event {num_events}: {event}, {event['duration']}")
            events_between.append(event)

    unique_events = remove_duplicate_events(events_between)

    return (len(unique_events), unique_events)


def format_datetime(dt: datetime) -> str:
    """
    Format a datetime object to a string in '%Y-%m-%d %H:%M:%S' format.
    """
    return dt.strftime('%m-%d-%Y %H:%M:%S')


def remove_duplicate_events(events: list[dict]) -> list[dict]:
    # pylint: disable=W0621
    """
    Removes duplicate events based on summary, start time, and end time.
    """
    seen = set()
    unique_events = []

    for event in events:
        # Ensure datetime objects are consistent
        # Remove microseconds for consistency
        dtstart = event['dtstart'].replace(tzinfo=None, microsecond=0)
        dtend = event['dtend'].replace(tzinfo=None, microsecond=0)
        summary = event.get('summary', '')

        # Create a unique identifier for the event
        event_id = (dtstart, dtend, summary)

        # print(f"Checking event: {event_id}")  # Debugging output

        if event_id not in seen:
            seen.add(event_id)
            unique_events.append(event)
        # else:
            # print(f"Duplicate found: {event_id}")  # Debugging output

    return unique_events


num_events, events = get_events_between(start_day, end_day)
# print(len(events))
# print(events)


def display_event_details(event: dict = None):  # pylint: disable=W0621
    """
    Method to display the event details.
    """
    print(f"Summary: {event['summary']}")
    print(f"Start: {format_datetime(event['dtstart'])}")
    print(f"End: {format_datetime(event['dtend'])}")
    print(f"Duration: {event['duration']}\n")


def display_events(number_shown: int):
    """
    Displays the specified number of events.
    """
    if number_shown == 0:
        return

    for event in events[:number_shown]:  # Shows the first two events
        display_event_details(event)


def sum_durations():
    """
    Method to sum the durations of the events of the same name (summary).
    """
    total = timedelta()

    for event in events:
        time_obj = datetime.strptime(event["duration"], "%H:%M:%S")

        time_duration = timedelta(
            hours=time_obj.hour,
            minutes=time_obj.minute,
            seconds=time_obj.second
        )

        total += time_duration
    total_duration = (
        datetime.min + total).strftime("%H:%M:%S")

    print("The total duration of all " +
          f"{num_events} events is {total_duration}.")


def what_next(number_to_display: str):
    """
    Method to determine what to do with the events after viewing them.
    Function should be called when the user chooses to display any number
    of events, including  0 (skip viewing).
    """
    if number_to_display == "all":
        number_to_display = num_events

    display_events(int(number_to_display))

    msg = "Would you like to continue?"
    msg += f"\nOptions:\n\tSum - Sum all {num_events} event durations"
    msg += "\n\tBlank - Exit\n\n"
    msg += "Answer: "
    while True:
        ans = input(msg).lower().strip()

        if not ans:  # blank
            os.system('cls' if os.name == 'nt' else 'clear')

            print("Goodbye, exiting...")
            sys.exit(0)

        if ans == "sum":
            sum_durations()

        break


def display_options():
    """
    Display options and handles IO.
    """
    msg = f"\nThere are {num_events} events, do you want to see them all?"
    msg += f"\nOptions:\n\tAll - to view all {num_events} events"
    msg += "\n\tAn integer x - to view first x events\n\t"
    msg += "Blank - Skip viewing\n\n"
    msg += "Answer: "
    while True:
        ans = input(msg).lower().strip()

        if not ans:  # blank
            what_next("0")
            break

        if ans == "all":
            what_next(ans)
            break

        try:
            ans = int(ans)
            if ans not in range(1, num_events + 1):
                print(f"You must enter a number 1 to {num_events}.\n")
                msg = "New answer: "
                continue
            else:
                what_next(ans)
                break
        except ValueError:
            pass

        # At this point it is not valid
        print("\n\nYou must select one of the available options.")
        msg = f"\nOptions:\n\tAll - to view all {num_events} events"
        msg += "\n\tAn integer x - to view first x events\n\t"
        msg += "Blank - Skip viewing\n\n"
        msg += "Answer: "


display_options()
# print(f"There are {num_events} events.")
# print("They are:")
# for event in events:
#     display_event_details(event)

# TODO: Sort the events in chronological order
