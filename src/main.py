"""
Modules used for this program, self explanatory...
"""
import os
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from collections import defaultdict
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
            │   ├─ ...
            │   ├─ testing1.ics
            │   ├─ testing2.ics
            │   └─ ...
            └─ main.py
"""
MANY_EVENTS = 5


def parse_ics(file_path: str, start: datetime, end: datetime) -> list[dict]:
    """
    Parse the calendar file to extract events, handling both single
    occurrences and recurrence rules, and return them as a list
    of event dictionaries.

    Args:
        file_path (str): The path to the file being parsed.
        start (datetime): The starting date to parse from.
        end (datetime): The ending date to end parsing.

    Returns:
        list[dict]: A list of the events that were parsed from the file.
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


def get_cal_path(calendar_file: str) -> str:
    """
    Get's the calendar file and returns the path. Defaults to test calendar if
    no other calendar file is provided.

    Args:
        calendar_file (str): The calendar filename

    Returns:
        str: A path to the file.
    """
    calendars_path = (Path(__file__).parent / "calendars/").resolve()
    return str(calendars_path) + f"/{calendar_file}.ics"


def get_start_day() -> datetime:
    """
    Gets the starting date.

    Returns:
        datetime: The starting date.
    """
    while True:
        try:
            start_date_in = input("Enter starting date in MM DD YY format: ")
            if start_date_in:
                date_arr = start_date_in.split()

                start_date = f"{date_arr[0]}-{date_arr[1]}-20{date_arr[2]}"
            else:
                today = date.today()
                start_date = today.strftime("%m-%d-%Y")

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


def get_end_day() -> datetime:
    """
    Gets the ending date.

    Returns:
        datetime: The ending date.
    """
    while True:
        try:
            end_date_in = input("Enter ending date in MM DD YY format: ")

            if end_date_in:
                date_arr = end_date_in.split()

                end_date = f"{
                    date_arr[0]}-{date_arr[1]}-20{date_arr[2]}"
            else:
                today = date.today()
                end_date = (today + timedelta(weeks=1)).strftime("%m-%d-%Y")

            end_datetime = datetime.strptime(end_date, "%m-%d-%Y")
            end_datetime = EST.localize(end_datetime)  # Localize to EST

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

    Returns:
        tuple[str, datetime, datetime]: A tuple containing the filepath, the
        starting date and ending date.
    """
    while True:
        try:
            cal_file = input(
                "Enter the calendar file's name (without extension): ")

            if not cal_file:
                num_test_files = 2
                num_test = input(f"There are {num_test_files} test files " +
                                 "available, enter a number to use one: ")
                cal_file = "testing" + num_test

            file_pathname = get_cal_path(cal_file)  # pylint: disable=W0621
            if not os.path.exists(file_pathname):
                raise FileNotFoundError
            break
        except ValueError:
            pass
        except FileNotFoundError:
            print("File not found. Check if file exists and also the " +
                  f"spelling. File structure should be:\n{FILE_STRUCT}")

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

    Args:
        start (date): A starting date object.
        end (date): A ending date object.

    Returns:
        tuple[int, list[dict]]: A tuple containing the amount of events between
        the staring and ending date as well as a list containing the events.
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

    Args:
        dt (datetime): A datetime object

    Returns:
        str: A formatted string of that datetime object.
    """
    return dt.strftime('%m-%d-%Y %H:%M:%S')


def remove_duplicate_events(events: list[dict]) -> list[dict]:
    # pylint: disable=W0621
    """
    Removes duplicate events based on summary, start time, and end time.

    Args:
        events (list[dict]): A list of event dictionaries.

    Returns:
        list[dict]: The list of events with duplicates removed.
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


def sort_events(events: list[dict]) -> list[dict]:  # pylint: disable=W0621
    """
    Sorts a list of events in chronological order based on the 'dtstart' field,
    ensuring all datetimes are converted to the specified timezone before
    sorting.

    Args:
        events (list[dict]): A list of event dictionaries, each containing
        'dtstart' and 'dtend' keys. timezone (pytz.timezone): The timezone
        to convert all datetime objects to before sorting.

    Returns:
        list[dict]: The sorted list of events.
    """
    for event in events:
        dtstart = event['dtstart']
        dtend = event['dtend']

        # Convert dtstart and dtend to the specified timezone (EST)
        if dtstart.tzinfo:
            dtstart = dtstart.astimezone(EST)
        else:
            dtstart = EST.localize(dtstart)
        if dtend.tzinfo:
            dtend = dtend.astimezone(EST)
        else:
            dtend = EST.localize(dtend)

        event['dtstart'] = dtstart
        event['dtend'] = dtend

    # Sort events based on dtstart
    events.sort(key=lambda e: e['dtstart'])

    return events


events = sort_events(events)


def display_event_details(event: dict = None):  # pylint: disable=W0621
    """
    Method to display the event details.

    Args:
        event (dict): Event to be displayed.
    """
    print(f"Summary: {event['summary']}")
    print(f"Start: {format_datetime(event['dtstart'])}")
    print(f"End: {format_datetime(event['dtend'])}")
    print(f"Duration: {event['duration']}\n")


def display_events(number_shown: int):
    """
    Displays the specified number of events.

    Args:
        number_shown (int): The number of events to be shown.

    """
    if number_shown == 0:
        return

    for event in events[:number_shown]:  # Shows the first two events
        display_event_details(event)


def sum_durations(list_events: list[dict]):
    """
    Method to sum the durations of the events of the same name (summary).
    """
    durations = defaultdict(timedelta)

    for event in list_events:
        summary = event['summary']
        duration_str = event['duration']

        # Debug: Print the duration string
        # print(f"Processing event: '{summary}', Duration: {duration_str}")

        # Parse the duration string into hours, minutes, and seconds
        # Parse the duration string into hours, minutes, and seconds
        try:
            hours, minutes, seconds = map(int, duration_str.split(':'))
        except ValueError as e:
            print(f"Error parsing duration string '{
                  duration_str}' for event '{summary}': {e}")
            continue

        duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)

        # Debug: Print the parsed timedelta
        # print(f"Parsed duration for '{summary}' as timedelta: {duration}\n")

        # Add the duration to the total for the corresponding summary
        durations[summary] += duration

    for summary, total_duration in durations.items():
        # Debug: Print the total_duration object
        # print(f"Total duration for '{summary}': {total_duration}")

        total_seconds = int(total_duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Format the total duration to H:M:S
        formatted_duration = f"{hours:02}:{minutes:02}:{seconds:02}"

        print(f"The total duration of all events with summary '{
              summary}' is {formatted_duration}.")


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
            sum_durations(events)

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
