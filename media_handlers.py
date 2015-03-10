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
    # Mangle dicts and lists into strings
    flat_post_dict = flatten(post_dict)
    for field in flat_post_dict:
        logging.debug("field: "+repr(field))
        # Text fields
        if ( (type(field) == type("")) or (type(field) == type(u"")) ):
            html = field
            logging.debug("html: "+repr(html))
            links += find_links_src(field)
            links += find_url_links(field)
    #elif ( (type(field) == type({})) or (type(field) == type([])) ):
    logging.debug("all links found in post: "+repr(links))
    return links


##def process_image_links(connection,post_dict, post_links):
##    """Select which links to download and then try to save them"""
##    logging.debug("Processing image links")
##    logging.warning("disabled:image chooser")
##    image_links = post_links
##    for image_link in image_links:
##        download_image_link(connection,image_link)
##    return



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
    return sha512base64_hash


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


##def handle_media(connection,post_dict):
##    """Encapsulate all functions relating to processing media"""
##    logging.debug("Handling media and links")
##    # Extract links from post
##    post_links = extract_post_links(post_dict)
##    logging.debug("post_links: "+repr(post_links))
##    # Remove links that are already in the DB and store mappings for those that are
##    old_link_mapping_dict = {} # {HASH:LINK}
##    new_links = []
##    for link_to_check in post_links:
##        link_hash = check_if_link_in_db(cursor,media_url)
##        if link_hash is None:# Put on queue to check if no record exists
##            new_links.append(link_to_check)
##        else:# Add exisiting mapping tif record ixists
##            old_link_mapping_dict[link_to_check] = link_hash
##    logging.debug("new_links: "+repr(new_links))
##    logging.debug("old_link_mapping_dict: "+repr(old_link_mapping_dict))
##    # Send links to a function for each type of media link
##    image_mapping_dict = process_image_links(connection,post_dict,new_links)
##    youtube_mapping_dict = process_youtube_links(connection,post_dict,new_links)
##    # Join link to hash mappings # {LINK:HASH}
##    link_to_hash_dict = merge_dicts(
##    image_mapping_dict,
##    youtube_mapping_dict
##    )
##    logging.debug("link_to_hash_dict: "+repr(link_to_hash_dict))
##    return link_to_hash_dict


##def download_media(cursor,media_url):
##    """Download a new link"""
##    # Images
##    media_hash = download_image_link(connection,image_link)
##    return media_hash


##def handle_media(connection,post_dict):
##    handle_images(connection,post_dict)
##    # Iterate through post fields and find links
##    fields_to_check = ["body",]
##    for field_to_check in fields_to_check:
##        try:
##            original_field_data = post_dict[field_to_check]
##        except KeyError, err:
##            continue
##        # EFind all links in the field
##        field_links = extract_field_links(original_field_data)
##        # Process each link in the field
##        for link in field_links:
##            # Lookup link in DB
##            link_hash = check_if_link_in_db(cursor,media_url)
##            if link_hash is None:
##                # Download unknown link
##                link_hash = download_media(cursor,media_url)
##            else:
##                pass # No need to redownload
##            # Replace link with identifier and hash "%%LINK=HASH_HASH_HASH%%/LINK%%
##            new_field_data = original_field_data
##        # Overwrite old field
##        post_dict[field_to_check] = new_field_data
##    # Send back updated post
##    return post_dict


def replace_links(link_dict,post_dict):
    """Replace all instances of a link in a post with a marker string for whoever does the frontend
    link_dict = {link:hash}
    post_dict = {field:_datastring}
    Return post dict with links replaced
    """
    new_post_dict = post_dict# Copy over everything so any fields without links
    marker_prefix = "%%LINK="
    marker_suffix = "%KNIL%%"
    for link in link_dict:
        for field in post_dict:
            # String replacement
            new_link_string = marker_prefix+link+marker_suffix
            field = string.replace(field, link, new_link_string)
            field = field
    return post_dict


def handle_image_links(connection,all_post_links):
    """Check and save images linked to by a post
    return link_hash_dict = {}# {link:hash}"""
    logging.debug("all_post_links"+repr(all_post_links))
    # Find all links in post dict
    # Select whick links are image links
    link_extentions = [
    "jpg","jpeg",
    "gif",
    "png",
    ]
    image_links = []
    for link in all_post_links:
        after_last_dot = link.split(".")[-1]
        before_first_q_mark = after_last_dot.split("?")[0]
        for extention in link_extentions:
            if extention in before_first_q_mark:
                image_links.append(link)
    # Save image links
    link_hash_dict = {}# {link:hash}
    for image_link in image_links:
        sha512base64_hash =  download_image_link(connection,image_link)
        link_hash_dict[image_link] = sha512base64_hash# {link:hash}
        continue
    return link_hash_dict


