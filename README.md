# Data Viewer GUI User Documentation

## Overview

The Data Viewer is a graphical user interface (GUI) application designed to facilitate the handling of biological sequence data. This guide will walk you through the various features and functionalities you can expect when using this tool.

---

## Main Window

Upon launching the application, a window titled `Data Viewer` will appear, and it is composed of various widgets for different functions:

### Search Bar

At the top of the window, you'll find a search bar that allows you to filter through the displayed data. 

#### Find

The search bar defaults to 'Find'. When you enter a term in the search bar, it highlights any cells that contain the search string. Search terms are case-sensitive.

Search terms may be submitted as individual strings (e.g. `synapse` or `YSLF`) or as a regular expression. Unless the `Use regex` box is ticked, `Find` (and `Find/replace`) will treat all characters literally. A brief explanation of regular expressions follows at the end of the user guide.

Searches can search all cells or be limited to specific columns using the column select menu. The default is `All`.

Pressing the "Confirm" button will create a new tab containing only the data matching your search.

#### Find/replace

If you toggle the `Find/replace` checkbox, you can access the find/replace function. The function still highlights cells matching the search term, but will generate a new tab containing data where the replacement has been made. PLEASE NOTE that although find highlights the whole cell, only the portion of the cell's text matching your search term or regex pattern will be replaced.

### Tabs

Below the search bar, there's an area that will display data in table format. Each open file will be displayed in a separate tab.

### Import/Export Buttons

On the right-hand side, you will find a set of buttons organized in a grid layout for the following functions:

1. **Import CSV**: Opens a file dialog that lets you select and import a CSV file into the application.
2. **Export CSV**: Opens a file dialog that lets you save the currently displayed table as a CSV file.
3. **Import FASTA**: Opens a file dialog that lets you select and import a FASTA file into the application.
4. **Export FASTA**: Opens a file dialog that lets you save the currently displayed table as a FASTA file.

### Other Buttons

Below the Import/Export buttons, there are additional buttons for specific functionalities:

1. **Generate tryptic peptides**: Performs tryptic digestion on the sequences and displays the peptides.
2. **Generate m/z**: Calculates and displays the mass-to-charge ratios (m/z) for the peptides.

---

## How To Use

### Getting started

1. Download the appropriate DataViewer version for your OS (`DataViewer_Mac` or `DataViewer_Windows`)
2. Move the file to your desired location
3. Open the folder and run the DataViewerApp executable (`DataViewerApp.app` or `DataViewerApp.exe`)

### To Import Data:

1. Click the `Import CSV` or `Import FASTA` button, depending on the file format.
2. Navigate to the directory where your file is located and select the file.
3. Click `Open`.

### To Export Data:

1. Ensure you are in the tab containing the data you wish to export.
2. Click `Export CSV` or `Export FASTA`, depending on your desired format.
3. Choose the location where you want to save the file and click `Save`.

PLEASE NOTE: Only files imported from FASTA then manipulated can be exported as FASTA or as CSV. However, Thermo-compatible CSV files can only be exported as CSV.

### To Search Through Data:

1. Click on the search bar at the top.
2. Select the column to search from the `column selector menu` or select `All`.
3. Enter the text you want to search for.
4. The table will automatically highlight the results as you type.
5. Press `Confirm` to create a new dataframe with filtered results

### To Generate Tryptic Peptides:

1. Import a FASTA file containing protein sequences.
2. Click the `Generate tryptic peptides` button.
3. The peptides will be displayed in a new tab.

### To Generate Mass-to-Charge Ratios:

1. Import a FASTA file or generate tryptic peptides.
2. Click the `Generate m/z` button.
3. The mass-to-charge ratios will be displayed in a new tab.

---

## A Primer on Regular Expressions

Regular expressions (often abbreviated as "regex") are powerful tools for matching patterns in text. Although the term may be unfamiliar, the concept is simple and incredibly useful in searching through large sets of data. In the Data Viewer's search bar, you can use regular expressions to make your search queries more powerful and flexible.

### Basic Regular Expression Symbols

In Python 3.10, the `re` library is used for regular expressions, and the Data Viewer's search bar also supports Python-compatible regular expressions. Below are some commonly used symbols and examples.

- `|` : OR condition (matches either the preceding or following expression)
- `.` : Matches any single character except a newline.
- `[ ]`: Matches any one of the characters within the square brackets.
- `( )`: Matches the characters within the parentheses as a single group (i.e. those exact character in that exact order)

(Note: The AND condition isn't natively supported by Python's `re` library in the way you might expect. You would typically achieve AND-like behavior by simply placing expressions next to each other without an operator, but this requires the expressions to occur in the specified order. For more generalized AND conditions, you would typically have to run multiple regular expression searches.)

### Examples

The following examples should be helpful. To test regex patterns on your own, check out [Regex101](www.regex101.com) and click `Python` under `Flavors`.

#### Using OR in Search

If you want to find all rows that contain either "gene1" or "gene2", you can use the OR symbol `|`.

Regular Expression Pattern:
```
gene1|gene2
```

This will match any string that contains either "gene1" or "gene2".

#### Using AND in Search

As mentioned, Python's regular expression engine doesn't natively support an AND condition (`&`). If you need to search for rows containing both "gene1" and "exon", you might have to perform two separate searches. Alternatively, you could use more complex regular expressions or code logic to achieve AND-like behavior.

Until an AND operator is implemented for the search bar, I recommend trying:

```
(?=.*(gene1))(?=.*(gene2))
```

This code matches "gene1" AND "gene2" in any order.


#### Matching Specific Strings

If you're interested in all entries that match `mtd-2`, `mtd-3`, ..., `mtd-9`, but not `mtd-1` or `mtd-10`, you can use:

```
mtd-[2-9]
```

In this example, `mtd-` matches the text "mtd-", and `[2-9]` matches any single digit between 2 and 9. So, this would match `mtd-2`, `mtd-3`, ..., `mtd-9`.
___
