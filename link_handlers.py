#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     28/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# Libraries
import sqlalchemy
import subprocess# For video and some audio downloads
import urllib# For encoding audio urls
import re
import logging
# This project
from utils import *
from sql_functions import Media
import sql_functions
import config # User settings






def find_links_src(html):
    """Given string containing '<img src="http://media.tumblr.com/tumblr_m7g6koAnx81r3kwau.jpg"/>'
    return ['http://media.tumblr.com/tumblr_m7g6koAnx81r3kwau.jpg']
    """
    embed_regex = """<\w+?\s+?src=["']([^>]+)["']/>"""
    links = re.findall(embed_regex,html, re.DOTALL)
    #logging.debug("src embed links: "+repr(links))
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
        #logging.debug("field: "+repr(field))
        # Text fields
        if ( (type(field) == type("")) or (type(field) == type(u"")) ):
            html = field
            #logging.debug("html: "+repr(html))
            links += find_links_src(field)
            links += find_url_links(field)
    #elif ( (type(field) == type({})) or (type(field) == type([])) ):
    #logging.debug("all links found in post: "+repr(links))
    return links


def handle_image_links(session,all_post_links):
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
    link_hash_dict = download_image_links(session,image_links)
    return link_hash_dict# {link:hash}


















def main():
    pass

if __name__ == '__main__':
    main()
