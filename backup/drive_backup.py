"""
Devil ERP — Google Drive Backup
Serverless backup: DB + invoices + reports → Google Drive
Uses Google Drive API v3 with OAuth2.
"""
import os
import json
import shutil
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "devil_erp.db"
BACKUP_DIR = BASE_DIR / "backups"
CREDS_FILE = BASE_DIR / "auth" / "drive_credentials.json"
TOKEN_FILE = BASE_DIR / "auth" / "drive_token.json"
FOLDER_NAME = "DevilERP_Backups"


class DriveBackup:
    def __init__(self):
        BACKUP_DIR.mkdir(exist_ok=True)
        self._service = None
        self._folder_id = None

    def _get_service(self):
        if self._service:
            return self._service
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            SCOPES = ["https://www.googleapis.com/auth/drive.file"]
            creds = None
            if TOKEN_FILE.exists():
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(CREDS_FILE), SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                TOKEN_FILE.write_text(creds.to_json())
            self._service = build("drive", "v3", credentials=creds)
        except Exception as e:
            print(f"[Drive] Service init failed: {e}")
        return self._service

    def _get_or_create_folder(self):
        service = self._get_service()
        if not service:
            return None
        if self._folder_id:
            return self._folder_id
        try:
            results = service.files().list(
                q=f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                fields="files(id, name)"
            ).execute()
            files = results.get("files", [])
            if files:
                self._folder_id = files[0]["id"]
                return self._folder_id
            meta = {"name": FOLDER_NAME,
                    "mimeType": "application/vnd.google-apps.folder"}
            folder = service.files().create(body=meta, fields="id").execute()
            self._folder_id = folder["id"]
        except Exception as e:
            print(f"[Drive] Folder error: {e}")
        return self._folder_id

    def _upload_file(self, local_path: Path, remote_name: str):
        service = self._get_service()
        folder_id = self._get_or_create_folder()
        if not service or not folder_id:
            return False
        try:
            from googleapiclient.http import MediaFileUpload
            meta = {"name": remote_name, "parents": [folder_id]}
            media = MediaFileUpload(str(local_path))
            service.files().create(body=meta, media_body=media, fields="id").execute()
            return True
        except Exception as e:
            print(f"[Drive] Upload failed: {e}")
            return False

    def backup_now(self) -> dict:
        """Create timestamped backup of DB and push to Drive."""
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"devil_erp_{ts}.db"

        if not DB_PATH.exists():
            return {"success": False, "error": "Database not found"}

        shutil.copy2(str(DB_PATH), str(backup_path))
        success = self._upload_file(backup_path, f"devil_erp_{ts}.db")

        return {
            "success": success,
            "local_backup": str(backup_path),
            "timestamp": ts,
            "remote_name": f"devil_erp_{ts}.db"
        }

    def list_backups(self):
        service = self._get_service()
        folder_id = self._get_or_create_folder()
        if not service or not folder_id:
            return []
        try:
            results = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                orderBy="createdTime desc",
                fields="files(id, name, createdTime, size)"
            ).execute()
            return results.get("files", [])
        except Exception:
            return []

    def restore_backup(self, file_id: str, dest_path: str = None):
        service = self._get_service()
        if not service:
            return False
        try:
            from googleapiclient.http import MediaIoBaseDownload
            import io
            request = service.files().get_media(fileId=file_id)
            dest = dest_path or str(DB_PATH.parent / "restored_backup.db")
            with open(dest, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            return dest
        except Exception as e:
            print(f"[Drive] Restore failed: {e}")
            return False
