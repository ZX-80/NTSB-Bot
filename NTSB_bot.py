#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Post all new NTSB aviation accident database entries to a subreddit"""

import praw
import pathlib
import test_db_access as av_mdb
from datetime import datetime

verbose=True
def print_debug(text):
    global verbose
    if verbose:
        print(text)

def save_id_database():
    open('id_database.txt','w').write('\n'.join(id_database))

def post_incident(document):
    global subreddit
    print(document.ntsb_no)
    print_debug('    Submitting post')
    subreddit.submit(title=document.title, selftext=document.text)
    print_debug('        Post Submitted successfully\n')

login_file=open('login.txt','r')
REDDIT_USERNAME = login_file.readline().strip('\n')
REDDIT_PASS = login_file.readline().strip('\n')
user_agent = login_file.readline().strip('\n')
print_debug('Logging in as: '+REDDIT_USERNAME)
r = praw.Reddit(user_agent = user_agent,client_id=login_file.readline().strip('\n'),client_secret=login_file.readline().strip('\n'),username=REDDIT_USERNAME,password=REDDIT_PASS)
print_debug('    Login Succesful\n')
subreddit_name=login_file.readline().strip('\n')
subreddit = r.subreddit(subreddit_name)
subscriber_count = subreddit.subscribers
print('Subscriber Count[',subscriber_count,']')
id_database=[]
for line in open('id_database.txt','r'):
    id_database.append(line.strip('\n'))
titles=[]

update_count=0
for document in av_mdb.parse_events():
    try:
        if document.event_id not in id_database:
            post_incident(document)
            id_database.append(document.event_id)
            update_count+=1
    except Exception as e: 
        print(str(e))
        print('Invalid data!')
save_id_database()

#update sidebar with new date
time_string = datetime.now().strftime("%d/%m/%Y")
subreddit.mod.update(description=subreddit.description[:-10]+time_string)
update_count_text = f"Scan complete: Added {update_count} incidents!"
print(update_count_text)

#make a report to desktop
with open(pathlib.Path.home() / "Desktop" / "NTSB_Report.txt", 'w') as report_file:
    report_file.write(f"{update_count_text}\n{time_string}\nSubs: {subscriber_count}")
