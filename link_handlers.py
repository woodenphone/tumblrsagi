#-------------------------------------------------------------------------------
# Name:        link_handlers
# Purpose:  code for links in post text and other things not given directly by the tumblr API
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
import requests

# This project
from utils import *
from sql_functions import Media
import sql_functions
import config # User settings
from image_handlers import *
import yt_dl_common
import imgur



def find_links_src(html):
    """Given string containing '<img src="http://media.tumblr.com/tumblr_m7g6koAnx81r3kwau.jpg"/>'
    return ['http://media.tumblr.com/tumblr_m7g6koAnx81r3kwau.jpg']
    """
    embed_regex = """src=["']([^'"]+)["']/>"""
    links = re.findall(embed_regex,html, re.DOTALL)
    #logging.debug("find_links_src() links: "+repr(links))
    return links


def find_url_links(html):
    """Find URLS in a string of text"""
    # Should return list of strings
    # Copied from:
    # http://stackoverflow.com/questions/520031/whats-the-cleanest-way-to-extract-urls-from-a-string-using-python
    # old regex http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+
    url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+~]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    links = re.findall(url_regex,html, re.DOTALL)
    #logging.debug("find_url_links() links: "+repr(links))
    assert(type(links) is type([]))# Should be list
    return links


def find_links(html):
    """Given a string of text or HTML, find any links.
    return a list of link strings"""
    links = []
    links += find_links_src(html)
    links += find_url_links(html)
    return links


def extract_post_links(post_dict):
    """Run all applicable extractors for a post"""
    # Collect links in the post text

    # collect together fields that would have text
    # Assuming anything that exists and is not None will be string
    fields_string = u""
    if u"body" in post_dict.keys():
        fields_string += (post_dict["body"]+u"\n\n")
    if u"title" in post_dict.keys():
        if post_dict["title"]:
            fields_string += (post_dict["title"]+u"\n\n")
    if u"text" in post_dict.keys():
        if post_dict["text"]:
            fields_string += (post_dict["text"]+u"\n\n")
    if u"source" in post_dict.keys():
        if post_dict["source"]:
            fields_string += (post_dict["source"]+u"\n\n")
    if u"description" in post_dict.keys():
        if post_dict["description"]:
            fields_string += (post_dict["description"]+u"\n\n")
    if u"url" in post_dict.keys():
        if post_dict["url"]:
            fields_string += (post_dict["url"]+u"\n\n")
    if u"source" in post_dict.keys():
        if post_dict["source"]:
            fields_string += (post_dict["source"]+u"\n\n")
    if u"caption" in post_dict.keys():
        if post_dict["caption"]:
            fields_string += (post_dict["caption"]+u"\n\n")
    if u"question" in post_dict.keys():
        if post_dict["question"]:
            fields_string += (post_dict["question"]+u"\n\n")
    if u"answer" in post_dict.keys():
        if post_dict["answer"]:
            fields_string += (post_dict["answer"]+u"\n\n")
    if u"source_url" in post_dict.keys():
        if post_dict["source_url"]:
            fields_string += (post_dict["source_url"]+u"\n\n")
    #logging.debug("extract_post_links() fields_string: "+repr(fields_string))

    # Search for links in string
    links = find_links(fields_string)
    #logging.debug("extract_post_links() links: "+repr(links))
    return links


def handle_image_links(session,all_post_links):
    """Check and save images linked to by a post
    return media_id_list = {}"""
    logging.debug("handle_image_links() all_post_links"+repr(all_post_links))
    # Find all links in post dict
    # Select whick links are image links
    valid_extentions = [
    "jpg","jpeg",
    "gif",
    "png",
    ]
    image_links = []
    for link in all_post_links:
        # Grab extention if one exists
        link_extention = get_file_extention(link)
        logging.debug("handle_image_links() "+"Link: "+repr(link)+" , link_extention: "+repr(link_extention))
        # Check if extention is one we want
        if link_extention in valid_extentions:
            logging.debug("handle_image_links() "+"Link has valid extention: "+repr(link))
            image_links.append(link)
    #logging.debug("handle_image_links() image_links: "+repr(image_links))
    # Save image links
    media_id_list = download_image_links(session,image_links)
    return media_id_list




