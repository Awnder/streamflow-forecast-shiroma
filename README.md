# Streamflow Forecast
![Screenshot of an example Streamflow Forecast plot.](/assets/streamflow_example.PNG)

## What is Streamflow Forecast?
Using an anchor date, this python file retrieves government-monitored river water data from the current year and the past nine years. This data is graphed to display certain unique or outstanding waterflow years.

## What is this program's purpose?
This program was designed for two hypothetical companies: first is the local water district that wants to predict how quickly their reservoir is filling up and the second a whitewater rafting company that wants to forecast river flows for the next week.

For real-world experience, this class project was created to demonstrate:
1) proficiency in Python
2) basic data analysis and data manipulation through Pandas and a touch of calculus
3) elementary data graphing using matplotlib's pyplot
4) descriptive variable naming to let docstrings and comments be secondary descriptors

## How to use this program?
Clone the respository!

Note this project uses the following packages. Use pip to install relevant uninstalled packages. 
```
pip install ____
```
1) pandas
2) matplotlib
3) datetime
4) argparse
5) [hydrofunctions](https://pypi.org/project/hydrofunctions/) - downloads water data from the [United States Geological Survey (USGS) National Water Information System (NWIS)](https://waterdata.usgs.gov/nwis)

Commandline arguments are used to get desired government water sensor and date. Use the ```-h``` or ```-help``` flag to get details.
```
python .\streamflow_forecast.py -h
```
There are three control inputs:
1) ```-n``` or ```-name```: the name of the desired river. As data is retrieved using the sensor ID, this does not impact data retrieval. This is displayed in the graph title, however. Default is "Trinity River at Burnt Range Gorge".
2) ```-s``` or ```-sensor```: the sensor ID. The user will have to manually find this ID from the USGS NWIS website. Default is "11527000".
3) ```-d``` or ```-date```: the anchor date on which to start data retrieval. Default is today's date.
