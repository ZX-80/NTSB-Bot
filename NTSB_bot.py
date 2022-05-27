#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Post all new NTSB aviation accident database entries to a subreddit"""

import csv
import praw
import traceback
import configparser
import test_db_access as av_mdb

from pathlib import Path
from datetime import datetime, date
from colorama import init, Fore, Back, Style

init(autoreset=True)

EPOCH = date.fromisoformat('2022-04-01') # YYYY-MM-DD
ID_DATABASE_FILEPATH = Path("id_database.csv")
ACCOUNT_INFO_FILEPATH = Path("account.ini")

def load_id_database():
    ID_DATABASE_FILEPATH.touch(exist_ok=True) # Create the ID database if it doesn't exist
    with open(ID_DATABASE_FILEPATH, 'r') as csv_fp:
        data = list(csv.reader(csv_fp))
        return data[0] if data else []

def save_id_database(id_database):
    with open(ID_DATABASE_FILEPATH, 'w') as csv_fp:
        csv.writer(csv_fp).writerow(id_database)

def get_subreddit():
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(ACCOUNT_INFO_FILEPATH)
    try:
        reddit = praw.Reddit(
            client_id=config["ACCOUNT INFO"]["client id"],
            client_secret=config["ACCOUNT INFO"]["client secret"],
            password=config["ACCOUNT INFO"]["password"],
            user_agent=config["ACCOUNT INFO"]["user agent"],
            username=config["ACCOUNT INFO"]["username"],
        )
        print(f'Logged in as {config["ACCOUNT INFO"]["username"]}')
        return reddit.subreddit(config["ACCOUNT INFO"]["subreddit name"])
    except BaseException as err:
        traceback.print_exception(err)
        return None

def get_download_bar(current_value, total_value):
    bar_length = 50
    percentage = current_value / total_value
    bar_completed = '\N{full block}' * int(bar_length * percentage)
    return f"\r   {percentage:>4.0%} |{bar_completed:<{bar_length}}| {current_value}/{total_value}"

def submit_new_documents(subreddit):
    failed = 0
    success = 0
    id_database = load_id_database()
    # TODO: Move filtering into av_mdb module
    valid_documents = [doc for doc in av_mdb.parse_events(EPOCH) if doc.event_id not in id_database]
    print("Submitting:")
    # TODO: use RotatingFileHandler?
    with open('submission_log.txt', 'w') as log_fp:
        for document in valid_documents:
            try:
                subreddit.submit(title=document.title, selftext=document.text)
                id_database.append(document.event_id)
                success += 1
            except BaseException as err:
                traceback.print_exception(err, file=log_fp)
                failed += 1
            errors_str = ' - ' + (Fore.RED + Style.DIM + f"ERR {failed}") if failed else ''
            print(get_download_bar(success + failed + 1, len(valid_documents)) + errors_str, end = '\r')
    save_id_database(id_database)
    print(f"\nScan complete: Added {success} incidents!")

def update_sidebar_date(subreddit):
    time_string = datetime.now().strftime("%d/%m/%Y")
    subreddit.mod.update(description=subreddit.description[:-10]+time_string)

if __name__ == "__main__":
    if (subreddit := get_subreddit()) is not None:
        submit_new_documents(subreddit)
        update_sidebar_date(subreddit)
