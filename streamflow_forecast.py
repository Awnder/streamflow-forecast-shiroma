import pandas as pd
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import hydrofunctions as hf
from datetime import datetime
from datetime import timedelta
import argparse

def get_commandline_input():
    ''' Guides commandline parsing for streamflow program.
    Default settings:
        name: Trinity River at Burnt Range Gorge (note only affects plot title and not the actual data gathering)
        sensor: 11527000 (the sensor for Burnt Range Gorge)
        date: the current date in form yy-mm-dd
   
    Settings can be modified:
        name: any string input
        sensor: string input of numbers (must be a valid USGS sensor number)
        date: string input in form yy-mm-dd

    Returns:
        (args.name, sensor, date_valid) (tuple of two strings and a datetime object)
    '''
    parser = argparse.ArgumentParser(description='Controls date input for streamflow graph.')
    parser.add_argument('-n', '--name', type=str, default='Trinity River at Burnt Range Gorge', help='Name of the desired river')
    parser.add_argument('-s', '--sensor', type=str, default='11527000', help='Sensor number to access')
    parser.add_argument('-d', '--date', type=str, default=datetime.strftime(datetime.now().date(), '%Y-%m-%d'), help='Anchor date to view')
    args = parser.parse_args()
    
    sensor = hf.check_parameter_string(args.sensor, 'site')
    date_valid = hf.check_datestr(args.date)
    date_valid = datetime.strptime(date_valid, '%Y-%m-%d').date()

    print(f'Acquring data for {args.name} for sensor {sensor} with anchor date {date_valid}')

    return (args.name, sensor, date_valid)

def get_streamflow_data(anchor_date):
    ''' Gets the past two weeks of water data from given date, plus the past nine years of water data two weeks before 
        and one week after given date.
    
    Args:
        anchor_date (date):
            should take on form 'yyyy-mm-dd'
    
    Returns:
        df_list (list of panda dataframes)
    '''
    sensor = '11527000'
    sd = anchor_date - timedelta(days=14)
    ed = anchor_date + timedelta(days=6) # 6 + start_time
    df = pd.DataFrame()
    df_list = []

    # retrieving water data for two weeks for this year (the third week is in the future) in UTC time
    data = hf.NWIS(sensor, 'iv', start_date=sd, end_date=anchor_date)
    df = data.df('discharge')
    
    # storing datetime64 index separately into Year and Month-Day-Time string-type columns
    # this allows different years to graph over each other instead of plotting continuously year-by-year
    df['year'] = df.index.to_series().dt.strftime('%Y')
    df['date'] = df.index.to_series().dt.strftime('%m-%d %H:%M:%S')
    df = df.set_index('date')
    
    # renaming the water data from a USGS number
    df = df.rename(columns={df.keys()[0] : 'streamflow'})

    df_list.append(df)

    # retrieving water data for three weeks for the past 9 years
    for i in range(9):
        sd = sub_year(sd)
        ed = sub_year(ed)
        data = hf.NWIS(sensor, 'iv', start_date=sd, end_date=ed)
        df = data.df('discharge')
        
        df['year'] = df.index.to_series().dt.strftime('%Y')
        df['date'] = df.index.to_series().dt.strftime('%m-%d %H:%M:%S')
        df = df.set_index('date')

        df = df.rename(columns={df.keys()[0] : 'streamflow'})

        df_list.append(df)
    
    return df_list

# https://bobbyhadz.com/blog/python-add-years-to-date
def sub_year(date):
    ''' Subtracts one year without changing days for leap year (because a leap year has 366 days)
        This keeps date queries from moving one day off the other whenever a there is a leap year.
        Attribution and modified from: https://bobbyhadz.com/blog/python-add-years-to-date

    Args: 
        date (datetime object):
            should be in the form yy-mm-dd

    Returns:
        a datetime object
    '''
    try:
        return date.replace(year=date.year-1)
    except:
        return date.replace(year=date.year-1, day=28)

