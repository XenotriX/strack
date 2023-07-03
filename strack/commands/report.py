from rich.style import Style
from rich.table import Table
from rich import print, box
import click
from datetime import date

from strack.utils import is_this_week, format_duration
from strack.data import Data

days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def create_table():
    '''Creates a table for the report command'''
    # Create the table
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

    return table


def get_project_duration_per_day(project):
    '''Returns a list of the duration per day for the project'''
    duration_per_day = [0 for _ in days]
    for session in project.sessions:
        # Ignare sessions that are not this week
        if not is_this_week(session.start):
            continue

        # Calculate duration
        duration = session.duration()

        # Increment time for the day
        weekday = session.start.weekday()
        duration_per_day[weekday] += duration

    return duration_per_day


@click.command(help='Show report')
@click.pass_obj
def report(data: Data):
    # Calculate the duration per day for each project
    total_per_day_per_project = [
        get_project_duration_per_day(project)
        for project in data.projects]

    # Calculate the total per day
    total_per_day = [sum(x) for x in zip(*total_per_day_per_project)]

    # Create the table
    table = create_table()

    # Fill the table
    for project, daily_total in zip(data.projects, total_per_day_per_project):
        # Format duration for each day
        per_day = [
            format_duration(time)
            if time > 0 else ''
            for time in daily_total]

        # Calculate weekly and all time total
        weekly_total = format_duration(sum(daily_total))
        total = format_duration(project.total_duration())

        table.add_row(project.name, *per_day, weekly_total, total)

    # Show daily totals in footer
    table.columns[0].footer = 'Total'
    for i, day_total in enumerate(total_per_day):
        table.columns[i + 1].footer = format_duration(day_total)

    # Show weekly total
    weekly_total = sum(total_per_day)
    table.columns[-2].footer = format_duration(weekly_total)

    print(table)
