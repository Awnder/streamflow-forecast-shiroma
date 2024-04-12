import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import hydrofunctions as hf
import datetime
from calendar import isleap


def get_historical_stream(start_datetime, end_datetime):
    sensor = '11527000'

    #one year ago, two years ago, etc
    df_year1, df_year2, df_year3, df_year4, df_year5, df_year6, df_year7, df_year8, df_year9 = pd.DataFrame()

    for year in range(9):
        delta = datetime.timedelta(days=365)
        if isleap(start_datetime.year - delta):
            delta = datetime.timedelta(days=366)
            data = hf.NWIS(sensor, 'iv', start_date=start_datetime-delta, end_date=end_datetime-delta)
        else:
            data = hf.NWIS(sensor, 'iv', start_date=start_datetime-delta, end_date=end_datetime-delta)
    water_dataframe = data.df('discharge')

def str_to_date(string):
    return datetime.datetime.strptime(string, "%Y%m%d")

def plot_stream():
    pass

def main():
    pass

if __name__ == "__main__":
    main()
