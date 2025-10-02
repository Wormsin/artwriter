import requests
import urllib.parse
import os
import json


def url_encoding(file_path):
    encoded_file = urllib.parse.quote(f"/{file_path}", safe="")
    return encoded_file


def create_folder(path: str):
    token = os.environ.get("YANDEX_OAuth_TOKEN")
    api_url = "https://cloud-api.yandex.net/v1/disk/resources"
    
    headers = {
        "Authorization": f"OAuth {token}"
    }
    params = {
        "path": path,
    }
    
    response = requests.put(api_url, headers=headers, params=params)
         
    return response.status_code

def save_file(disk_folder, file):
    token = os.environ.get("YANDEX_OAuth_TOKEN")
    path= f"/{disk_folder}/{file.filename}"
    api_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"

    headers = {
        "Authorization": f"OAuth {token}"
    }
    params = {
        "path": path
    }

    response = requests.get(api_url, headers=headers, params=params)
    print(response.json())
    href = response.json()["href"]
    response_saving = requests.put(href, data = file.file)

    return response_saving.status_code

def get_file(path):
    token = os.environ.get("YANDEX_OAuth_TOKEN")
    api_url = "https://cloud-api.yandex.net/v1/disk/resources/download"

    headers = {
        "Authorization": f"OAuth {token}"
    }
    params = {
        "path": path
    }

    response = requests.get(api_url, headers=headers, params=params)
    href = response.json()["href"]
    response_download = requests.get(href)

    return response_download.status_code
