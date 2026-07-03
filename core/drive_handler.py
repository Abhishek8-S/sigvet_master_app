import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from core.config_loader import get_config

SCOPES = ['https://www.googleapis.com/auth/drive']
TARGET_FOLDER_ID = get_config().get('google_drive', {}).get('target_folder_id', '1z1f0s62R7g1WnD1sKo8UJxPaLwQHN_4Q')

def authenticate_gdrive():
    import glob
    config = get_config().get('google_drive', {})
    valid_path = None
    
    token_scan_dir = config.get('token_scan_dir', '/home/sigvet/')
    fallback_token = config.get('fallback_token_path', '/home/sandbox/skilled-bonus-152013-5339881607a7.json')
    
    # Check scan dir
    sigvet_tokens = glob.glob(os.path.join(token_scan_dir, '*.json'))
    if sigvet_tokens:
        valid_path = sigvet_tokens[0]
    
    # Developer fallback while in sandbox
    if not valid_path and os.path.exists(fallback_token):
        valid_path = fallback_token
            
    if not valid_path:
        return None
        
    try:
        creds = Credentials.from_service_account_file(valid_path, scopes=SCOPES)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Auth error: {e}")
        return None

def create_or_get_folder(service, parent_id, folder_name):
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    try:
        results = service.files().list(
            q=query, spaces='drive', fields='files(id, name)',
            supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        items = results.get('files', [])
        
        if not items:
            # Create folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            file = service.files().create(
                body=file_metadata, fields='id', supportsAllDrives=True
            ).execute()
            return file.get('id'), ""
        else:
            return items[0]['id'], ""
    except Exception as e:
        print(f"Error creating folder: {e}")
        return None, str(e)

def upload_report_to_drive(pdf_path, device_id, passed_tolerance=True):
    service = authenticate_gdrive()
    if not service:
        # Graceful fallback logging message if no credentials available
        return False, "Missing or invalid Google credentials. Mocked successful workflow log."
        
    try:
        # 1. Get/Create "Benchmark Results" folder
        benchmark_results_id, err_msg = create_or_get_folder(service, TARGET_FOLDER_ID, "Benchmark Results")
        if not benchmark_results_id:
            return False, f"Could not create 'Benchmark Results' subfolder! Error: {err_msg}"
            
        # 2. Get/Create "Passed Tolerance" or "Failed Tolerance" folder
        tol_folder_name = "Passed Tolerance" if passed_tolerance else "Failed Tolerance"
        tol_folder_id, err_msg_tol = create_or_get_folder(service, benchmark_results_id, tol_folder_name)
        if not tol_folder_id:
            return False, f"Could not create tolerance folder '{tol_folder_name}'! Error: {err_msg_tol}"
            
        # 3. Get/Create device id subfolder
        device_folder_id, err_msg_dev = create_or_get_folder(service, tol_folder_id, device_id)
        if not device_folder_id:
            return False, f"Could not create device folder '{device_id}' inside {tol_folder_name}! Error: {err_msg_dev}"
            
        # 4. Upload file with date and time formatting
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        new_file_name = f"{device_id}_{timestamp}.pdf"

        file_metadata = {
            'name': new_file_name,
            'parents': [device_folder_id]
        }
        media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=True)
        file = service.files().create(
            body=file_metadata, media_body=media, fields='id', supportsAllDrives=True
        ).execute()
        return True, f"Successfully uploaded {new_file_name} to Drive subfolder '{tol_folder_name}/{device_id}'!"
    except Exception as e:
        return False, f"Drive API Exception: {e}"
