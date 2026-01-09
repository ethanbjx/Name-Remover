This Python script cleans comma-separated names in Google Sheets by removing blacklisted entries.
It reads data from up to 2 different sheets, compares names against a blacklist sheet, and writes the cleaned results to an output sheet.
It can be expanded to as many sheets as you want with some tweaks to the code.

It was created for my school's use, but if you find it useful, you're welcome to use it.

The script uses a Google Service Account and includes automatic retry logic to handle temporary API failures.

# Requirements

Python 3.8+

Git 2.0+

Google account with access to the target spreadsheet

# Installation
Install gspread Google authentication

	pip install gspread google-auth

## Google Service Account Setup

Go to Google Cloud Console

Create a Service Account

Generate a JSON key file

Download the file and place it in the same directory as the script

Share your Google Spreadsheet with the service account email
(looks like xxxx@project-id.iam.gserviceaccount.com)

Give it Editor access

# Steps to use
Open your command prompt

Clone the repository

	git clone  https://github.com/ethanbjx/Name-Remover/tree/main

Edit main.py by substituting the JSON file name, SHEET_ID, sheet name and column name

Go to the file locations in your cmd

	cd Name-Remover

Then run main.py

	python main.py

# Error Handling

Retries API calls automatically (configurable)

Missing sheets

Missing columns

Protected output sheets

Prints detailed error messages for debugging
