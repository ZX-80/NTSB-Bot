<div align="center">
    
# NTSB Bot

![badge](https://badgen.net/badge/version/v5.0/orange?style=flat-square)
![badge](https://badgen.net/badge/platform/win-32%20|%20win-64/green?style=flat-square)
![badge](https://badgen.net/badge/python/3.10/blue?style=flat-square)

<p align = "center">
  <img width="350" src="https://user-images.githubusercontent.com/44975876/170371764-c7144f96-ad73-4d78-92b0-869c2fc259f9.png">
</p>

Produces markdown reports from the NTSB aviation accident database and uploads them to Reddit
    
[File Descriptions](#file-descriptions) •
[Images](#images)
    
</div>

# File Descriptions
* :file_folder: **Logs:** stores the logs from past submissions
* :file_folder: **Aviation_Data:** stores that months aviation data
    * :page_facing_up: **id_database.csv:** stores the incident IDs so the program knows what it's already uploaded
* :page_facing_up: **account.ini:** stores the login info for the bot
* 💾 **avdata.py:** downloads the latest NTSB aviation accident database
* 💾 **mdb_reader.py:** reads the relevent mdb files and creates the formatted reports to submit
* 💾 **NTSB_bot.py:** submits the reports generated by mdb_reader.py 

```mermaid
graph LR;
    0["NTSB AADB"] -.-> 1["avdata.py"] --> 2["mdb_reader.py"] --> 3["NTSB_bot.py"] -.-> 6["forum"]
    4["account.ini"]--> 3 --> 7["Logs"]
    5["id_database.csv"] --> 3
```

# Images

<div align="center">
    
  <img width="1426" alt="image" src="https://user-images.githubusercontent.com/44975876/170373681-bb7f0f2a-a050-4b6c-b138-f8949861f744.png">

</div>