def handle_video_file_links(session,all_post_links):# WIP
    """Check and save video files linked to by a post
    return media_id_list"""
    logging.debug("handle_video_file_links() all_post_links"+repr(all_post_links))
    # Find all links in post dict
    # Select whick links are image links
    valid_extentions = [
    "wmv",
    "mp4",
    "mov",
    # Flash
    "fla",
    "swf",
    ]
    video_links = []
    for link in all_post_links:
        # Grab extention if one exists
        link_extention = get_file_extention(link)
        logging.debug("handle_video_file_links() "+"Link: "+repr(link)+" , link_extention: "+repr(link_extention))
        # Check if extention is one we want
        if link_extention in valid_extentions:
            logging.debug("handle_video_file_links() "+"Link has valid extention: "+repr(link))
            video_links.append(link)
    logging.debug("handle_video_file_links() video_links: "+repr(video_links))
    # Save image links
    media_id_list = download_image_links(session,video_links)
    return media_id_list


def handle_video_links(session,all_post_links):# WIP
    media_id_list = []
    for link in all_post_links:
        # Site handlers
        # Youtube
        if ("youtube.com" in link[0:100]) or ("youtu.be" in link[0:100]):
            continue
            logging.debug("Link is youtube video: "+repr(link))
            media_id_list += yt_dl_common.run_yt_dl_single(
                session=session,
                download_url=link,
                extractor_used="link_handlers.handle_video_links:youtube.com",
                )

        # gfycat.com
        elif "gfycat.com/" in link[0:20]:
            logging.debug("Link is gfycat video: "+repr(link))
            media_id_list += yt_dl_common.run_yt_dl_single(
                session=session,
                download_url=link,
                extractor_used="link_handlers.handle_video_links:gfycat.com",
                )

        # http://webmshare.com
        elif "webmshare.com" in link[0:20]:
            logging.debug("Link is webmshare video: "+repr(link))
            media_id_list += yt_dl_common.run_yt_dl_single(
                session=session,
                download_url=link,
                extractor_used="link_handlers.handle_video_links:webmshare.com",
                )

    return media_id_list




def remove_tumblr_links(link_list):
    """Remove links to posts and other known unwanted tumblr links"""
    wanted_links = []
    for link in link_list:
        # Reject tumblr posts ex. "http://somescrub.tumblr.com/post/110535365780/joshy-gifs-8-bit-tits"
        if ".tumblr.com/post/" in link:
            continue
        elif "//tmblr.co/" in link:
            continue
        # If not rejected by any filter, keep the link
        wanted_links.append(link)
        continue
    return wanted_links


def handle_generic_link(session,link):
    logging.debug("handle_generic_link() link:"+repr(link))
    # Ensure the protocol bit is there ("http://","ftp://"...)
    if "://" not in link:
        logging.debug("handle_generic_link() prepending 'http://' to link")
        link = "http://"+link
    attempt_counter = 0
    max_attempts = 10
    while attempt_counter <= max_attempts:
        attempt_counter += 1
        if attempt_counter > 1:
            logging.debug("Attempt "+repr(attempt_counter)+"to process link: "+repr(link))
        # Get header to check filetype
        try:
            # AnonTheCuck> you should make an HTTP Head request and check the file type to see if it is something we want (image, video) and if it is, then pull it
            # http://stackoverflow.com/questions/107405/how-do-you-send-a-head-http-request-in-python
            resp = requests.head(link)
            if "content-type" not in resp.headers:
                logging.error("handle_generic_link() No content-type header!")
                logging.debug("handle_generic_link() locals()"+repr(locals))
                continue
            content_type = resp.headers["content-type"]

            logging.debug("content_type:"+repr(content_type))

            # Skip if bad content-type header
            ignored_content_types = [
                "text/html",
                ]
            if content_type in ignored_content_types:
                return []
            else:
                # Try saving if content-type is not a know bad value
                media_id_list = download_image_links(session,[link])
                return media_id_list

        except requests.ConnectionError, err:
            logging.exception(err)
            logging.error("Connection error getting content-type!")
            logging.debug("(locals():"+repr(locals() ) )
            continue
        except requests.exceptions.InvalidSchema, err:
            logging.exception(err)
            logging.debug("(locals():"+repr(locals() ) )
            break# We can't handle this link.
    logging.error("Too many retries getting content-type, failing.")
    appendlist(
        link,
        list_file_path=os.path.join("debug","link_handlers.handle_generic_link.failed.txt"),
        initial_text="# handle_generic_link() failed.\n"
        )
    return []

