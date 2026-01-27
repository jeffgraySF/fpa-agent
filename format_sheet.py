#!/usr/bin/env python3
"""Format Headcount Input sheet - font, number formats, freeze panes."""

import pickle
from pathlib import Path
from googleapiclient.discovery import build

def get_credentials():
    token_path = Path('token.pickle')
    with open(token_path, 'rb') as token:
        return pickle.load(token)

def get_sheet_id(service, spreadsheet_id, sheet_name):
    """Get the sheet ID for a given sheet name."""
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    raise ValueError(f"Sheet '{sheet_name}' not found")

def format_headcount_input(spreadsheet_id):
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    sheet_id = get_sheet_id(service, spreadsheet_id, 'Headcount Input')
    print(f"Formatting Headcount Input (sheet ID: {sheet_id})...")

    requests = []

    # 1. Set entire sheet to Roboto 10
    print("\n1. Setting font to Roboto 10...")
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
            },
            'cell': {
                'userEnteredFormat': {
                    'textFormat': {
                        'fontFamily': 'Roboto',
                        'fontSize': 10
                    }
                }
            },
            'fields': 'userEnteredFormat.textFormat(fontFamily,fontSize)'
        }
    })

    # 2. Bold header row (row 1)
    print("2. Bolding header row...")
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 0,
                'endRowIndex': 1
            },
            'cell': {
                'userEnteredFormat': {
                    'textFormat': {
                        'bold': True
                    }
                }
            },
            'fields': 'userEnteredFormat.textFormat.bold'
        }
    })

    # 3. Format date columns (D and E) as dates
    print("3. Formatting date columns...")
    # Column D (Start Date) - index 3
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 1,  # Skip header
                'startColumnIndex': 3,
                'endColumnIndex': 4
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        'type': 'DATE',
                        'pattern': 'M/d/yyyy'
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    })

    # Column E (End Date) - index 4
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 1,
                'startColumnIndex': 4,
                'endColumnIndex': 5
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        'type': 'DATE',
                        'pattern': 'M/d/yyyy'
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    })

    # 4. Format currency columns (F, G, H, I) as currency
    print("4. Formatting currency columns...")
    # Columns F-I (Salary, Bonus, Commission, Benefits) - indices 5-8
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 1,
                'startColumnIndex': 5,
                'endColumnIndex': 9
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        'type': 'CURRENCY',
                        'pattern': '"$"#,##0'
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    })

    # 5. Format monthly cost columns (J-AG, indices 9-32) as currency
    print("5. Formatting monthly cost columns as currency...")
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 1,
                'startColumnIndex': 9,
                'endColumnIndex': 33  # Column AG = index 32, so end at 33
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        'type': 'CURRENCY',
                        'pattern': '"$"#,##0'
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    })

    # 6. Format header row month columns (J1-AG1) as month-year
    print("6. Formatting header dates as MMM-YY...")
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 0,
                'endRowIndex': 1,
                'startColumnIndex': 9,
                'endColumnIndex': 33
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        'type': 'DATE',
                        'pattern': 'MMM-yy'
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    })

    # 7. Freeze row 1 and columns A-C
    print("7. Freezing header row and columns A-C...")
    requests.append({
        'updateSheetProperties': {
            'properties': {
                'sheetId': sheet_id,
                'gridProperties': {
                    'frozenRowCount': 1,
                    'frozenColumnCount': 3  # Freeze A, B, C (Name, Dept, Title)
                }
            },
            'fields': 'gridProperties.frozenRowCount,gridProperties.frozenColumnCount'
        }
    })

    # Execute all formatting requests
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    print("\n✓ Formatting complete!")
    print("\nApplied:")
    print("  - Font: Roboto 10 (entire sheet)")
    print("  - Header row: Bold")
    print("  - Date columns (D, E): M/d/yyyy format")
    print("  - Currency columns (F-I, J-AG): $#,##0 format")
    print("  - Header dates (J1-AG1): MMM-yy format")
    print("  - Frozen: Row 1, Columns A-C")

if __name__ == '__main__':
    spreadsheet_id = '1RfOxWa8VIqc9IDq3ySrxQmrQ2BgPC2MxhF4pjOz7Q2w'
    format_headcount_input(spreadsheet_id)
