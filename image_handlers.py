#-------------------------------------------------------------------------------
# Name:        image_handlers
# Purpose: Code for saving image URL, should be called elsewhere
#
# Author:      User
#
# Created:     30/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------



# Libraries
import sqlalchemy
import re
import logging
# This project
from utils import *
from sql_functions import Media
import sql_functions
import config # User settings
# Media handler modules


def download_image_link(session,media_url):
    """Load an image link and hash the data recieved,
    then add an entry to the DB for the URL
    and if no match is found for the hash, save the file to disk"""
    media_already_saved = None # Init var to unknown
    logging.debug("download_image_link() ""Processing image: "+repr(media_url))

    # Check if URL is in the DB already, if so return hash.
    url_check_row_dict = sql_functions.check_if_media_url_in_DB(session,media_url)
    if url_check_row_dict:
        media_already_saved = True
        return url_check_row_dict["sha512base64_hash"]

    # Load URL
    file_data = get(media_url)
    if not file_data:
        logging.error("Could not load image URL!")
        return
    time_of_retreival = get_current_unix_time()

    # Generate hash
    sha512base64_hash = hash_file_data(file_data)

    # Generate filename for output file (With extention)
    cropped_full_image_url = media_url.split("?")[0]# Remove after ?
    full_image_filename = os.path.split(cropped_full_image_url)[1]
    extention = full_image_filename.split(".")[-1]
    image_filename = str(time_of_retreival)+"."+extention
    logging.debug("download_image_link() ""image_filename: "+repr(image_filename))
    file_path = generate_media_file_path_timestamp(root_path=config.root_path,filename=image_filename)
    logging.debug("download_image_link() ""file_path: "+repr(file_path))

    # Compare hash with database and add new entry for this URL
    hash_check_row_dict = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
    if hash_check_row_dict:
        media_already_saved = True
        image_filename = hash_check_row_dict["local_filename"]

    # Add new row
    new_media_row = Media(
        media_url=media_url,
        sha512base64_hash=sha512base64_hash,
        local_filename=image_filename,
        date_added=time_of_retreival,
        extractor_used="download_image_link",
        )
    session.add(new_media_row)
    session.commit()

    # If hash was already in DB, don't bother saving file
    if media_already_saved:
        logging.debug("Hash already in DB, no need to save file to disk")
    else:
        # Save file to disk, using the hash as a filename
        logging.debug("Hash was not in DB, saving file: "+repr(file_path))
        save_file(filenamein=file_path,data=file_data,force_save=False)
    session.commit()
    return sha512base64_hash


def download_image_links(session,media_urls):
    # Save image links
    media_urls = uniquify(media_urls)
    link_hash_dict = {}# {link:hash}
    for media_urls in media_urls:
        sha512base64_hash =  download_image_link(session,media_urls)
        link_hash_dict[media_urls] = sha512base64_hash# {link:hash}
        continue
    return link_hash_dict# {link:hash}





def main():
    pass

if __name__ == '__main__':
    main()
