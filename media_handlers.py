#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     05/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import hashlib# Needed to hash file data
import base64 # Needed to do base32 encoding of filenames
import re
import logging
from utils import *
from sql_functions import *
import config # User settings

def find_links_src(html):
    """Given string containing '<img src="http://media.tumblr.com/tumblr_m7g6koAnx81r3kwau.jpg"/>'
    return ['http://media.tumblr.com/tumblr_m7g6koAnx81r3kwau.jpg']
    """
    embed_regex = """<\w+?\s+?src=["']([^>]+)["']/>"""
    links = re.findall(embed_regex,html, re.DOTALL)
    logging.debug("src embed links: "+repr(links))
    return links


def find_url_links(html):
    """Find URLS in a string of text"""
    # Should return list of strings
    # Copied from:
    # http://stackoverflow.com/questions/520031/whats-the-cleanest-way-to-extract-urls-from-a-string-using-python
    # old regex http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+
    url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+~]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    links = re.findall(url_regex,html, re.DOTALL)
    assert(type(links) is type([]))# Should be list
    return links


def extract_post_links(post_dict):
    """Run all applicable extractors for a post"""
    links = []
    # Collect links in the post text
    html = post_dict["body"]
    links.append(find_links_src(html))
    links.append(find_url_links(html))
    # Collect links in
    logging.debug("all links found in post: "+repr(links))
    return links




def process_image_links(connection,post_dict, post_links):
    """Select which links to download and then try to save them"""
    logging.debug("Processing image links")
    logging.warning("disabled:image chooser")
    image_links = post_links
    for image_link in image_links:
        download_image_link(connection,image_link)
    return



def download_youtube_link(connection,post_link):
    """Download a youtube link"""
    # Call youtube_dl?
    # Insert info to DB
    return




def process_youtube_links(connection,post_dict,post_links):
    """Download youtube links"""
    youtube_domains = [
    "youtube.com"
    ]
    for youtube_domain in youtube_domains:
        for post_link in post_links:
            if youtube_domain in post_link:
                # Extract video ID
                video_id = ""
                # Check if video ID is in the DB
                logging.warning("disabled:video ID check")
                video_id_in_db = False # Disabled for coding FIXME
                # If ID is not in the DB, download it and add to DB
                download_youtube_link(connection,post_link)



def download_image_link(connection,media_url):
    """Load an image link and hash the data recieved,
    then add an entry to the DB for the URL
    and if no match is found for the hash, save the file to disk"""
    logging.debug("Processing image: "+repr(media_url))
    # Check if URL is in the DB already, if so return.
    # Load URL
    file_data = get(media_url)
    time_of_retreival = get_current_unix_time()
    # Generate hash
    sha512base64_hash = hash_file_data(file_data)
    # Generate filename for output file (With extention)
    cropped_full_image_url = media_url.split("?")[0]# Remove after ?
    full_image_filename = os.path.split(cropped_full_image_url)[1]
    extention = full_image_filename.split(".")[-1]
    image_filename = str(time_of_retreival)+"."+extention
    logging.debug("image_filename: "+repr(image_filename))
    file_path = generate_media_file_path_timestamp(root_path=config.root_path,filename=image_filename)
    logging.debug("file_path: "+repr(file_path))
    # Compare hash with database and add new entry for this URL
    media_already_saved = add_image_to_db(connection,media_url,sha512base64_hash,image_filename,time_of_retreival)
    # If hash was already in DB, return
    if media_already_saved:
        logging.debug("Hash already in DB, no need to save file to disk")
    else:
        # Save file to disk, using the hash as a filename
        logging.debug("Hash was not in DB, saving file: "+repr(file_path))
        save_file(filenamein=file_path,data=file_data,force_save=False)
    connection.commit()
    return





def hash_file_data(file_data):
    """Take the data from a file and hash it for deduplication
    Return a base32 encoded hash of the data"""
    m = hashlib.sha512()
    m.update(file_data)
    raw_hash = m.digest()
    logging.debug("raw_hash: "+repr(raw_hash))
    sha512base64_hash = base64.b64encode(raw_hash)
    sha512base32_hash = base64.b32encode(raw_hash)
    sha512base16_hash = base64.b16encode(raw_hash)
    logging.debug("sha512base64_hash: "+repr(sha512base64_hash))
    logging.debug("sha512base32_hash: "+repr(sha512base32_hash))
    logging.debug("sha512base16_hash: "+repr(sha512base16_hash))
    return sha512base64_hash

def generate_media_file_path_hash(root_path,filename):
    assert(len(filename) == 128)# Filenames should be of fixed length
    folder = filename[0:4]
    file_path = os.path.join(root_path,folder,filename)
    return file_path

def generate_media_file_path_timestamp(root_path,filename):
    first_four_chars = filename[0:4]
    second_two_chars = filename[4:6]
    file_path = os.path.join(root_path,first_four_chars,second_two_chars,filename)
    return file_path


def handle_media(connection,post_dict):
    """Encapsulate all functions relating to processing media"""
    logging.debug("Handling media and links")
    # Extract links from post
    post_links = extract_post_links(post_dict)
    logging.debug("post_links: "+repr(post_links))
    # Remove links that are already in the DB and store mappings for those that are
    old_link_mapping_dict = {} # {LINK:HASH}
    new_links = []
    for link_to_check in post_links:
        link_hash = check_if_link_in_db(cursor,media_url)
        if link_hash is None:# Put on queue to check if no record exists
            new_links.append(link_to_check)
        else:# Add exisiting mapping tif record ixists
            old_link_mapping_dict[link_to_check] = link_hash
    logging.debug("new_links: "+repr(new_links))
    logging.debug("old_link_mapping_dict: "+repr(old_link_mapping_dict))
    # Send links to a function for each type of media link
    image_mapping_dict = process_image_links(connection,post_dict,new_links)
    youtube_mapping_dict = process_youtube_links(connection,post_dict,new_links)
    # Join link to hash mappings # {LINK:HASH}
    link_to_hash_dict = merge_dicts(
    image_mapping_dict,
    youtube_mapping_dict
    )
    logging.debug("link_to_hash_dict: "+repr(link_to_hash_dict))
    return link_to_hash_dict







def main():
    pass
    setup_logging(log_file_path=os.path.join("debug","media-handlers-log.txt"))
    logging.debug("Opening DB connection")
    connection = mysql.connector.connect(**config.sql_login)
    download_image_link(connection,"https://derpicdn.net/spns/W1siZiIsIjIwMTQvMDEvMTAvMDJfNDBfMjhfNjUyX2RlcnBpYm9vcnVfYmFubmVyLnBuZyJdXQ.png")
    logging.debug("Closing DB connection")
    connection.close()

if __name__ == '__main__':
    main()
