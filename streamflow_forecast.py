import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import hydrofunctions as hf
from datetime import datetime
from datetime import timedelta
from calendar import isleap
import argparse

def get_commandline_input():
    ''' Guides commandline parsing for streamflow program. Optional input string in form 'yyyy-mm-dd'. 
        If no input is given, returns today's date.
    '''
    parser = argparse.ArgumentParser(description='Controls date input for streamflow graph.')
    parser.add_argument('date_string', nargs='?', type=str, default='')
    args = parser.parse_args()

    if args.date_string == '':
        return datetime.now().date()
    
    try:
        date = str_to_date(args.date_string)
        return date
    except Exception as e:
        print(e)
        return

def get_streamflow_data(anchor_date):
    ''' Gets the past two weeks of water data from given date, plus the past nine years of water data two weeks before 
        and one week after given date.
    
    Args:
        anchor_date (date):
            should take on form 'yyyy-mm-dd'
    '''

    sensor = '11527000'
    sd = anchor_date - timedelta(days=14)
    ed = anchor_date + timedelta(days=6) # 6 + start_time
    df = pd.DataFrame()
    df_list = []

    # retrieving water data for two weeks for this year (the third week is in the future)
    # if date or time looks a bit odd, remember this is in UTC
    data = hf.NWIS(sensor, 'iv', start_date=sd, end_date=anchor_date)
    df = data.df('discharge')
    df_list.append(df)

    # retrieving water data for three weeks for the past 9 years
    for i in range(9):
        delta = timedelta(days=365)
        if isleap((anchor_date - delta).year): # taking into account leap years
            delta = timedelta(days=366)
            sd -= delta
            ed -= delta
            data = hf.NWIS(sensor, 'iv', start_date=sd, end_date=ed)
        else:
            sd -= delta
            ed -= delta
            data = hf.NWIS(sensor, 'iv', start_date=sd, end_date=ed)
        # df = pd.concat([df, data.df('discharge')]) # 'appending' to dataframe for a single dataframe with all years' data
        df = data.df('discharge')
        df_list.append(df)
    
    return df_list

def get_streamflow_change(df):
    ''' Gets the rate of instantaneous change in CFS/hr at the last two points of the dataframe

    Args:
        df (pandas dataframe)
    '''

    streamflow = df.iloc[:,0]
    water0, water1 = streamflow.tail(2)    
    deltaY = water0 - water1
    deltaX = 15
    return (deltaY / deltaX) * 60

def get_streamflow_volume(df):
    ''' Gets the total volume of an interval in cubic feet 
    
    Args:
        df (pandas dataframe)
    '''

    streamflow = df.iloc[:,0]
    
    # calculate the middle riemann sum
    width = 15 * 60 # min to sec as flow measured in CFS
    avg_sum = 0
    for point in range(len(streamflow)-1):
        height = streamflow.iloc[point]
        difference = (streamflow.iloc[point+1] - height) / 2 # find difference between two points and add it to first point
        avg_sum += width * (height + difference)
    return avg_sum

def get_special_streamflow(df_list):
    ''' Using the total volume of a given streamflow, gets the highest, lowest, average and returns their dataframes
    
    Args:
        df_list (list of pandas dataframes)
    '''

    volume_list = []
    for df in df_list:
        volume_list.append(get_streamflow_volume(df))

    df_max_inx = volume_list.index(max(volume_list))
    df_min_idx = volume_list.index(min(volume_list))
    df_avg_idx = volume_list.index(sum(volume_list)/len(volume_list))


def str_to_date(date_string):
    ''' Converts a string to a date
    
    Args:
        date_string (str):
            should be in the form 'yyyy-mm-dd'
    '''

    return datetime.strptime(date_string, "%Y-%m-%d").date()

def plot_stream():
    pass

def main():
    date = get_commandline_input()
    df_list = get_streamflow_data(date)
    instant_rate = get_streamflow_change(df_list[0])


    print(get_streamflow_volume(df_list[0]))

if __name__ == "__main__":
    main()
