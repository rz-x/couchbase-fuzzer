import json
import requests
from requests.auth import HTTPBasicAuth
from base64 import b64decode
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# connect info
HOST_USER = "admin"
HOST_PASS = "password"
HOST_ADDR = "http://IP:8091"
HEADERS = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
BASE64CONTENT = "/Users/rzdonczyk/develop/poligon/couchbase_fuzzer/big-list-of-naughty-strings/blns.base64.txt"

# fuzz parameters
MIN_STRING_LENGHT = 3

# endpoint targets
ENDPOINTS = [
    "/settings/rbac/users/local/",
    "/settings/indexes/",
    "/pools/default/",
]
METHODS = ['PUT', 'POST']

def fuzz_endpoint(endpoint, method, f_user, f_roles):
    url = HOST_ADDR + endpoint + f_user
    data = f"roles={f_roles}&name={f_user}&password=admin123"
    
    try:
        if method == 'PUT':
            response = requests.put(url, data=data, headers=HEADERS, auth=HTTPBasicAuth(HOST_USER, HOST_PASS))
        elif method == 'POST':
            response = requests.post(url, data=data, headers=HEADERS, auth=HTTPBasicAuth(HOST_USER, HOST_PASS))
        # elif method == 'DELETE':
        #     response = requests.delete(url, headers=HEADERS, auth=HTTPBasicAuth(HOST_USER, HOST_PASS))
        else:
            logging.error(f"unsupported method: {method}")
            return

        response.raise_for_status()
    except requests.RequestException as err:
        logging.error(f"HTTP request failed: {err}")
        return

    if response.status_code != 200:
        logging.warning(f"HTTP response code: {response.status_code}")

    if len(response.text) > 2:
        logging.info(f"response: {response.text} \nData: {f_user} & {f_roles}")

def check_couchbase_status(endpoint, method, fuzz_word):
    try:
        response = requests.get(HOST_ADDR + "/pools/default", auth=HTTPBasicAuth(HOST_USER, HOST_PASS))
        response.raise_for_status()
        #logging.info("healthy")
    except requests.RequestException as err:
        logging.error(f"couchbase stopped responding: {err}")
        logging.info(f"[CRASH CANDIDATE] method: {method}, endpoint: {endpoint}, fuzz word: {fuzz_word}")
        # exit()

def read_file_and_fuzz(filepath):
    try:
        with open(filepath, 'r') as b64file:
            for line in b64file:
                if line.startswith("#"):
                    continue
                decoded_word = b64decode(line).decode('utf-8')
                if len(decoded_word) > MIN_STRING_LENGHT:
                    for endpoint in ENDPOINTS:
                        for method in METHODS:
                            fuzz_endpoint(endpoint, method, decoded_word, "query_external_access")
                            check_couchbase_status(endpoint, method, decoded_word)
    except IOError as err:
        logging.error(f"file error: {err}")

if __name__ == "__main__":
    read_file_and_fuzz(BASE64CONTENT)
