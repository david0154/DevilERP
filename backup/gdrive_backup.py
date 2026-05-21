"""
Devil ERP — Google Drive Backup Module
Serverless architecture: Local DB + Google Drive = no server needed.
Backup includes: database, invoices, reports, AI data, user settings.
"""

import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from core.config import BASE_DIR, GDRIVE_CREDENTIALS_FILE, GDRIVE_BACKUP_FOLDER


class GoogleDriveBackup:
    def __init__(self):
        self._service = None

    def _get_service(self):
        """Authenticate and return Google Drive API service."""
        if self._service:
            return self._service
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        token_file = BASE_DIR / "backup" / "token.json"

        creds = None
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GDRIVE_CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open(token_file, 'w') as f:
                f.write(creds.to_json())
        from googleapiclient.discovery import build
        self._service = build('drive', 'v3', credentials=creds)
        return self._service

    def _create_backup_zip(self) -> Path:
        """Create a zip archive of all backup items."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"DevilERP_Backup_{timestamp}"
        zip_path = BASE_DIR / "backup" / f"{backup_name}.zip"
        zip_path.parent.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Database
            db_file = BASE_DIR / "database" / "devil_erp.sqlite"
            if db_file.exists():
                zf.write(db_file, "database/devil_erp.sqlite")
            # Reports
            reports_dir = BASE_DIR / "reports" / "exports"
            if reports_dir.exists():
                for f in reports_dir.rglob('*'):
                    zf.write(f, f.relative_to(BASE_DIR))
        return zip_path

    def backup_now(self) -> dict:
        """Perform manual backup to Google Drive."""
        try:
            zip_path = self._create_backup_zip()
            service = self._get_service()
            from googleapiclient.http import MediaFileUpload

            folder_id = self._get_or_create_folder(service)
            file_metadata = {'name': zip_path.name, 'parents': [folder_id]}
            media = MediaFileUpload(str(zip_path), mimetype='application/zip')
            file = service.files().create(
                body=file_metadata, media_body=media, fields='id'
            ).execute()

            zip_path.unlink()  # Remove local zip after upload
            return {"success": True, "file_id": file.get('id'), "name": zip_path.name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_or_create_folder(self, service) -> str:
        """Get or create DevilERP_Backups folder on Google Drive."""
        results = service.files().list(
            q=f"name='{GDRIVE_BACKUP_FOLDER}' and mimeType='application/vnd.google-apps.folder'",
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])
        if files:
            return files[0]['id']
        folder_metadata = {
            'name': GDRIVE_BACKUP_FOLDER,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')

    def list_backups(self) -> list:
        """List all available backups on Google Drive."""
        service = self._get_service()
        folder_id = self._get_or_create_folder(service)
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            orderBy="createdTime desc",
            fields="files(id, name, createdTime, size)"
        ).execute()
        return results.get('files', [])
