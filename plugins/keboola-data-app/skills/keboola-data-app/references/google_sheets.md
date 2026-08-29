# Google Sheets Export Integration

Export data from Keboola Data App to Google Sheets using service account.

## Setup

1. Create service account in Google Cloud Console
2. Enable Google Sheets API and Google Drive API
3. Download JSON key file
4. Set environment variable:
   - `GOOGLE_SERVICE_ACCOUNT_JSON` - inline JSON string, or
   - `GOOGLE_SERVICE_ACCOUNT_FILE` - path to JSON file

## Initialize Service

```python
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "")

def get_google_sheets_service():
    """Get Google Sheets and Drive API services."""
    if not GOOGLE_SERVICE_ACCOUNT_JSON and not GOOGLE_SERVICE_ACCOUNT_FILE:
        return None, None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        # Load from file or env variable
        if GOOGLE_SERVICE_ACCOUNT_FILE and os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
            with open(GOOGLE_SERVICE_ACCOUNT_FILE, "r") as f:
                service_account_info = json.load(f)
        else:
            service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)

        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=scopes
        )

        sheets_service = build('sheets', 'v4', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)

        return sheets_service, drive_service

    except Exception as e:
        return None, None
```

## Create and Populate Spreadsheet

```python
def export_to_google_sheets(data: list[list], title: str, share_with: str = None) -> str | None:
    """
    Create spreadsheet with data and optionally share it.
    Returns spreadsheet URL or None on error.
    """
    sheets_service, drive_service = get_google_sheets_service()
    if not sheets_service:
        return None

    try:
        # Create spreadsheet
        spreadsheet_body = {
            "properties": {"title": title},
            "sheets": [{
                "properties": {
                    "title": "Data",
                    "gridProperties": {
                        "frozenRowCount": 1,  # Freeze header row
                        "frozenColumnCount": 1
                    }
                }
            }]
        }

        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
        spreadsheet_id = spreadsheet.get("spreadsheetId")
        spreadsheet_url = spreadsheet.get("spreadsheetUrl")

        # Write data
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Data!A1",
            valueInputOption="RAW",
            body={"values": data}
        ).execute()

        # Format header row
        requests = [
            {
                "repeatCell": {
                    "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.2},
                            "textFormat": {
                                "bold": True,
                                "foregroundColor": {"red": 1, "green": 1, "blue": 1}
                            }
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            },
            {
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": 0,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": len(data[0]) if data else 1
                    }
                }
            }
        ]

        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests}
        ).execute()

        # Share with user
        if share_with and drive_service:
            permission = {
                "type": "user",
                "role": "writer",
                "emailAddress": share_with
            }
            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                sendNotificationEmail=False
            ).execute()

        return spreadsheet_url

    except Exception as e:
        return None
```

## Requirements

Add to `requirements.txt`:
```
google-auth
google-api-python-client
```
