import click
from datetime import datetime, timedelta
from rich.table import Table
from rich import print, box
from rich.text import Text
from rich.style import Style
from typing import List

from .data import Data
from .utils import round_time, is_this_week

days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def earliest_and_latest(sessions_per_day):
    earliest = None
    latest = None

    for day in days:
        for start, end, *_ in sessions_per_day[day]:
            earliest = min(start, earliest) if earliest else start
            latest = max(end, latest) if latest else end

    return earliest, latest


def get_sessions_per_day(data: Data):
    sessions_per_day = {day: [] for day in days}

    # Round the time to the nearest half hour and group by day
    for project in data.projects:
        for session in project.sessions:
            start = session.start
            end = session.end or datetime.now()

            # Ignore sessions that are not this week
            if not is_this_week(start):
                continue

            weekday = days[start.weekday()]

            # Round the time to the nearest half hour
            start = round_time(start)
            end = round_time(end)

            # Truncate the date and only keep the time
            start = start.replace(year=1900, month=1, day=1)
            end = end.replace(year=1900, month=1, day=1)

            sessions_per_day[weekday].append(
                (start, end, project, session.comment))

    return sessions_per_day


def get_intervals(earliest: datetime, latest: datetime):
    total_interval = latest - earliest
    # Get the number of half hours
    total_interval = total_interval.total_seconds() / 1800
    intervals = []
    for i in range(int(total_interval)):
        start = earliest + timedelta(minutes=30 * i)
        end = start + timedelta(minutes=30)
        intervals.append((start, end))

    return intervals


def get_text_color(rgb_color, threshold=128):
    # Calculate the grayscale value
    gray = 0.299 * rgb_color[0] + 0.587 * rgb_color[1] + 0.114 * rgb_color[2]

    # Return black or white based on the grayscale value and threshold
    if gray >= threshold:
        return 'black'  # black
    else:
        return 'white'  # white


def print_calendar(intervals, sessions_per_day):
    table = Table(show_header=True, box=box.ROUNDED, expand=False,
                  collapse_padding=True, padding=(0, 0))
    table.add_column('Time')

    for day in days:
        table.add_column(day, min_width=5, justify='center')

    for start, end in intervals:
        row: List[str | Text] = [f'{start.strftime("%H:%M")}']
        for day in days:
            cell = ''
            for dr in sessions_per_day[day]:
                if dr[0] <= start and dr[1] >= end:
                    color = dr[2].color
                    text_color = get_text_color(color.triplet)
                    cell = Text('', style=Style(color=text_color, bgcolor=color))
                    if dr[0] == start:
                        project_name, comment = dr[2].name, dr[3]
                        cell.append(project_name)
                        if comment:
                            cell += f' ({comment})'
            row.append(cell)
        table.add_row(*row)

    print(table)


@click.command('cal', help='Show calendar for the week')
@click.pass_obj
def calendar(data: Data):
    sessions_per_day = get_sessions_per_day(data)

    # Find the earliest and latest time regardless of the day
    earliest, latest = earliest_and_latest(sessions_per_day)
    assert earliest and latest, 'No sessions found for this week'

    # Get intervals
    intervals = get_intervals(earliest, latest)

    print_calendar(intervals, sessions_per_day)
