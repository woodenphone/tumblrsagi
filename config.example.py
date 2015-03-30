#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     15/02/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os # for cross-platform paths




# File paths
root_path = os.path.join("download")
youtube_dl_path = os.path.join("/usr/local/bin/youtube-dl")# Path to the YT-DL executable
blog_list_path = "input_list.txt"



sqlalchemy_login = "sqlite:///tutorial.db"#TODO FIXME!
echo_sql = False # Echo SQL crap from SQLAlchemy?

#Tumblr API consumer key
consumer_key = "KEYGOesHEre"


# Media download options
save_images = True
save_videos = True
save_audio = True
save_photos = True
save_all_photo_sizes = False# If save_photos is true, should all sizes be saved?

save_external_links = True# Should things not provided directly by the API be saved?

# Debug options
log_db_rows = False# Output each row to insert into the DB to the log file




def main():
    pass

if __name__ == '__main__':
    main()
