#!/usr/bin/env python3

import argparse
import sys
import time
import datetime
import json


class TimeTracker:
    '''Implementats all the functionalities'''

    def __init__(self):
        self.data = None
        self.load()

    def load(self):
        '''Loads the file containing the persistent data'''
        try:
            with open('timetracker.json') as file:
                self.data = json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.data = {}

    def save(self):
        '''Saves the data to a file'''
        with open('timetracker.json', 'w') as file:
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
            print('You are already checked in')

        session = self.newSession()
        session['start'] = time.strftime("%H:%M", checkin_time)
        if self.currentDay() is None:
            self.newDay()
        self.save()

    def checkout(self, checkout_time):
        '''Registers a checkout'''
        if self.currentSession() is None:
            return print('You are not checked in')
        session = self.currentSession()
        session['end'] = time.strftime("%H:%M", checkout_time)
        self.save()

    def track(self, name):
        '''Tracks a task'''
        session = self.currentSession()
        if (session is None):
            return print('You are not checked in')
        currentTime = datetime.datetime.now().strftime('%H:%M')
        session['end'] = currentTime
        session = self.newSession()
        session['name'] = name
        session['start'] = currentTime
        print(f'Tracking new task: {name}')
        self.save()

    def status(self):
        '''Generates a status report'''
        if self.currentSession() is not None:
            if self.currentSession()['name']:
                print(f'Current task: {self.currentSession()["name"]}')
            else:
                print('Not tracking any tasks')
        else:
            print('You are currently not checked in')

        time_worked = datetime.timedelta()
        previous_session = None
        for session in self.currentDay():
            if previous_session is not None:
                if session['start'] != previous_session['end']:
                    print(f'{previous_session["end"]} Checked out\n')

            print(f'{session["start"]} {session["name"] or "Checked in"}')
            
            if session['end'] is not None:
                time_delta = datetime.datetime.strptime(session['end'], '%H:%M') - datetime.datetime.strptime(session['start'], '%H:%M')
            else:
                now = datetime.datetime.now().strftime('%H:%M')
                time_delta = datetime.datetime.strptime(now, '%H:%M') - datetime.datetime.strptime(session['start'], '%H:%M')

            time_worked += time_delta
            previous_session = session

        print(f'Hours worked: {str(time_worked)}')


class CommandLine:

    def __init__(self):
        self.tracker = TimeTracker()
        parser = argparse.ArgumentParser(
            usage='''timetracker <command> [<args>]

commands:
    checkin     Records the time you started working
    checkout    Records the time you stopped working
'''
        )
        parser.add_argument('command', help='Command to run')

        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        getattr(self, args.command)()

    def checkin(self):
        parser = argparse.ArgumentParser(description='check in')
        parser.add_argument('time')
        args = parser.parse_args(sys.argv[2:])
        try:
            checkin_time = time.strptime(args.time, '%H:%M')
        except ValueError:
            print('Could not parse the time')
        print('Checked in at %s' % time.strftime('%H:%M', checkin_time))
        self.tracker.checkin(checkin_time)

    def checkout(self):
        parser = argparse.ArgumentParser(description='check out')
        parser.add_argument('time')
        args = parser.parse_args(sys.argv[2:])
        try:
            checkout_time = time.strptime(args.time, '%H:%M')
        except ValueError:
            print('Could not parse the time')
        print('Checked out at %s' % time.strftime('%H:%M', checkout_time))
        self.tracker.checkout(checkout_time)

    def status(self):
        self.tracker.status()

    def track(self):
        parser = argparse.ArgumentParser(
            description='Track a task')
        parser.add_argument('name', help='Name of the session to track')
        parser.add_argument('time', nargs='?', help='Start time')
        args = parser.parse_args(sys.argv[2:])
        self.tracker.track(args.name)


if __name__ == '__main__':
    CommandLine()
