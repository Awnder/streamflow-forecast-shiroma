import pandas as pd
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
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

    sensor = int(args.sensor)

    if args.date.strip() == '':
        return (args.name, sensor, datetime.now().date())
    else:
        date = str_to_yeardate(args.date)
        return (args.name, sensor, date)

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
    df.loc[:,'year'] = df.index.to_series().dt.strftime('%Y')
    df.loc[:,'date'] = df.index.to_series().dt.strftime('%m-%d %H:%M:%S')
    df.set_index('date', inplace=True)
    df_list.append(df)

    # retrieving water data for three weeks for the past 9 years
    for i in range(9):
        # delta = timedelta(days=365)
        # ignoring leap years for now
        #if isleap((anchor_date - delta).year): # taking into account leap years
        #    delta = timedelta(days=366)
        #    sd -= delta
        #    ed -= delta
        #    data = hf.NWIS(sensor, 'iv', start_date=sd, end_date=ed)
        #else:
        #sd -= delta
        #ed -= delta

        sd = sub_year(sd)
        ed = sub_year(ed)
        data = hf.NWIS(sensor, 'iv', start_date=sd, end_date=ed)
        df = data.df('discharge')
        
        df.loc[:,'year'] = df.index.to_series().dt.strftime('%Y')
        # changing datetime64 index values to month-day strings (this allows graphing over each other ie: 2014 and 2015)
        df.loc[:,'date'] = df.index.to_series().dt.strftime('%m-%d %H:%M:%S')
        df.set_index('date', inplace=True)

        df_list.append(df)
    
    return df_list

# https://bobbyhadz.com/blog/python-add-years-to-date
def sub_year(date):
    ''' Subtracts one year without accounting for leap years
    
    Args: 
        date (datetime object):
            should be in the form yy-mm-dd
    '''
    try:
        return date.replace(year=date.year-1)
    except:
        return date.replace(year=date.year-1, day=28)

