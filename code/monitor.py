# search for new IceCube alerts

import datetime
import os

from check_amon import AMON
from alert_properties import make_alert_list
from observability import Event
from utils import ctio, kpno
from plots import make_plots
from reporting import event_page, send_email, git_push

def send_alert_email(alert, receiver):
    subject = alert.name
    body = "https://rmorgan10.github.io/AlertMonitoring/"
    body += alert.name + '_' + str(alert.revision) + '/\n\n'
    body += "Good luck!"
    
    send_email(body, subject, receiver)
    return

receiving_emails = ['robert.morgan@wisc.edu']
    

observatories = [ctio(), kpno()]

alerts = []
for stream in [AMON()]:
    
    if stream.new_alert:
        alerts += make_alert_list(stream.new_events)
        stream.save_alerts()
        
if len(alerts) != 0:
    # New Alert!
    
    for alert in alerts:
        
        # make an alert directory
        os.mkdir('../' + alert.name + '_' + str(alert.revision))
        
        # process events
        events = []
        for observatory in observatories:
            event = Event(alert.ra, alert.dec, observatory, event_id=alert.name)
            events.append(event)
            
            # make all observability plots
            make_plots(event, alert)
                     
        # create a webpage
        event_page(alert, events)
        git_push("add {} information".format(alert.name + '_' + str(alert.revision)))
        
        # send emails
        for receiving_email in receiving_emails:
            send_alert_email(alert, receiving_email)
            
else:
    # heartbeat email
    current_time = datetime.now()
    if current_time.hour == 9 and current_time.minute > 28 and current_time.minute < 33:
        send_email("I am alive and well!", "Yooo", "robert.morgan@wisc.edu")
    
