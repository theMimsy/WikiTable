# File:        wikitable.py
# Description: A parser specifically for extracting HTML tables from wikipedia
# Author:      Dawid Minorczyk
# Date:        July 19 2017

# Libraries for general parsing
import re

# Libraries for parsing html and xml
import requests
from bs4 import BeautifulSoup

# Libraries for data management
import numpy as np
import pandas as pd

# Libraries for iteration and grouping
import itertools
import operator

# Want to use context management for optional values
from contextlib import contextmanager

class WikiTableOptions(dict):
    def __init__(self, kwargs):
        '''
        A dictionary-like object used to set defaults for class `WikiTable`.
        '''
        # Get defaults and override with user input
        options = self._default_options.copy()
        options.update(kwargs)

        # Apply overriden options to self
        dict.__init__(self, options)
        self.__dict__ = self

    # A class variable holding every option in WikiTable and their defaults
    _default_options = {
        'url'      : None,  'tab_num'  : 0,     'tab_fil'  : None,
        'col_th'   : False, 'row_th'   : False,
        'col_ex'   : None,  'row_ex'   : None,
        'col_ref'  : [],    'row_ref'  : [],
        'regex_ex' : None,  'regex_pos': None,  'regex_max': None,
        'on_link'  : None
    }

    @property
    def default_options(self):
        '''
        The getter funtion for the `default_options` class variable. Always looks up the class
        variable as opposed to the instance variable.
        '''
        return type(self)._default_options

    @default_options.setter
    def default_options(self, value):
        '''
        The setter function for the `default_options` class variable. For the sake of expectant
        behavior, does not allow user to change default values.
        '''
        raise Exception('Default WikiTable options should not be modified')

    @contextmanager
    def updated(self, kwargs):
        '''
        A context manager that temporarily overrides options using `kwargs`. Example:

            ```
            old_options = WikiTableOptions()
            # Do stuff here with the old options.

            with old_options.updated(overrides) as new_options:
                # The new options contain the same information as the old options all options
                # specified in the overrides are changed.
                # Do stuff here with the new options.
            ```
        '''
        # Save old options and override with new ones
        saved_options = self.copy()
        self.update(kwargs)

        # Return the new options as a context
        yield self

        # Revert new options to old options
        dict.__init__(self, saved_options)
        self.__dict__ = self
    