def get_streamflow_change(df):
    ''' Gets the rate of instantaneous change in CFS/hr at the last two points of the dataframe

    Args:
        df (pandas dataframe)

    Returns:
        a float
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
    
    Returns:
        avg_sum (float)
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

def get_streamflow_outliers(df_list):
    ''' Using the total volume of a given streamflow, gets the highest, lowest, average dataframes and returns them
    
    Args:
        df_list (list of pandas dataframes)

    Returns:
        (df_list[df_max_idx], df_list[df_min_idx]) (tuple of two pandas dataframes)
    '''
    volume_list = []
    for df in df_list:
        volume_list.append(get_streamflow_volume(df))

    df_max_idx = volume_list.index(max(volume_list))
    df_min_idx = volume_list.index(min(volume_list))

    return (df_list[df_max_idx], df_list[df_min_idx])

def get_streamflow_average(df_list):
    ''' Gets the average by summing up across each column and dividing by the number of columns (9 historical years)
    
    Args:
        df_list (list of pandas dataframes)

    Returns: 
        df_merged (pandas dataframe)
    '''
    # removing current data - only want historical
    df_list.pop(0)

    # merging all dataframes together and dropping year column
    df_merged = pd.concat([df.drop('year', axis='columns') for df in df_list], axis='columns', ignore_index=True)

    df_merged['avg'] = df_merged.sum(axis='columns') / df_merged.shape[1]
    
    return df_merged

def calculate_linear_regression(df):
    ''' Calculates the linear regression for the streamflow of a given dataframe. Removes date indexing to allow this.

    Args: 
        df (pandas dataframe)

    Returns: 
        (y1, y2) (tuple of two floats)
    '''
    df = df.reset_index(drop=True)
    xs = [x for x in df['streamflow'].tolist() if isinstance(x, float)]
    ys = df.index.to_list()

    # evaluating the linear regression line's slope and y_int
    sum_x = 0
    sum_y = 0
    sum_xy = 0
    sum_x_sq = 0
    n = len(xs)

    for x, y in zip(xs, ys):
        sum_x += x
        sum_y += y
        sum_xy += x * y
        sum_x_sq += x ** 2

    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_sq - sum_x ** 2)
    y_int = (sum_y - slope * sum_x) / n

    # finding the linear regression line's smallest and largest points
    min_x = min(xs)
    max_x = max(ys)
    y1 = y_int + slope * min_x
    y2 = y_int + slope * max_x

    return (y1, y2)

def index_to_datetime(date_string):
    ''' Converts the string index to a datetime object without a year
    
    Args:
        date_string (str) in form 'mm-dd H:M:S'

    Returns:
        a datetime object in form '%m-%d %H:%M:%S'
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
    df_max, df_min = get_streamflow_outliers(df_list)
    df_avg = get_streamflow_average(df_list)

    instant_rate = get_streamflow_change(df_cur)
    total_volume = get_streamflow_volume(df_cur)
    avg_std = df_avg['avg'].std()
    reg_y1, reg_y2 = calculate_linear_regression(df_cur)
    reg_difference = df_cur['streamflow'].iloc[-1] - reg_y1

    # indecies of all dataframes are in string format (see get_streamflow_data function) so converting back to datetime
    df_cur_idx = [index_to_datetime(idx) for idx in df_cur.index]
    # max, min, and avg all share the same dates (besides year) so can use same index for all of them
    df_hist_idx = [index_to_datetime(idx) for idx in df_max.index]

    cur_last_index = len(df_cur_idx)-1
    hist_last_index = len(df_hist_idx)-1

    plt.figure(figsize=(14,9))

    plt.plot(df_hist_idx, df_max['streamflow'], label = f'Highest ({df_max.iat[2,1]})')
    plt.plot(df_hist_idx, df_min['streamflow'], label = f'Lowest ({df_min.iat[2,1]})')
    plt.plot(df_cur_idx, df_cur['streamflow'], label = f'Current ({df_cur.iat[2,1]})', color='green')

    # plots standard deviation of the streamflow average of 9 prior years  
    plt.fill_between(df_hist_idx, df_avg['avg']-avg_std, df_avg['avg']+avg_std, color='grey', alpha=0.2)

    # plots linear regression line from end of df_cur plot to end of df_max/min plot, and shifts y values up
    plt.plot([df_cur_idx[cur_last_index], df_hist_idx[hist_last_index]], [reg_y1+reg_difference, reg_y2+reg_difference], color='green')

    # have to convert index string -> datetime -> string to format
    axvline_time = datetime.strftime(datetime.strptime(df_cur.index[-1], '%m-%d %H:%M:%S'), '%b %d %H:%M')
    plt.axvline(x=df_cur_idx[cur_last_index], label=f'{axvline_time}', color='red', linewidth=0.8, alpha=0.5)

    plt.suptitle(f'{inputs[0]} (CFS)', fontsize=15, y=0.93, weight='bold')
    if instant_rate > 0:
        plt.title(f'{total_volume:,.0f} acre-feet : rising {instant_rate:.1f} CFS/hr', fontsize=11)
    elif instant_rate < 0:
        plt.title(f'{total_volume:,.0f} acre-feet : dropping {instant_rate:.1f} CFS/hr', fontsize=11)
    else:
        plt.title(f'{total_volume:,.0f} acre-feet : stable at {instant_rate:.1f} CFS/hr', fontsize=11)
    
    # displaying dates as abbreviation and day
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b%d'))
    plt.xlabel('Time')
    plt.ylabel('Water')
    plt.legend(loc='best')
    plt.show()

def main():
    # turns warnings off
    pd.options.mode.chained_assignment = None

    plot_streamflow()

if __name__ == "__main__":
    main()