def save_media(connection,post_dict):
    logging.info("Saving post media")
    logging.debug("post_dict"+repr(post_dict))
    # Get list of links
    all_post_links = extract_post_links(post_dict)
    logging.debug("all_post_links"+repr(all_post_links))
    # Remove links already in DB
    preexisting_link_dict = {}# TODO FIXME
    logging.debug("preexisting_link_dict"+repr(preexisting_link_dict))
    new_links = []
    preexisting_links = preexisting_link_dict.keys()
    for post_link in all_post_links:
        if post_link in preexisting_links:
            continue
        else:
            new_links.append(post_link)
    logging.debug("new_links"+repr(new_links))
    # Save image links
    image_link_dict = handle_image_links(connection,new_links)
    # Join mapping dicts
    link_to_hash_dict = merge_dicts(
    preexisting_link_dict,
    image_link_dict,
    )
    logging.debug("link_to_hash_dict"+repr(link_to_hash_dict))
    # Replace links with marker string
    new_post_dict = replace_links(link_to_hash_dict,post_dict)
    new_post_dict["link_to_hash_dict"] = link_to_hash_dict
    logging.debug("new_post_dict"+repr(new_post_dict))
    return new_post_dict




def main():
    pass
    setup_logging(log_file_path=os.path.join("debug","media-handlers-log.txt"))
    logging.debug("Opening DB connection")
    connection = mysql.connector.connect(**config.sql_login)
    post_dict = {u'highlighted': [], u'reblog_key': u'RSNOnudd', u'format': u'html', u'timestamp': 1401396780, u'note_count': 429, u'tags': [u'porn', u'furry', u'anthro', u'art', u'fantasy', u'compilation', u'myart', u'futa', u'female', u'nude', u'werewolf'], 'link_to_hash_dict': {}, u'photos': [{u'caption': u'My character Gwen, the hermaphrodite Unicorn. Short for I Guinevere.', u'original_size': {u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_1280.jpg', u'width': 1280, u'height': 1739}, u'alt_sizes': [{u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_1280.jpg', u'width': 1280, u'height': 1739}, {u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_500.jpg', u'width': 500, u'height': 679}, {u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_400.jpg', u'width': 400, u'height': 543}, {u'url': u'http://40.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_250.jpg', u'width': 250, u'height': 340}, {u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_100.jpg', u'width': 100, u'height': 136}, {u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'A young man and one of his harem concubines.', u'original_size': {u'url': u'http://40.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_1280.jpg', u'width': 1280, u'height': 1037}, u'alt_sizes': [{u'url': u'http://40.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_1280.jpg', u'width': 1280, u'height': 1037}, {u'url': u'http://40.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_500.jpg', u'width': 500, u'height': 405}, {u'url': u'http://41.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_400.jpg', u'width': 400, u'height': 324}, {u'url': u'http://40.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_250.jpg', u'width': 250, u'height': 203}, {u'url': u'http://41.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_100.jpg', u'width': 100, u'height': 81}, {u'url': u'http://40.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'Gift-art for Robotjoe at FA.', u'original_size': {u'url': u'http://40.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_1280.jpg', u'width': 1280, u'height': 1280}, u'alt_sizes': [{u'url': u'http://40.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_1280.jpg', u'width': 1280, u'height': 1280}, {u'url': u'http://41.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_500.jpg', u'width': 500, u'height': 500}, {u'url': u'http://41.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_400.jpg', u'width': 400, u'height': 400}, {u'url': u'http://41.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_250.jpg', u'width': 250, u'height': 250}, {u'url': u'http://40.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_100.jpg', u'width': 100, u'height': 100}, {u'url': u'http://40.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'Giftart for Ritts at FA.', u'original_size': {u'url': u'http://41.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_1280.jpg', u'width': 1280, u'height': 1152}, u'alt_sizes': [{u'url': u'http://41.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_1280.jpg', u'width': 1280, u'height': 1152}, {u'url': u'http://40.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_500.jpg', u'width': 500, u'height': 450}, {u'url': u'http://40.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_400.jpg', u'width': 400, u'height': 360}, {u'url': u'http://40.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_250.jpg', u'width': 250, u'height': 225}, {u'url': u'http://40.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_100.jpg', u'width': 100, u'height': 90}, {u'url': u'http://41.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'', u'original_size': {u'url': u'http://41.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_1280.jpg', u'width': 1153, u'height': 1920}, u'alt_sizes': [{u'url': u'http://41.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_1280.jpg', u'width': 1153, u'height': 1920}, {u'url': u'http://40.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_500.jpg', u'width': 450, u'height': 750}, {u'url': u'http://40.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_400.jpg', u'width': 360, u'height': 600}, {u'url': u'http://40.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_250.jpg', u'width': 240, u'height': 400}, {u'url': u'http://41.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_100.jpg', u'width': 100, u'height': 167}, {u'url': u'http://36.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'She shot herself in the face, or did others? Up to you.', u'original_size': {u'url': u'http://41.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_1280.jpg', u'width': 841, u'height': 1400}, u'alt_sizes': [{u'url': u'http://41.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_1280.jpg', u'width': 841, u'height': 1400}, {u'url': u'http://40.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_500.jpg', u'width': 451, u'height': 750}, {u'url': u'http://41.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_400.jpg', u'width': 360, u'height': 600}, {u'url': u'http://40.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_250.jpg', u'width': 240, u'height': 400}, {u'url': u'http://40.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_100.jpg', u'width': 100, u'height': 166}, {u'url': u'http://36.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u"They're now twins.", u'original_size': {u'url': u'http://36.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_1280.jpg', u'width': 1153, u'height': 1920}, u'alt_sizes': [{u'url': u'http://36.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_1280.jpg', u'width': 1153, u'height': 1920}, {u'url': u'http://36.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_500.jpg', u'width': 450, u'height': 750}, {u'url': u'http://41.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_400.jpg', u'width': 360, u'height': 600}, {u'url': u'http://40.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_250.jpg', u'width': 240, u'height': 400}, {u'url': u'http://41.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_100.jpg', u'width': 100, u'height': 167}, {u'url': u'http://41.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'This is knot a funny joke.', u'original_size': {u'url': u'http://36.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_1280.jpg', u'width': 1000, u'height': 1000}, u'alt_sizes': [{u'url': u'http://36.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_1280.jpg', u'width': 1000, u'height': 1000}, {u'url': u'http://40.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_500.jpg', u'width': 500, u'height': 500}, {u'url': u'http://40.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_400.jpg', u'width': 400, u'height': 400}, {u'url': u'http://36.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_250.jpg', u'width': 250, u'height': 250}, {u'url': u'http://40.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_100.jpg', u'width': 100, u'height': 100}, {u'url': u'http://40.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'Gift-art for Quillu at FA.', u'original_size': {u'url': u'http://41.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_1280.jpg', u'width': 800, u'height': 1410}, u'alt_sizes': [{u'url': u'http://41.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_1280.jpg', u'width': 800, u'height': 1410}, {u'url': u'http://40.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_500.jpg', u'width': 426, u'height': 750}, {u'url': u'http://41.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_400.jpg', u'width': 340, u'height': 600}, {u'url': u'http://41.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_250.jpg', u'width': 227, u'height': 400}, {u'url': u'http://40.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_100.jpg', u'width': 100, u'height': 176}, {u'url': u'http://41.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'Werewolf herm, in heat. Watch out!', u'original_size': {u'url': u'http://36.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_1280.jpg', u'width': 1280, u'height': 962}, u'alt_sizes': [{u'url': u'http://36.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_1280.jpg', u'width': 1280, u'height': 962}, {u'url': u'http://41.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_500.jpg', u'width': 500, u'height': 376}, {u'url': u'http://41.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_400.jpg', u'width': 400, u'height': 301}, {u'url': u'http://36.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_250.jpg', u'width': 250, u'height': 188}, {u'url': u'http://36.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_100.jpg', u'width': 100, u'height': 75}, {u'url': u'http://40.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_75sq.jpg', u'width': 75, u'height': 75}]}], u'id': 87231460597L, u'post_url': u'http://zaggatar.tumblr.com/post/87231460597/i-thought-i-would-upload-some-of-what-i-think-is', u'caption': u'<p><span>I thought I would upload s</span>ome of what I think is best of my older stuff.</p>\n<p>As you can see, I am guilty for liking horsegirls with big dicks.</p>\n<p>Enjoy.</p>', u'state': u'published', u'short_url': u'http://tmblr.co/Zlxuxu1HFPdJr', u'date': u'2014-05-29 20:53:00 GMT', u'type': u'photo', u'slug': u'i-thought-i-would-upload-some-of-what-i-think-is', u'photoset_layout': u'1111111111', u'blog_name': u'zaggatar'}
    #print flatten(post_dict)
    new_post_dict = save_media(connection,post_dict)
    #download_image_link(connection,"https://derpicdn.net/spns/W1siZiIsIjIwMTQvMDEvMTAvMDJfNDBfMjhfNjUyX2RlcnBpYm9vcnVfYmFubmVyLnBuZyJdXQ.png")
    logging.debug("Closing DB connection")
    connection.close()

if __name__ == '__main__':
    main()
