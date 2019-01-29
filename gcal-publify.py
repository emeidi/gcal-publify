#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

# Logging purposes ...
def d(msg=None, newline=True):
    if(args.verbose):
        if(msg != None):
            msg = msg.encode('utf-8')

            if newline:
                print(msg)
            else:
                sys.stdout.write(msg)

import sys
import os

import datetime
import dateutil.parser
import argparse
import subprocess

import datetime
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

scriptdir = os.path.dirname(os.path.realpath(__file__))
stringToSearchFor = 'stringToSearchFor'

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'

# argparse
parser = argparse.ArgumentParser(description='google-calendar-publify')
parser.add_argument('--string', help='What events to search', action="store", required=False)
parser.add_argument('--verbose', help='Print debug information', action="store_true", required=False)

args = parser.parse_args()

if args.string:
    d('Received string "' + args.string + '" from command line. Overriding pre-defined string "' + stringToSearchFor + '" to look for events.')
    stringToSearchFor = args.string

store = file.Storage(scriptdir + '/token.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets(scriptdir + '/credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('calendar', 'v3', http=creds.authorize(Http()))

# 'Z' indicates UTC time
d('Querying server for all future events which contain "' + stringToSearchFor + '" ... ')
now = datetime.datetime.utcnow().isoformat() + 'Z'
events_result = service.events().list(calendarId='primary',
                                        timeMin=now,
                                        singleEvents=True,
                                        orderBy='startTime',
                                        q=stringToSearchFor).execute()
events = events_result.get('items', [])

if not events:
    d('No upcoming events retrieved. Script ends here.')
    sys.exit(0)

d(str(len(events)) + ' events retrieved. Analyzing them.')

for event in events:
    if 'visibility' not in event:
        # E.g. Some invites don't have it, somehow
        availableAttributes = '[' + ', '.join(event.keys()) + ']'
        d('Event "' + event['summary'] + '" has no attribute "visibility" ' + availableAttributes +'. Skipping.')
        continue

    if event['visibility'] != 'private':
        d('Event "' + event['summary'] + '" has correct visibility "' + event['visibility'] + '". Skipping.')
        continue

    start = event['start'].get('dateTime', event['start'].get('date'))

    msg = 'Attempting to update event "' + event['summary'] + '" taking place on ' + start + ' with visibility "' + event['visibility'] + '" ...'
    d(msg)

    event['visibility'] = 'public'
    updated_event = service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()

    msg = 'Event "' + updated_event['summary'] + '" taking place on ' + start + ' was updated at ' + updated_event['updated'] + ' and now has visibility "' + updated_event['visibility'] + '"'
    print(msg.encode('utf-8'))

sys.exit(0)
