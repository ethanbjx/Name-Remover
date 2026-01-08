This Python script cleans comma-separated names in Google Sheets by removing blacklisted entries.
It reads data from up to 2 different sheets, compares names against a blacklist sheet, and writes the cleaned results to an output sheet.
It can be expanded to as many sheets as you want with some tweaks to the code.

It was created for my school's use, but if you find it useful, you're welcome to use it.

The script uses a Google Service Account and includes automatic retry logic to handle temporary API failures.
