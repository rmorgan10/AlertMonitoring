# search for new IceCube alerts

import datetime
import os

from alert_properties import make_alert_list
from check_amon import AMON
from make_json import generate_script
from observability import Event
from plots import make_plots
from reporting import event_page, send_email, git_push, main_page, send_text, slack_post
from utils import ctio, kpno


# Check for alerts
alerts = []
for stream in [AMON()]:
    
    if stream.new_alert:
        alerts += make_alert_list(stream.new_events)
        stream.save_alerts()
        
if len(alerts) != 0:
    # New Alert!
    
    # Read protected information
    with open(".emails", 'r') as f:
        receiving_emails = [x.strip() for x in f.readlines()]

    #with open(".phones", 'r') as f:
    #    _data = [x.strip() for x in f.readlines()]
    #    numbers = [x.split(',')[0] for x in _data]
    #    carriers = [x.split(',')[1] for x in _data]

    with open(".webhooks", 'r') as f:
        webhooks = [x.strip() for x in f.readlines()]

    # inform me
    send_email(("An observability report is currently being produced.\n\n"
                "https://gcn.gsfc.nasa.gov/gcn/amon_icecube_gold_bronze_events.html"), 
               "There is an alert", receiving_emails[0])


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

            # generate observing scripts
            generate_script(event, alert)
                     
        # create a webpage
        #event_page(alert, events)
        #main_page(alert)
        #git_push("add {} information".format(alert.name + '_' + str(alert.revision)))

        # alert us
        subject = alert.name
        body = "https://rmorgan10.github.io/AlertMonitoring/"
        body += alert.name + '_' + str(alert.revision) + '/'
        body += '\n\nBackup: https://github.com/rmorgan10/AlertMonitoring/blob/main/'
        body += alert.name + '_' + str(alert.revision) + '/README.md'
        signoff = "\n\nGood luck!"

        ## - slack
        try:
            for webhook in webhooks:
                slack_post("*" + subject + "* \n" + body, webhook)
        except Exception as err:
            print(err)
            
        ## - text
        #try:
        #    for number, carrier in zip(numbers, carriers):
        #        send_text(number, carrier, body + signoff)
        #except Exception as err:
        #    print(err)
            
        ## - email
        try:
            for receiving_email in receiving_emails:
                send_email(body + signoff, subject, receiving_email)
        except Exception as err:
            print(err)
            
else:
    # heartbeat email
    current_time = datetime.datetime.now()
    if current_time.hour == 9 and current_time.minute > 28 and current_time.minute < 33:
        send_email("I am alive and well!", "Yooo", "robert.morgan@wisc.edu")
    
