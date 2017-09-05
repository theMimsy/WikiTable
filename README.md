*WARNING: This package is still very much in its infancy, with only about 30% of its advertised functionality. While it might be useful in very specific use cases, at the moment it has limited usability and limited documentation. Use at your own risk!*

# WikiTable

Do you have an HTML table (or a bunch of them) that you want to convert into a neater format for analysis or visualization? Does this table contain column spans and row spans that make it hard to parse using existing libraries? Furthermore, does the table contain links to other URLs that you wish you could automatically integrate into the final output? If so, allow me to introduce `WikiTable`, a simple `bs4`-based parser for all your table parsing needs (well, not yet, see above *WARNING*).

## How it Works:

The best way to demonstrate how to use the package is with an example. Say you want to extract a HTML table from a specific URL (for example a WikiPedia table) that contains rowspans and internal links. Say, a table that maps animals to their habitats:

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

Now that we've seen the input for our example lets take a look at the output. We want a `pandas.DataFrame` object that looks as follows:

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
- The rowspans were handled correctly.
- There is now an additional column called `Conservation Status`. This column was extracted from the links in the original table.

Most libraries that attempt to accomplish something like (including `pandas`) would fail to do it correctly. It is the purpose of this small package to solve the `rowspan`/`colspan` problem as well as provide a bit of additional functionality (extracting information from internal links).