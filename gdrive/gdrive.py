import os
import requests
import json
from io import BytesIO
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
from google.auth.transport import requests as grequests
from google.oauth2 import service_account


class Authentication:
    ACCOUNT_SECRETS = None
    scope = None

    @classmethod
    def initialize_service(cls, ACCOUNT_SECRETS, scope):
        cls.ACCOUNT_SECRETS = ACCOUNT_SECRETS
        cls.scope = scope

    @classmethod
    def get_access_token(cls):
        ACCOUNT_SECRETS = cls.ACCOUNT_SECRETS
        scope = cls.scope

        credentials = service_account.Credentials.from_service_account_file(
            ACCOUNT_SECRETS, scopes=scope)
        credentials.refresh(grequests.Request())

        return credentials.token

    @classmethod
    def get_drive_service(cls):
        ACCOUNT_SECRETS = cls.ACCOUNT_SECRETS
        scope = cls.scope
        gauth = GoogleAuth()

        gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            ACCOUNT_SECRETS, scope)
        drive = GoogleDrive(gauth)

        return drive, gauth


class Google_Drive(Authentication):
    drive = None
    gauth = None
    PARENT_FOLDER_ID = None

    @classmethod
    def init(
        cls,
        ACCOUNT_SECRETS,
        PARENT_FOLDER_ID=None,
        scope=["https://www.googleapis.com/auth/drive"],
    ):
        cls.PARENT_FOLDER_ID = PARENT_FOLDER_ID
        cls.initialize_service(ACCOUNT_SECRETS, scope)
        cls.drive, cls.gauth = cls.get_drive_service()

    @classmethod
    def find_folder_by_name(cls, name):
        folder_id = None
        for file in cls.drive.ListFile({
                "q":
                "mimeType='application/vnd.google-apps.folder' and trashed=false"
        }).GetList():
            if file['title'] == name:
                folder_id = file['id']
                break

        return folder_id

    @classmethod
    def find_file_by_name(cls, name, folder_id):
        file_id = None
        for file in cls.drive.ListFile({
                'q':
                "'root' in parents and trashed=false"
        }).GetList():
            if file['title'] == name:
                file_id = file['id']
                break

        return file_id

    @classmethod
    def create_folder(cls, name, parent_id):
        folder = cls.drive.CreateFile({
            "title": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [{
                'id': parent_id
            }]
        })
        folder.Upload()
        folder_id = folder['id']
        return folder_id

    @classmethod
    def create_file(cls, name, parent_id, binary_data, mimetype):
        assert isinstance(binary_data, BytesIO)
        assert mimetype in [
            "image/jpeg",
            "image/png",
            "application/pdf",
            "textx/plain",
            "application/json",
        ]

        file = cls.drive.CreateFile()

        file["title"] = name
        file["parents"] = [{'id': parent_id}]
        file.content = binary_data
        file['mimeType'] = mimetype

        file.Upload()
        file_id = file['id']
        return file_id

    @classmethod
    def find_file_by_id(cls, id):
        file = cls.drive.CreateFile({'id': id})
        file.FetchMetadata()
        return file

    @classmethod
    def get_public_url_file(cls, file_id):
        return f"https://drive.google.com/uc?export=view&id={file_id}"

    @classmethod
    def get_public_view_url(cls, file_id):
        return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

    @classmethod
    def get_public_url_folder(cls, file_id):
        return f"https://drive.google.com/drive/folders/{file_id}?usp=sharing"

    @classmethod
    def delete_file(cls, file_id):
        file = cls.drive.CreateFile({'id': file_id})
        file.Delete()

    @classmethod
    def get_file_list(cls):
        return cls.drive.ListFile({
            'q': "'root' in parents and trashed=false"
        }).GetList()

    @classmethod
    def put_file_to_folder_resumable(
        cls,
        file_name,
        mimeType,
        folder_id,
        file_path=None,
        bytesO=None,
    ):
        access_token = cls.get_access_token()
        file_size = (bytesO and len(bytesO)) or os.path.getsize(file_path)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        metadata = {
            "name": file_name,
            "mimeType": mimeType,
            "parents": [folder_id]
        }

        r = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
            headers=headers,
            data=json.dumps(metadata))

        location = r.headers["Location"]

        headers = {
            "Content-Range":
            "bytes 0-" + str(file_size - 1) + "/" + str(file_size)
        }

        r = requests.put(
            location,
            headers=headers,
            data=bytesO or open(file_path, 'rb'),
        )

        file_id = r.json()["id"]
        return file_id

    @classmethod
    def make_file_public(cls, file_id):
        file = cls.drive.CreateFile({'id': file_id})
        file.FetchMetadata()
        new_permission = file.InsertPermission({
            'id': 'anyoneWithLink',
            'type': 'anyone',
            'value': 'anyoneWithLink',
            'withLink': True,
            'role': 'reader'
        })
        return new_permission
