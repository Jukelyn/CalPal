"""
Modules used for this program, self explanatory...
"""
import glob
import os
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from time import sleep
from collections import defaultdict
from typing import Optional
import pytz  # type: ignore # pylint: disable=E0401
from icalendar import Calendar  # type: ignore # pylint: disable=E0401
import recurring_ical_events  # type: ignore # pylint: disable=E0401

TIMEZONE = pytz.timezone('US/Eastern')
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
CALENDARS_DIR = (Path(__file__).parent / "calendars/").resolve()


def clear_terminal() -> None:
    """
    Clears the terminal for cleaner outputting
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def exit_program() -> None:
    """
    Exit's the program.
    """
    print("Goodbye, exiting...")
    sleep(1)

    clear_terminal()
    sys.exit(0)


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
        print(f"File {file_path} not found." +
              " Check if file exists and also the spelling. " +
              f"File structure should be:\n{FILE_STRUCT}")
        exit_program()

    events_list = []
    single_occurrence_events = []

    for component in calendar.walk():
        if component.name == "VEVENT":
            dtstart = component.get('dtstart').dt
            dtend = component.get('dtend').dt
            summary = str(component.get('summary'))

            if dtstart.tzinfo:
                dtstart = dtstart.astimezone(TIMEZONE)
            else:
                dtstart = TIMEZONE.localize(dtstart)
            if dtend.tzinfo:
                dtend = dtend.astimezone(TIMEZONE)
            else:
                dtend = TIMEZONE.localize(dtend)

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
    return str(CALENDARS_DIR) + f"/{calendar_file}.ics"


def get_num_test_files() -> int:
    """
    Gets the nummber of testing .ics files available.

    Returns:
        int: Number of available files.
    """
    pattern = os.path.join(CALENDARS_DIR, 'testing[0-9]*.ics')
    matching_files = glob.glob(pattern)

    return len(matching_files)


NUM_TEST_FILES = get_num_test_files()


def get_calendar_file() -> str:
    """
    Get's the calendar file path, handles errors if not found.
    If no path is found, the testing file will be used instead.

    Raises:
        FileNotFoundError: If the file is not found.

    Returns:
        str: The file path
    """
    while True:
        try:
            cal_file = input(
                "Enter the calendar file's name (blank for test files): ")

            if not cal_file:
                num_test = input(f"There are {NUM_TEST_FILES} test files " +
                                 "available, enter a number to use one: ")
                cal_file = "testing" + num_test

            file_pathname = get_cal_path(cal_file)  # pylint: disable=W0621
            if not os.path.exists(file_pathname):
                raise FileNotFoundError
            break
        except ValueError:
            pass
        except FileNotFoundError:
            clear_terminal()
            print(f"Testing file {cal_file}.ics not found." +
                  " Check if file exists and also the " +
                  f"spelling. File structure should be:\n{FILE_STRUCT}")

    clear_terminal()
    return file_pathname


file_pathname = get_calendar_file()


def get_start_day() -> datetime:
    """
    Gets the starting date.

    Returns:
        datetime: The starting date.
    """
    print("\nThe starting date will default to today if left blank.")
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
            start_datetime = TIMEZONE.localize(start_datetime)

            break
        except IndexError:
            print("Must be a valid date in the correct format, MM DD YY.")
        except ValueError as err:
            if str(err) == "day is out of range for month":
                print("Enter a valid date.")
                continue
            print("Must be a valid date in the correct format, MM DD YY.")
            continue

    return start_datetime


start_day = get_start_day()


def get_end_day(default_date: datetime = start_day) -> datetime:
    """
    Gets the ending date.

    Args:
        default_date (datetime, optional): Used for logic after undefined user
        input. Default value is start_day and the return value will be one week
        from that date. Likewise, if an argument is passed in here, the return
        value will be one week from that date.

    Returns:
        datetime: The ending date.
    """

    print("\nThe ending date will default to a week from the starting date" +
          " if left blank.")

    while True:
        try:
            end_date_in = input("Enter ending date in MM DD YY format: ")

            if end_date_in:
                date_arr = end_date_in.split()

                end_date = f"{
                    date_arr[0]}-{date_arr[1]}-20{date_arr[2]}"
            else:
                end_date = (default_date + timedelta(weeks=1)
                            ).strftime("%m-%d-%Y")

            end_datetime = datetime.strptime(end_date, "%m-%d-%Y")
            end_datetime = TIMEZONE.localize(end_datetime)

            break
        except IndexError:
            print("Must be a valid date in the correct format, MM DD YY.")
        except ValueError as err:
            if str(err) == "day is out of range for month":
                print("Enter a valid date.")
                continue
            print("Must be a valid date in the correct format, MM DD YY.")
            continue

    return end_datetime


end_day = get_end_day(start_day)
events = parse_ics(file_pathname, start_day, end_day)


def get_events_between(start: datetime,
                       end: datetime) -> tuple[int, list[dict]]:
    """
    Get's a list of the events between two dates.

    Args:
        start (datetime): A starting datetime object.
        end (datetime): A ending datetime object.

    Returns:
        tuple[int, list[dict]]: A tuple containing the amount of events between
        the staring and ending date as well as a list containing the events.
    """
    if start.tzinfo is None:
        start = TIMEZONE.localize(start)
    if end.tzinfo is None:
        end = TIMEZONE.localize(end)

    events_between = []  # pylint: disable=W0621

    for event in events:  # pylint: disable=W0621
        event_start = event['dtstart']
        event_end = event['dtend']

        if event_start.tzinfo is None:
            event_start = TIMEZONE.localize(event_start)
        if event_end.tzinfo is None:
            event_end = TIMEZONE.localize(event_end)

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


def view_events_in_range(start: datetime,
                         end: datetime,
                         path: str) -> tuple[int, list[dict]]:
    """
    Encapsulates the logic for checking if there are events within
    the given date range and prompting the user to enter a new date
    range if none are found.

    Args:
        start (datetime): The starting datetime
        end (datetime): The ending datetime
        path (str): The ics file path

    Returns:
        tuple[int, list[dict]]: Tuple with the number of events and the events
    """
    number_events, list_events = get_events_between(start, end)

    while number_events == 0:
        print(f"There are no events to view from {start.strftime("%m-%d-%Y")} "
              + f"to {end.strftime("%m-%d-%Y")}.\n")

        msg = "Enter a new date range? (\"y\" to proceed or blank to quit): "
        keep_going = input(msg).lower()

        if not keep_going or keep_going == "n":
            exit_program()

        if keep_going != "y":
            print("Invalid response.")
            continue

        clear_terminal()
        new_start = get_start_day()
        new_end = get_end_day(new_start)

        list_events = parse_ics(path, new_start, new_end)
        number_events, list_events = get_events_between(new_start, new_end)
    return (number_events, list_events)


num_events, events = view_events_in_range(start_day, end_day, file_pathname)
# print(len(events))
# print(events)


def sort_events(events: list[dict]) -> list[dict]:  # pylint: disable=W0621
    """
    Sorts a list of events in chronological order based on the 'dtstart' field,
    ensuring all datetimes are converted to the specified timezone before
    sorting.

    Args:
        events (list[]): A list of event dictionaries, each containing
        'dtstart' and 'dtend' keys. timezone (pytz.timezone): The timezone
        to convert all datetime objects to before sorting.

    Returns:
        list[dict]: The sorted list of events.
    """
    for event in events:
        dtstart = event['dtstart']
        dtend = event['dtend']

        # Convert dtstart and dtend to the specified timezone (TIMEZONE)
        if dtstart.tzinfo:
            dtstart = dtstart.astimezone(TIMEZONE)
        else:
            dtstart = TIMEZONE.localize(dtstart)
        if dtend.tzinfo:
            dtend = dtend.astimezone(TIMEZONE)
        else:
            dtend = TIMEZONE.localize(dtend)

        event['dtstart'] = dtstart
        event['dtend'] = dtend

    # Sort events based on dtstart
    events.sort(key=lambda e: e['dtstart'])

    return events


events = sort_events(events)


def display_event_details(event: Optional[dict] = None) -> None:
    """
    Method to display the event details.

    Args:
        event (Optional[dict]): Event to be displayed. Defaults to None.
    """
    if event is None:
        return

    print(f"Summary: {event['summary']}")
    print(f"Start: {format_datetime(event['dtstart'])}")
    print(f"End: {format_datetime(event['dtend'])}")
    print(f"Duration: {event['duration']}\n")


def display_events(number_shown: int) -> None:
    """
    Displays the specified number of events.

    Args:
        number_shown (int): The number of events to be shown.
    """
    if number_shown == 0:
        return

    for event in events[:number_shown]:  # Shows the first two events
        display_event_details(event)


def sum_durations(list_events: list[dict]) -> None:
    """
    Method to sum the durations of the events of the same name (summary).

    Args:
        list_events (list[dict]): The list of events being summed.
    """
    durations: defaultdict[None, timedelta] = defaultdict(timedelta)

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

    what_next()


def what_next(number_to_display: str = "0") -> None:
    """
    Method to determine what to do with the events after viewing them.
    Function should be called when the user chooses to display any number
    of events, including  0 (skip viewing).

    Args:
        number_to_display (str): The number of events to be shown. Defaults to
        "0".
    """
    if number_to_display == "all":
        number_to_display = str(num_events)

    display_events(int(number_to_display))

    msg = "\nWould you like to continue?"
    msg += f"\nOptions:\n\tSum - Sum all {num_events} event durations"
    msg += "\n\tBlank - Exit\n\n"
    msg += "Answer: "

    options = ["sum"]
    while True:
        ans = input(msg).lower().strip()

        if ans not in options:  # blank
            exit_program()

        if ans == "sum":
            sum_durations(events)

        break


def display_options() -> None:
    """
    Display options and handles IO.
    """
    msg = f"\nThere are {
        num_events} events between these dates, do you want to see them all?"
    msg += f"\nOptions:\n\tAll - to view all {num_events} events"
    msg += "\n\tAn integer x - to view first x events\n\t"
    msg += "Blank - Skip viewing\n\n"
    msg += "Answer: "

    while True:
        ans = input(msg).lower().strip()

        if not ans:  # blank
            what_next()
            break

        if ans == "all":
            what_next(ans)
            break

        try:
            ans_int = int(ans)
            if ans_int not in range(1, num_events + 1):
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
