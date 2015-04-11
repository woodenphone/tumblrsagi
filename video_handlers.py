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
from yt_dl_common import *
from utils import *
#from sql_functions import Media
from tables import *# This module only has the table classes
import sql_functions
import config # User settings



def crop_youtube_id(url):
    video_id_regex ="""youtube.com/(?:embed/)?(?:watch\?v=)?([a-zA-Z0-9]+)"""
    video_id_search = re.search(video_id_regex, url, re.IGNORECASE|re.DOTALL)
    if video_id_search:
        video_id = video_id_search.group(1)
        logging.debug("Extracted id: "+repr(video_id)+" from url: "+repr(url))
        return video_id
    else:
        return



# updated for new tables and yt-dl wrapper
def handle_youtube_video(session,post_dict):# NEW TABLES
    """Download youtube videos from video posts
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    assert(post_dict["type"] == u"video")# Ensure calling code isn't broken
    assert(post_dict["video_type"] == u"youtube")# Ensure calling code isn't broken

    logging.debug("Processing youtube video")
    video_page = post_dict["post_url"]
    post_id = str(post_dict["id"])
    logging.debug("video_page: "+repr(video_page))
    logging.debug("post_id: "+repr(post_id))

    # Extract youtube links from video field
    # ex. https://www.youtube.com/embed/lGIEmH3BoyA
    video_items = post_dict["player"]
    youtube_urls = []
    for video_item in video_items:
        # Get a youtube URL
        embed_code = video_item["embed_code"]
        # Skip if no embed code to process (Known to happen) "u'player': [{u'embed_code': False, u'width': 250},"
        if embed_code:
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"']+)\?"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                youtube_urls.append(embed_url)
        continue

    # Check if videos are already saved
    download_urls = []
    for youtube_url in youtube_urls:
        video_id = crop_youtube_id(youtube_url)
        # Look up ID in DB
        video_page_query = sqlalchemy.select([Media]).where(Media.video_id == video_id)
        video_page_rows = session.execute(video_page_query)
        video_page_row = video_page_rows.fetchone()
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
        else:
            download_urls.append(youtube_url)
        continue

    # Download videos if there are any
    video_dicts = []
    for download_url in download_urls:
        video_dict = run_yt_dl_single(
            session,
            download_url = download_url,
            extractor_used="handle_youtube_video",
            video_id = crop_youtube_id(download_url),
            )
        video_dicts.append(video_dict)
        continue

    # Join the info dicts together
    combined_video_dict =  merge_dicts(*video_dicts)# Join the dicts for different videos togather
    assert(type(combined_video_dict) is type({}))# Must be a dict

    return combined_video_dict






def handle_vimeo_videos(session,post_dict):# New table
    """Handle downloading of vimeo videos
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md"""
    logging.debug("Processing vimeo videos")
    post_id = str(post_dict["id"])
    # Extract video links from post dict
    video_items = post_dict["player"]
    vimeo_urls = []
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="250" height="156" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'
        # https://player.vimeo.com/video/118912193?
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"']+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                vimeo_urls.append(embed_url)
        continue

    # Deduplicate links
    vimeo_urls = uniquify(vimeo_urls)
    logging.debug("vimeo_urls: "+repr(vimeo_urls))

    # Skip IDs that have already been done
    download_urls = []
    for vimeo_url in vimeo_urls:
        video_page_row = sql_functions.lookup_media_url(
            session,
            table_class=Media,
            media_url=vimeo_url
            )
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
            continue
        download_urls.append(vimeo_url)
        continue
    logging.debug("download_urls: "+repr(download_urls))

    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        download_urls = download_urls,
        extractor_used="handle_vimeo_videos",
        )
    logging.debug("Finished downloading vimeo embeds")
    return combined_video_dict


def handle_imgur_videos(session,post_dict):# NEW TABLES
    """This is where I plan to put code for imgur videos"""
    logging.debug("Processing imgur videos")
    post_id = str(post_dict["id"])

    # Extract video links from post dict
    imgur_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'
        # http://i.imgur.com/wSBlRyv.gifv
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"'#]+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                imgur_urls.append(embed_url)
        continue

    # Deduplicate links
    imgur_urls = uniquify(imgur_urls)
    logging.debug("imgur_urls: "+repr(imgur_urls))

    # Skip IDs that have already been done
    download_urls = []
    for imgur_url in imgur_urls:
        video_page_row = sql_functions.lookup_media_url(
            session,
            table_class=Media,
            media_url=imgur_url
            )
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
            continue
        download_urls.append(imgur_url)
        continue
    logging.debug("download_urls: "+repr(download_urls))

    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        download_urls = download_urls,
        extractor_used="handle_imgur_videos",
        )
    logging.debug("Finished downloading imgur_video embeds")
    return combined_video_dict


def handle_vine_videos(session,post_dict):# New table
    """Handle downloading of vine videos
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md"""
    logging.debug("Processing vine videos")
    post_id = str(post_dict["id"])

    # Extract video links from post dict
    video_items = post_dict["player"]
    vine_urls = []
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="500" height="500" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'
        # https://vine.co/v/hjWIUFOYD31
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"']+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                vine_urls.append(embed_url)
        continue

    # Deduplicate links
    vine_urls = uniquify(vine_urls)
    logging.debug("vine_urls: "+repr(vine_urls))

    # Skip URLs that have already been done
    download_urls = []
    for vine_url in vine_urls:
        # Extract video ID
        # https://vine.co/v/hjWIUFOYD31/embed/simple -> hjWIUFOYD31
        id_regex ="""vine.co/v/([a-zA-Z0-9]+)/?"""
        id_search = re.search(id_regex, vine_url, re.IGNORECASE|re.DOTALL)
        if id_search:
            # Look up ID in media DB
            video_id = id_search.group(1)
            logging.debug("video_id: "+repr(video_id))
            video_page_row = sql_functions.lookup_media_url(
            session,
            table_class=Media,
            media_url=vine_url
            )
            if video_page_row:
                logging.debug("Skipping previously saved video: "+repr(video_page_row))
                continue
        download_urls.append(vine_url)
        continue
    logging.debug("download_urls: "+repr(download_urls))

    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        download_urls = download_urls,
        extractor_used="handle_vine_videos",
        )
    logging.debug("Finished downloading Vine embeds")
    return combined_video_dict


def handle_tumblr_videos(session,post_dict):
    """Download tumblr-hosted videos from video posts
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    logging.debug("Processing tumblr video")
    video_page = post_dict["post_url"]
    post_id = str(post_dict["id"])
    logging.debug("video_page: "+repr(video_page))
    logging.debug("post_id: "+repr(post_id))

    # Check if video is already saved, return URL:Hash pair if it is
    video_page_row = sql_functions.lookup_media_url(
            session,
            table_class=Media,
            media_url=video_page
            )
    if video_page_row:
        preexisting_filename = video_page_row["filename"]
        sha512base64_hash = video_page_row["sha512base64_hash"]
        return {video_page:sha512base64_hash}

    download_urls = [video_page]
    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        download_urls = download_urls,
        extractor_used="handle_tumblr_videos",
        )
    logging.debug("Finished downloading Tumblr embeds")
    return combined_video_dict


