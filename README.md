# folder-synchronizer
Simple tool for keeping two folders in the same state using Twisted web server

**Programming language:** Python3

Communication goes through **8880** port

When a **Client** takes a folder with existing data (files and other folders) as an argument, this data is transfered to a **Server**

**Preconditions:**
* Install [pywin32](https://sourceforge.net/projects/pywin32/) if running on Windows machine
* Install required modules ```pip install twisted treq```

How **Server** works:
* Does not have any console arguments to run with. Just execute ```python3 web_server.py```
* Runs from any folder
* Performs all files and folders changes received from **Client**'s side
* Creates a working root folder in it's local directory after connection with a **Client** is established
* Removes a working root folder adter a **Client** drops session

How **Client** works:
* **Client** usage example: ```python3 web_client.py <folder_path>```
* All files and folders changes are tracked on the **Client**'s side and sent to a **Server**

**Common:**
* To stop a **Server** or a **Client**, just press ```Enter``` in the command line
