import re
import os
import sys
import zipfile
import requests

from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colorama import init, Fore, Style
from datetime import datetime, timezone
from dateutil.parser import parse as parsedate

init(autoreset=True)
requests.urllib3.disable_warnings(requests.urllib3.exceptions.InsecureRequestWarning)

def list_zip_files():
    url = 'https://data.ntsb.gov'
    page = requests.get(urljoin(url, 'avdata')).text
    soup = BeautifulSoup(page, 'html.parser')

    dates = [parsedate(node.string) for node in soup.find_all('td') if node.get('id') == "fileDate"]
    names = [node.string for node in soup.find_all('td') if node.get('id') == "fileName"]
    urls = [urljoin(url, node.get('href')) for node in soup.find_all('a')]
    return zip(names, urls, dates)

def get_download_bar(downloaded_bytes, total_bytes):
    percentage = round(downloaded_bytes / total_bytes * 100, 2)
    bar_length = 50
    complete = '\N{full block}' * int(bar_length * percentage / 100)
    incomplete = ' ' * int(50 - bar_length * percentage / 100)
    return f"\r    |{complete}{incomplete}| {downloaded_bytes}/{total_bytes} ({percentage:.2f}%)"
                    

def download_file(file_path, url):
    response = requests.get(url, verify=False, stream=True)
    if response.ok:
        total_bytes = response.headers.get('content-length')
        with open(file_path, 'wb') as fp:
            if total_bytes is None:
                sys.stdout.write(get_download_bar(0, 1))
                fp.write(response.content)
                sys.stdout.write(get_download_bar(1, 1))
            else:
                downloaded_bytes = 0
                for chunk in response.iter_content(chunk_size=4096):
                    downloaded_bytes += len(chunk)
                    fp.write(chunk)
                    sys.stdout.write(get_download_bar(downloaded_bytes, int(total_bytes)))
                    sys.stdout.flush()
                sys.stdout.write('\n')
    else:
        print(Style.BRIGHT + Fore.RED + f"Error: status code {response.status_code}\n{response.text}")
    return response.ok


def unzip(file_path):
    with zipfile.ZipFile(file_path, "r") as zip_fp:
        zip_fp.extractall("avdata")
    os.remove(file_path)

if __name__ == "__main__":
    month_short  = datetime.today().strftime("%b").upper()
    file_pattern = re.compile(fr"((up[0-9][0-9]{month_short})|(avall))\.zip")
    records_path = Path(__file__).parent.resolve() / "avdata"
    records_path.mkdir(exist_ok=True)

    print(f"Searching for \"{file_pattern.pattern}")
    for file_name, url, file_date in list_zip_files():
        file_path = records_path / file_name
        file_created_this_month = file_date.month == datetime.today().month and file_date.year == datetime.today().year

        if file_path.with_suffix(".mdb").exists() and file_created_this_month:
            print(Style.BRIGHT + Fore.GREEN + file_name)
            print("    File already exists")

        elif file_pattern.match(file_name):
            print(Style.BRIGHT + Fore.GREEN + file_name)
            if download_file(file_path, url):
                unzip(file_path)
        else:
            print(Style.BRIGHT + Fore.RED + file_name)

    print("Done.")