def handle_livestream_videos(session,post_dict):
    """This is where I plan to put code for imgur videos"""
    logging.debug("Processing livestream video")
    post_id = str(post_dict["id"])

    # Extract video links from post dict
    livestream_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="250" height="140" frameborder="0" scrolling="no"> </iframe>'
        # http://new.livestream.com/accounts/1249127/events/3464519/player?
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"'#]+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                livestream_urls.append(embed_url)
        continue

    # Deduplicate links
    livestream_urls = uniquify(livestream_urls)
    logging.debug("livestream_urls: "+repr(livestream_urls))

    # Skip IDs that have already been done
    download_urls = []
    for livestream_url in livestream_urls:
        video_page_row = sql_functions.lookup_media_url(
            session,
            table_class=Media,
            media_url=livestream_url
            )
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
            continue
        download_urls.append(livestream_url)
        continue
    logging.debug("download_urls: "+repr(download_urls))

    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        download_urls = download_urls,
        extractor_used="handle_livestream_videos",
        )

    logging.debug("Finished downloading livestream embeds")
    return combined_video_dict




def handle_yahoo_videos(session,post_dict):
    """TODO"""

    logging.debug("Processing yahoo video")
    post_id = str(post_dict["id"])

    # Extract video links from post dict
    yahoo_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="250" height="140" frameborder="0" scrolling="no"> </iframe>'
        # http://new.livestream.com/accounts/1249127/events/3464519/player?
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"'#]+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                yahoo_urls.append(embed_url)
        continue

    # Deduplicate links
    yahoo_urls = uniquify(yahoo_urls)
    logging.debug("yahoo_urls: "+repr(yahoo_urls))

    # Skip IDs that have already been done
    download_urls = []
    for yahoo_url in yahoo_urls:
        video_page_row = sql_functions.lookup_media_url(
            session,
            table_class=Media,
            media_url=yahoo_url
            )
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
            continue
        download_urls.append(yahoo_url)
        continue
    logging.debug("download_urls: "+repr(download_urls))

    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        download_urls = download_urls,
        extractor_used="handle_yahoo_videos",
        )

    logging.debug("Finished downloading yahoo embeds")
    return combined_video_dict


    assert(False)# Unimplimented
    pass