class WikiTable:
    '''
    An html parser based off of bs4.BeautifulSoup that extracts tables from a given url. The parser
    expects a url of the page containing the table --support for other forms of input such as html
    files is coming soon--. If there are more than one table on the page, the user can specify which
    one to extract, but only one is extracted per call to `WikiTable`. The output is a 
    `pandas.DataFrame` object --other output formats coming soon--.

    Keyword arguments:
    url     -- A string containing the full path to the html page to parse. (default None)
    tab_num -- A zero indexed integer specifying which table to extract from the page. For example,
        if there are three tables on a given url, then vaild values of `tab_num` are 0, 1, and 2.
        (default 0)
    col_th  -- A boolean specifying whether to treat <th></th> tags on the first row as column names
        of  the output `DataFrame`. If the first row contains <td></td> tags or a mix of <th></th>
        and <td></td> tags, then the <td></td> tags are ignored and not put in as column names.
        (default False)
    row_th  -- A boolean specifying whether to treat <th></th> tags on the first column as the
        index of the output `DataFrame`. If the first column contains <td></td> tags or a mix of 
        <th></th> tags and <td></td> tags, then the <td></td> tags are ignored and not integrated
        into the index. (default False)
    col_ex  -- A list of columns to extract from the table. If `None`, will extract all columns.
        (default None)
    row_ex  -- A list of rows to extract from the table. If `None`, will extract all rows.
        (default None)
    col_ref -- A list of columns from the table to check for hyperlinks. If a hyperlink is found, 
        the parser given by `on_link` will be used to extact more data. If `None`, will look at 
        all columns.  (default [])
    row_ref -- A list of rows from the table to check for hyperlinks. If a hyperlink is found, the
        parser given by `on_link` will be used to extract more data. If `None`, will look at all 
        rows. (default [])
    '''
    def __init__(self, **kwargs):
        '''
        Initializes the parser object. If options are passed during construction, they are merged
        into the default options.
        '''
        self._options = WikiTableOptions(kwargs)

    def pandas_from_url(self, **kwargs):
        '''
        '''
        # Temporarily update options for this operation
        with self._options.updated(kwargs) as options:
            # Get XML/HTML from source URL
            page = requests.get(options.url)

            # Extract
            soup = BeautifulSoup(page.content, 'lxml')
            if options.tab_fil is None:
                table_soup = soup.find_all('table')[options.tab_num]
            else:
                table_soup = soup.find_all('table', options.tab_fil)[options.tab_num]

            # Turn over calculation to internal function
            return self._pandas_from_soup(table_soup, options)
    
    def pandas_from_soup(self, table_soup, **kwargs):
        '''
        '''
        # Temporarily update options for this operation
        with self._options.updated(kwargs) as options:

            # Turn over calculation to internal function
            return self._pandas_from_soup(table_soup, options)

    def _pandas_from_soup(self, table_soup, options):
        '''
        '''
        # Make a list of rows in the table
        tr_soup_list = table_soup.find_all('tr')

        # Parse through the first row for header information
        col_idx = self._handle_col_th(tr_soup_list, options)
        row_idx = self._handle_row_th(tr_soup_list, options)

        # Create a generator for the data
        raw_table_generator = self._generate_body(tr_soup_list, options)
        filtered_table_generator = self._generate_extracted_body(raw_table_generator, options)

        # Make a `DataFrame` from the generator
        data_df = pd.DataFrame(data = filtered_table_generator, index = row_idx)

        # Extend column names to match data length
        col_num = len(data_df.columns)
        col_idx = col_idx + list( range(len(col_idx), col_num) )
        data_df.columns = col_idx

        return self._pandas_extract(data_df, options)

    def _pandas_extract(self, data_df, options):
        '''
        '''
        # Do we want to extract subset of data using a regex
        regex_ex = options.regex_ex
        if regex_ex is None:
            return data_df

        # We want to do extraction but first we need positioning data for each regex
        regex_pos = options.regex_pos
        if regex_pos is None:
            regex_pos = [(0, 0) for index in range(len(regex_ex))]
        else:
            regex_pos = regex_pos + [(0, 0) for index in range(len(regex_ex) - len(regex_pos))]

        # Empty list for future extracted cell contents
        to_extract = []

        for rex, pos in zip(regex_ex, regex_pos):

            # Find all matches to given regex and represent it using Boolean DataFrame
            result_df = pd.DataFrame()
            for col_idx in data_df:
                result_col = data_df[col_idx].str.contains(rex)
                result_df[col_idx] = result_col

            # Create a list of (row, col) index pairs for every match
            true_list = []
            for col_idx in result_df:
                row_idx_list = result_df.loc[result_df[col_idx] == True].index
                true_list = true_list + [(row_idx, col_idx) for row_idx in row_idx_list]

            # Adjust this list by the values given in `regex_pos`
            extract_list = [(orig[0] + pos[0], orig[1] + pos[1]) for orig in true_list]
            
            # Remove unwanted values as specified by `regex_max`
            extract_list = extract_list[0:options.regex_max]

            for row_ex, col_ex in extract_list:
                to_extract.append(data_df.loc[row_ex, col_ex])

        return to_extract

    def _th_check(self, elem_default, elem_soup):
        '''
        '''
        if elem_soup.name == 'th':
            return self.get_clean_text_from_soup(elem_soup)
        else:
            return elem_default 

    def _handle_col_th(self, tr_soup_list, options):
        '''
        '''
        # First row of the given table
        th_td_soup_list = tr_soup_list[0].find_all(['th', 'td'])

        # Default column names
        col_len = 0
        for th_td_soup in th_td_soup_list:
            if th_td_soup.has_attr('colspan'):
                col_len = col_len + int(th_td_soup.get('colspan'))
            else:
                col_len = col_len + 1

        col_idx = list( range(col_len) )

        # Parse in column names depending on options
        if options.col_th:
            for idx, th_td_soup in enumerate(th_td_soup_list):
                col_idx[idx] = self._th_check(idx,  th_td_soup)

        # Get rid of unwanted colmns
        if options.col_ex is None:
            return col_idx
        else:
            return [col_idx[i] for i in options.col_ex] 
    
    def _handle_row_th(self, tr_soup_list, options):
        '''
        '''
        # Default row names
        start_row = 1 if options.col_th else 0
        row_idx = list( range(len(tr_soup_list) - start_row) )

        # Parse in row names depending on options
        if options.row_th:
            #First column of the given table
            th_td_soup_list = [x.find(['th', 'td']) for x in tr_soup_list[start_row:]]

            for idx, th_td_soup in enumerate(th_td_soup_list):
                row_idx[idx] = self._th_check(idx,  th_td_soup)

        # Get rid of unwanted rows
        if options.row_ex is None:
            return row_idx
        else:
            return [row_idx[i] for i in options.row_ex]

    def _save_row_col_span(self, row, col, cell_soup, row_col_spans):
        '''
        '''
        has_rowspan = cell_soup.has_attr('rowspan')
        has_colspan = cell_soup.has_attr('colspan')
        has_both = has_rowspan & has_colspan

        if has_both:
            colspan = int(cell_soup.get('colspan'))
            colspan_list = list(range(colspan))
            rowspan = int(cell_soup.get('rowspan'))
            rowspan_list = list(range(rowspan))

            for r_off, c_off in itertools.product(colspan_list, rowspan_list):
                row_col_spans[(row + r_off, col + c_off)] = \
                        self.get_clean_text_from_soup(cell_soup)
            return

        if has_rowspan:
            rowspan = int(cell_soup.get('rowspan'))

            for r_off in range(rowspan):
                row_col_spans[(row + r_off, col)] = \
                        self.get_clean_text_from_soup(cell_soup)
            return

        if has_colspan:
            colspan = int(cell_soup.get('colspan'))

            for c_off in range(colspan):
                row_col_spans[(row, col + c_off)] = \
                        self.get_clean_text_from_soup(cell_soup)
            return

    def _load_row_col_span(self, row, col, row_col_spans):
        '''
        '''
        repeat_cells = [(r, c) for (r, c) in row_col_spans.keys() if r == row and c >= col]
        # Get all of the spanned cells in this row following this columns
        repeat_cells = sorted(repeat_cells, key = operator.itemgetter(1)) # Sort by column

        # No more spanned cells in this row
        if not repeat_cells:
            return []

        # We will work with just the columns
        repeat_cols = [c for (r, c) in repeat_cells]

        if repeat_cols[0] != col and repeat_cols[0] != col + 1:
            return []

        # Magic groupby and tuple indexing
        continuous_groups = itertools.groupby(enumerate(repeat_cols), key = lambda i: i[1] - i[0])
        next_repeat_cells = list( next( continuous_groups )[1] )
        next_repeat_cells = [(row, c) for (i, c) in next_repeat_cells]
        next_repeat_phrases = [row_col_spans[key] for key in next_repeat_cells]

        return next_repeat_phrases

    def _want_links(self, row, col, options):
        '''
        '''
        # All possible filtering methods
        row_care = options.row_ref is not None and options.row_ref != []
        col_care = options.col_ref is not None and options.col_ref != []
        both_care = col_care and row_care # We try to link on both (not possible)
        none_care = (not col_care) and (not row_care) # We link on neither

        # Simplest method is not to do anything
        if none_care:
            return False

        # We can't do linking across both rows and cols
        if both_care:
            raise Exception('Can\'t follow links across both rows and cols simultaneously')

        # Handle correct dimention
        if row_care:
            index_list = options.row_ref
            if index_list is None:
                return True
            else:
                return row in index_list
        if col_care:
            index_list = options.col_ref
            if index_list is None:
                return True
            else:
                return col in options.col_ref

        # Flow should not reach here
        return False

    def _handle_links(self, row, col, cell_soup, options):
        '''
        '''
        # Do we want to check this row/col for a reference?
        if self._want_links(row, col, options):

            # Does a reference exist?
            a_soup = cell_soup.find('a')
            if a_soup is not None:
                href = a_soup.get('href')

                href_is_relative = href.startswith('/')
                if href_is_relative:
                    top_level_regex = re.compile('^(?:https?://)?(.*?(?=/|$))')
                    top_level_domain = top_level_regex.match(options.url).group(0)
                    next_url = top_level_domain + href
                else:
                    next_url = href

                ref_list = options.on_link.pandas_from_url(url = next_url)
                return ref_list

        # Default to empty list
        return []

    def _generate_body(self, tr_soup_list, options):
        '''
        '''
        # Take care of header options 
        start_row = 1 if options.col_th else 0 # Start at later row if we have col index
        start_col = 1 if options.row_th else 0 # Start at later col if we have row index

        # Dictionary to keep track of colspan and rowspan information
        row_col_spans = {}

        # Iterate over all rows and columns to generate data
        for row_idx, tr_soup in enumerate(tr_soup_list[start_row:]):

            # Check for previous rowspans
            to_yield = self._load_row_col_span(row_idx, 0, row_col_spans)
            col_off = len(to_yield)

            # Account of for any linked data
            linked_data = []

            td_soup_list = tr_soup.find_all(['th', 'td'])
            for col_raw, td_soup in enumerate(td_soup_list[start_col:]):

                # Calculate col offset due to spans
                col_idx = col_raw + col_off

                # Save off any colspans and rowspans for future cells
                self._save_row_col_span(row_idx, col_idx, td_soup, row_col_spans)

                # Add cell to yielding array if not already added
                covered = row_col_spans.keys()
                if not (row_idx, col_idx) in covered:
                    cell_str = self.get_clean_text_from_soup(td_soup)
                    to_yield.append(cell_str)

                # Check for previous colspans 
                repeat_cells = self._load_row_col_span(row_idx, col_idx, row_col_spans)
                to_yield += repeat_cells
                if (not td_soup.has_attr('colspan')) and (not td_soup.has_attr('rowspan')):
                    col_off += len(repeat_cells)

                # Add to links
                linked_data = linked_data + self._handle_links(row_idx, col_idx, td_soup, options)

            yield to_yield + linked_data

    def _generate_extracted_body(self, body_generator, options):
        '''
        '''
        # All possible filtering methods
        row_care = options.row_ex is not None # We care about which row we output
        col_care = options.col_ex is not None # We care about which col we output
        none_care = (not col_care) and (not row_care) # We don't want to filter

        # Simplest method is not to filter
        if none_care:
            yield from body_generator

        # Convert options to booleans
        def handle_care(care, index, index_list):
            if care:
                return index in index_list
            else:
                return True

        # First look at rows
        for row_idx, row in enumerate(body_generator):
            row_extract = handle_care(row_care, row_idx, options.row_ex) 

            # Check if we want this row
            if not row_extract:
                continue # We don't so skip

            # We want this row so look at cols
            to_yield = []
            for col_idx, col in enumerate(row):
                col_extract = handle_care(col_care, col_idx, options.col_ex)

                # Check if we want this column
                if not col_extract:
                    continue # We don't so skip

                # We want this col so append to output
                to_yield.append(col)

            yield to_yield

    def get_clean_text_from_soup(self, td_soup):
        '''
        '''
        # Tags that we want to remove from td
        tag_list = ['sup', 'small', 'br']

        # Remove child tags
        for tag in tag_list:
            if td_soup.find_all(tag):
                exec('td_soup.' + tag + '.extract()')

        # Check for geo coordinates
        geo_check = td_soup.find('span', {'class' : 'geo'})
        if geo_check is None:
            to_return = td_soup.get_text()
        else:
            to_return = geo_check.get_text()

        # Clean it up
        to_return = to_return.strip()
        to_return = to_return.replace('\n', ' ')
        to_return = to_return.replace('\u2013', '-')

        return to_return
