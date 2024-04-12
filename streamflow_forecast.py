import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import hydrofunctions

def get_input():


def get_historical_stream():
    sensor = '11527000'

    data = hf.NWIS(sensor, 'iv', start_date='2024-04-01', end_date='2024-04-05')
    # interested in 00060 datatype (discharge data)
    print(data)

    df = data.df('discharge')
    # datetime series  and  value data
    print(df)

def plot_stream():
    pass

if __name__ == "__main__":
    main()