def handle_video_posts(session,post_dict):
    """Decide which video functions to run and pass back what they return"""
    # Check if post is a video post
    if post_dict["type"] != u"video":
        return {}
    logging.debug("Post is video")
    # Youtube
    if post_dict["video_type"] == u"youtube":
        logging.debug("Post is youtube")
        return handle_youtube_video(session,post_dict)
    # Tumblr
    elif post_dict["video_type"] == u"tumblr":
        logging.debug("Post is tumblr video")
        return handle_tumblr_videos(session,post_dict)
    # Vine
    elif post_dict["video_type"] == u"vine":
        logging.debug("Post is vine video")
        return handle_vine_videos(session,post_dict)
    # vimeo
    elif post_dict["video_type"] == u"vimeo":
        logging.debug("Post is vimeo video")
        return handle_vimeo_videos(session,post_dict)
    # Yahoo
    elif post_dict["video_type"] == u"yahoo":
        logging.debug("Post is yahoo video")
        return handle_yahoo_videos(session,post_dict)
    # "unknown" - special cases?
    elif (post_dict["video_type"] == u"unknown"):
        logging.warning("API reports video type as unknown, handlers may be inappropriate or absent.")
        # imgur
        if "imgur-embed" in repr(post_dict["player"]):
            logging.debug("Post is imgur video")
            return handle_imgur_videos(session,post_dict)
        # Livestream
        elif "livestream.com" in repr(post_dict["player"]):
            logging.debug("Post is livestream video")
            return handle_livestream_videos(session,post_dict)
    # If no handler is applicable, stop for fixing
    logging.error("Unknown video type!")
    logging.error("locals(): "+repr(locals()))
    assert(False)# Not implimented
    return {}


