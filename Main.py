import gspread
import os
import sys
import time
from functools import wraps

# ==========================================
# Configuration
# ==========================================
# Path to your Google Service Account JSON key file
SERVICE_ACCOUNT_FILE = #Enter JSON key file name here

# Spreadsheet ID or Name (Make sure the service account has access!)
# You can find the ID in the URL: docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
SPREADSHEET_ID = #Enter SPREADSHEET_ID here

# Sheet (Tab) Names and Column Headers
SOURCE_SHEET_NAME_1 = 'Data Bank 2026_r1'         # The tab containing the data to clean
SOURCE_COLUMN_HEADER_1 = 'STUDENT'        # The header of the column to clean

SOURCE_SHEET_NAME_2 = 'School Guardian data 2026 (class change)'         # The tab containing the data to clean
SOURCE_COLUMN_HEADER_2 = 'STUDENT'      # The header of the column to clean

BLACKLIST_SHEET_NAME = 'Graduated'   # The tab containing the blacklist
BLACKLIST_COLUMN_HEADER = 'Name'     # The header of the blacklist column

OUTPUT_SHEET_NAME = 'School(without Graduated)'   # The tab where cleaned data will be saved

# ==========================================
# Helper Functions
# ==========================================

def retry_api_call(max_retries=3, delay=5):
    """
    Decorator to retry API calls on failure.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f"  [Attempt {attempt + 1}/{max_retries}] API call failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
            print(f"  [Error] Max retries reached for {func.__name__}.")
            raise last_exception
        return wrapper
    return decorator

def clean_names(source_str, blacklist_set):
    """
    Splits source_str by comma, strips whitespace, filters out names in blacklist_set,
    and rejoins the result.
    Case-insensitive matching for blacklist.
    """
    if not source_str or not isinstance(source_str, str):
        return ""
    
    # Names match checking is handled by preparing the blacklist set beforehand
    
    names = source_str.split(',')
    cleaned_names = []
    
    for name in names:
        name_clean = name.strip()
        if not name_clean:
            continue
        # Check against lowercased blacklist set
        if name_clean.lower() not in blacklist_set:
            cleaned_names.append(name_clean)
            
    return ", ".join(cleaned_names)

@retry_api_call(max_retries=3, delay=5)
def fetch_all_values(worksheet):
    return worksheet.get_all_values()

def get_column_data(worksheet, column_header):
    """
    Fetches all data from a worksheet and extracts the specific column by header.
    Returns the column index (0-based) and the list of values (excluding header).
    """
    all_values = fetch_all_values(worksheet)
    if not all_values:
        raise ValueError(f"Sheet '{worksheet.title}' is empty.")
    
    headers = all_values[0]
    try:
        col_index = headers.index(column_header)
    except ValueError:
        raise ValueError(f"Column '{column_header}' not found in sheet '{worksheet.title}'.")
        
    # Extract data from that column, skipping the header
    data = [row[col_index] if len(row) > col_index else "" for row in all_values[1:]]
    return col_index, data, all_values

def main():
    # Authentication
    print("Authenticating with Google Sheets...")
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"Error: '{SERVICE_ACCOUNT_FILE}' not found. Please place your service account JSON file in this directory.")
        return

    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        # Set timeout to 300 seconds (5 minutes)
        print("Setting API timeout to 300 seconds...")
        gc.set_timeout(300)
        
        sh = gc.open_by_key(SPREADSHEET_ID) # Or gc.open(SPREADSHEET_NAME) if you prefer names
        print(f"Connected to spreadsheet: {sh.title}")
    except Exception as e:
        print(f"Authentication/Connection Error: {e}")
        return

    try:
        # Load Blacklist
        print(f"Loading blacklist from '{BLACKLIST_SHEET_NAME}'...")
        try:
            blacklist_ws = sh.worksheet(BLACKLIST_SHEET_NAME)
        except gspread.WorksheetNotFound:
            print(f"Error: Blacklist sheet '{BLACKLIST_SHEET_NAME}' not found.")
            return

        _, blacklist_data, _ = get_column_data(blacklist_ws, BLACKLIST_COLUMN_HEADER)
        
        # Create a set of lowercased blacklisted names for fast O(1) lookup
        blacklist_set = {name.strip().lower() for name in blacklist_data if name and name.strip()}
        print(f"Blacklist loaded: {len(blacklist_set)} unique names.")

        # Process Sources
        sources = [
            (SOURCE_SHEET_NAME_1, SOURCE_COLUMN_HEADER_1),
            (SOURCE_SHEET_NAME_2, SOURCE_COLUMN_HEADER_2)
        ]
        
        # Filter out unique (sheet, header) pairs to avoid redundant processing
        unique_sources = []
        seen_sources = set()
        for s, h in sources:
            if not s: continue
            if (s, h) not in seen_sources:
                unique_sources.append((s, h))
                seen_sources.add((s, h))
        
        all_cleaned_rows = []
        headers = None
        total_changes = 0

        for sheet_name, col_header in unique_sources:
            
            print(f"Processing source sheet '{sheet_name}'...")
            try:
                ws = sh.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                print(f"Warning: Source sheet '{sheet_name}' not found. Skipping.")
                continue

            target_col_index, source_col_data, all_source_rows = get_column_data(ws, col_header)
            
            # Use headers from the first sheet we successfully load
            if headers is None:
                headers = all_source_rows[0]
                all_cleaned_rows.append(headers)
            
            sheet_changes = 0
            for i, original_str in enumerate(source_col_data):
                original_row = all_source_rows[i + 1]
                cleaned_str = clean_names(original_str, blacklist_set)
                
                if cleaned_str != original_str:
                    sheet_changes += 1
                
                new_row = list(original_row)
                while len(new_row) <= target_col_index:
                    new_row.append("")
                new_row[target_col_index] = cleaned_str
                all_cleaned_rows.append(new_row)
            
            print(f"  - '{sheet_name}': Processed {len(source_col_data)} rows. Found {sheet_changes} cells requiring updates.")
            total_changes += sheet_changes

        if not all_cleaned_rows:
            print("No data was processed. Check your sheet names.")
            return

        # 4. Write to Output Sheet
        print(f"Writing to output sheet '{OUTPUT_SHEET_NAME}'...")
        try:
            output_ws = sh.worksheet(OUTPUT_SHEET_NAME)
            try:
                print(f"Attempting to clear existing sheet '{OUTPUT_SHEET_NAME}'...")
                output_ws.clear()
            except Exception as e:
                if "protected" in str(e).lower():
                    print(f"Warning: Cannot clear '{OUTPUT_SHEET_NAME}' because it contains protected cells.")
                    from datetime import datetime
                    new_sheet_name = f"Cleaned_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    print(f"Creating a new output sheet: '{new_sheet_name}'")
                    output_ws = sh.add_worksheet(title=new_sheet_name, rows=len(all_cleaned_rows)+100, cols=len(headers)+5)
                else:
                    raise e
        except gspread.WorksheetNotFound:
            print(f"Creating new sheet '{OUTPUT_SHEET_NAME}'...")
            # Use reasonable dimensions
            output_ws = sh.add_worksheet(title=OUTPUT_SHEET_NAME, rows=len(all_cleaned_rows)+100, cols=len(headers)+5)
        
        @retry_api_call(max_retries=3, delay=10)
        def update_sheet(ws, range_name, values):
            ws.update(range_name, values)

        update_sheet(output_ws, 'A1', all_cleaned_rows)
        print(f"Done! Cleaned data ({len(all_cleaned_rows)-1} total rows) has been saved. Total changes made: {total_changes}")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
