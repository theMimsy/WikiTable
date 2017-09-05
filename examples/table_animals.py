# File:        table_animals.py
# Description: An example script that extracts an HTML table about animal conservation
# Author:      Dawid Minorczyk
# Date:        September 5 2017

# Data manipulation import
import numpy as np
import pandas as pd
import csv

# Custom table parsing import
from ../wikitable import WikiTable

URL = ''

# Recursive lookup
conservation_table = WikiTable(
    tab_fil = {'class' : 'infobox'},    # When following links, look for at the WikiPedia infoboxes
    tab_num = 0,                        # Always look at the first infobox (should only be one)
    regex_ex = ['Conservation status'], # Look for cells in infobox that match this regex
    regex_pos = [(0, 1)]                # If a regex match is found, extract the cell to the below
                                        # extract_row = match_row + 1, extract_col = match_col + 0
)

# Root lookup
animal_table = WikiTable(
    url = URL,                            # Path to the main HTML table
    tab_fil = {'class' : 'animal-table'}, # The table has class `animal-table`
    tab_num = 0,                          # Take the first one
    col_ref = [1],                        # The second column (`col = 1`) has links for recursion
    col_th = True,                        # The first row of the table is a header
    on_link = conservation_table          # What to extract when we come across a link
)

# Gather data
table_df = animal_table.pandas_from_url()

# Save the data into a csv file
table_df.to_csv('animal_conservation.csv', index = False, quoting = csv.QUOTE_ALL)