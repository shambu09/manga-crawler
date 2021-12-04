"""
TODO: Write tests for the crawler.
"""
# import os
# import requests
# import json
# from dotenv import load_dotenv
# import io

# load_dotenv()
# from config import get_drive_service, public_put_file_to_folder_resumable, public_get_document_view_url

# bytesO = "haha"
# bytesO = bytes(bytesO.encode())
# print(len(bytesO))

# folder_id = os.environ.get("DATA_FOLDER_ID")
# file_name = "tmp.txt"

# drive, gauth = get_drive_service()
# _id = public_put_file_to_folder_resumable(drive, file_name, "text/plain", folder_id)

# print(public_get_document_view_url(_id))

# import logging

# logging.getLogger().setLevel(logging.INFO)
# from asyncio_blocks import Google_Drive

# ACCOUNT_SECRETS = os.environ.get("ACCOUNT_SECRETS")
# parent_id = os.environ.get("DATA_FOLDER_ID")

# from gdrive import Google_Drive
# Google_Drive.init(ACCOUNT_SECRETS)

# with open("spider/res/1/2.jpg", 'rb') as f:
#     file = io.BytesIO(f.read())

# file_id = Google_Drive.create_file("3.jpg", parent_id, file, "image/jpeg")
# logging.info(Google_Drive.get_public_url_file(file_id))
# # Google_Drive.delete_file(file_id)

# import pprint

# pp = pprint.PrettyPrinter(indent=6)
# pp.pprint(Google_Drive.find_file_by_id(file_id))

# for i in Google_Drive.get_file_list():
#     pp.pprint(i['title'])

# import json
# import os
# import sys

# sys.path.append("../")
# from gdrive.gdrive import Google_Drive

# from dotenv import load_dotenv

# load_dotenv("../.env")

# ACCOUNT_SECRETS = "../" + os.environ.get("ACCOUNT_SECRETS")
# PARENT_FOLDER_ID = os.environ.get("DATA_FOLDER_ID")

# with open("res.json", 'r') as f:
#     res = f.read()

# import io
# res = io.BytesIO(res.encode())

import json
import os

import requests
from dotenv import load_dotenv

from gdrive import Google_Drive
from main import METADATA_JSON, PARENT_FOLDER_ID

load_dotenv()
ACCOUNT_SECRETS = os.environ.get("ACCOUNT_SECRETS")
PARENT_FOLDER_ID = os.environ.get("DATA_FOLDER_ID")
METADATA_JSON = os.environ.get("METADATA_JSON")
Google_Drive.init(ACCOUNT_SECRETS)

# k = Google_Drive.download_json_file(METADATA_JSON)
# del k['hi']
# k = json.dumps(k, indent=6)
# Google_Drive.update_json_file(METADATA_JSON, k)

# print(Google_Drive.drive)
# import io
# import gc

# def hi():
#     f = io.BytesIO()
#     f.write(b"haha")

# print(gc.collect())

# --------------------------------------------------------------------------------
# print(Google_Drive.get_public_url_file(METADATA_JSON))

# k = Google_Drive.download_json_file(METADATA_JSON)

# updated = {}
# for i in k:
#     updated[Google_Drive.get_public_url_file(i)] = k[i]

# Google_Drive.update_json_file(METADATA_JSON, json.dumps(updated, indent=6))
# k = requests.get(Google_Drive.get_public_url_file(METADATA_JSON))
# print(json.loads(k.text))
#----------------------------------------------------------------------------------
# meta = Google_Drive.download_json_file(METADATA_JSON)

# for i in meta:
#     if i == "1DTtLO3BMZ51EdSrHQ78V9NjcMrf2FDwx": continue
#     g = Google_Drive.download_json_file(i)
#     for chap in g:
#         del chap["images"]
    
#     out = {
#         "title": meta[i],
#         "num_chapters": len(g),
#         "chapters": g,
#     }
#     Google_Drive.update_json_file(i, json.dumps(out, indent=6))
#----------------------------------------------------------------------------------
# j = Google_Drive.download_json_file("13iEugdhj_3MMsYOMpIKXQ4qNixsw1jg9")
# j = j["chapters"]

# assert isinstance(j, dict)
# Google_Drive.update_json_file("13iEugdhj_3MMsYOMpIKXQ4qNixsw1jg9", json.dumps(j, indent=6))
#----------------------------------------------------------------------------------