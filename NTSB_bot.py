#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Post all new NTSB aviation accident database entries to a subreddit"""

import csv
import praw
import pathlib
import traceback
import configparser
import test_db_access as av_mdb

from datetime import datetime

def load_id_database():
    with open('id_database.csv', 'r') as csv_fp:
        return list(csv.reader(csv_fp))[0]

def save_id_database(id_database):
    with open('id_database.csv', 'w') as csv_fp:
        csv.writer(csv_fp).writerow(id_database)

def post_incident(document, subreddit):
    print(document.ntsb_no)
    print('    Submitting post')
    subreddit.submit(title=document.title, selftext=document.text)
    print('        Post Submitted successfully\n')

def get_subreddit():
    config = configparser.ConfigParser(allow_no_value=True)
    config.read("account.ini")
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

if (subreddit := get_subreddit()) != None:
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
    save_id_database()

    #update sidebar with new date
    time_string = datetime.now().strftime("%d/%m/%Y")
    subreddit.mod.update(description=subreddit.description[:-10]+time_string)
    update_count_text = f"Scan complete: Added {success} incidents!"
    print(update_count_text)

    #make a report to desktop
    with open(pathlib.Path.home() / "Desktop" / "NTSB_Report.txt", 'w') as report_file:
        report_file.write(f"{update_count_text}\n{time_string}\nSubs: {subreddit.subscribers}")
