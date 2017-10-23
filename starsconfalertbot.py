# -*- coding: utf-8 -*-

import sys
import time
import telepot
from telepot.loop import MessageLoop
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pendulum
from datetime import timedelta as td
from pprint import pprint

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

response = client.execute(query)
users = {
    4624152: {
        'alerttime': 5,
        'active': True
    },
    274908043: {
        'alerttime': 5,
        'active': True
    }
}


helpmsg = '''
Current commands are:

/start          # start alerts
/help           # show this help

'''

def start(chatid, kw):
    users[chatid][u'active'] = True
    bot.sendMessage(
        chatid,
        'Alertas reiniciadas'
    )

dispatch = {
    u'/start': start
}


def handle(msg):
    flavor = telepot.flavor(msg)
    summary = telepot.glance(msg, flavor=flavor)
    chatid = summary[2]
    pprint(summary)

    # first time user
    if chatid not in users:
        users[chatid] = {
            'alerttime': 5,
            'active': True
        }

    # dispatch commands
    if msg[u'text'][0] == u'/':
        commands = msg[u'text'].split()
        command = commands[0]
        if command in dispatch:
            dispatch[command](chatid, commands[1:])
        else:
            bot.sendMessage(
                chatid,
                'Comando no implementado!'
            )
            helpme(chatid)

TOKEN = sys.argv[1]
bot = telepot.Bot(TOKEN)
MessageLoop(bot, handle).run_as_thread()


# parse response and take care of timezones
talks = []
for talk in response[u'allTalks']:
    datestr = '{} {}'.format(
        talk[u'timeSlot'][u'date'],
        talk[u'timeSlot'][u'start']
    )
    talks.append({
        u'name': talk[u'name'],
        u'date': pendulum.parse(datestr, tz='America/Santiago'),
        u'users': []})

pprint(talks)

print 'Listening ...'
while True:
    now = pendulum.now()
    print users
    for chatid in users.keys():
        user = users[chatid]
        for talk in talks:
            if (talk[u'date'] - now).total_seconds() > 0:
                minutes_to_talk = (talk[u'date'] - now).total_seconds() / 60.
                if (minutes_to_talk < user[u'alerttime'] and
                        chatid not in talk[u'users']):
                    bot.sendMessage(
                        chatid,
                        '{} está a {} minutos de comenzar!'.format(
                            talk[u'name'],
                            user[u'alerttime']
                        )
                    )
                    # user already alerted
                    talk[u'users'].append(chatid)
    time.sleep(2)