def debug():
    """For WIP, debug, ect function calls"""
    session = sql_functions.connect_to_db()

    # Youtube
    youtube_dict_1 = {u'reblog_key': u'HfjckfH7', u'short_url': u'http://tmblr.co/ZUGffq1cfuHuJ', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}], u'id': 110224285203L, u'post_url': u'http://askbuttonsmom.tumblr.com/post/110224285203/throwback-can-you-believe-its-been-almost-2yrs', u'tags': [u"button's mom", u'hardcopy', u'song', u'shadyvox'], u'highlighted': [], u'state': u'published', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1423197599, u'note_count': 145, u'video_type': u'youtube', u'date': u'2015-02-06 04:39:59 GMT', u'thumbnail_height': 360, u'permalink_url': u'https://www.youtube.com/watch?v=lGIEmH3BoyA', u'slug': u'throwback-can-you-believe-its-been-almost-2yrs', u'blog_name': u'askbuttonsmom', u'caption': u'<p>Throwback! Can you believe it&#8217;s been almost 2yrs since this came out? Mommy&#8217;s getting old&#8230;</p>', u'thumbnail_url': u'https://i.ytimg.com/vi/lGIEmH3BoyA/hqdefault.jpg'}
    youtube_dict_2 = {u'highlighted': [], u'reblog_key': u'qO3JnfS7', u'player': [{u'width': 250, u'embed_code': False}, {u'width': 400, u'embed_code': False}, {u'width': 500, u'embed_code': False}], u'format': u'html', u'timestamp': 1390412461, u'note_count': 4282, u'tags': [], u'video_type': u'youtube', u'id': 74184911379L, u'post_url': u'http://askbuttonsmom.tumblr.com/post/74184911379/ask-thecrusaders-bar-buddies-dont-worry', u'caption': u'<p><a class="tumblr_blog" href="http://ask-thecrusaders.tumblr.com/post/74162414750/bar-buddies-dont-worry-neon-you-will-have-your">ask-thecrusaders</a>:</p>\n<blockquote>\n<p><strong>"Bar Buddies"</strong><br/><br/>Dont\u2019 worry Neon, you will have your music video soon enough.</p>\n</blockquote>\n<p>Honestly, that Neon Lights is a TERRIBLE influence!! No son of mine will grow up to be a drunken drug-shooting bass dropping hipster! :C</p>', u'state': u'published', u'html5_capable': False, u'reblog': {u'comment': u'<p>Honestly, that Neon Lights is a TERRIBLE influence!! No son of mine will grow up to be a drunken drug-shooting bass dropping hipster! :C</p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://ask-thecrusaders.tumblr.com/post/74162414750/bar-buddies-dont-worry-neon-you-will-have-your">ask-thecrusaders</a>:</p><blockquote>\n<p><strong>"Bar Buddies"</strong><br/><br/>Dont\u2019 worry Neon, you will have your music video soon enough.</p>\n</blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'title_font': u'Helvetica Neue', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'avatar_shape': u'circle', u'show_avatar': True, u'background_color': u'#F6F6F6', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f'}, u'name': u'ask-thecrusaders'}, u'comment': u'<p><strong>"Bar Buddies"</strong><br><br>Dont\u2019 worry Neon, you will have your music video soon enough.</p>', u'post': {u'id': u'74162414750'}}]}, u'short_url': u'http://tmblr.co/ZUGffq155m_eJ', u'date': u'2014-01-22 17:41:01 GMT', u'type': u'video', u'slug': u'ask-thecrusaders-bar-buddies-dont-worry', u'blog_name': u'askbuttonsmom'}
    youtube_result_1 = handle_video_posts(session,youtube_dict_1)
    youtube_result_2 = handle_video_posts(session,youtube_dict_2)

    # Vimeo
    vimeo_dict_1 = {u'reblog_key': u'3BuzwM1q', u'reblog': {u'comment': u'', u'tree_html': u'<p><a href="http://robscorner.tumblr.com/post/110250942998/a-hyperfast-preview-video-for-the-kind-of-content" class="tumblr_blog">robscorner</a>:</p><blockquote><p>A hyperfast preview video for the kind of content I\u2019m featuring on Patreon (patreon.com/robaato)! Slower version will be available for my supporters!<br/>MUSIC: The End (T.E.I.N. Pt. 2) | 12th Planet<br/></p><p>Support for high-resolution art, PSDs, process videos, tutorials, character requests, and more!<br/></p></blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 1071, u'title_color': u'#FFFFFF', u'header_bounds': u'92,1581,978,3', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/a5a733e78671519e8eb9cf3700ccfb70/ybimlef/1eon5zyi0/tumblr_static_tumblr_static_2df9bnxrqh1c4c8sgk8448s80_focused_v3.jpg', u'show_description': False, u'header_full_width': 1600, u'header_focus_width': 1578, u'header_stretch': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/cfa3addece89b58093ea0a8a87082653/ybimlef/FWyn5zyhv/tumblr_static_2df9bnxrqh1c4c8sgk8448s80_2048_v2.png', u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 886, u'background_color': u'#337db1', u'header_image': u'http://static.tumblr.com/cfa3addece89b58093ea0a8a87082653/ybimlef/FWyn5zyhv/tumblr_static_2df9bnxrqh1c4c8sgk8448s80.png'}, u'name': u'robscorner'}, u'comment': u'<p>A hyperfast preview video for the kind of content I\u2019m featuring on Patreon (patreon.com/robaato)! Slower version will be available for my supporters!<br>MUSIC: The End (T.E.I.N. Pt. 2) | 12th Planet<br></p><p>Support for high-resolution art, PSDs, process videos, tutorials, character requests, and more!<br></p>', u'post': {u'id': u'110250942998'}}]}, u'thumbnail_width': 295, u'player': [{u'width': 250, u'embed_code': u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="250" height="156" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="400" height="250" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="500" height="312" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'}], u'id': 110255840681, u'post_url': u'http://nsfw.kevinsano.com/post/110255840681/robscorner-a-hyperfast-preview-video-for-the-kind', u'source_title': u'robscorner', u'tags': [u'reblog', u'erohua'], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/Zo9zBq1chmfsf', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1423238010, u'note_count': 415, u'video_type': u'vimeo', u'source_url': u'http://robscorner.tumblr.com/post/110250942998/a-hyperfast-preview-video-for-the-kind-of-content', u'date': u'2015-02-06 15:53:30 GMT', u'thumbnail_height': 184, u'permalink_url': u'https://vimeo.com/118912193', u'slug': u'robscorner-a-hyperfast-preview-video-for-the-kind', u'blog_name': u'nsfwkevinsano', u'caption': u'<p><a href="http://robscorner.tumblr.com/post/110250942998/a-hyperfast-preview-video-for-the-kind-of-content" class="tumblr_blog">robscorner</a>:</p><blockquote><p>A hyperfast preview video for the kind of content I\u2019m featuring on Patreon (patreon.com/robaato)! Slower version will be available for my supporters!<br/>MUSIC: The End (T.E.I.N. Pt. 2) | 12th Planet<br/></p><p>Support for high-resolution art, PSDs, process videos, tutorials, character requests, and more!<br/></p></blockquote>', u'thumbnail_url': u'https://i.vimeocdn.com/video/506047324_295x166.jpg'}
    vimeo_result_1 = handle_video_posts(session,vimeo_dict_1)

    # Imgur
    imgur_post_dict = {u'highlighted': [], u'reblog_key': u'qX0EtplN', u'player': [{u'width': 250, u'embed_code': u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'}, {u'width': 400, u'embed_code': u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'}, {u'width': 500, u'embed_code': u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'}], u'format': u'html', u'timestamp': 1415466120, u'note_count': 109, u'tags': [], u'thumbnail_width': 0, u'id': 102102282191, u'post_url': u'http://jessicaanner.tumblr.com/post/102102282191/front-view-clothed-large-version-gif-back', u'caption': u'<p><em><strong><a href="http://jessicaanner.tumblr.com/post/101601852991/front-view-clothed-large-version-gif-back">Front View (Clothed)</a> <a href="http://i.imgur.com/fDixfAC.gifv"><span class="auto_link" title="">(Large version)</span></a><a href="http://d.facdn.net/art/benezia/1414952655.benezia_front_armored_optimized.gif"><span class="auto_link" title=""> (GIF)</span></a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/101666148721/front-view-clothed-large-version-gif-back">Back View (Clothed)</a> <a href="http://i.imgur.com/QYfRNeQ.gifv" title="">(Large version)</a> <a href="http://d.facdn.net/art/benezia/1415012804.benezia_back_armored_optimized.gif">(GIF)</a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/101768307896/front-view-clothed-large-version-gif-back">Front View (Nude)</a> <a href="http://i.imgur.com/0N7ir7o.gifv">(Large version)</a> <a href="http://d.facdn.net/art/benezia/1415120393.benezia_front_nude_optimized.gif" title="">(GIF)</a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/101852253284/front-view-clothed-large-version-gif-back">Back View (Nude)</a> <a href="http://i.imgur.com/sP5h9ux.gifv" title="">(Large version)</a> <a href="http://d.facdn.net/art/benezia/1415120590.benezia_back_nude_optimized.gif" title="">(GIF)</a></strong></em><br/><strong><em><a href="http://jessicaanner.tumblr.com/post/101934955336/front-view-clothed-large-version-gif-back">Buttocks Closeup View</a> <a href="http://i.imgur.com/BXMYuxk.gifv" title="">(Large version)</a> <a href="http://i.imgur.com/3bhzRP2.gif">(GIF)</a></em></strong><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/102102282191/front-view-clothed-large-version-gif-back">Crotch Closeup View</a> <a href="http://i.imgur.com/wSBlRyv.gifv">(Large version)</a> <a href="http://i.imgur.com/UiDU1XB.gif">(GIF)</a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/102017653601/front-view-clothed-large-version-gif-back">Bust Closeup View</a> <a href="http://i.imgur.com/S5M6PID.gifv">(Large version)</a> <a href="http://i.imgur.com/BlMYohP.gif">(GIF)</a></strong></em></p>', u'state': u'published', u'html5_capable': False, u'video_type': u'unknown', u'short_url': u'http://tmblr.co/ZLO7Om1V5nI-F', u'date': u'2014-11-08 17:02:00 GMT', u'thumbnail_height': 0, u'thumbnail_url': u'', u'type': u'video', u'slug': u'front-view-clothed-large-version-gif-back', u'blog_name': u'jessicaanner'}
    imgur_result = handle_video_posts(session,imgur_post_dict)

    # Vine
    vine_dict = {u'reblog_key': u'A5DhHt28', u'reblog': {u'comment': u'<p>Have a nice weekend, Tumblr.&nbsp;</p>', u'tree_html': u'', u'trail': []}, u'placement_id': u'{"i":"mF4avY6GyshXjaQmfk0v","v":4,"t":1427193020,"c":{"p":"113540981790","b":"staff"},"d":{"v":{"e":"hjWIUFOYD31"}},"h":"3291f1aa07"}', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="250" height="250" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}, {u'width': 400, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="400" height="400" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}, {u'width': 500, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="500" height="500" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}], u'id': 113540981790L, u'post_url': u'http://staff.tumblr.com/post/113540981790/have-a-nice-weekend-tumblr', u'source_title': u'weloveshortvideos.com', u'tags': [], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZE5Fby1flaUGU', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1426282797, u'note_count': 48309, u'video_type': u'vine', u'source_url': u'http://weloveshortvideos.com', u'date': u'2015-03-13 21:39:57 GMT', u'thumbnail_height': 480, u'permalink_url': u'https://vine.co/v/hjWIUFOYD31', u'slug': u'have-a-nice-weekend-tumblr', u'blog_name': u'staff', u'caption': u'<p>Have a nice weekend, Tumblr.\xa0</p>', u'thumbnail_url': u'http://v.cdn.vine.co/r/thumbs/FE4C8DC8781008139866036658176_1c16044fdd3.3.4.mp4_l_pAXVyCckNVnk2OzdadqNB_6bq4mYoBHpBFRIF8Hi3OdOW1vmjP1TR075G1ZegT.jpg?versionId=abawWSw4Y_QFv2TKPWz6j8N5y7.6LOGq'}
    vine_restult = handle_video_posts(session,vine_dict)

    # Tumblr
    tumblr_video_post_dict = {u'reblog_key': u'3bqfxHgy', u'short_url': u'http://tmblr.co/Z_sLQw1eYTSqS', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}], u'id': 112247295260L, u'post_url': u'http://tsitra360.tumblr.com/post/112247295260/my-latest-art-timelapse-is-up-see-how-i-drew', u'tags': [], u'highlighted': [], u'state': u'published', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1425068852, u'note_count': 79, u'video_type': u'youtube', u'date': u'2015-02-27 20:27:32 GMT', u'thumbnail_height': 360, u'permalink_url': u'https://www.youtube.com/watch?v=tT5pifkZzEk', u'slug': u'my-latest-art-timelapse-is-up-see-how-i-drew', u'blog_name': u'tsitra360', u'caption': u'<p>My latest art timelapse is up! See how I drew Berry Swirl on my youtube channel.</p>', u'thumbnail_url': u'https://i.ytimg.com/vi/tT5pifkZzEk/hqdefault.jpg'}
    tumblr_Result = handle_video_posts(session,tumblr_video_post_dict)

    # Yahoo video
    yahoo_post_dict = {u'reblog_key': u'GGWw7A77', u'reblog': {u'comment': u'<p>It&rsquo;s really happening!</p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://whitehouse.tumblr.com/post/88396016693/obamairl">whitehouse</a>:</p><blockquote>\n<p>President Obama is answering your questions on education and college affordability in his first-ever Tumblr Q&amp;A today.</p>\n<p>Tune in right here at 4 p.m. ET, and make sure to follow us @<a class="tumblelog" href="http://tmblr.co/mWgXp6TEB4GEsC_jKXfrSvw">whitehouse</a>.</p>\n</blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 1056, u'title_color': u'#444444', u'header_bounds': u'43,1500,887,0', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/861cd9f032b93a7ace681b4fcb7d05e4/mjqkjev/pEEn56435/tumblr_static_tumblr_static_17trsnvc8xes0og8kgk88coc0_focused_v3.jpg', u'show_description': True, u'header_full_width': 1500, u'header_focus_width': 1500, u'header_stretch': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/861cd9f032b93a7ace681b4fcb7d05e4/mjqkjev/sgln56432/tumblr_static_17trsnvc8xes0og8kgk88coc0_2048_v2.jpg', u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 844, u'background_color': u'#FAFAFA', u'header_image': u'http://static.tumblr.com/861cd9f032b93a7ace681b4fcb7d05e4/mjqkjev/sgln56432/tumblr_static_17trsnvc8xes0og8kgk88coc0.jpg'}, u'name': u'whitehouse'}, u'comment': u'<p>President Obama is answering your questions on education and college affordability in his first-ever Tumblr Q&A today.</p>\n<p>Tune in right here at 4 p.m. ET, and make sure to follow us @<a class="tumblelog" href="http://tmblr.co/mWgXp6TEB4GEsC_jKXfrSvw">whitehouse</a>.</p>', u'post': {u'id': u'88396016693'}}]}, u'thumbnail_width': 320, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" src="https://news.yahoo.com/video/tumblr-goes-white-house-190000218.html?format=embed" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" src="https://news.yahoo.com/video/tumblr-goes-white-house-190000218.html?format=embed" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" src="https://news.yahoo.com/video/tumblr-goes-white-house-190000218.html?format=embed" frameborder="0" allowfullscreen></iframe>'}], u'id': 88400573880, u'post_url': u'http://staff.tumblr.com/post/88400573880/whitehouse-president-obama-is-answering-your', u'tags': [u'ObamaIRL'], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZE5Fby1IL5RMu', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1402430040, u'note_count': 9899, u'video_type': u'yahoo', u'date': u'2014-06-10 19:54:00 GMT', u'thumbnail_height': 180, u'permalink_url': u'https://news.yahoo.com/video/tumblr-goes-white-house-190000218.html', u'slug': u'whitehouse-president-obama-is-answering-your', u'blog_name': u'staff', u'caption': u'<p><a class="tumblr_blog" href="http://whitehouse.tumblr.com/post/88396016693/obamairl">whitehouse</a>:</p>\n<blockquote>\n<p>President Obama is answering your questions on education and college affordability in his first-ever Tumblr Q&amp;A today.</p>\n<p>Tune in right here at 4 p.m. ET, and make sure to follow us @<a class="tumblelog" href="http://tmblr.co/mWgXp6TEB4GEsC_jKXfrSvw">whitehouse</a>.</p>\n</blockquote>\n<p>It\u2019s really happening!</p>', u'thumbnail_url': u'https://s1.yimg.com/uu/api/res/1.2/JW58D_.UFfRLkBOrIemIXw--/dz0zMjA7c209MTtmaT1maWxsO3B5b2ZmPTA7aD0xODA7YXBwaWQ9eXRhY2h5b24-/http://l.yimg.com/os/publish-images/ivy/2014-06-10/912811c0-f0c6-11e3-bb53-bd3ad1c7b3ec_06102014_tumblr_white_house.jpg'}
    yahoo_result = handle_video_posts(session,yahoo_post_dict)


    # Livestream
    livestream_post_dict ={u'reblog_key': u'oapXWQlr', u'reblog': {u'comment': u'<p><span>To reiterate: this an&nbsp;</span><strong>only</strong><span>&nbsp;and an&nbsp;</span><strong>exclusive&nbsp;</strong><span>and it&nbsp;</span><strong>starts in just a few minutes</strong><span>. Hurry on over. &nbsp;</span></p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://92y.tumblr.com/post/101031505431/watch-the-92y-livestream-of-game-of-thrones">92y</a>:</p><blockquote>\n<p>Watch the 92Y Livestream of <strong>Game of Thrones</strong> creator <strong>George R.R. Martin, TONIGHT at 8\xa0pm ET</strong>, in his <strong>only</strong> public U.S. appearance for the release of <a href="http://www.amazon.com/gp/product/B00EGMGGVK/ref=as_li_tl?ie=UTF8&amp;camp=1789&amp;creative=390957&amp;creativeASIN=B00EGMGGVK&amp;linkCode=as2&amp;tag=92y-20&amp;linkId=V3MMY57QIQ7QVFNK"><em>The World of Ice and Fire: The Untold History of Westeros and the Game of Thrones</em></a>. Exclusively on Tumblr!</p>\n</blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_13_focused_v3.png?_v=2f4063be1dd2ee91e4eca54332e25191', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_13_focused_v3.png?_v=2f4063be1dd2ee91e4eca54332e25191', u'avatar_shape': u'square', u'show_avatar': True, u'background_color': u'#FAFAFA', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_13.png?_v=2f4063be1dd2ee91e4eca54332e25191'}, u'name': u'92y'}, u'comment': u'<p>Watch the 92Y Livestream of <strong>Game of Thrones</strong> creator <strong>George R.R. Martin, TONIGHT at 8\xa0pm ET</strong>, in his <strong>only</strong> public U.S. appearance for the release of <a href="http://www.amazon.com/gp/product/B00EGMGGVK/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B00EGMGGVK&linkCode=as2&tag=92y-20&linkId=V3MMY57QIQ7QVFNK"><em>The World of Ice and Fire: The Untold History of Westeros and the Game of Thrones</em></a>. Exclusively on Tumblr!</p>', u'post': {u'id': u'101031505431'}}]}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="250" height="140" frameborder="0" scrolling="no"> </iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="400" height="225" frameborder="0" scrolling="no"> </iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="500" height="281" frameborder="0" scrolling="no"> </iframe>'}], u'id': 101038462325, u'post_url': u'http://staff.tumblr.com/post/101038462325/92y-watch-the-92y-livestream-of-game-of-thrones', u'tags': [], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZE5Fby1U6N9Lr', u'html5_capable': False, u'type': u'video', u'format': u'html', u'timestamp': 1414366397, u'note_count': 917, u'video_type': u'unknown', u'date': u'2014-10-26 23:33:17 GMT', u'thumbnail_height': 0, u'slug': u'92y-watch-the-92y-livestream-of-game-of-thrones', u'blog_name': u'staff', u'caption': u'<p><a class="tumblr_blog" href="http://92y.tumblr.com/post/101031505431/watch-the-92y-livestream-of-game-of-thrones">92y</a>:</p>\n<blockquote>\n<p>Watch the 92Y Livestream of <strong>Game of Thrones</strong> creator <strong>George R.R. Martin, TONIGHT at 8\xa0pm ET</strong>, in his <strong>only</strong> public U.S. appearance for the release of <a href="http://www.amazon.com/gp/product/B00EGMGGVK/ref=as_li_tl?ie=UTF8&amp;camp=1789&amp;creative=390957&amp;creativeASIN=B00EGMGGVK&amp;linkCode=as2&amp;tag=92y-20&amp;linkId=V3MMY57QIQ7QVFNK"><em>The World of Ice and Fire: The Untold History of Westeros and the Game of Thrones</em></a>. Exclusively on Tumblr!</p>\n</blockquote>\n<p><span>To reiterate: this an\xa0</span><strong>only</strong><span>\xa0and an\xa0</span><strong>exclusive\xa0</strong><span>and it\xa0</span><strong>starts in just a few minutes</strong><span>. Hurry on over. \xa0</span></p>', u'thumbnail_url': u''}
    livestream_result = handle_video_posts(session,livestream_post_dict)

    return


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","video-handlers-log.txt"))
        debug()
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
