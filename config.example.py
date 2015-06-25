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
root_path = os.path.join("F:\\tumblrsagi","download")
#youtube_dl_path = os.path.join("/usr/local/bin/youtube-dl")# Path to the YT-DL executable
youtube_dl_path = os.path.join("youtube-dl", "youtube-dl.exe")# Path to the YT-DL executable
blog_list_path = "tumblr_todo_list.txt"
done_list_path = "done_list.txt"

# mysql://scott:tiger@hostname/dbname
#sqlalchemy_login = "sqlite:///local.db"
sqlalchemy_login = "postgresql://postgres:postgres@localhost/example"
#sqlalchemy_login = "sqlite:///local.db"#TODO FIXME!
# Echo SQL crap from SQLAlchemy?
echo_sql = True

#Tumblr API consumer key
consumer_key = "Tumblr API consumer key goes here"

# Multithread worker settings
number_of_post_grab_workers = 1 # How many post grabbing threads should be used at once?
number_of_media_workers = 1 # how many simultanious download threads should we have?

# Auto rerunner settings
get_posts_restart_delay = 60# Time in seconds to wait before restarting post getter
get_media_restart_delay = 60# Time in seconds to wait before restarting post getter
## 3600 - 1 hour

# Media download options
save_images = True
save_videos = True
save_audio = True
save_photos = True
save_all_photo_sizes = False# If save_photos is true, should all sizes be saved? (Default: False)
# Media that isn't from the API directly
save_external_links = True# Should things not provided directly by the API be saved?

# -max-filesize SIZE              Do not download any videos larger than SIZE (e.g. 50k or 44.6m)
youtube_dl_max_filesize = "1000m"

# Imgur API
imgur_client_id = "Imgur client ID goes here"
imgur_client_secret = "Imgue cliend secret goes here"



# When updating blog avatar, should the tumblr default avatars be skipped?
# ex. if a blog is deleted and the avatar reverts to default
skip_default_avatars = False

store_full_posts = True # Should the original post be saved back as raw json?

stop_loading_posts_when_timestamp_match = True

# Debug options
log_db_rows = True# Output each row to insert into the DB to the log file
max_pages_to_check = 1# Max number of api pages to load. Set to None when not debugging or you will miss almost all posts

# Logging messages, see table below for possible options
console_log_level = 10
# these numbers are defined in the logging library
##CRITICAL = 50
##FATAL = CRITICAL
##ERROR = 40
##WARNING = 30
##WARN = WARNING
##INFO = 20
##DEBUG = 10
##NOTSET = 0

def main():
    pass

if __name__ == '__main__':
    main()
