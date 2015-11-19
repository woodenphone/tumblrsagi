#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     07/01/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import time
import datetime
import os
import sys
import re
#import mechanize
#import cookielib
import logging
import logging.handlers
import urllib2
import httplib
import random
import HTMLParser
import json
import shutil
import socket
import string
import hashlib# Needed to hash file data
import base64 # Needed to do base32 encoding of filenames
import ssl # So we can turn SSL off
#import requests # Because urllib2 has a hang issue

import config# Local config
import lockfiles







def setup_logging(log_file_path,timestamp_filename=True,max_log_size=104857600):
    """Setup logging (Before running any other code)
    http://inventwithpython.com/blog/2012/04/06/stop-using-print-for-debugging-a-5-minute-quickstart-guide-to-pythons-logging-module/
    """
    assert( len(log_file_path) > 1 )
    assert( type(log_file_path) == type("") )
    global logger

    # Make sure output dir(s) exists
    log_file_folder =  os.path.dirname(log_file_path)
    if log_file_folder is not None:
        if not os.path.exists(log_file_folder):
            os.makedirs(log_file_folder)

    # Add timetamp for filename if needed
    if timestamp_filename:
        # http://stackoverflow.com/questions/8472413/add-utc-time-to-filename-python
        # '2015-06-30-13.44.15'
        timestamp_string = datetime.datetime.utcnow().strftime("%Y-%m-%d %H.%M.%S%Z")
        # Full log
        log_file_path = add_timestamp_to_log_filename(log_file_path,timestamp_string)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # 2015-07-21 18:56:23,428 - t.11028 - INFO - ln.156 - Loading page 0 of posts for u'mlpgdraws.tumblr.com'
    formatter = logging.Formatter("%(asctime)s - t.%(thread)d - %(levelname)s - ln.%(lineno)d - %(message)s")

    # File 1, log everything
    # https://docs.python.org/2/library/logging.handlers.html
    # Rollover occurs whenever the current log file is nearly maxBytes in length; if either of maxBytes or backupCount is zero, rollover never occurs.
    fh = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        # https://en.wikipedia.org/wiki/Binary_prefix
        # 104857600 100MiB
        maxBytes=max_log_size,
        backupCount=10,# Ten should be enough to debug but not use too mcuh storage
        )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console output
    ch = logging.StreamHandler()
    ch.setLevel(config.console_log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logging.info("Logging started.")
    return logger


def add_timestamp_to_log_filename(log_file_path,timestamp_string):
    """Insert a string before a file extention"""
    base, ext = os.path.splitext(log_file_path)
    return base+"_"+timestamp_string+ext


def save_file(file_path,data,force_save=False,allow_fail=False):
    assert_is_string(file_path)
    counter = 0
    while counter <= 10:
        counter += 1

        if not force_save:
            if os.path.exists(file_path):
                logging.debug("save_file()"" File already exists! "+repr(file_path))
                return
        foldername = os.path.dirname(file_path)
        if len(foldername) != 0:
            if not os.path.exists(foldername):
                try:
                    os.makedirs(foldername)
                except WindowsError, err:
                    pass
        try:
            file = open(file_path, "wb")
            file.write(data)
            file.close()
            return
        except IOError, err:
            logging.exception(err)
            logging.error(repr(file_path))
            time.sleep(1)
            continue
    logging.warning("save_file() Too many failed write attempts! "+repr(file_path))
    if allow_fail:
        return
    else:
        logging.critical("save_file() Passing on exception")
        logging.critical(repr(file_path))
        raise


def read_file(path):
    """grab the contents of a file"""
    assert_is_string(path)
    f = open(path, "r")
    data = f.read()
    f.close()
    return data


def add_http(url):
    """Ensure a url starts with http://..."""
    if "http://" in url.lower():
        return url
    elif "https://" in url.lower():
        return url
    else:
        #case //derpicdn.net/img/view/...
        first_two_chars = url[0:2]
        if first_two_chars == "//":
            output_url = "https:"+url
            return output_url
        else:
            logging.error("Error adding HTTP to URL string")
            logging.error("add_http() locals:"+repr(locals()))
            raise ValueError


def deescape(html):
    # de-escape html
    # http://stackoverflow.com/questions/2360598/how-do-i-unescape-html-entities-in-a-string-in-python-3-1
    deescaped_string = HTMLParser.HTMLParser().unescape(html)
    return deescaped_string


def get_url(url):
    #try to retreive a url. If unable to return None object
    #Example useage:
    #html = get_url("")
    #if html:
    #logging.debug( "getting url ", locals())
    gettuple = getwithinfo(url)
    if gettuple:
        reply, info, r = gettuple
        return reply
    else:
        return

def getwithinfo(url):
    """Try to retreive a url.
    If successful return (reply,info,request)
    If unable to return None objects
    Example useage:
    html = get_url("")
        if html:
    """
    attemptcount = 0
    max_attempts = 10
    retry_delay = 10
    request_delay = 0.5#avoid hammering the site too hard
    assert_is_string(url)
    deescaped_url = deescape(url)
    url_with_protocol = add_http(deescaped_url)
    # Remove all ssl because ATC said to
    # http://stackoverflow.com/questions/19268548/python-ignore-certicate-validation-urllib2
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    while attemptcount < max_attempts:
        attemptcount = attemptcount + 1
        if attemptcount > 1:
            delay(retry_delay)
        logging.debug( "Attempt "+repr(attemptcount)+" for URL: "+repr(url) )
        try:
##            save_file(
##                file_path = os.path.join("debug","get_last_url.txt"),
##                data = url,
##                force_save = True,
##                allow_fail = True
##                )
            request = urllib2.Request(url_with_protocol)
            request.add_header("User-agent", "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1")
            #request.add_header('Referer', 'http://www.tumblr.com/')
            r = urllib2.urlopen(
                request,
                context=ctx
                )
            info = r.info()
            reply = r.read()
            delay(request_delay)

##            # Save html responses for debugging
##            if "html" in info["content-type"]:
##                save_file(
##                    file_path = os.path.join("debug","get_last_html.htm"),
##                    data = reply,
##                    force_save = True,
##                    allow_fail = True
##                    )
##            else:
##                pass
##                save_file(
##                    file_path = os.path.join("debug","get_last_not_html.txt"),
##                    data = reply,
##                    force_save = True,
##                    allow_fail = True
##                    )
            # Retry if empty response and not last attempt
            if (len(reply) < 1) and (attemptcount < max_attempts):
                logging.error("Reply too short :"+repr(reply))
                continue
            return reply,info,r

        except urllib2.HTTPError, err:
            logging.exception(err)
            logging.error(repr(err))
            if err.code == 404:
                logging.error("404 error! "+repr(url))
                return
            elif err.code == 403:
                logging.error("403 error, ACCESS DENIED! url: "+repr(url))
                return
            elif err.code == 410:
                logging.error("410 error, GONE")
                return
            else:
                save_file(
                    file_path = os.path.join("debug","HTTPError.htm"),
                    data = err.fp.read(),
                    force_save = True,
                    allow_fail = True
                    )
                continue

        except urllib2.URLError, err:
            logging.exception(err)
            logging.error(repr(err))
            if "unknown url type:" in err.reason:
                return
            else:
                continue

        except httplib.BadStatusLine, err:
            logging.exception(err)
            logging.error(repr(err))
            continue

        except httplib.IncompleteRead, err:
            logging.exception(err)
            logging.error(repr(err))
            logging.exception(err)
            continue

        except socket.timeout, err:
            logging.exception(err)
            logging.error(repr( type(err) ) )
            logging.error(repr(err))
            continue

        except Exception, err:
            logging.exception(err)
            # We have to do this because socket.py just uses "raise"
            logging.error("getwithinfo() caught an exception")
            logging.error("getwithinfo() repr(err):"+repr(err))
            logging.error("getwithinfo() str(err):"+str(err))
            logging.error("getwithinfo() type(err):"+repr(type(err)))
            continue

    logging.error("Too many retries, failing.")
    return






# def get_url(url):
#     #try to retreive a url. If unable to return None object
#     #Example useage:
#     #html = get_url("")
#     #if html:
#     #logging.debug( "getting url ", locals())
#     get_tuple = get_requests(url)
#     if get_tuple:
#         reply, request = get_tuple
#         return reply
#     else:
#         return

# def get_requests(url):
#     """foo"""
#     max_attempts = 10
#     attempt_counter = 0
#     while attempt_counter <= max_attempts:
#         attempt_counter += 1
#         if attempt_counter > 1:
#             logging.debug("Attempt "+repr(attempt_counter)+" to open URL: "+repr(url))
#         try:

#             response = requests.get(
#                 url,
#                 timeout=10,# fail if no communication for 10 seconds
#                 )
#             response.raise_for_status()
#             return (response.content, response)

#         except requests.ConnectionError, err:
#             logging.exception(err)
#             logging.error("Connection error getting content-type!")
#             logging.debug("(locals():"+repr(locals() ) )
#             continue
#         except requests.exceptions.InvalidSchema, err:
#             logging.exception(err)
#             logging.debug("(locals():"+repr(locals() ) )
#             break# We can't handle this link.
#         except requests.exceptions.InvalidURL, err:
#             logging.exception(err)
#             logging.debug("(locals():"+repr(locals() ) )
#             break# We can't handle this link.
#     return


def assert_is_string(object_to_test):
    """Make sure input is either a string or a unicode string"""
    if( (type(object_to_test) == type("")) or (type(object_to_test) == type(u"")) ):
        return
    logging.error("assert_is_string() test failed!")
    logging.critical(repr(locals()))
    raise(ValueError)


def delay(basetime,upperrandom=0):
    #replacement for using time.sleep, this adds a random delay to be sneaky
    sleeptime = basetime + random.randint(0,upperrandom)
    #logging.debug("pausing for "+repr(sleeptime)+" ...")
    time.sleep(sleeptime)


def get_current_unix_time():
    """Return the current unix time as an integer"""
    # https://timanovsky.wordpress.com/2009/04/09/get-unix-timestamp-in-java-python-erlang/
    current_time = time.time()
    timestamp = int(current_time *1000)
    return timestamp



def merge_dicts(*dict_args):
    # http://stackoverflow.com/questions/38987/how-can-i-merge-two-python-dictionaries-in-a-single-expression
    '''
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    '''
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def flatten(sequence,contents=[]):
    """Take a dict, tuple, or list, and flatten it."""
    # Flatten dicts
    if (type(sequence) == type({})):
        for dict_key in sequence.keys():
            field = sequence[dict_key]
            if ( (type(field) == type({})) or (type(field) == type([])) or (type(field) == type((1,2)))):
                contents.append(flatten(field,contents))
            else:
                contents.append(field)
    # Flatten lists and tuples
    elif (
    (type(sequence) == type([])) or
    (type(sequence) == type(()))
    ):
        for item in sequence:
            contents.append(item)
    return contents


def uniquify(seq, idfun=None):
    # List uniquifier from
    # http://www.peterbe.com/plog/uniqifiers-benchmark
   # order preserving
   if idfun is None:
       def idfun(x): return x
   seen = {}
   result = []
   for item in seq:
       marker = idfun(item)
       # in old Python versions:
       # if seen.has_key(marker)
       # but in new ones:
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
   return result


def move_file(original_path,final_path,max_attempts=30):
    """Move a file from one location to another"""
    assert_is_string(original_path)
    assert_is_string(final_path)

    attempt_counter = 0
    while attempt_counter < max_attempts:
        attempt_counter += 1
        if attempt_counter > 1:
            # Pause if something went wrong, (yt-dl is a suspect, might not be closing files?)
            time.sleep(attempt_counter)
            logging.debug("Attempt "+repr(attempt_counter)+" to move "+repr(original_path)+" to "+repr(final_path))
        try:
            # Make sure output folder exists
            output_dir = os.path.dirname(final_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            assert(os.path.exists(output_dir))
            # Move file
            shutil.move(original_path, final_path)
            assert(not os.path.exists(original_path))
            assert(os.path.exists(final_path))
            return
        except WindowsError, err:
            logging.exception(err)
            logging.error("Failed to move file: "+repr(original_path)+" to "+repr(final_path))
            continue
    # If we get here we already have an exception to re-raise
    logging.critical("move_file() Too many failed attempts to move a file!")
    logging.critical("move_file()"+repr(locals()))
    raise


def delete_file(file_path,max_attempts=30):
    """Delete a file"""
    assert_is_string(file_path)

    attempt_counter = 0
    while attempt_counter < max_attempts:
        attempt_counter += 1
        if attempt_counter > 1:
            # Pause if something went wrong, (yt-dl is a suspect, might not be closing files?)
            time.sleep(attempt_counter)
            logging.debug("Attempt "+repr(attempt_counter)+" to delete "+repr(file_path))
        try:
            # Delete file
            os.remove(file_path)
            assert(not os.path.exists(file_path))
            return
        except WindowsError, err:
            logging.exception(err)
            logging.error("Failed to delete file: "+repr(file_path))
            continue
    # If we get here we already have an exception to re-raise
    logging.critical("delete_file() Too many failed attempts to delete a file!")
    logging.critical("delete_file()"+repr(locals()))
    raise


def hash_file_data(file_data):
    """Take the data from a file and hash it for deduplication
    Return a base16 encoded hash of the data"""
    m = hashlib.sha512()
    m.update(file_data)
    raw_hash = m.digest()
    #logging.debug("raw_hash: "+repr(raw_hash))
    #sha512base64_hash = base64.b64encode(raw_hash)
    #sha512base32_hash = base64.b32encode(raw_hash)
    sha512base16_hash = base64.b16encode(raw_hash)
    #logging.debug("sha512base64_hash: "+repr(sha512base64_hash))
    #logging.debug("sha512base32_hash: "+repr(sha512base32_hash))
    #logging.debug("sha512base16_hash: "+repr(sha512base16_hash))
    return sha512base16_hash


def hash_file(file_path):
    #http://stackoverflow.com/questions/30478972/hashing-files-with-python
    assert(os.path.exists(file_path))
    blocksize = 65536
    with open(file_path, "rb") as f:
        hasher = hashlib.sha512()
        buf = f.read(blocksize)
        while len(buf)>0:
            hasher.update(buf)
            buf = f.read(blocksize)
        raw_hash =  hasher.digest()
    sha512base16_hash = base64.b16encode(raw_hash)
    return sha512base16_hash


def generate_filename(ext,sha512base16_hash=None):
    """Abstraction for generating filenames, this is so only one function needs to care about it
    Take the file extention and maybe some other info and return a filename"""
##    # Timestamp filename
##    timestamp = str(get_current_unix_time())
##    filename = timestamp+"."+ext
    # Base16 hash filename
    filename = sha512base16_hash+"."+ext
    return filename


def generate_path(root_path,filename):
    """Abstraction for generating file paths
    Take a filename and create a path for it
    Uses /12/34/56/ style due to folders containing 16^n subfolders
    where n is number of digits per foldername"""
    file_path = os.path.join(
        root_path,
        filename[0:2],# First two chars of filename
        filename[2:4],# Second two chars of filename
        filename[4:6],# Third two chars of filename
        filename
        )
    return file_path


def clean_blog_url(raw_url):
    """Given a blog name or URL, mangle it into something the tumblr API will probably like"""
    # Example urls that need handling:
    # http://jessicaanner.tumblr.com/post/113520547711/animated-versions-here-main-view-webm-gif
    # http://havesomemoore.tumblr.com/
    # http://pwnypony.com/
    # (?:https?://)([^#/'"]+)
    stripped_url = raw_url.strip("\r\n\t ")
    logging.debug("stripped_url: "+repr(stripped_url))
    blog_url_regex = """(?:https?://)?([^#/'"]+)"""
    blog_url_search = re.search(blog_url_regex, stripped_url, re.IGNORECASE)
    if blog_url_search:
        blog_url = blog_url_search.group(1)
        return blog_url
    else:
        logging.error("Can't parse list item! Skipping it.")
        logging.error("clean_blog_url()"+" "+"raw_url"+": "+repr(raw_url))
        return ""


def clean_list_line(line):
    stripped_url = line.strip("\r\n\t ")
    return stripped_url


def import_blog_list(list_file_path="tumblr_todo_list.txt"):
    """Import (open and parse) list file of blogs to save
    return a list of api-friendly blog url strings"""
    logging.debug("import_blog_list() list_file_path: "+repr(list_file_path))
    # Make sure list file folder exists
    list_file_folder =  os.path.dirname(list_file_path)
    if list_file_folder:
        if not os.path.exists(list_file_folder):
            os.makedirs(list_file_folder)
    # Create new empty list file if no list file exists
    if not os.path.exists(list_file_path):
        logging.debug("import_blog_list() Blog list file not found, creating it.")
        new_file = open(list_file_path, "w")
        new_file.write('# Add one URL per line, comments start with a #, nothing but username on a line that isnt a comment\n\n')
        new_file.close()
        return []
    # Read each line from the list file and process it
    blog_urls = []
    list_file = open(list_file_path, "rU")
    line_counter = 0
    for line in list_file:
        line_counter += 1
        # Strip empty and comment lines
        if line[0] in ["#", "\r", "\n"]:
            continue
        else:
            cleaned_url = clean_list_line(line)
            if cleaned_url:
                blog_urls.append(cleaned_url+u"")
            else:
                logging.error("import_blog_list(): Cleaning line "+repr(line_counter)+" : "+repr(line)+"Failed!")
    blog_urls = uniquify(blog_urls)
    logging.debug("import_blog_list() blog_urls: "+repr(blog_urls))
    return blog_urls


def appendlist(lines,list_file_path="tumblr_done_list.txt",initial_text="# List of completed items.\n"):
    # Append a string or list of strings to a file; If no file exists, create it and append to the new file.
    # Strings will be seperated by newlines.
    # Make sure we're saving a list of strings.
    if ((type(lines) is type(""))or (type(lines) is type(u""))):
        lines = [lines]
    # Ensure file exists.
    if not os.path.exists(list_file_path):
        list_file_segments = os.path.split(list_file_path)
        list_dir = list_file_segments[0]
        if list_dir:
            if not os.path.exists(list_dir):
                os.makedirs(list_dir)
        nf = open(list_file_path, "w")
        nf.write(initial_text)
        nf.close()
    # Write data to file.
    f = open(list_file_path, "a")
    for line in lines:
        outputline = line+"\n"
        f.write(outputline)
    f.close()
    return


def get_file_extention(file_path):
    """Take a file name, URL, or path and return the extention
    If no extention, return None"""
    # http://domain.tld/foo.bar -> foo.bar
    filename = os.path.basename(file_path)# Make sure we don't include domain names
    # foo.bar -> bar
    # foo.bar?baz -> bar
    # foobar/baz -> None
    # foobar/baz?fizz -> None
    file_extention_regex = """\.([a-zA-Z0-9]+)[?]?"""
    file_extention_search = re.search(file_extention_regex, filename, re.IGNORECASE)
    if file_extention_search:
        file_extention = file_extention_search.group(1)
        return file_extention


def parse_tumblr_timsetamp_string(date_string):
    """Parse tumblr datestring to unix time
    u'date': u'2014-01-24 19:40:00 GMT'"""
    return datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S %Z")


def split_list(list_in,number_of_pieces):
    """Take a list and split it into segments
    Return a list of lists
    [1,2,3,4,5,6] -> [[1,2,3], [4,5,6]]
    """
    output_length = len(list_in) / number_of_pieces
    output = []
    piece = []
    counter = 0
    for list_item in list_in:
        counter += 1
        piece.append(list_item)
        if counter >= output_length:
            output.append(piece)
            counter = 0
            piece = []
    # Make sure nothing is missed
    if len(piece) > 0:
        output.append(piece)
    return output


def generate_md5b64_for_file(file_path):
    """Generate 4chan-style bd5base64 hashes from files"""
    #http://stackoverflow.com/questions/30478972/hashing-files-with-python
    assert(os.path.exists(file_path))
    blocksize = 65536
    with open(file_path, "rb") as f:
        hasher = hashlib.md5()
        buf = f.read(blocksize)
        while len(buf)>0:
            hasher.update(buf)
            buf = f.read(blocksize)
        raw_hash =  hasher.digest()
    md5base64_hash = base64.b64encode(raw_hash)
    return md5base64_hash


def generate_md5b64_for_memory(file_data):
    """Generate 4chan-style bd5base64 hashes from objects in memory"""
    m = hashlib.md5()
    m.update(file_data)
    raw_hash = m.digest()
    md5base64_hash = base64.b64encode(raw_hash)
    return md5base64_hash


def find_file_size(file_path):
    size_in_bytes = os.path.getsize(file_path)
    return size_in_bytes





def main():
    # Test split_list
    print split_list(range(7), 2)
    print split_list(range(6), 3)
    print split_list(range(100), 10)
    print split_list([{1:1},{2:2},{3:3},{4:4}], 10)
    # Test get_file_extention
    print get_file_extention("http://41.media.tumblr.com/5f52121f2a8f03b086aff076a00a5e2d/tumblr_nfcz9lPRUR1qbvkmso1_1280.jpg?")# jpg
    print get_file_extention(u'https://www.tumblr.com/explore/links')# None
    print get_file_extention("gLdiLePCFaV6t1x56uokkwMvcuTNwhFYksCfR6h4zk3gU2bvGjnIprjtcKaLNUW8Snxl9iFutq51hjgO2DLB9A==")# None
    print get_file_extention("http://www.papermag.com/2014/11/arabelle_sicardi.php")# php

    print parse_tumblr_timsetamp_string("2014-01-24 19:40:00 GMT")
    # Test hashing of files
    test_filename = "hashtest.txt"
    hash_a = hash_file(test_filename)
    print hash_a
    with open(test_filename) as f:
        file_data = f.read()
    hash_b = hash_file_data(file_data)
    print hash_b
    print "Hashes matched?", (hash_a == hash_b)

if __name__ == '__main__':
    main()