def handle_dropbox_link(session,link):
    """Supported link formats:
        https://dl.dropboxusercontent.com/s/cdxam7r5iwv3ax6/test.swf
        https://www.dropbox.com/s/npga7y1r24a5dqo/comma%20seperated%20tags.PNG?dl=0

        """
    assert( ("dropbox.com" in link) or ("dropboxusercontent.com" in link) )# Make sure the link is actually for dropbox
    dropbox_link_segment_search = re.search(""".com/s/([^?<>\s"']+)""", link, re.DOTALL)
    if dropbox_link_segment_search:
        # ex. cdxam7r5iwv3ax6/test.swf
        dropbox_link_segment = dropbox_link_segment_search.group(1)
        dropbox_link = "https://dl.dropbox.com/s/"+dropbox_link_segment
        logging.debug("Dropbox link:"+repr(dropbox_link))
        return download_image_links(session,[dropbox_link])
    else:
        logging.error("Cannot parse dropbox link!")
        appendlist(
            link,
            list_file_path=os.path.join("debug","bad_dropbox_links.txt"),
            initial_text="# dropbox handler failed.\n"
            )
        return []




def handle_fastswf_link(session,link):# TODO FIXME
    """http://www.fastswf.com/ - Free Flash and Unity Hosting
        Supported link formats:
        http://www.fastswf.com/5MH9MZw

        """
    assert( ("fastswf.com" in link))# Make sure the link is actually for fastswf
    #assert(False)#TODO FIXME
    # Load page
    s = requests.Session()

    page_html_request = s.get(link)
    page_html = page_html_request.text
    if page_html is None:
        logging.error("Filed to load page, skipping.")
        return []
    # Find flash file
    page_links = find_links(page_html)
    logging.debug("handle_fastswf_link() page_links: "+repr(page_links))
    links_to_save = []
    for page_link in page_links:
        if ".swf" in page_link.lower():
            links_to_save.append(page_link)
    logging.debug("handle_fastswf_link() links_to_save: "+repr(links_to_save))

    # Save flash file and add to DB
    media_id_list = []
    for link_to_save in links_to_save:
        response = s.get(link_to_save)
        logging.debug("response"+repr(response))
        media_id_list += handle_generic_link(session,link_to_save)
    return media_id_list


def handle_links(session,post_dict):# TODO FIXME
    """Call other functions to handle non-tumblr API defined links and pass data from them back"""
    logging.debug("Handling external links...")
    logging.warning("External links handling not yet implimented, fix this!")# TODO FIXME

    # Get list of links
    all_post_links = extract_post_links(post_dict)
    logging.debug("handle_links() all_post_links"+repr(all_post_links))

    # Remove any links that are tumblr posts ex."http://somescrub.tumblr.com/post/110535365780/joshy-gifs-8-bit-tits"
    non_tumblr_links = remove_tumblr_links(all_post_links)
    logging.debug("handle_links() non_tumblr_links: "+repr(non_tumblr_links))

    # Make sure we don't have duplicate links
    new_links = uniquify(non_tumblr_links)

    # Check each link to decide what to do with it
    logging.debug("new_links: "+repr(new_links))
    media_id_list = []
    for link in new_links:
        logging.debug("Processing link:"+repr(link))
        # -Multi format-

        # Dropbox
        # AnonTheCuck> Example: https://www.dropbox.com/s/npga7y1r24a5dqo/comma%20seperated%20tags.PNG?dl=0
        #  -> https://dl.dropbox.com/s/npga7y1r24a5dqo/comma%20seperated%20tags.PNG
        if "www.dropbox.com/s/" in link:
            logging.debug("Link is dropbox: "+repr(link))
            media_id_list += handle_dropbox_link(session,link)
            continue

        # e621.net
        # https://e621.net/post/show/599802

        # -Image-
        # Imgur
        if "//imgur.com/" in link:
            logging.debug("Link is imgur: "+repr(link))
            media_id_list += imgur.save_imgur(session,link)

        # -Video-
        # Youtube
        if ("youtube.com" in link[0:100]) or ("youtu.be" in link[0:100]):
            continue
            logging.debug("Link is youtube video: "+repr(link))
            media_id_list += yt_dl_common.run_yt_dl_single(
                session=session,
                download_url=link,
                extractor_used="link_handlers.handle_video_links:youtube.com",
                )
            continue

        # gfycat.com
        #https://gfycat.com/MatureSilkyEwe
        elif "gfycat.com/" in link[0:20]:
            logging.debug("Link is gfycat video: "+repr(link))
            media_id_list += yt_dl_common.run_yt_dl_single(
                session=session,
                download_url=link,
                extractor_used="link_handlers.handle_video_links:gfycat.com",
                )
            continue

        # http://webmshare.com
        elif "webmshare.com" in link[0:20]:
            logging.debug("Link is webmshare video: "+repr(link))
            media_id_list += yt_dl_common.run_yt_dl_single(
                session=session,
                download_url=link,
                extractor_used="link_handlers.handle_video_links:webmshare.com",
                )
            continue

        # webmup.com
        # http://webmup.com/c8197/
        elif "webmup.com/" in link[0:20]:
            logging.debug("Link is webmup.com video: "+repr(link))
            media_id_list += yt_dl_common.run_yt_dl_single(
                session=session,
                download_url=link,
                extractor_used="link_handlers.handle_video_links:webmup.com",
                )
            continue

        # http://webm.host
        # http://webm.host/ec2fc/
        elif "webm.host/" in link[0:20]:
            logging.debug("Link is webmup.com video: "+repr(link))
            media_id_list += yt_dl_common.run_yt_dl_single(
                session=session,
                download_url=link,
                extractor_used="link_handlers.handle_video_links:webm.host",
                )
            continue


        # -Audio-


        # Flash
        # fastswf.com
        elif "fastswf.com" in link[0:20]:
            logging.debug("Link is fastswf.com: "+repr(link))
            #media_id_list += handle_fastswf_link(session,link)


        # -Generic-
        desired_extentions = [
            # Image
            "jpg","jpeg",
            "gif",
            "png",
            # Audio
            "mp3",
            # Video
            "wmv",
            "mp4",
            "mov",
            # Flash
            "fla",
            "swf",
            ]
        link_extention = get_file_extention(link)
        logging.debug("link_extention:"+repr(link_extention))
        if link_extention in desired_extentions:
            logging.debug("Link matched a desired extention.")
            media_id_list += handle_generic_link(session,link)
            continue

        # If no handler matches, skip link.
        logging.debug("No handler for link:"+repr(link))
        continue

    return media_id_list








