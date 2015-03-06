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




def process_image_links(post_links):
    """Select which links to download and then try to save them"""
    logging.debug("Processing image links")
    image_links = post_links
    for image_link in image_links:
        download_image_link(image_link)
    return post_links # During coding, just save everything. FIXME


def download_image_link(image_link):
    """Load an image link and hash the data recieved,
    then add an entry to the DB for the URL
    and if no match is found for the hash, save the file to disk"""
    logging.debug("Processing image: "+repr(image_link))
    # Check if URL is in the DB already, if so return.
    # Load URL
    file_data = get(image_link)
    # Generate hash
    sha512base32_hash = hash_file_data(file_data)
    logging.debug("sha512base32_hash: "+repr(sha512base32_hash))
    # Generate filename for output file (With extention)
    cropped_full_image_url = image_link.split("?")[0]# Remove after ?
    full_image_filename = os.path.split(cropped_full_image_url)[1]
    extention = full_image_filename.split(".")[-1]
    filename = sha512base32_hash+extention
    logging.debug("filename: "+repr(filename))
    # Compare hash with database and add new entry for this URL
    # If hash was already in DB, return
    # Save file to disk, using the hash as a filename
    return


def hash_file_data(file_data):
    """Take the data from a file and hash it for deduplication
    Return a base32 encoded hash of the data"""
    m = hashlib.sha512()
    m.update(file_data)
    raw_hash = m.digest()
    logging.debug("raw_hash: "+repr(raw_hash))
    sha512base32_hash = base64.b32encode(raw_hash)
    sha512base16_hash = base64.b16encode(raw_hash)
    logging.debug("sha512base32_hash: "+repr(sha512base32_hash))
    logging.debug("sha512base16_hash: "+repr(sha512base16_hash))
    return sha512base32_hash

def generate_media_file_path(root_path,filename):
    assert(len(filename) == 128)# Filenames should be of fixed length
    folder = filename[0:16]
    file_path = os.path.join(root_path,folder,filename)
    return file_path


def handle_media(post_dict):
    """Encapsulate all functions relating to processing media"""
    logging.debug("Handling media and links")
    # Extract links from post
    post_links = extract_post_links(post_dict)
    # Send links to a function for each type of media link
    process_image_links(post_links)
    return







def main():
    pass
    setup_logging(log_file_path=os.path.join("debug","media-handlers-log.txt"))
    download_image_link("https://derpicdn.net/spns/W1siZiIsIjIwMTQvMDEvMTAvMDJfNDBfMjhfNjUyX2RlcnBpYm9vcnVfYmFubmVyLnBuZyJdXQ.png")

if __name__ == '__main__':
    main()
