# -*- coding: utf-8 -*-

import sys
import time
import telepot
from telepot.loop import MessageLoop
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pendulum
from datetime import timedelta as td

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

users = {}


helpmsg = '''
Current commands are:

/alerttime 5    # Alert time in minutes
/stop           # Stop alerts
/restart        # Restart alerts
/help           # show this help

'''

def helpme(chatid, *kw):
    bot.sendMessage(
        chatid,
        helpmsg
    )


def alerttime(chatid, kw):
    users[chatid][u'alerttime'] = int(kw[0])
    bot.sendMessage(
        chatid,
        'Tiempo cambiado a {} minutos'.format(int(kw[0]))
    )


def stop(chatid, kw):
    users[chatid][u'active'] = False
    bot.sendMessage(
        chatid,
        'Alertas detenidas'
    )


def restart(chatid, kw):
    users[chatid][u'active'] = True
    bot.sendMessage(
        chatid,
        'Alertas reiniciadas'
    )

dispatch = {
    u'/alerttime': alerttime,
    u'/restart': restart,
    u'/stop': stop,
    u'/help': helpme
}


def handle(msg):
    flavor = telepot.flavor(msg)
    summary = telepot.glance(msg, flavor=flavor)
    chatid = summary[2]

    # first time user
    if chatid not in users:
        users[chatid] = {
            'alerttime': 5,
            'active': True
        }
        helpme(chatid)

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

print 'Listening ...'
while True:
    now = pendulum.now()
    for chatid in users.keys():
        user = users[chatid]
        for talk in talks:
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
    time.sleep(10)
