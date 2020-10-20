# functions to create reports

from email.mime.text import MIMEText
import json
import math
import os
import platform
import shlex
import smtplib
import subprocess
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
              '<a href="https://gcn.gsfc.nasa.gov/gcn/notices_amon_g_b/{0}_{1}.amon" target="_blank">'.format(alert.run_num, alert.event_num) +
              'Link to IceCube Alert Details</a>\n\n'
              '<a href="https://rmorgan10.github.io/AlertMonitoring/'
              '{0}/{1}_skymap.png" target="_blank">\n'.format(alert.name + '_' + str(alert.revision), events[0].observatory.name) +
              '  <img src="{0}_skymap.png" alt="{1} Skymap" style="width:700px;height:400px;">\n'.format(events[0].observatory.name, events[0].observatory.name) +
              '</a>\n\n')
    
    for event in events:
        report += ("\n## {} Report\n\n".format(event.observatory.name) +
                   "**Observations Start at**  `{}`  **Madison Time**".format(event.optimal_madison_time) +
                   '\n\n<a href="https://github.com/rmorgan10/AlertMonitoring/blob/main/{0}/{1}.json" target="_blank">'.format(alert.name + '_' + str(alert.revision), event.observatory.name) +
                   'Link to Observing Scripts'
                   "\n\n### Alert Diagnostics\n\n```")
        for line in event.diagnostics(return_lines=True):
            report += line + '\n'

        report += ("```\n### Observability Plots\n\n"
                   '<a href="https://rmorgan10.github.io/AlertMonitoring/'
                   '{0}/{1}_forecast.png" target="_blank">\n'.format(alert.name + '_' + str(alert.revision), event.observatory.name) +
                   '  <img src="{0}_forecast.png" alt="{1} Forecast" style="width:700px;height:233px;">\n'.format(event.observatory.name, event.observatory.name) +
                   '</a>\n\n'
                   '<a href="https://rmorgan10.github.io/AlertMonitoring/'
                   '{0}/{1}_airmass.png" target="_blank">\n'.format(alert.name + '_' + str(alert.revision), event.observatory.name) +
                   '  <img src="{0}_airmass.png" alt="{1} Airmass" style="width:320px;height:320px;">\n'.format(event.observatory.name, event.observatory.name) +
                   '</a>\n'
                   '<a href="https://rmorgan10.github.io/AlertMonitoring/'
                   '{0}/{1}_fov.png" target="_blank">\n'.format(alert.name + '_' + str(alert.revision), event.observatory.name) +
                   '  <img src="{0}_fov.png" alt="{1} FoV" style="width:320px;height:320px;">\n</a>\n\n'.format(event.observatory.name, event.observatory.name))

    # create README file
    filename = '../' + alert.name + '_' + str(alert.revision) + '/README.md'
    with open(filename, 'w+') as stream:
        stream.writelines(report)
        
    return

def _sort_alerts(alerts):
    alert_dict = {}
    for alert in alerts:
        name = alert.split('[IC')[1][0:6]
        year = int('20' + name[0:2])
        month = int(name[2:4])
        day = int(name[4:6])

        # load into a dictionary
        if year in alert_dict.keys():
            if month in alert_dict[year].keys():
                if day in alert_dict[year][month].keys():

                    alert_dict[year][month][day].append(alert)
                else:
                    alert_dict[year][month][day] = [alert]
            else:
                alert_dict[year][month] = {day : [alert]}
        else:
            alert_dict[year] = {month : {day : [alert]}}
    
    # iterate through the dictionary and build of the sorted alerts
    month_map = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
                 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September',
                 10: 'October', 11: 'November', 12: 'December'}

    out_alerts = []
    for year in sorted(alert_dict.keys(), reverse=True):
        out_alerts.append('### ' + str(year) + '\n')
        for month in sorted(alert_dict[year].keys(), reverse=True):
            out_alerts.append('**' + month_map[month] + '**\n\n')
            for day in sorted(alert_dict[year][month].keys(), reverse=True):
                for alert in alert_dict[year][month][day]:
                    out_alerts.append(alert + '\n')
            out_alerts.append('\n\n')

    return out_alerts

def main_page(alert):
    os.chdir('..')
    name = alert.name + '_' + str(alert.revision)
    link = "https://rmorgan10.github.io/AlertMonitoring/" + name + '/'

    # read all alerts and parse by date
    stream = open('README.md', 'r')
    lines = stream.readlines()
    stream.close()

    header = "# Alert Monitoring\n\nMonitoring IceCube GOLD and BRONZE alerts.\n\n## Alerts\n"
    alerts = [x.strip() for x in lines if x.startswith('-')]
    alerts.append('- [{0}]({1})'.format(name, link))
    sorted_alerts = _sort_alerts(alerts)

    stream = open('README.md', 'w+')
    stream.writelines([header] + sorted_alerts)
    stream.close()
    
    os.chdir('code')
    return

def git_push(message="commit message"):
    os.chdir('..')
    os.system('git add .')
    os.system('git commit -m "{}"'.format(message))
    os.system('git push > monitor.log')
    os.chdir('code')
    return

def send_text(to_number, carrier, message):

    with open('.cred', 'r') as creds:
        auth = [x.strip() for x in creds.readlines()]

    carriers = {'att': '@mms.att.net',
                'tmobile': '@tmomail.net',
                'verizon': '@vtext.com',
                'sprint': '@page.nextel.com'}

    to_address = to_number + carriers[carrier]

    # Log in to gmail account
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(auth[0], auth[1])

    # send message
    server.sendmail(auth[0], to_address, message)
    
    return

def slack_post(message, webhook):

    def run(string):
        """ run a UNIX command """

        # shlex.split will preserve inner quotes
        prog = shlex.split(string)
        p0 = subprocess.Popen(prog, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        
        stdout0, stderr0 = p0.communicate()
        rc = p0.returncode
        p0.stdout.close()

        return stdout0, stderr0, rc

    """ Styles a slack post and pushes it to slack """

    payload = {}
    payload["text"] = message
    
    cmd = "curl -X POST --data-urlencode 'payload={}' {}".format(json.dumps(payload), webhook)
    run(cmd)
    
    return
