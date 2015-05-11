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
import os
import sys
import re
#import mechanize
#import cookielib
import logging
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


















def setup_logging(log_file_path,concise_log_file_path=None):
    """Setup logging (Before running any other code)
    http://inventwithpython.com/blog/2012/04/06/stop-using-print-for-debugging-a-5-minute-quickstart-guide-to-pythons-logging-module/
    """
    assert( len(log_file_path) > 1 )
    assert( type(log_file_path) == type("") )
    global logger
    # Make sure output dir exists
    log_file_folder =  os.path.dirname(log_file_path)
    if log_file_folder is not None:
        if not os.path.exists(log_file_folder):
            os.makedirs(log_file_folder)
    if concise_log_file_path is not None:
        concise_log_folder = os.path.dirname(concise_log_file_path)
        if concise_log_folder is not None:
            if not os.path.exists(concise_log_folder):
                os.makedirs(concise_log_folder)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    # File 1, log everything
    fh = logging.FileHandler(log_file_path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # File 2, INFO and higher level for a concise log
    if concise_log_file_path:
        cfh = logging.FileHandler(concise_log_file_path)
        cfh.setLevel(logging.INFO)
        cfh.setFormatter(formatter)
        logger.addHandler(cfh)
        print"cfh"
    # Console output
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logging.info("Logging started.")
    return


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
        if len(foldername) >= 1:
            if not os.path.isdir(foldername):
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
            logging.error(repr(locals()))
            time.sleep(0.1)
            continue
    logging.warning("save_file() Too many failed write attempts! "+repr(file_path))
    if allow_fail:
        return
    else:
        logging.critical("save_file() Passing on exception")
        logging.critical(repr(locals()))
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
    if "http://" in url:
        return url
    elif "https://" in url:
        return url
    else:
        #case //derpicdn.net/img/view/...
        first_two_chars = url[0:2]
        if first_two_chars == "//":
            output_url = "https:"+url
            return output_url
        else:
            logging.error("Error adding HTTP to URL string")
            logging.error(repr(locals()))
            raise ValueError


def deescape(html):
    # de-escape html
    # http://stackoverflow.com/questions/2360598/how-do-i-unescape-html-entities-in-a-string-in-python-3-1
    deescaped_string = HTMLParser.HTMLParser().unescape(html)
    return deescaped_string


def get(url):
    #try to retreive a url. If unable to return None object
    #Example useage:
    #html = get("")
    #if html:
    assert_is_string(url)
    deescaped_url = deescape(url)
    url_with_protocol = add_http(deescaped_url)
    #logging.debug( "getting url ", locals())
    gettuple = getwithinfo(url_with_protocol)
    if gettuple:
        reply, info = gettuple
        return reply
    else:
        return


def getwithinfo(url):
    """Try to retreive a url. If unable to return None objects
    Example useage:
    html = get("")
        if html:
    """
    attemptcount = 0
    max_attempts = 10
    retry_delay = 10
    request_delay = 0.5#avoid hammering the site too hard
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
            r = urllib2.urlopen(url)
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
            return reply,info

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


def move_file(original_path,final_path):
    """Move a file from one location to another"""
    assert_is_string(original_path)
    assert_is_string(final_path)
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


def hash_file_data(file_data):
    """Take the data from a file and hash it for deduplication
    Return a base64 encoded hash of the data"""
    m = hashlib.sha512()
    m.update(file_data)
    raw_hash = m.digest()
    #logging.debug("raw_hash: "+repr(raw_hash))
    sha512base64_hash = base64.b64encode(raw_hash)
    #sha512base32_hash = base64.b32encode(raw_hash)
    #sha512base16_hash = base64.b16encode(raw_hash)
    #logging.debug("sha512base64_hash: "+repr(sha512base64_hash))
    #logging.debug("sha512base32_hash: "+repr(sha512base32_hash))
    #logging.debug("sha512base16_hash: "+repr(sha512base16_hash))
    return sha512base64_hash


def _generate_media_file_path_hash(root_path,filename):
    assert(len(filename) == 128)# Filenames should be of fixed length
    folder = filename[0:4]
    file_path = os.path.join(root_path,folder,filename)
    return file_path


def _generate_media_file_path_timestamp(root_path,filename):
    first_four_chars = filename[0:4]
    second_two_chars = filename[4:6]
    file_path = os.path.join(root_path,first_four_chars,second_two_chars,filename)
    return file_path


def generate_filename(ext,hash=None):# WIP
    """Abstraction for generating filenames, this is so only one function needs to care about it
    Take the file extention and maybe some other info and return a filename"""
    # Timestamp filename
    timestamp = str(get_current_unix_time())
    filename = timestamp+"."+ext
    return filename


def generate_path(root_path,filename):#WIP
    """Abstraction for generating file paths
    Take a filename and create a path for it"""
    return _generate_media_file_path_timestamp(root_path,filename)# Lazy but good enough


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
            cleaned_url = clean_blog_url(line)
            if cleaned_url:
                blog_urls.append(cleaned_url)
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


def main():
    pass
    # Test get_file_extention
    print get_file_extention("http://41.media.tumblr.com/5f52121f2a8f03b086aff076a00a5e2d/tumblr_nfcz9lPRUR1qbvkmso1_1280.jpg?")# jpg
    print get_file_extention(u'https://www.tumblr.com/explore/links')# None
    print get_file_extention("gLdiLePCFaV6t1x56uokkwMvcuTNwhFYksCfR6h4zk3gU2bvGjnIprjtcKaLNUW8Snxl9iFutq51hjgO2DLB9A==")# None
    print get_file_extention("http://www.papermag.com/2014/11/arabelle_sicardi.php")# php

if __name__ == '__main__':
    main()
