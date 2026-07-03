from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']
creds_path='/home/sandbox/skilled-bonus-152013-5339881607a7.json'

try:
    print("Loading creds from", creds_path)
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    print("Building service...")
    service = build('drive', 'v3', credentials=creds)
    print("Calling API...")
    results = service.files().list(q="trashed=false", spaces='drive', fields='files(id, name)', pageSize=1).execute()
    print("Success! Discovered files:", results.get('files', []))
except Exception as e:
    import traceback
    traceback.print_exc()
