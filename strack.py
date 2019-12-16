#!/usr/bin/env python3

import click
import sys
from time import strptime, strftime
import datetime
import json
from pathlib import Path


DATA_FILE = str(Path.home()) + '/timetracker.json'


class TimeTracker:
    '''Implementats all the functionalities'''

    def __init__(self):
        self.data = None
        self.load()

    def __del__(self):
        self.save()

    def load(self):
        '''Loads the file containing the persistent data'''
        try:
            with open(DATA_FILE) as file:
                self.data = json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.data = {}

    def save(self):
        '''Saves the data to a file'''
        with open(DATA_FILE, 'w') as file:
            json.dump(self.data, file, indent=2)

    def newSession(self):
        session = {
            'name': None,
            'start': None,
            'end': None,
        }
        self.currentDay().append(session)
        return self.currentSession()

    def newDay(self):
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        self.data[date] = []

    def currentDay(self):
        '''Returns the sessions for the current day'''
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        if date not in self.data:
            return None
        return self.data[date]

    def currentSession(self):
        '''Returns the current session'''
        day = self.currentDay()
        if day is None:
            return None
        session = day[len(day)-1]
        if session['end'] is None:
            return session
        else:
            return None

    def checkin(self, checkin_time):
        '''Registers a checkin'''
        if self.currentSession() is not None:
            return False

        if self.currentDay() is None:
            self.newDay()
        session = self.newSession()
        session['start'] = strftime("%H:%M", checkin_time)
        return True

    def checkout(self, checkout_time):
        '''Registers a checkout'''
        if self.currentSession() is None:
            return False
        session = self.currentSession()
        session['end'] = strftime("%H:%M", checkout_time)
        return True

    def track(self, name, time):
        '''Tracks a task'''
        session = self.currentSession()
        if session is None:
            return False
        if time:
            startTime = strftime("%H:%M", time)
        else:
            startTime = datetime.datetime.now().strftime('%H:%M')
        session['end'] = startTime
        session = self.newSession()
        session['name'] = name
        session['start'] = startTime
        return True

    def status(self):
        '''Generates a status report'''
        if self.currentSession() is not None:
            if self.currentSession()['name']:
                return f'Current task: {self.currentSession()["name"]}'
            else:
                return 'Not tracking any tasks'
        else:
            return 'You are currently not checked in'

        # time_worked = datetime.timedelta()
        # previous_session = None
        # for session in self.currentDay():
        #     if previous_session is not None:
        #         if session['start'] != previous_session['end']:
        #             print(f'{previous_session["end"]} Checked out\n')

        #     print(f'{session["start"]} {session["name"] or "Checked in"}')

        #     if session['end'] is not None:
        #         time_delta = datetime.datetime.strptime(session['end'], '%H:%M') - datetime.datetime.strptime(session['start'], '%H:%M')
        #     else:
        #         now = datetime.datetime.now().strftime('%H:%M')
        #         time_delta = datetime.datetime.strptime(now, '%H:%M') - datetime.datetime.strptime(session['start'], '%H:%M')

        #     time_worked += time_delta
        #     previous_session = session

        # print(f'Hours worked: {str(time_worked)}')

    def log(self):
        if self.currentDay() is None:
            return 'There are no sessions yet'
        # Split data into 3 lists
        name_list = [session['name'] for session in self.currentDay()]
        start_list = [session['start'] for session in self.currentDay()]
        end_list = [session['end'] for session in self.currentDay()]
        # Fill empty values with defaults
        name_list = list(map(lambda x: x if x else 'unnamed', name_list))
        start_list = list(map(lambda x: x if x else '', start_list))
        end_list = list(map(lambda x: x if x else '', end_list))
        # Find the longest name
        longest_name = len(max(name_list, key=len))
        lines = []
        for name, start, end in zip(name_list, start_list, end_list):
            lines.append(f'{name:<{longest_name + 3}}{start:<8}{end}')
        return '\n'.join(lines)


@click.group()
@click.pass_context
@click.version_option()
def cli(ctx):
    """Tracks works session"""
    ctx.obj = {}
    ctx.obj['tracker'] = TimeTracker()


@cli.command()
@click.pass_context
@click.argument("time")
def checkin(ctx, time):
    """Starts a new session"""
    try:
        checkin_time = strptime(time, '%H:%M')
    except ValueError:
        print('Could not parse the time')
    if ctx.obj['tracker'].checkin(checkin_time):
        print('Checked in at %s' % strftime('%H:%M', checkin_time))
    else:
        print('You are already checked in')


@cli.command()
@click.pass_context
@click.argument("time")
def checkout(ctx, time):
    """Ends current session"""
    try:
        checkout_time = strptime(time, '%H:%M')
    except ValueError:
        print('Could not parse the time')
    if ctx.obj['tracker'].checkout(checkout_time):
        print('Checked out at %s' % time.strftime('%H:%M', checkout_time))
    else:
        print('You are not checked in')


@cli.command()
@click.pass_context
def status(ctx):
    """Prints an overview of the current task"""
    print(ctx.obj['tracker'].status())


@cli.command()
@click.pass_context
def log(ctx):
    """Prints all the sessions of the current day as a list"""
    print(ctx.obj['tracker'].log())


@cli.command()
@click.pass_context
@click.argument("name")
@click.argument("time")
def track(ctx, name, time):
    """Tracks a new session with the given name"""
    try:
        time = strptime(time, '%H:%M')
    except ValueError:
        print('Could not parse the time')
    if ctx.obj['tracker'].track(name, time):
        print(f'Tracking new task: {name}')
    else:
        print('You are not checked in')


if __name__ == '__main__':
    cli()
