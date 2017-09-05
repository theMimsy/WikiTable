# File:        scrape_wiki.py
# Description: A script that extracts HTML tables about the Sinclair Broadcast Group
# Author:      Dawid Minorczyk
# Date:        July 20 2017

# Command line argument import
import os
import sys
import argparse

# Data manipulation import
import numpy as np
import pandas as pd
import csv

# General parsing import
import re

# Custom parsing import
from wikitable import WikiTable

def get_sinclair_wiki_table(table_number):
    '''
    Utilizes the WikiTable library to extract tables about stations owned by the Sinclair Broadcast Group. There are 
    two tables in the hard-coded URL, this function extracts and saves one of these based on the option `table_number` 
    which can take on values of 0 or 1.
    '''
    URL = 'https://en.wikipedia.org/wiki/List_of_stations_owned_or_operated_by_Sinclair_Broadcast_Group'

    # Recursive lookup
    stations_table = WikiTable(
        tab_fil = {'class' : 'infobox'}, # Recursive lookup only in the infoboxes on Wikipedia
        tab_num = 0,                     # Always look at the first infobox (there should only be one)
        regex_ex = ['Transmitter.*'],    # Look for cells in the infobox that match this regex
        regex_max = 1,                   # If there is more than one match, only take one
        regex_pos = [(0, 1)]             # If a regex match is found, extract the cell to the right
                                         # extract_row = match_row + 0 and extract_col = match_col + 1
    )

    # Root lookup
    sinclair_table = WikiTable(
        url = URL,                          # Path to the HTML page to start looking
        tab_fil = {'class' : 'toccolours'}, # Only look at TOC Colours tables
        tab_num = table_number,             # There are two tables to extract on this page
        col_ref = [1],                      # The second column (col = 1) has links that we should follow
        col_th = True,                      # The first row of the table should be treated as a header
        on_link = stations_table            # What to extract when we come across a link that we should follow
    )

    # Gather the data
    table_df = sinclair_table.pandas_from_url()

    # Fix the data up depending on the table
    if table_number == 0:
        table_df.columns = ['Market', 'Station', 'Channel(RF)', 'Year', 
                'DF1', 'DF2', 'DF3', 'DF4', 'Power', 'Location']
    if table_number == 1:
        table_df.columns = ['Market', 'Station', 'Channel(RF)', 'Year',
                'Current_Ownership', 'Power', 'Location']

    # Extract latitute and longitude information
    lat_lon_re_str = '(?P<Latitude>\d+\.\d+);\s+(?P<Longitude>-\d+.\d+)'
    lat_lon_df = table_df.Location.str.extract(lat_lon_re_str, expand = True)
    table_df = pd.concat([table_df, lat_lon_df], axis = 1)

    # Extract power information
    power_re_str = '(?P<Power>\d[,.\d]+\s+kW)'
    table_df.Power = table_df.Power.str.extract(power_re_str, expand = True)

    # Extract station information
    station_re_str = '\s*(?P<Station>[\w-]+)'
    table_df.Station = table_df.Station.str.extract(station_re_str, expand = True)

    # Clean up text
    for col_name in table_df:
        table_df[col_name] = table_df[col_name].str.strip()
   
    # Finally, save off into a csv file depending on table
    if table_number == 0:
        table_df.to_csv('sinclair_stations.csv', index = False, quoting = csv.QUOTE_ALL)
    if table_number == 1:
        table_df.to_csv('sinclair_stations_previous.csv', index = False, quoting = csv.QUOTE_ALL)

def main(argv):
    '''
    This function parses input command line arguments in `sys.argv` and decides whether to parse Wikipedia 
    information. There are two possible command line inputs. The first is `-t` or `--table`, which defines what table
    to extract from Wikipedia. If the table is not specified, both will be parsed out. The second command line
    argument is `-f` or `--force`. By default, this script will not extract a table if it already exists as a csv file
    in the current directory. The `-f` argument forces the script to re-parse the table from the URL. 
    '''
    # Create a command line parser
    parser = argparse.ArgumentParser(
        description = 'Command line input for parsing out Sinclair Broadcast station data from Wikipedia')

    parser.add_argument('-t', '--table', type = int, choices = [0, 1], default = None)
    parser.add_argument('-f', '--force', type = bool, nargs = '?', default = False, const = True)

    # Parse the arguments
    options = parser.parse_args(argv)

    # Yes, I know code repetition is bad but I like the way this looks :)
    # First table
    if options.table is None or options.table == 0:

        # Check for existance or forcing
        file_exists = os.path.isfile('sinclair_stations.csv')
        file_force = options.force
        if not file_exists or file_force:
            print('Extracting first table.')
            get_sinclair_wiki_table(0)

    # Second table
    if options.table is None or options.table == 1:

        # Check for existance or forcing
        file_exists = os.path.isfile('sinclair_stations_previous.csv')
        file_force = options.force
        if not file_exists or file_force:
            print('Extracting second table.')
            get_sinclair_wiki_table(1)

if __name__ == '__main__':
    main(sys.argv[1:])
