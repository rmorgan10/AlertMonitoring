# A class to collect alert properties

import pandas as pd

class Alert:
    def __init__(self, row):
        
        self.ra = float(row['RA [deg]'])
        self.dec = float(row['Dec [deg]'])
        self.err90 = float(row['Error90 [arcmin]'])
        self.err50 = float(row['Error50 [arcmin]'])
        self.run_num = str(row['RunNum_EventNum'].split('_')[0])
        self.event_num = str(row['RunNum_EventNum'].split('_')[1])
        self.notice_type = str(row['NoticeType'])
        self.energy = float(row['Energy'])
        self.signalness = float(row['Signalness'])
        self.far = float(row['FAR [#/yr]'])
        self.revision = int(row['Rev'])
        self.time_UT = pd.to_datetime(str(row['Date']) + 'T' + str(row['Time UT']),
                                      format="%y/%m/%dT%H:%M:%S.%f")
        return
        
def make_alert_list(amon_df):
    alerts = []
    for index, row in amon_df.iterrows():
        alerts.append(Alert(row))

    return alerts


