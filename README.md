*WARNING: This package is still very much in its infancy, with only about 30% of its advertised functionality. While it might be useful in very specific use cases, at the moment it has limited usability and limited documentation. Use at your own risk!*

# WikiTable

Do you have an HTML table (or a bunch of them) that you want to convert into a neater format for analysis or visualization? Does this table contain column spans and row spans that make it hard to parse using existing libraries? Furthermore, does the table contain links to other URLs that you wish you could automatically integrate into the final output? If so, allow me to introduce `WikiTable`, a simple `bs4`-based parser for all your table parsing needs (well, not yet, see above *WARNING*).

## How it Works

The best way to demonstrate how to use the package is with an example. Say you want to extract an HTML table from a specific URL (for example a WikiPedia table) that contains rowspans and internal links. Say, a table that maps animals to their habitats:

<table class="animal-table">
  <tr>
    <th>Animal Habitat</th>
    <th>Animal Name</th>
  </tr>
  <tr>
    <td rowspan="3">Sahara</td>
    <td><a href="https://en.wikipedia.org/wiki/Desert_hedgehog">Desert Hedgehog</a></td>
  </tr>
  <tr>
    <td><a href="https://en.wikipedia.org/wiki/Fennec_fox">Sand Fox</a></td>
  </tr>
  <tr>
    <td><a href="https://en.wikipedia.org/wiki/Barbary_sheep">Barbary Sheep</a></td>
  </tr>
  <tr>
    <td rowspan="2">Tibet</td>
    <td><a href="https://en.wikipedia.org/wiki/Goa_(antelope)">Goa</a></td>
  </tr>
  <tr>
    <td><a href="https://en.wikipedia.org/wiki/Snow_leopard">Snow Leopard</a></td>
  </tr>
</table>

The code for the table above (with `<a></a>` tags removed for simplicity) might look like:

```html
<table class="animal-table">
  <tr>
    <th>Animal Habitat</th>
    <th>Animal Name</th>
  </tr>
  <tr>
    <td rowspan="3">Sahara</td>
    <td>Desert Hedgehog</td>
  </tr>
  <tr>
    <td>Sand Fox</td>
  </tr>
  <tr>
    <td>Barbary Sheep</td>
  </tr>
  <tr>
    <td rowspan="2">Tibet</td>
    <td>Goa</td>
  </tr>
  <tr>
    <td>Snow Leopard</td>
  </tr>
</table>
```
Notice that this table utilizes the `rowspan` option to make "Sahara" and "Tibet" span across multiple rows.

Now that we've seen the input for our example lets take a look at the desired output. We want a `pandas.DataFrame` object that looks as follows:

<table>
  <tr>
    <th>Animal Habitat</th>
    <th>Animal Name</th>
    <th>Conservation Status</th>
  </tr>
  <tr>
    <td>Sahara</td>
    <td>Desert Hedgehog</td>
    <td>Least Concern</td>
  </tr>
  <tr>
    <td>Sahara</td>
    <td>Sand Fox</td>
    <td>Least Concern</td>
  </tr>
  <tr>
    <td>Sahara</td>
    <td>Barbary Sheep</td>
    <td>Vulnerable</td>
  </tr>
  <tr>
    <td>Tibet</td>
    <td>Goa</td>
    <td>Near Threatened</td>
  </tr>
  <tr>
    <td>Tibet</td>
    <td>Snow Leopard</td>
    <td>Endangered</td>
  </tr>
</table>

Two important details:
- The rowspans were handled correctly and expanded into their correct rows.
- There is now an additional column called `Conservation Status`. This column was extracted from the links in the original table.

Most libraries that attempt to accomplish something like this (including `pandas`) would fail to do it correctly. It is the purpose of this small package to solve the `rowspan`/`colspan` problem as well as provide a bit of additional functionality (extracting information from internal links).

### The Code

I've provided that code that accomplishes the above in the [examples directory](https://github.com/theMimsy/WikiTable/tree/master/examples). For the lazy, here's a copy of the animal script:

```python
# Data manipulation import
import numpy as np
import pandas as pd
import csv

# Custom table parsing import
from wikitable import WikiTable

URL = 'https://github.com/theMimsy/WikiTable'

# Recursive lookup
conservation_table = WikiTable(
    tab_fil = {'class' : 'infobox'},    # When following links, look for at the WikiPedia infoboxes
    tab_num = 0,                        # Always look at the first infobox (should only be one)
    regex_ex = ['Conservation status'], # Look for cells in infobox that match this regex
    regex_max = 1,                      # If there is more than one match, only take the first
    regex_pos = [(1, 0)]                # If a regex match is found, extract the cell to the below
                                        # extract_row = match_row + 1, extract_col = match_col + 0
)

# Root lookup
animal_table = WikiTable(
    url = URL,                    # Path to the main HTML table
    tab_num = 1,                  # We want the second table on the page (`index = 1`)
    col_ref = [1],                # The second column (`col = 1`) has links for recursion
    col_th = True,                # The first row of the table is a header
    on_link = conservation_table  # What to extract when we come across a link
)

# Gather data
table_df = animal_table.pandas_from_url()

# Fix up column names
table_df.columns = ['Animal Habitat', 'Animal Name', 'Conservation Status']

# Save the data into a csv file
table_df.to_csv('animal_conservation.csv', index = False, quoting = csv.QUOTE_ALL)
```

The line that actually initiates the parsing is `animal_table.pandas_from_url()`. This function call follows the given `URL` (which is actually the page you're reading right now, so meta), looks for the second table on the page (the table I showed above), and begins extraction. When it gets to the second column of the table, it looks for links and start parsing using the information provided to `conservation_table`; this is a recursive call.

The output of the script is given saved into [this csv file](https://github.com/theMimsy/WikiTable/tree/master/examples/animal_conservation.csv)

## How to Install

Since this package is still being worked on (and expected to change dramatically), I suggest simply cloning the repository of even copy-pasting the code.