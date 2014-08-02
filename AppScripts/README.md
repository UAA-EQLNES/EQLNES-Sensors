# Google AppScripts for EQLNES Sensors

This directory contains Google AppScripts that process sensor readings from the
EQLNES Sensor platform. Sensors in the field currently sends text messages to
a Google Voice number, which then get forwarded to a GMail account for
processing. Because GMail labels entire threads and not individual emails, the
"starring" mechanism must be used to differentiate between processed and
unprocessed sensor readings. From there the Google AppScript will parse the
emails and store them in a Google SpreadSheet or Fusion Table.

`SMS to Sheets v2.gscript` is the only script that works with the current
message format, which contains a letter to represent the type of sensor and can
handle a varying number of readings per message.

The others have not been updated yet and can only process the old format, which
allowed two sensor readings and did not differentiate by the type of sensors.

## 1. Script descriptions

Each script does the same basic task of parsing GMail messages and storing them
in a spreadsheet or Fusion table, however there some differences in behavior,
such as file naming conventions and types of files created.

### 1.1 SMS to Sheets v2.gscript

This is the most up-to-date script that can parse the new message format.
Currently, all readings are stored in one spreadsheet.

The main drawback is that the spreadsheet may become unusable as the amount of
sensors and data grows. In addition, there is a lot of redundant data when
recording data from a single sensor platform.

### 1.2 SMS to Sheets.gscript

This script parses the old message format and creates a separate spreadsheet
for each sensor based on phone number.

### 1.3 SMS to Fusion.gscript

This scripts parses the old format and stores data in a Fusion table. This
allows for better performance and better ways to visualize data.

The main drawback is that Fusion tables is not that popular and could be
axed by Google. Another limitation may be data storage limits.

### 1.4 EQLNES Sensor SMS Bot.gscript.gscript

This script demonstrates how different storage backends can be swapped in and
out. Examples include Google Spreadsheets and Fusion tables. Another example
could be Twitter or a remote MySQL database.

## 2. Installation instructions

To use the Google AppScripts, a Google Account will be needed. A Google Voice
account is optional. You just need a way to get the sensor readings to GMail.

You may also need to enable Google AppScripts and Fusion Tables in your Drive
account. They can be added by clicking on the `Create Button` and then clicking
on `Connect More Apps`.

### 2.1 GMail setup

1. Create a filter that stars any emails with a subject that begins with
`SMS from (XXX) XXX-XXX`.
  - This is the format that Google Voice uses when forwarding text messages.
  - A simple, but broad rule that can be used is `SMS From *`

### 2.2 AppScript setup

**Create a new script**

1. From your Drive account, click `Script` and select `Blank Project`.
2. Name the project by clicking on `Untitled project`.
3. Paste in the script that you plan to use.

**Set project defaults**

1. Click `File` followed by `Project properties`.
2. Select the `Script properties` tab and add a property named `DEFAULT_NAME`.
This will be the name for the Spreadsheet or Fusion table. The only exception
is `SMS to Sheets.gscript`, which uses the sensor platform's phone number as
the title.

**Set script to run a regular intervals**

1. Click `Resources` and then `Current projects triggers`.
2. Click `No triggers set up. Click here to add one now.`
3. Select `main_program` for function to be called. The only exception is
`UA Sensor SMS Bot.gscript` where there are two options to choose from.
4. See the interval that the script should be run. Minimum is every minute, but
it would be best to select slower interval to prevent throttling errors.
5. Save trigger.
