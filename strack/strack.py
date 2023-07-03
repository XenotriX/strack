import click
from datetime import datetime, date
from rich import print, box
from rich.table import Table
from rich.prompt import Confirm
from rich.style import Style
from rich.console import Console
from os import path

from .data import Data
from .session import Session
from .utils import is_this_week, format_duration
from .file_utils import load_file, save_file, set_file
from . import project_command, calendar_command

console = Console()


@click.group()
@click.pass_context
@click.option('--file',
              default=path.expanduser('~/strack_data.json'),
              help='Path to the data file',
              type=click.Path(exists=False, dir_okay=False, resolve_path=True))
def cli(ctx, file):
    set_file(file)
    ctx.obj = load_file()
    pass


cli.add_command(project_command.project)
cli.add_command(calendar_command.calendar)


@cli.command(help='Start tracking a project')
@click.argument('project_name')
@click.option('-t', '--time', default=None,
              help='Start time (current time is used if not specified)')
@click.pass_obj
def start(data: Data, project_name, time):
    # Check that there is no active project
    if data.is_active():
        print(f'Project "{data.get_active().name}" is currently active.')
        print('Use [bold]strack stop[/bold] to stop the current session')
        return

    # Check that the project exists#
    if not data.has_project(project_name):
        print(f'Project "{project_name}" doesn\'t exist.')
        if Confirm.ask('Do you want to create it?'):
            data.add_project(project_name)
        else:
            exit()

    # Start the session
    date = datetime.now()
    if time:
        start_time = datetime.strptime(time, '%H:%M')
        date = datetime.combine(date, start_time.time())
    data.active_project = project_name
    data.get_active().add_session(Session(start=date))
    save_file(data)
    print(f'{project_name} is now active.')


@cli.command()
@click.option('-c', '--comment', default=None, help='Add a comment')
@click.option('-t', '--time', default=None,
              help='End time (current time is used if not specified)')
@click.pass_obj
def stop(data: Data, comment, time):
    if not data.is_active():
        print('No active project.')
        return

    active_project = data.get_active()
    active_session = active_project.active_session()

    # Set end time
    date = datetime.now()
    if time:
        end_time = datetime.strptime(time, '%H:%M')
        date = datetime.combine(date, end_time.time())
    active_session.end = date

    # Add comment
    if comment:
        active_session.comment = comment

    data.active_project = None
    save_file(data)

    # Print summary
    duration_str = active_session.duration_str()
    print((f'Session {active_project.name} stopped '
           f'(Duration: {duration_str})'))


def print_report(active_project, data: Data):
    time_total = 0
    time_week = 0
    time_today = 0
    for session in active_project.sessions:
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
def status(data: Data):
    # Check if there is an active project
    if not data.is_active():
        print('No active project.')
        print(('Start a session by typing: '
               '[bold]strack start [italic]project_name'))
        return

    # Print status
    active_project = data.get_active()
    print(f'Active project: [bold]{active_project.name}[/bold]')
    active_session = active_project.active_session()
    duration_str = active_session.duration_str()
    print((f'Current session: [bold]{duration_str}[/bold] '
           f'started at {active_session.start:%H:%M}'))

    print_report(active_project, data)


@cli.command(help='Show report')
@click.pass_obj
def report(data: Data):
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
        day_projects = [format_duration(
            time) if time > 0 else '' for time in projects[project]]
        # Add project total
        total = sum(projects[project])

        table.add_row(project, *day_projects, format_duration(total),
                      format_duration(project_totals[project]))

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
@click.option('-n', '--limit', default=None, type=click.INT,
              help='Limit the number of sessions shown')
# @click.option('--since', default=None,
#               help='Only show sessions started after this date')
# @click.option('--before', default=None,
#               help='Only show sessions ended before this date')
@click.pass_obj
def list_sessions(data: Data, project_name, limit):
    headers = ['Project', 'Date', 'Start', 'End', 'Duration', 'Comment']
    table = Table(*headers, box=box.ROUNDED)

    # Get list of sessions with project
    sessions = [{'project': proj, 'session': session}
                for proj in data.projects for session in proj.sessions]

    # Sort by start time
    sessions.sort(key=lambda x: x['session'].start, reverse=True)

    # Filter by project name
    if project_name:
        sessions = list(
            filter(lambda x: x['project'].name == project_name, sessions))

    # Limit number of sessions
    if limit:
        sessions = sessions[:limit]

    # Construct table
    for session in sessions:
        duration_str = session['session'].duration_str()
        start_time = session['session'].start
        end_time = session['session'].end or datetime.now()
        table.add_row(session['project'].name,
                      f'{start_time:%Y-%m-%d}', f'{start_time:%H:%M}',
                      f'{end_time:%H:%M}', f'{duration_str}',
                      session['session'].comment or '')

    # Display table
    if len(sessions) > console.height:
        with console.pager():
            console.print(table)
    else:
        print(table)


if __name__ == '__main__':
    cli()
