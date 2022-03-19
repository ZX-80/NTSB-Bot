<div align="center">
    
# NTSB Bot

![badge](https://badgen.net/badge/version/v2.0.0/orange?style=flat-square)
![badge](https://badgen.net/badge/platform/win-32%20|%20win-64/green?style=flat-square)
![badge](https://badgen.net/badge/python/3/blue?style=flat-square)

Produces markdown reports from the NTSB, uploading them to Reddit
    
</div>

# Getting Started

tbd

# File Descriptions
* :file_folder: **Aviation_Data:** stores that months aviation data
* :page_facing_up: **id_database.txt:** stores the incident ids so the program knows what it's already uploaded
* :page_facing_up: **login.txt:** stores the login info for the bot
* :page_facing_up: **NTSB_bot.py:** the program

# Example Output
```
Logging in as: RedditUser27
    Login Succesful
    
list index out of range
Invalid data!
Scan complete: Added 0 incidents!
```
or
```
Logging in as: RedditUser27
    Login Succesful
    
20170116X24104
C:\Python27\lib\site-packages\requests\packages\urllib3\connectionpool.py:843: InsecureRequestW
arning: Unverified HTTPS request is being made. Adding certificate verification is strongly adv
ised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
InsecureRequestWarning)
Appending
    Submitting post
        Post Submitted succesfully
        
20170136X24104
C:\Python27\lib\site-packages\requests\packages\urllib3\connectionpool.py:843: InsecureRequestW
arning: Unverified HTTPS request is being made. Adding certificate verification is strongly adv
ised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
InsecureRequestWarning)
Appending
    Submitting post
        Post Submitted succesfully
        
list index out of range
Invalid data!
Scan complete: Added 2 incidents!

```
