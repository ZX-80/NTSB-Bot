#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Post all new NTSB aviation accident database entries to a subreddit"""

import csv
import praw
import logging
import configparser

import avdata
import mdb_reader

from pathlib import Path
from datetime import datetime, date
from colorama import init, Fore, Back, Style
from logging.handlers import RotatingFileHandler

init(autoreset=True)

DRY_RUN = True # No submissions will be made if true
EPOCH = date.fromisoformat("2022-04-01") # YYYY-MM-DD
ID_DATABASE_FILEPATH = Path("Aviation_Data/id_database.csv")
ACCOUNT_INFO_FILEPATH = Path("account.ini")

def load_id_database():
    ID_DATABASE_FILEPATH.touch() # Create the ID database if it doesn't exist
    with open(ID_DATABASE_FILEPATH, 'r') as csv_fp:
        data = list(csv.reader(csv_fp))
        return data[0] if data else []

def save_id_database(id_database):
    with open(ID_DATABASE_FILEPATH, 'w') as csv_fp:
        csv.writer(csv_fp).writerow(id_database)

def get_subreddit():
    config = configparser.ConfigParser(allow_no_value=True)
    try:
        config.read(ACCOUNT_INFO_FILEPATH)
        reddit = praw.Reddit(
            client_id=config["ACCOUNT INFO"]["client id"],
            client_secret=config["ACCOUNT INFO"]["client secret"],
            password=config["ACCOUNT INFO"]["password"],
            user_agent=config["ACCOUNT INFO"]["user agent"],
            username=config["ACCOUNT INFO"]["username"],
        )
        reddit.validate_on_submit = True
        print(f'Logged in as {Style.BRIGHT + Fore.GREEN + config["ACCOUNT INFO"]["username"]}')
        return reddit.subreddit(config["ACCOUNT INFO"]["subreddit name"])
    except Exception: # Don't catch KeyboardInterrupt
        logging.exception("Login Exception")
        return None

def get_upload_bar(current_value, total_value):
    bar_length = 50
    percentage = (current_value / total_value) if total_value != 0 else 1.0
    bar_completed = "\N{full block}" * int(bar_length * percentage)
    return f"\r   {percentage:>4.0%} |{bar_completed:<{bar_length}}| {current_value}/{total_value}"

def submit_new_documents(subreddit, relevant_mdb_filepaths):
    id_database = load_id_database()
    total_success = 0
    for relevant_mdb_filepath in relevant_mdb_filepaths:
        failed = 0
        succeeded = 0
        skipped = 0
        errors_str= ''
        doc_generator = mdb_reader.parse_events(EPOCH, relevant_mdb_filepath)
        documents_len = next(doc_generator)
        print(f"\nSubmitting {Style.BRIGHT + Fore.GREEN + relevant_mdb_filepath.name}:")
        print(get_upload_bar(0, documents_len), end = '\r')
        for document in doc_generator:
            if document.event_id not in id_database: # TODO: Move filtering into mdb_reader module
                try:
                    if not DRY_RUN: subreddit.submit(title=document.title, selftext=document.text)
                    id_database.append(document.event_id)
                    if not DRY_RUN: save_id_database(id_database)
                    succeeded += 1
                except Exception: # Don't catch KeyboardInterrupt
                    logging.exception("Submission Exception")
                    failed += 1
                    errors_str = " - " + (Style.BRIGHT + Fore.RED + f"ERR {failed}")
            else:
                skipped += 1
            print(get_upload_bar(succeeded + failed + skipped, documents_len) + errors_str, end = '\r')
        print()
        total_success += succeeded
    print(f"\nScan complete: Added {total_success} incidents!")

def update_sidebar_date(subreddit):
    print("Updating sidebar: ", end='')
    try:
        time_string = datetime.now().strftime("%d/%m/%Y")
        sidebar = subreddit.wiki["config/sidebar"]
        sidebar.edit(content=subreddit.description[:-10]+time_string)
    except Exception: # Don't catch KeyboardInterrupt
        logging.exception("Sidebar Exception")
        print(Style.BRIGHT + Fore.RED + "ERR - ", end='')
    print("done")

# Initialize logging
logs_path = Path(__file__).parent.resolve() / "Logs"
logs_path.mkdir(exist_ok=True)
file_handler = RotatingFileHandler(logs_path / "log.txt", maxBytes=1024*512, backupCount=1) # 2 x 512K log files
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s"))
logging.root.addHandler(file_handler)
logging.basicConfig(level=logging.NOTSET)

if __name__ == "__main__":
    logging.info("Program started.")
    relevant_mdb_filepaths = avdata.update()
    if (subreddit := get_subreddit()) is not None:
        submit_new_documents(subreddit, relevant_mdb_filepaths)
        if not DRY_RUN: update_sidebar_date(subreddit)
