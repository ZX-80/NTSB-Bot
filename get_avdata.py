#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Downloads the latest NTSB aviation accident dataset"""

import os
import re
import requests
import zipfile

from bs4 import BeautifulSoup
from colorama import init, Fore, Style

from datetime import datetime
from dateutil.parser import parse as parsedate
from pathlib import Path
from urllib.parse import urljoin

init(autoreset=True)
requests.urllib3.disable_warnings(requests.urllib3.exceptions.InsecureRequestWarning)

def list_zip_files():
    """Fetch the names, urls, and dates of all files available.

    Returns
    -------
    list of tuple of string and string and datetime.datetime
        The file information for all zip files available.
    """
    url = 'https://data.ntsb.gov'
    page = requests.get(urljoin(url, 'avdata')).text
    soup = BeautifulSoup(page, 'html.parser')

    dates = [parsedate(node.string) for node in soup.find_all('td') if node.get('id') == "fileDate"]
    names = [node.string for node in soup.find_all('td') if node.get('id') == "fileName"]
    urls = [urljoin(url, node.get('href')) for node in soup.find_all('a')]
    return zip(names, urls, dates)

def get_download_bar(downloaded_bytes, total_bytes):
    """Create a download bar string.

    Parameters
    ----------
    downloaded_bytes : int
        This is the amount of bytes download so far.
    total_bytes : int
        This is the file size.

    Returns
    -------
    string
        The download bar string.
    """
    bar_length = 50
    percentage = downloaded_bytes / total_bytes
    bar_completed = '\N{full block}' * int(bar_length * percentage)
    return f"\r   {percentage:>4.0%} |{bar_completed:<{bar_length}}| {downloaded_bytes}/{total_bytes}"

def download_file(file_path, url):
    """Download a file from url.

    Parameters
    ----------
    file_path : pathlib.Path
        This is the filename and location to store the file.
    url : string
        This is the url to download the file from.

    Returns
    -------
    int
        The success of the request.
    """
    response = requests.get(url, verify=False, stream=True)
    if response.ok:
        total_bytes = response.headers.get('content-length')
        with open(file_path, 'wb') as fp:
            if total_bytes is None:
                fp.write(response.content)
                print(get_download_bar(1, 1))
            else:
                downloaded_bytes = 0
                for chunk in response.iter_content(chunk_size=8192):
                    downloaded_bytes += len(chunk)
                    fp.write(chunk)
                    print(get_download_bar(downloaded_bytes, int(total_bytes)), end='')
                print()
    else:
        print(f"    Error {response.status_code}:\n{response.text}")
    return response.ok


def unzip(file_path):
    """Unzip file_path to retrieve the Microsoft Access 2000 MDB file.

    Parameters
    ----------
    file_path : pathlib.Path
        This is the file to unzip.
    """
    with zipfile.ZipFile(file_path, "r") as zip_fp:
        zip_fp.extractall("avdata")
    os.remove(file_path)

def main():
    """Check for and download any new files for this month"""
    month_short  = datetime.today().strftime("%b").upper()
    file_pattern = re.compile(fr"((up[0-9][0-9]{month_short})|(avall))\.zip")
    records_path = Path(__file__).parent.resolve() / "avdata"
    records_path.mkdir(exist_ok=True)

    print(f"Searching for {file_pattern.pattern}")
    for file_name, url, server_file_date in list_zip_files():
        file_path = records_path / file_name
        computer_file_created_this_month = False
        if file_path.with_suffix(".mdb").exists():
            computer_file_date = datetime.fromtimestamp(file_path.with_suffix(".mdb").stat().st_mtime)
            computer_file_created_this_month = computer_file_date.month == datetime.today().month and computer_file_date.year == datetime.today().year
        server_file_created_this_month = server_file_date.month == datetime.today().month and server_file_date.year == datetime.today().year

        if file_path.with_suffix(".mdb").exists() and server_file_created_this_month and computer_file_created_this_month:
            print(Style.BRIGHT + Fore.GREEN + file_name)
            print("    File already exists")

        elif file_pattern.match(file_name):
            print(Style.BRIGHT + Fore.GREEN + file_name)
            if download_file(file_path, url):
                unzip(file_path)
        else:
            print(Style.BRIGHT + Fore.RED + file_name)

    print("Done.")

if __name__ == "__main__":
    main()
