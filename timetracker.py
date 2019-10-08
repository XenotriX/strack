#!/usr/bin/env python3

import argparse
import sys
import time
import datetime
import json
from collections import namedtuple

Session = namedtuple('Session', 'start end name')


class TimeTracker:
    '''Implementats all the functionalities'''

    def __init__(self):
        self.data = None
        self.load()

    def load(self):
        '''Loads the file containing the persistent data'''
        with open('timetracker.json') as file:
            try:
                self.data = json.load(file)
            except json.decoder.JSONDecodeError:
                self.data = {}

    def save(self):
        '''Saves the data to a file'''
        with open('timetracker.json', 'w') as file:
            json.dump(self.data, file)

    def currentDay(self):
        '''Returns the sessions for the current day'''
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        if date not in self.data:
            self.data[date] = []
        return self.data[date]

    def currentSession(self):
        '''Returns the current session'''
        day = self.currentDay()
        if len(day) < 1:
            day.append([])
        return self.currentDay()[len(self.currentDay())-1]

    def checkin(self, checkin_time):
        '''Registers a checkin'''
        session = self.currentSession()
        if len(session) == 2:
            self.currentDay().append([])
            session = self.currentSession()
        if len(session) == 1:
            print('You are already checked in')
        else:
            session.append(time.strftime("%H:%M", checkin_time))
        self.save()

    def checkout(self, checkout_time):
        '''Registers a checkout'''
        session = self.currentSession()
        if len(session) == 1:
            session.append(time.strftime("%H:%M", checkout_time))
        else:
            print('You are already checked out')
        self.save()

    def status(self):
        '''Generates a status report'''
        output = 'Status\n'
        time_worked = datetime.timedelta()
        for session in self.currentDay():
            if len(session) == 2:
                output += f'-> {session[0]}\n'
                output += f'<- {session[1]}\n'
                time_delta = datetime.datetime.strptime(session[1], '%H:%M')
                - datetime.datetime.strptime(session[0], '%H:%M')
            elif len(session) == 1:
                output += f'-> {session[0]}\n'
                now = datetime.datetime.now().strftime('%H:%M')
                time_delta = datetime.datetime.strptime(now, '%H:%M')
                - datetime.datetime.strptime(session[0], '%H:%M')

            time_worked += time_delta

        output += f'Hours worked: {str(time_worked)}'

        return output


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
        print(self.tracker.status())

    def track(self):
        print('Not yet implemented')


if __name__ == '__main__':
    CommandLine()
