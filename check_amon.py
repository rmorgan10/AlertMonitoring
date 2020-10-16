# Script to check AMON for new alerts

import pandas as pd

class AMON:
    """
    Class to interact with AMON and search for new alerts.
    """
    def __init__(self, url="https://gcn.gsfc.nasa.gov/gcn/amon_icecube_gold_bronze_events.html"):
        """
        Query AMON and select new alerts.

        :param url: str, the web address to check
        """
        self.url = url
        self._query_amon()
        self._filter_new()
        self._is_there_a_new_event()
        return

    def _query_amon(self):
        """
        Scrape all events from AMON website
        """
        web_data = pd.read_html(self.url)
        data = web_data[0].values
        columns = [x[1] for x in web_data[0].columns]
        self.df = pd.DataFrame(data=data, columns=columns)
        return

    def _filter_new(self):
        """
        Create a second dataframe with only new events
        """
        old_events = pd.read_csv('data/previous_alerts.csv')
        merged_df = old_events.merge(self.df, how='right', indicator=True)
        self.new_events = merged_df[merged_df['_merge'].values == 'right_only'].copy().reset_index(drop=True)
        return

    def _is_there_a_new_event(self):
        """
        Check if there are new events
        """
        self.alert = len(self.new_events) > 0
        return
    
    
if __name__ == "__main__":
    stream = AMON()
