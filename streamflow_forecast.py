import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import hydrofunctions as hf
from datetime import datetime
from datetime import timedelta
from calendar import isleap
import argparse
import statistics

def get_commandline_input():
    ''' Guides commandline parsing for streamflow program. Optional input string in form 'yyyy-mm-dd'. 
        If no input is given, returns today's date.
    '''
    parser = argparse.ArgumentParser(description='Controls date input for streamflow graph.')
    parser.add_argument('-n', '--name', type=str, default='Trinity River', help='Name of the desired river')
    parser.add_argument('-s', '--sensor', type=str, default='11527000', help='Sensor number to access')
    parser.add_argument('-d', '--date', type=str, default='', help='Anchor date to view')
    args = parser.parse_args()

    # fix this error checking
    if args.name == '' and args.sensor == '' and args.date == '':
        return (args.name, args.sensor, datetime.now.date())

    if args.date == '':
        return (args.name, args.sensor, datetime.now().date())
    
    try:
        date = str_to_date(args.date)
        return (args.name, args.sensor, date)
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

def get_streamflow_stdev(df):
    ''' Uses statistics to calculate standard deviation of all points and returns a numpy array of values 
    
    Args:
        df (pandas dataframe)
    '''
    stdev_values = statistics.stdev(df.iloc[:,0])
    
    
def get_streamflow_specials(df_list):
    ''' Using the total volume of a given streamflow, gets the highest, lowest, average dataframes and returns them
    
    Args:
        df_list (list of pandas dataframes)
    '''

    volume_list = []
    for df in df_list:
        volume_list.append(get_streamflow_volume(df))

    df_max_idx = volume_list.index(max(volume_list))
    df_min_idx = volume_list.index(min(volume_list))
    df_avg_idx = len(sorted(volume_list)) // 2

    return (df_list[df_max_idx], df_list[df_min_idx], df_list[df_avg_idx])

def str_to_date(date_string):
    ''' Converts a string to a date
    
    Args:
        date_string (str):
            should be in the form 'yyyy-mm-dd'
    '''

    return datetime.strptime(date_string, "%Y-%m-%d").date()

def plot_streamflow():
    inputs = get_commandline_input()
    df_list = get_streamflow_data(inputs[2])
    df_current = df_list[0]
    instant_rate = get_streamflow_change(df_current)
    df_max, df_min, df_avg = get_streamflow_specials(df_list)
    
    fig = plt.figure(figsize=(12,9))

    plt.plot(df_max.index, df_max[df_max.keys()[0]], label = 'Highest')
    plt.plot(df_min.index, df_min[df_min.keys()[0]], label = 'Lowest')
    plt.plot(df_current.index, df_current[df_current.keys()[0]], label = 'Current')

    plt.title('Name of place (CFS)')
    plt.xlabel('Water')
    plt.ylabel('Time')

    plt.show()


def main():
    #inputs = get_commandline_input()
    #df_list = get_streamflow_data(inputs[2])
    #print(df_list[0].keys()[0])
    plot_streamflow()

if __name__ == "__main__":
    main()
