# -*- coding: utf-8 -*-

import sys
import time
import telepot
from telepot.loop import MessageLoop
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pendulum

SECONDS_BEFORE = 5 * 60

chatids = []

transport = RequestsHTTPTransport('https://api-starsconf.synaptic.cl/graphql.')
client = Client(transport=transport)
query = gql('''
{
    allTalks {
        name,
        timeSlot {
            date,
            start,
            end
        }
  }
}

''')


def handle(msg):
    flavor = telepot.flavor(msg)
    summary = telepot.glance(msg, flavor=flavor)
    chatids.append(summary[2])

TOKEN = sys.argv[1]
bot = telepot.Bot(TOKEN)
MessageLoop(bot, handle).run_as_thread()

response = client.execute(query)

talks = []
for talk in response[u'allTalks']:
    datestr = '{} {}'.format(
        talk[u'timeSlot'][u'date'],
        talk[u'timeSlot'][u'start']
    )
    talks.append({
        u'name': talk[u'name'],
        u'date': pendulum.parse(datestr, tz='America/Santiago')})

print 'Listening ...'
while True:
    now = pendulum.now()
    for talk in talks:
        if (talk['date'] - now).total_seconds() < SECONDS_BEFORE:
            for chatid in chatids:
                bot.sendMessage(
                    chatid,
                    '{} está por comenzar'.format(talk[u'name'])
                )
            talks.remove(talk)
    time.sleep(10)
