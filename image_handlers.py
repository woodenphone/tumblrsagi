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
    remote_filename = os.path.basename(cropped_full_image_url)
    file_extention = get_file_extention(remote_filename)
    if not file_extention:
        logging.error("download_image_link() No file extention!")
        logging.error(repr(locals()))
        assert(False)# Something broke and then called this
    local_filename = generate_filename(ext=file_extention,hash=sha512base64_hash)
    logging.debug("download_image_link() ""local_filename: "+repr(local_filename))
    file_path = generate_path(root_path=config.root_path,filename=local_filename)
    logging.debug("download_image_link() ""file_path: "+repr(file_path))

    # Compare hash with database and add new entry for this URL
    hash_check_row_dict = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
    if hash_check_row_dict:
        media_already_saved = True
        local_filename = hash_check_row_dict["local_filename"]

    # Add new row
    new_media_row = Media(
        media_url=media_url,
        sha512base64_hash=sha512base64_hash,
        local_filename=local_filename,
        remote_filename = remote_filename,
        file_extention=file_extention,
        date_added=time_of_retreival,
        extractor_used="image_handlers.download_image_link()",
        )
    session.add(new_media_row)
    session.commit()

    # If hash was already in DB, don't bother saving file
    if media_already_saved:
        logging.debug("Hash already in DB, no need to save file to disk")
    else:
        # Save file to disk, using the hash as a filename
        logging.debug("Hash was not in DB, saving file: "+repr(file_path))
        save_file(
            file_path=file_path,
            data=file_data,
            force_save=False,
            allow_fail=False
            )
    session.commit()
    return sha512base64_hash


def download_image_links(session,media_urls):
    # Save image links
    media_urls = uniquify(media_urls)
    link_hash_dict = {}# {link:hash}
    for media_url in media_urls:
        sha512base64_hash =  download_image_link(session,media_url)
        if sha512base64_hash:
            link_hash_dict[media_url] = sha512base64_hash# {link:hash}
        continue
    return link_hash_dict# {link:hash}





def main():
    pass

if __name__ == '__main__':
    main()
