# search for new IceCube alerts

import datetime
import os

from check_amon import AMON
from alert_properties import make_alert_list
from observability import Event
from utils import ctio, kpno
from plots import make_plots
from reporting import event_page, send_email, git_push, main_page, send_text, slack_post

# Read protected information
with open(".emails", 'r') as f:
    receiving_emails = [x.strip() for x in f.readlines()]

with open(".phones", 'r') as f:
    _data = [x.strip() for x in f.readlines()]
    numbers = [x.split(',')[0] for x in _data]
    carriers = [x.split(',')[1] for x in _data]

with open(".webhooks", 'r') as f:
    webhooks = [x.strip() for x in f.readlines()]


# Check for alerts
alerts = []
for stream in [AMON()]:
    
    if stream.new_alert:
        alerts += make_alert_list(stream.new_events)
        stream.save_alerts()
        
if len(alerts) != 0:
    # New Alert!

    # Initialize observatories
    observatories = [ctio(), kpno()]
    
    for alert in alerts:
        
        # make an alert directory
        os.mkdir('../' + alert.name + '_' + str(alert.revision))
        
        # process events
        events = []
        for observatory in observatories:
            event = Event(alert.ra, alert.dec, observatory, eventid=alert.name, search_time=alert.time_UT)
            events.append(event)
            
            # make all observability plots
            make_plots(event, alert)
                     
        # create a webpage
        event_page(alert, events)
        main_page(alert)
        git_push("add {} information".format(alert.name + '_' + str(alert.revision)))

        # alert us
        subject = alert.name
        body = "https://rmorgan10.github.io/AlertMonitoring/"
        body += alert.name + '_' + str(alert.revision) + '/'
        signoff = "\n\nGood luck!"

        ## - text
        for number, carrier in zip(numbers, carriers):
            send_text(number, carrier, body + signoff)

        continue
            
        ## - email
        for receiving_email in receiving_emails:
            send_email(body + signoff, subject, receiving_email)

        ## - slack
        for webhook in webhooks:
            slack_post("*" + subject + "* \n" + body, webhook)
            
else:
    # heartbeat email
    current_time = datetime.datetime.now()
    if current_time.hour == 9 and current_time.minute > 28 and current_time.minute < 33:
        send_email("I am alive and well!", "Yooo", "robert.morgan@wisc.edu")
    
