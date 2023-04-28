import click
from datetime import datetime, date, timedelta
from rich import print, box
from rich.table import Table
from rich.prompt import Confirm
from rich.style import Style
from rich.text import Text
from pathlib import Path
from os import path
from typing import List
from rich.console import Console

from .data import Data
from .session import Session

DATA_FILE = path.join(Path.home(), "strack_data.json")

console = Console()

def load_file() -> Data:
    try:
        with open(DATA_FILE) as f:
            data = Data.from_file(f)
    except FileNotFoundError:
        data = Data()

    return data


def save_file(data):
    with open(DATA_FILE, 'w') as f:
        data.to_file(f)
        

def is_this_week(dt):
    # Get the ISO calendar year, week number, and weekday of the input datetime
    year, week, weekday = dt.isocalendar()

    # Get the ISO calendar year, week number, and weekday of the current date
    today_year, today_week, today_weekday = date.today().isocalendar()

    # Check if the input datetime is from the same week as the current date
    return year == today_year and week == today_week and weekday <= today_weekday


def format_duration(seconds):
    seconds = round(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}"


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = load_file()
    pass

@cli.group()
def project():
    pass

@project.command(name='add', help='Add a new project')
@click.argument('project_name')
@click.pass_obj
def project_add(data, project_name):
    if data.has_project(project_name):
        print(f"Project \"{project_name}\" already exists.")
    else:
        data.add_project(project_name)
        save_file(data)
        print(f"Project \"{project_name}\" added.")


@project.command(name='remove', help='Remove a project')
@click.argument('project_name')
@click.pass_obj
def project_remove(data, project_name):
    if not data.has_project(project_name):
        print(f"Project \"{project_name}\" doesn't exist.")
        exit(1)

    session_count = data.get_project(project_name).session_count()
    confirmed = Confirm.ask(f'Are you sure you want to remove the project "{project_name}" and delete {session_count} sessions?')

    if confirmed:
        data.remove_project(project_name)
        save_file(data)
        print(f"Project \"{project_name}\" has been removed.")


@project.command(name='rename', help='Rename a project')
@click.argument('old_name')
@click.argument('new_name')
@click.pass_obj
def project_rename(data, old_name, new_name):
    if not data.has_project(old_name):
        print(f"Project \"{old_name}\" doesn't exist.")
        exit(1)

    if data.has_project(new_name):
        print(f'There is already a project with the name "{new_name}".')
        exit(1)

    data.get_project(old_name).name = new_name
    save_file(data)
    print(f'Project \"{old_name}\" has been renamed to "{new_name}".')


@project.command(name='list', help='List projects')
@click.pass_obj
def project_list(data):

    for project in data.projects:
        print(project.name)


@cli.command(help='Start tracking a project')
@click.argument('project_name')
@click.option('-t', '--time', default=None, help='Start time (current time is used if not specified)')
@click.pass_obj
def start(data, project_name, time):
    if data.active_project is not None:
        print(f'Project "{data.get_active().name}" is currently active.')
        print(f'You can terminate the current session by using [bold]strack stop')
        return

    if not data.has_project(project_name):
        print(f"Project \"{project_name}\" doesn't exist.")
        if Confirm.ask('Do you want to create it?'):
            data.add_project(project_name)
        else:
            exit()

    date = datetime.now()
    if time:
        start_time = datetime.strptime(time, "%H:%M")
        date = datetime.combine(date, start_time.time())
    data.active_project = project_name
    data.get_active().add_session(Session(start=date))
    save_file(data)
    print(f"{project_name} is now active.")



@cli.command()
@click.option('-c', '--comment', default=None, help='Add a comment')
@click.option('-t', '--time', default=None, help='End time (current time is used if not specified)')
@click.pass_obj
def stop(data, comment, time):
    if not data.is_active():
        print("No active project.")
    else:
        active_project = data.get_active()
        active_session = active_project.active_session()

        # Set end time
        date = datetime.now()
        if time:
            end_time = datetime.strptime(time, "%H:%M")
            date = datetime.combine(date, end_time.time())
        active_session.end = date

        if comment:
            active_session.comment = comment

        data.active_project = None
        save_file(data)

        duration = active_session.duration()
        duration_hours = format_duration(duration)
        print(f"Session {active_project} stopped (Duration: {duration_hours})")


def print_report(active_project, data: Data):
    time_total = 0
    time_week = 0
    time_today = 0
    for session in data.get_project(active_project).sessions:
        duration = session.duration()
        time_total += duration
        if is_this_week(session.start):
            time_week += duration
        if session.start.date() == date.today():
            time_today += duration

    print(f'Today: {format_duration(time_today)}')
    print(f'Week: {format_duration(time_week)}')
    print(f'Total: {format_duration(time_total)}')


@cli.command()
@click.pass_obj
def status(data):

    if data.is_active():
        active_project = data.get_active()
        print(f'Active project: [bold]{active_project}[/bold]')
        active_session = active_project.active_session()
        duration = active_session.duration()
        duration_hours = format_duration(duration)
        print((f'Current session: [bold]{duration_hours}[/bold] '
               f'started at {active_session.start:%H:%M}'))

        print_report(active_project, data)
    else:
        print('No active project.')
        print(('Start a session by typing: '
               '[bold]strack start [italic]project_name'))


