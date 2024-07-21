# Calendar Parser
This program is designed to parse `.ics` calendar files, extract event details, handle recurring events, and perform various operations on the extracted data, such as sorting events by start time and summing event durations. The program is intended for users who need to manage and analyze calendar events within a specified date range.

## Features

1. ICS File Parsing
   - The program reads and parses `.ics` calendar files to extract event details.
   - Handles both single occurrence and recurring events using the `icalendar` and `recurring_ical_events` modules.
2. Timezone Handling
   - Ensures all datetime objects are consistent and localized to a specified timezone. Currently only supporting EST.
   - Converts datetime objects to the EST timezone before performing operations.
3. Sorting Events
   - Sorts events chronologically based on their start time (`dtstart`).
4. Summing Event Durations
   - Sums the durations of events grouped by their summary.
   - Displays the total duration for each unique event summary.
5. User Interaction via CLI:
   - Prompts the user to input the desired calendar file, start date, and end date.
   - Offers options to display a specified number of events, sum event durations, or exit the program.

## Usage
The input dates assume 21st century. If for some reason somebody sees this project beyond 2099, feel free to edit that in the `get_start_day` and `get_end_day` functions.

Default dates (leaving blank when asked) are from the current day to a week from the current day. Current day, as in, literally today, the day you are using the program, not the day I am writing this.

More stuff TBA...

## Test .ics files
`testing1.ics` has some events from July 15 to July 19, 2024

`testing2.ics` has some events from July 22 to August 2, 2024

`testing3.ics` is a combination of `testing1.ics` and `testing2.ics`

## Upcoming Features
- More timezone options
- More options for what to do with the events
- Maybe a GUI...