def get_streamflow_change(df):
    ''' Gets the rate of instantaneous change in CFS/hr at the last two points of the dataframe
    Attribution and modified from: https://bobbyhadz.com/blog/python-add-years-to-date

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
    
    # converting cubic feet to acre feet
    avg_sum = avg_sum * (2.29568 * 10 ** -5)
    return avg_sum

def get_streamflow_stdev(df):
    ''' Uses statistics to calculate standard deviation of a dataframe and returns a float 
    
    Args:
        df (pandas dataframe)
    '''
    return statistics.stdev(df.iloc[:,0])
    
def get_streamflow_outliers(df_list):
    ''' Using the total volume of a given streamflow, gets the highest, lowest, average dataframes and returns them
    
    Args:
        df_list (list of pandas dataframes)
    '''
    volume_list = []
    for df in df_list:
        volume_list.append(get_streamflow_volume(df))

    df_max_idx = volume_list.index(max(volume_list))
    df_min_idx = volume_list.index(min(volume_list))

    return (df_list[df_max_idx], df_list[df_min_idx])

def get_streamflow_average(df_list):
    # new standard deviation method for above to calculate across the years (not in one year)
    df_list.pop(0) # removing current data - only want historical

    # merging all dataframes together and dropping year column
    merged_df = pd.concat([df.drop('year', axis='columns') for df in df_list], axis='columns', ignore_index=True)
    print(merged_df.head())
    merged_df = merged_df.reset_index(drop=True)
    merged_df['avg'] = merged_df.sum(axis='columns') / merged_df.shape[1]
    
    return merged_df

def calculate_linear_regression(df):
    return
    # evaluating the linear regression line's slope and y_int
    sum_x = 0
    sum_y = 0
    sum_xy = 0
    sum_x_sq = 0
    n = len(x_data)

    for x, y in zip(x_data, y_data):
        sum_x += x
        sum_y += y
        sum_xy += x * y
        sum_x_sq += x ** 2

    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_sq - sum_x ** 2)
    y_int = (sum_y - slope * sum_x) / n

    # finding the linear regression line's smallest and largest points
    min_x = min(x_data)
    max_x = max(x_data)
    y1 = y_int + slope * min_x
    y2 = y_int + slope * max_x

    return (min_x, max_x, y1, y2)


def str_to_yeardate(date_string):
    ''' Converts a string to a datetime object with a year
    
    Args:
        date_string (str):
            should be in the form 'yyyy-mm-dd'
    '''
    return datetime.strptime(date_string, '%Y-%m-%d').date()

def index_to_datetime(date_string):
    ''' Converts the string index to a datetime object without a year
    
    Args:
        date_string (str):
            should be in the form 'mm-dd H:M:S'
    '''
    return datetime.strptime(date_string, '%m-%d %H:%M:%S')

def plot_streamflow():
    ''' Plots max, min, avg, and current day streamflows using matplotlib '''
    # tells matplotlib to use tkinter to display, without will result in FigureCanvasAgg non-interactable error
    matplotlib.use('TkAgg')

    try:
        inputs = get_commandline_input()
    except Exception as e:
        print(e)
        return
    
    df_list = get_streamflow_data(inputs[2])

    df_cur = df_list[0]
    instant_rate = get_streamflow_change(df_cur)
    total_volume = get_streamflow_volume(df_cur)

    df_max, df_min = get_streamflow_outliers(df_list)
    df_avg = get_streamflow_average(df_list)
    df_max_idx = [index_to_datetime(idx) for idx in df_max.index]
    df_min_idx = [index_to_datetime(idx) for idx in df_min.index]
    df_cur_idx = [index_to_datetime(idx) for idx in df_cur.index]

    # calculate_linear_regression(df_cur)

    plt.figure(figsize=(14,9))

    plt.plot(df_max_idx, df_max[df_max.keys()[0]], label = f'Highest ({df_max.iat[2,1]})')
    plt.plot(df_min_idx, df_min[df_min.keys()[0]], label = f'Lowest ({df_min.iat[2,1]})')
    plt.plot(df_cur_idx, df_cur[df_cur.keys()[0]], label = f'Current ({df_cur.iat[2,1]})')

    # plt.plot(np.linspace())
    # plt.plot(df_cur_idx[len(df_cur_idx)-1], [instant_rate for i in range(df_cur_idx[len(df_cur_idx)-1], len(df_max_idx)-1)])

    # have to convert index string -> datetime -> string to format
    axvline_time = datetime.strftime(datetime.strptime(df_cur.index[-1], '%m-%d %H:%M:%S'), '%b %d %H:%M')
    plt.axvline(x=df_cur_idx[len(df_cur_idx)-1], label=f'{axvline_time}', color='red', linewidth=0.7, alpha=0.5)

    plt.suptitle('Name of place (CFS)', fontsize=15, y=0.93, weight='bold')
    if instant_rate > 0:
        plt.title(f'{total_volume:,.0f} acre-feet : rising {instant_rate:.1f} CFS/hr', fontsize=11)
    elif instant_rate < 0:
        plt.title(f'{total_volume:,.0f} acre-feet : dropping {instant_rate:.1f} CFS/hr', fontsize=11)
    else:
        plt.title(f'{total_volume:,.0f} acre-feet : stable at {instant_rate:.1f} CFS/hr', fontsize=11)
    
    # setting dates to 
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b%d'))
    plt.xlabel('Time')
    plt.ylabel('Water')
    plt.legend(loc='best')
    plt.show()

def main():
    #inputs = get_commandline_input()
    #df_list = get_streamflow_data(inputs[2])
    #print(get_streamflow_change(df_list[0]))
    #print(get_streamflow_volume(df_list[0]))
    #get_streamflow_specials(df_list)
    #print(get_streamflow_stdev(df_list[0]))
    # get_streamflow_average(df_list)
    # print(df_list[0].index)
    plot_streamflow()

if __name__ == "__main__":
    main()
