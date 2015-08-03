Tumblrsagi
Python automated archiver for Tumblr blogs


To add blogs to the DB:
Put blog URLs in "tumblr_todo_list.txt", one URL per line
Run add_blogs.py


To save the blogs in the DB takes several steps

Raw post text/JSON must be collected first by running get_posts.py

To fetch media related to posts and prepare posts for display, get_media.py must be run

WARNING:
Do not run multiple instances of any script at once!
Unexpected or destructive behavior may result from this.
Lockfiles are used to help prevent this.


External libraries required:
Requests

SQLAlchemy

HTMLParser

Executable version of youtube-dl