@cli.command(help='Show report')
@click.pass_obj
def report(data):
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    table = Table(box=box.ROUNDED, show_footer=True)

    table.add_column('Project')
    today_day = date.today().weekday()
    for index, day in enumerate(days):
        if index == today_day:
            table.add_column(day, justify='center',
                             style=Style(color='blue'),
                             header_style=Style(color='blue'),
                             footer_style=Style(color='blue'))
        elif index > today_day:
            table.add_column(day, justify='center',
                             style=Style(color='bright_black'),
                             header_style=Style(color='bright_black'),
                             footer_style=Style(color='bright_black'))
        else:
            table.add_column(day, justify='center')
    table.add_column('Week')
    table.add_column('Total')

    projects = {}
    project_totals = {}

    for project in data.projects:
        projects[project.name] = [0 for _ in days]
        data = projects[project.name]
        project_totals[project.name] = 0
        for session in project.sessions:
            # Calculate duration
            duration = session.duration()

            project_totals[project.name] += duration

            # Ignare sessions that are not this week
            if not is_this_week(session.start):
                continue

            # Increment time for the day
            weekday = session.start.weekday()
            data[weekday] += duration

    for project in projects:
        day_projects = [format_duration(time) if time > 0 else '' for time in projects[project]]
        # Add project total
        total = sum(projects[project])

        table.add_row(project, *day_projects, format_duration(total), format_duration(project_totals[project]))

    # Show daily totals in footer
    table.columns[0].footer = 'Total'
    for i in range(len(days)):
        day_total = sum([projects[project][i] for project in projects])
        table.columns[i + 1].footer = format_duration(day_total)

    # Show weekly total
    total = sum([sum(projects[project]) for project in projects])
    table.columns[-2].footer = format_duration(total)

    print(table)


@cli.command(name='list', help='Lists sessions')
@click.argument('project_name', required=False)
@click.option('-n', '--limit', default=None, type=click.INT, help='Limit the number of sessions shown')
# @click.option('--since', default=None, help='Only show sessions started after this date')
# @click.option('--before', default=None, help='Only show sessions ended before this date')
@click.pass_obj
def list_sessions(data, project_name, limit):
    headers = ['Project', 'Date', 'Start', 'End', 'Duration', 'Comment']
    table = Table(*headers, box=box.ROUNDED)

    sessions = [(proj.name, session.start, session.end, session.comment or '')
                for proj in data.projects for session in proj.sessions]

    sessions.sort(key=lambda x:x[1], reverse=True)

    if project_name:
        sessions = list(filter(lambda session: session[0] == project_name, sessions))

    if limit:
        sessions = sessions[:limit]

    for session in sessions:
        start_time = session[1]
        end_time = session[2] or datetime.now()
        duration = (end_time - start_time).total_seconds() / 3600
        duration_str = format_duration(int(duration * 3600))
        table.add_row(session[0], f'{start_time:%Y-%m-%d}', f'{start_time:%H:%M}', f'{end_time:%H:%M}', f'{duration_str}', session[3])

    if len(sessions) > console.height:
        with console.pager():
            console.print(table)
    else:
        print(table)

def merge_ranges(ranges):
    sorted_ranges = sorted(ranges, key=lambda x: x[0])
    merged_ranges = []

    for current_start, current_end in sorted_ranges:
        if not merged_ranges or current_start > merged_ranges[-1][1]:
            merged_ranges.append((current_start, current_end))
        else:
            merged_ranges[-1] = (merged_ranges[-1][0], max(merged_ranges[-1][1], current_end))

    return merged_ranges

def round_time(dt: datetime) -> datetime:
    if dt.minute < 30:
        dt = dt.replace(minute=0, second=0, microsecond=0)
    else:
        dt = dt.replace(minute=30, second=0, microsecond=0)
    return dt

def create_week_table(data: Data):
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_ranges = {day: [] for day in days}

    earliest_time = None
    latest_time = None

    for project in data.projects:
        for session in project.sessions:
            start_time = session.start

            if not is_this_week(start_time):
                continue

            end_time = session.end or datetime.now()

            # Round the time to the nearest half hour
            start_time = round_time(start_time)
            end_time = round_time(end_time)

            weekday = days[start_time.weekday()]
            
            # Truncate the date and only keep the time
            start_time = start_time.replace(year=1900, month=1, day=1)
            end_time = end_time.replace(year=1900, month=1, day=1)

            # Find the earliest and latest time regardless of the day
            earliest_time = min(start_time, earliest_time) if earliest_time else start_time
            latest_time = max(end_time, latest_time) if latest_time else end_time

            day_ranges[weekday].append((start_time, end_time, project.name, session.comment))

    assert earliest_time and latest_time, "No sessions found for this week"

    table = Table(show_header=True, box=box.ROUNDED, expand=False, collapse_padding=True, padding=(0, 0))
    table.add_column("Time")

    for day in days:
        table.add_column(day, min_width=5, justify='center')

    # Get intervals
    total_interval = latest_time - earliest_time;
    # Get the number of half hours
    total_interval = total_interval.total_seconds() / 1800
    intervals = []
    for i in range(int(total_interval)):
        start_time = earliest_time + timedelta(minutes=30 * i)
        end_time = start_time + timedelta(minutes=30)
        intervals.append((start_time, end_time))

    for start_time, end_time in intervals:
        row: List[str | Text] = [f"{start_time.strftime('%H:%M')}"]
        for day in days:
            cell = ""
            for dr in day_ranges[day]:
                if dr[0] <= start_time and dr[1] >= end_time:
                    cell = Text('', style=Style(bgcolor="blue"))
                    if dr[0] == start_time:
                        project_name, comment = dr[2], dr[3]
                        cell.append(project_name)
                        if comment:
                            cell += f" ({comment})"
            row.append(cell)
        table.add_row(*row)

    print(table)

@cli.command(help='Lists sessions')
@click.pass_obj
def cal(data):
    create_week_table(data)


if __name__ == '__main__':
    cli()
