#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Post all new NTSB aviation accident database entries to a subreddit"""

import csv
import praw
import traceback
import configparser
import test_db_access as av_mdb

from pathlib import Path
from datetime import datetime

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

def post_incident(document, subreddit):
    print(document.ntsb_no)
    print('    Submitting post')
    subreddit.submit(title=document.title, selftext=document.text)
    print('        Post Submitted successfully\n')

def get_subreddit():
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(ACCOUNT_INFO_FILEPATH)
    print(f'Logging in as: {config["ACCOUNT INFO"]["username"]}')
    try:
        reddit = praw.Reddit(
            client_id=config["ACCOUNT INFO"]["client id"],
            client_secret=config["ACCOUNT INFO"]["client secret"],
            password=config["ACCOUNT INFO"]["password"],
            user_agent=config["ACCOUNT INFO"]["user agent"],
            username=config["ACCOUNT INFO"]["username"],
        )
        print('    Login Successful\n')
        return reddit.subreddit(config["ACCOUNT INFO"]["subreddit name"])
    except BaseException as err:
        traceback.print_exception(err)
        print('    Login Failed\n')
        return None

def update_sidebar_date(subreddit):
    time_string = datetime.now().strftime("%d/%m/%Y")
    subreddit.mod.update(description=subreddit.description[:-10]+time_string)

def scan_for_updates():
    success = 0
    fail = 0
    id_database = load_id_database()
    for document in av_mdb.parse_events():
        try:
            if document.event_id not in id_database:
                post_incident(document, subreddit)
                id_database.append(document.event_id)
                success += 1
        except BaseException as err:
            traceback.print_exception(err)
            fail += 1
    save_id_database(id_database)
    print(f"Scan complete: Added {success} incidents!")

if __name__ == "__main__":
    if (subreddit := get_subreddit()) != None:
        scan_for_updates(subreddit)
        update_sidebar_date(subreddit)
