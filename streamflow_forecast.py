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

def get_water_data(anchor_date):
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

    # retrieving water data for two weeks for this year (the third week is in the future)
    # if date or time looks a bit odd, remember this is in UTC
    data = hf.NWIS(sensor, 'iv', start_date=sd, end_date=anchor_date)
    df = data.df('discharge')

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
        df = pd.concat([df, data.df('discharge')]) # 'appending' to dataframe
    
    return df

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
    df = get_water_data(date)

if __name__ == "__main__":
    main()
