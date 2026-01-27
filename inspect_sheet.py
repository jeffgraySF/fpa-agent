#!/usr/bin/env python3
"""Inspect specific cells in a Google Sheet."""

import pickle
from pathlib import Path
from googleapiclient.discovery import build

def get_credentials():
    token_path = Path('token.pickle')
    with open(token_path, 'rb') as token:
        return pickle.load(token)

def inspect_sheet(spreadsheet_id, sheet_name, range_spec="A1:J20"):
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!{range_spec}"
    ).execute()

    print(f"=== {sheet_name} ===\n")
    for i, row in enumerate(result.get('values', []), 1):
        print(f"{i}: {row}")

if __name__ == '__main__':
    spreadsheet_id = '1RfOxWa8VIqc9IDq3ySrxQmrQ2BgPC2MxhF4pjOz7Q2w'
    inspect_sheet(spreadsheet_id, 'Headcount Input', 'A1:I10')