def debug():
    """For WIP, debug, ect function calls"""
    session = sql_functions.connect_to_db()
    handle_generic_link(session,link="media.tumblr.com/80638dc40978c286b5d3f18b2bfcf3d6/tumblr_inline_mfb0pxs7lf1qfi5b1.gif")

    #fastswf_result = handle_fastswf_link(session,"http://www.fastswf.com/5MH9MZw")
    return
    result = handle_links(
        session,
        post_dict = {u'highlighted': [], u'asking_url': None, u'reblog_key': u'O3UPhQYC', u'format': u'html', u'asking_name': u'Anonymous', u'timestamp': 1430518955, u'note_count': 43253, u'tags': [], u'question': u'lauren will you tell us a story', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 1226, u'title_color': u'#8f1e03', u'header_bounds': u'87,647,433,31', u'title_font': u'Courier New', u'link_color': u'#ffdd00', u'header_image_focused': u'http://static.tumblr.com/cafca27bb4f69629bf936818efb44e6f/88apzkd/fEXnhmx2i/tumblr_static_tumblr_static_983gvr4ppg4cgkgcs8c8owk4o_focused_v3.png', u'show_description': True, u'header_full_width': 677, u'header_focus_width': 616, u'header_stretch': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/cafca27bb4f69629bf936818efb44e6f/88apzkd/h29nhmx2f/tumblr_static_983gvr4ppg4cgkgcs8c8owk4o_2048_v2.png', u'avatar_shape': u'circle', u'show_avatar': True, u'header_focus_height': 346, u'background_color': u'#f38321', u'header_image': u'http://static.tumblr.com/cafca27bb4f69629bf936818efb44e6f/88apzkd/h29nhmx2f/tumblr_static_983gvr4ppg4cgkgcs8c8owk4o.png'}, u'name': u'iguanamouth'}, u'content': u'<p>ok heres something</p><p>around a year ago someone asked me to draw <a href="http://iguanamouth.tumblr.com/post/82902281208/draw-danny-devito-as-a-kitty">danny devito as a kitty</a>, spawning this terrible terrible image\xa0</p><figure data-orig-width="500" data-orig-height="406" class="tmblr-full"><img src="https://41.media.tumblr.com/d7549754fd8c427d3393eb702939652f/tumblr_inline_nnld4fWtJH1qmoaae_540.png" alt="image" data-orig-width="500" data-orig-height="406"></figure><p>time passes. a lot of time passes. then two months ago i get an email from a group of people called <a href="https://www.facebook.com/fpoafm">FPOAFM</a> doing a pottery installation event, and theyre going around gathering artwork from artists to put onto cups and dishes to sell,, in exchange for a few pieces with the artists work on them</p><p>and i said SURE you can use some of my stuff \u2026 . but in exchange.\u2026 <b>\xa0i want something with kitty devito on it. </b>i dont care if you put it on anything else, but one item that i get in return has to have this cat man abomination</p><p>i give them my address and a few images and months pass. i forget about it. THEN literally two days ago i get this big package on my doorstep, and INSIDE OF IT\u2026. is the holy grail</p><p>in addition to <a href="https://40.media.tumblr.com/cdd10d787d5bd9c4ab797fca37671cb0/tumblr_nneimxvAoS1rhtthso2_r3_1280.png">two</a> <a href="https://40.media.tumblr.com/7e01bf6e04497f0c9da80ed0b83cc3df/tumblr_nneimxvAoS1rhtthso3_r2_540.png">plates</a> is this incredible porcelain cup with the fabled kitty devito on it, proudly grinning his terrible cat grin</p><figure data-orig-width="800" data-orig-height="885" class="tmblr-full"><img src="https://41.media.tumblr.com/aca0ef3ca89612a513ef9143a439b48d/tumblr_inline_nnldwbZNR91qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="885"></figure><p>the thing that pushes this cup into the Far Reaches of Awful isnt just the image stamped on it. its that it is one hundred percent made from a mold of a styrofoam cup</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://40.media.tumblr.com/7ce202e1b1877d34c0211876cdbb575e/tumblr_inline_nnleakjIpO1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"></figure><p>its finger presses on the rim, those little lines going around</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://36.media.tumblr.com/75f6a2b06915bac6aec356d18f226a47/tumblr_inline_nnleefM9Ty1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"></figure><p>and all this jargon on the bottom, right under the glaze. the amount of effort that went into reproducing this styrofoam cup is incredible and i can stick it in my shelf and drink soup from it at four in the morning with danny devitos smug cat face looking out over everything i do, forever. follow your dreams</p>', u'post': {u'id': u'117728731307'}, u'is_root_item': True}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#FFFFFF', u'header_bounds': 0, u'title_font': u'Gibson', u'link_color': u'#56BC8A', u'header_image_focused': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'avatar_shape': u'square', u'show_avatar': False, u'background_color': u'#37475c', u'header_image': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040.gif'}, u'name': u'staff'}, u'content': u'<p>Have a follow-your-dreams weekend, Tumblr.</p>', u'post': {u'id': u'117887933455'}, u'is_current_item': True}], u'id': 117887933455L, u'post_url': u'http://staff.tumblr.com/post/117887933455/lauren-will-you-tell-us-a-story', u'answer': u'<p><a class="tumblr_blog" href="http://iguanamouth.tumblr.com/post/117728731307/lauren-will-you-tell-us-a-story">iguanamouth</a>:</p>\n\n<blockquote><p>ok heres something</p><p>around a year ago someone asked me to draw <a href="http://iguanamouth.tumblr.com/post/82902281208/draw-danny-devito-as-a-kitty">danny devito as a kitty</a>, spawning this terrible terrible image\xa0</p><figure data-orig-width="500" data-orig-height="406" class="tmblr-full"><img src="https://41.media.tumblr.com/d7549754fd8c427d3393eb702939652f/tumblr_inline_nnld4fWtJH1qmoaae_540.png" alt="image" data-orig-width="500" data-orig-height="406"/></figure><p>time passes. a lot of time passes. then two months ago i get an email from a group of people called <a href="https://www.facebook.com/fpoafm">FPOAFM</a> doing a pottery installation event, and theyre going around gathering artwork from artists to put onto cups and dishes to sell,, in exchange for a few pieces with the artists work on them</p><p>and i said SURE you can use some of my stuff \u2026 . but in exchange.\u2026 <b>\xa0i want something with kitty devito on it. </b>i dont care if you put it on anything else, but one item that i get in return has to have this cat man abomination</p><p>i give them my address and a few images and months pass. i forget about it. THEN literally two days ago i get this big package on my doorstep, and INSIDE OF IT\u2026. is the holy grail</p><p>in addition to <a href="https://40.media.tumblr.com/cdd10d787d5bd9c4ab797fca37671cb0/tumblr_nneimxvAoS1rhtthso2_r3_1280.png">two</a> <a href="https://40.media.tumblr.com/7e01bf6e04497f0c9da80ed0b83cc3df/tumblr_nneimxvAoS1rhtthso3_r2_540.png">plates</a> is this incredible porcelain cup with the fabled kitty devito on it, proudly grinning his terrible cat grin</p><figure data-orig-width="800" data-orig-height="885" class="tmblr-full"><img src="https://41.media.tumblr.com/aca0ef3ca89612a513ef9143a439b48d/tumblr_inline_nnldwbZNR91qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="885"/></figure><p>the thing that pushes this cup into the Far Reaches of Awful isnt just the image stamped on it. its that it is one hundred percent made from a mold of a styrofoam cup</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://40.media.tumblr.com/7ce202e1b1877d34c0211876cdbb575e/tumblr_inline_nnleakjIpO1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"/></figure><p>its finger presses on the rim, those little lines going around</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://36.media.tumblr.com/75f6a2b06915bac6aec356d18f226a47/tumblr_inline_nnleefM9Ty1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"/></figure><p>and all this jargon on the bottom, right under the glaze. the amount of effort that went into reproducing this styrofoam cup is incredible and i can stick it in my shelf and drink soup from it at four in the morning with danny devitos smug cat face looking out over everything i do, forever. follow your dreams</p></blockquote><p><p>Have a follow-your-dreams weekend, Tumblr.</p></p>', u'state': u'published', u'reblog': {u'tree_html': u'<p><a class="tumblr_blog" href="http://iguanamouth.tumblr.com/post/117728731307/lauren-will-you-tell-us-a-story">iguanamouth</a>:</p><blockquote><p>ok heres something</p><p>around a year ago someone asked me to draw <a href="http://iguanamouth.tumblr.com/post/82902281208/draw-danny-devito-as-a-kitty">danny devito as a kitty</a>, spawning this terrible terrible image\xa0</p><figure data-orig-width="500" data-orig-height="406" class="tmblr-full"><img src="https://41.media.tumblr.com/d7549754fd8c427d3393eb702939652f/tumblr_inline_nnld4fWtJH1qmoaae_540.png" alt="image" data-orig-width="500" data-orig-height="406"/></figure><p>time passes. a lot of time passes. then two months ago i get an email from a group of people called <a href="https://www.facebook.com/fpoafm">FPOAFM</a> doing a pottery installation event, and theyre going around gathering artwork from artists to put onto cups and dishes to sell,, in exchange for a few pieces with the artists work on them</p><p>and i said SURE you can use some of my stuff \u2026 . but in exchange.\u2026 <b>\xa0i want something with kitty devito on it. </b>i dont care if you put it on anything else, but one item that i get in return has to have this cat man abomination</p><p>i give them my address and a few images and months pass. i forget about it. THEN literally two days ago i get this big package on my doorstep, and INSIDE OF IT\u2026. is the holy grail</p><p>in addition to <a href="https://40.media.tumblr.com/cdd10d787d5bd9c4ab797fca37671cb0/tumblr_nneimxvAoS1rhtthso2_r3_1280.png">two</a> <a href="https://40.media.tumblr.com/7e01bf6e04497f0c9da80ed0b83cc3df/tumblr_nneimxvAoS1rhtthso3_r2_540.png">plates</a> is this incredible porcelain cup with the fabled kitty devito on it, proudly grinning his terrible cat grin</p><figure data-orig-width="800" data-orig-height="885" class="tmblr-full"><img src="https://41.media.tumblr.com/aca0ef3ca89612a513ef9143a439b48d/tumblr_inline_nnldwbZNR91qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="885"/></figure><p>the thing that pushes this cup into the Far Reaches of Awful isnt just the image stamped on it. its that it is one hundred percent made from a mold of a styrofoam cup</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://40.media.tumblr.com/7ce202e1b1877d34c0211876cdbb575e/tumblr_inline_nnleakjIpO1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"/></figure><p>its finger presses on the rim, those little lines going around</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://36.media.tumblr.com/75f6a2b06915bac6aec356d18f226a47/tumblr_inline_nnleefM9Ty1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"/></figure><p>and all this jargon on the bottom, right under the glaze. the amount of effort that went into reproducing this styrofoam cup is incredible and i can stick it in my shelf and drink soup from it at four in the morning with danny devitos smug cat face looking out over everything i do, forever. follow your dreams</p></blockquote>'}, u'short_url': u'http://tmblr.co/ZE5Fby1jognmF', u'date': u'2015-05-01 22:22:35 GMT', u'type': u'answer', u'slug': u'lauren-will-you-tell-us-a-story', u'blog_name': u'staff'}
        )
    logging.debug("result:"+repr(result))






def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","link_handlers_log.txt"))
        debug()
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
