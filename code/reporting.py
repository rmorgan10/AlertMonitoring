# functions to create reports

from email.mime.text import MIMEText
import math
import os
import platform
import smtplib
import sys

def send_email(body, subject, receiver):
    """
    Send an email
    """
    sender = "IceCubeAlert@{}".format(platform.node())

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        sm = smtplib.SMTP('localhost')
        sm.sendmail(sender, receiver, msg.as_string())
    except smtplib.SMTPException:
        sys.exit("ERROR sending mail")

    return


def event_page(alert, events):
    """
    Can take single event or list of events
    - meant to be same "event" at different observatories
    """
    if not isinstance(events, list):
        events = [events]
    
    report = ("# {0} ({1}_{2})\n\n".format(alert.name, alert.run_num, alert.event_num) + 
              "### IceCube Data\n\n"
              "| Rev | Type | Time (UTC) | Energy (TeV) | Signalness | FAR (#/yr) | 90% Area (sq. deg.) |\n"
              "| --- | --- | --- | --- | --- | --- | --- |\n"
              "| " + str(alert.revision) + " | " + alert.notice_type + " | " +
              alert.time_UT.strftime("%m/%d/%Y  %H:%M:%S") + " | "
              "%.3f" %(alert.energy) + " | " + "%.3f" %(alert.signalness) + " | "
              "%.6f" %(alert.far) + " | %.2f |\n\n" %(math.pi * (alert.err90 / 60)**2) +
              "[Link to IceCube Alert Details](https://gcn.gsfc.nasa.gov/gcn/notices_amon_g_b/"
              "{0}_{1}.amon)\n\n".format(alert.run_num, alert.event_num) +
              "![]({}_skymap.png)\n\n".format(event.observatory.name)) 
    
    for event in events:
        report += ("\n## {} Report\n\n".format(event.observatory.name) +
                   "### Observations Start at {} Madison Time".format(event.optimal_madison_time) + 
                   "### Alert Diagnostics\n\n```")
        for line in event.diagnostics(return_lines=True):
            report += line + '\n'

        report += ("```\n### Observability Plots\n\n"
                   "![]({}_forecast.png)\n\n".format(event.observatory.name) +
                   "![]({}_airmass.png)\n".format(event.observatory.name) +
                   "![]({}_fov.png)\n".format(event.observatory.name))

    # create README file
    filename = '../' + alert.name + '_' + str(alert.revision) + '/README.md'
    with open(filename, 'w+') as stream:
        stream.writelines(report)
        
    return

def main_page(alert):
    os.chdir('..')
    name = alert.name + '_' + str(alert.revision)
    link = "https://rmorgan10.github.io/AlertMonitoring/" + name + '/'
    with open('README.md', 'a') as stream:
        stream.write('- [{0}]({1})'.format(name, link))
    os.chdir('code')
    return

def git_push(message="commit message"):
    os.chdir('..')
    os.system('git add .')
    os.system('git commit -m "{}"'.format(message))
    os.system('git push')
    os.chdir('code')
    return

def text_message(to_number, carrier, message):

    with open('.cred', 'r') as creds:
        auth = [x.strip() for x in creds.readlines()]

    carriers = {'att': '@mms.att.net',
                'tmobile': '@tmomail.net',
                'verizon': '@vtext.com',
                'sprint': '@page.nextel.com'}

    to_address = to_number + get_carrier_address(carrier)

    # Log in to gmail account
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(auth[0], auth[1])

    # send message
    server.sendmail(auth[0], to_address, message)
    
    return
