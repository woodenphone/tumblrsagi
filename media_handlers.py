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
# Media handler modules
import audio_handlers
import video_handlers
import link_handlers
from image_handlers import *






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





def handle_thumbnail(session,post_dict):
    if "thumbnail_url" in post_dict.keys():
        logging.debug("Saving thumbnail")
        thumbnail_link = [post_dict["thumbnail_url"]]
        link_hash_dict = download_image_links(session,thumbnail_link)
    return link_hash_dict# {link:hash}


def handle_tumblr_photos(session,post_dict):
    """Download the photos section from tumblr posts"""
    # Return if post has no photos
    if "photos" not in post_dict.keys():
        return {}
    # Grab photo links from API dict
    photos_list = post_dict["photos"]
    logging.debug("photos_list: "+repr(photos_list))
    photo_url_list = []
    for photo_dict in photos_list:
        # Grab original size url
        logging.debug("photo_dict: "+repr(photo_dict))
        original_size_url = photo_dict["original_size"]["url"]
        logging.debug("original_size_url: "+repr(original_size_url))
        photo_url_list.append(original_size_url)
        if config.save_all_photo_sizes:
            # Grab alt size urls
            alt_sizes_list = photo_dict["alt_sizes"]
            for alt_size_dict in alt_sizes_list:
                alt_size_url = alt_size_dict["url"]
                photo_url_list.append(alt_size_url)
    logging.debug("photo_url_list: "+repr(photo_url_list))
    # Save new photo links
    link_hash_dict = download_image_links(session,photo_url_list)
    return link_hash_dict# {link:hash}








def save_media(session,post_dict):
    """ Main function for saving a posts media
    return post dict with links replaced by pointers to saved file in the database"""
    #logging.info("Saving post media")
    #logging.debug("post_dict"+repr(post_dict))
    logging.debug('post_dict["type"] '+repr(post_dict["type"] ))

    # Save anything not provided directly through the tumblr API (Remote) ex. http://foo.com/image.jpg
    # I.E. Links (<a href = "http://example.com/image.png">blah</a>)
    if config.save_external_links:
        remote_link_dict = link_handlers.handle_links(session,post_dict)# TODO FIXME
    else:
        remote_link_dict = {}
    # Save photos sections (Tumblr)
    if config.save_photos:
        tumblr_photos_link_dict = handle_tumblr_photos(session,post_dict)# {link:hash}
    else:
        tumblr_photos_link_dict = {}
    # Save videos, both tumblr and youtube (Tumblr & Youtube)
    if config.save_videos:
        video_embed_dict = video_handlers.handle_video_posts(session,post_dict)
    else:
        video_embed_dict = {}
    # Save audio
    if config.save_audio:
        audio_embed_dict = audio_handlers.handle_audio_posts(session,post_dict)
    else:
        audio_embed_dict = {}
    # Join mapping dicts # {link:hash}
    link_to_hash_dict = merge_dicts(
    remote_link_dict,
    tumblr_photos_link_dict,
    video_embed_dict,
    audio_embed_dict,
    )
    # Replace links with marker string
    logging.debug("link_to_hash_dict: "+repr(link_to_hash_dict))
    new_post_dict = replace_links(link_to_hash_dict,post_dict)
    new_post_dict["link_to_hash_dict"] = link_to_hash_dict
    logging.debug("new_post_dict: "+repr(new_post_dict))
    return new_post_dict


def debug():
    """Code for debugging during programming goes here so everything is logged to file"""
    session = sql_functions.connect_to_db()

    # Debug video DB check
    #sql_functions.check_if_video_in_db(connection,media_url="https://www.youtube.com/embed/lGIEmH3BoyA",youtube_id=None,sha512base64_hash=None,post_id=None)
    #return

    # Debug images
    logging.debug("Debug images")
    image_post_dict = {u'highlighted': [], u'reblog_key': u'RSNOnudd', u'format': u'html', u'timestamp': 1401396780, u'note_count': 429, u'tags': [u'porn', u'furry', u'anthro', u'art', u'fantasy', u'compilation', u'myart', u'futa', u'female', u'nude', u'werewolf'], 'link_to_hash_dict': {}, u'photos': [{u'caption': u'My character Gwen, the hermaphrodite Unicorn. Short for I Guinevere.', u'original_size': {u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_1280.jpg', u'width': 1280, u'height': 1739}, u'alt_sizes': [{u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_1280.jpg', u'width': 1280, u'height': 1739}, {u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_500.jpg', u'width': 500, u'height': 679}, {u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_400.jpg', u'width': 400, u'height': 543}, {u'url': u'http://40.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_250.jpg', u'width': 250, u'height': 340}, {u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_100.jpg', u'width': 100, u'height': 136}, {u'url': u'http://41.media.tumblr.com/51dc06d26888063e978967b9effdd79d/tumblr_n6csptiJ5u1rzato1o1_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'A young man and one of his harem concubines.', u'original_size': {u'url': u'http://40.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_1280.jpg', u'width': 1280, u'height': 1037}, u'alt_sizes': [{u'url': u'http://40.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_1280.jpg', u'width': 1280, u'height': 1037}, {u'url': u'http://40.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_500.jpg', u'width': 500, u'height': 405}, {u'url': u'http://41.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_400.jpg', u'width': 400, u'height': 324}, {u'url': u'http://40.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_250.jpg', u'width': 250, u'height': 203}, {u'url': u'http://41.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_100.jpg', u'width': 100, u'height': 81}, {u'url': u'http://40.media.tumblr.com/df5d6e743955acef44262810e7e68196/tumblr_n6csptiJ5u1rzato1o2_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'Gift-art for Robotjoe at FA.', u'original_size': {u'url': u'http://40.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_1280.jpg', u'width': 1280, u'height': 1280}, u'alt_sizes': [{u'url': u'http://40.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_1280.jpg', u'width': 1280, u'height': 1280}, {u'url': u'http://41.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_500.jpg', u'width': 500, u'height': 500}, {u'url': u'http://41.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_400.jpg', u'width': 400, u'height': 400}, {u'url': u'http://41.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_250.jpg', u'width': 250, u'height': 250}, {u'url': u'http://40.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_100.jpg', u'width': 100, u'height': 100}, {u'url': u'http://40.media.tumblr.com/027e4e40a7b6dd7437ba19bb0bf66394/tumblr_n6csptiJ5u1rzato1o3_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'Giftart for Ritts at FA.', u'original_size': {u'url': u'http://41.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_1280.jpg', u'width': 1280, u'height': 1152}, u'alt_sizes': [{u'url': u'http://41.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_1280.jpg', u'width': 1280, u'height': 1152}, {u'url': u'http://40.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_500.jpg', u'width': 500, u'height': 450}, {u'url': u'http://40.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_400.jpg', u'width': 400, u'height': 360}, {u'url': u'http://40.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_250.jpg', u'width': 250, u'height': 225}, {u'url': u'http://40.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_100.jpg', u'width': 100, u'height': 90}, {u'url': u'http://41.media.tumblr.com/b04099342f13a3aaad3ef8d7f9f3080f/tumblr_n6csptiJ5u1rzato1o4_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'', u'original_size': {u'url': u'http://41.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_1280.jpg', u'width': 1153, u'height': 1920}, u'alt_sizes': [{u'url': u'http://41.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_1280.jpg', u'width': 1153, u'height': 1920}, {u'url': u'http://40.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_500.jpg', u'width': 450, u'height': 750}, {u'url': u'http://40.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_400.jpg', u'width': 360, u'height': 600}, {u'url': u'http://40.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_250.jpg', u'width': 240, u'height': 400}, {u'url': u'http://41.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_100.jpg', u'width': 100, u'height': 167}, {u'url': u'http://36.media.tumblr.com/96a2f5867ff3269def55cba3ddb42282/tumblr_n6csptiJ5u1rzato1o5_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'She shot herself in the face, or did others? Up to you.', u'original_size': {u'url': u'http://41.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_1280.jpg', u'width': 841, u'height': 1400}, u'alt_sizes': [{u'url': u'http://41.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_1280.jpg', u'width': 841, u'height': 1400}, {u'url': u'http://40.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_500.jpg', u'width': 451, u'height': 750}, {u'url': u'http://41.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_400.jpg', u'width': 360, u'height': 600}, {u'url': u'http://40.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_250.jpg', u'width': 240, u'height': 400}, {u'url': u'http://40.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_100.jpg', u'width': 100, u'height': 166}, {u'url': u'http://36.media.tumblr.com/879c064933cf138ae169a152dbd717a4/tumblr_n6csptiJ5u1rzato1o6_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u"They're now twins.", u'original_size': {u'url': u'http://36.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_1280.jpg', u'width': 1153, u'height': 1920}, u'alt_sizes': [{u'url': u'http://36.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_1280.jpg', u'width': 1153, u'height': 1920}, {u'url': u'http://36.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_500.jpg', u'width': 450, u'height': 750}, {u'url': u'http://41.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_400.jpg', u'width': 360, u'height': 600}, {u'url': u'http://40.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_250.jpg', u'width': 240, u'height': 400}, {u'url': u'http://41.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_100.jpg', u'width': 100, u'height': 167}, {u'url': u'http://41.media.tumblr.com/56df999c75b2ea6e10d9e9e3a4248db6/tumblr_n6csptiJ5u1rzato1o7_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'This is knot a funny joke.', u'original_size': {u'url': u'http://36.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_1280.jpg', u'width': 1000, u'height': 1000}, u'alt_sizes': [{u'url': u'http://36.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_1280.jpg', u'width': 1000, u'height': 1000}, {u'url': u'http://40.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_500.jpg', u'width': 500, u'height': 500}, {u'url': u'http://40.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_400.jpg', u'width': 400, u'height': 400}, {u'url': u'http://36.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_250.jpg', u'width': 250, u'height': 250}, {u'url': u'http://40.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_100.jpg', u'width': 100, u'height': 100}, {u'url': u'http://40.media.tumblr.com/dd7b3f0723d26d0cf9a5daff5cb82e8a/tumblr_n6csptiJ5u1rzato1o8_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'Gift-art for Quillu at FA.', u'original_size': {u'url': u'http://41.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_1280.jpg', u'width': 800, u'height': 1410}, u'alt_sizes': [{u'url': u'http://41.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_1280.jpg', u'width': 800, u'height': 1410}, {u'url': u'http://40.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_500.jpg', u'width': 426, u'height': 750}, {u'url': u'http://41.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_400.jpg', u'width': 340, u'height': 600}, {u'url': u'http://41.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_250.jpg', u'width': 227, u'height': 400}, {u'url': u'http://40.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_100.jpg', u'width': 100, u'height': 176}, {u'url': u'http://41.media.tumblr.com/e02229ba14b4fb3be2866595e371aaa7/tumblr_n6csptiJ5u1rzato1o9_75sq.jpg', u'width': 75, u'height': 75}]}, {u'caption': u'Werewolf herm, in heat. Watch out!', u'original_size': {u'url': u'http://36.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_1280.jpg', u'width': 1280, u'height': 962}, u'alt_sizes': [{u'url': u'http://36.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_1280.jpg', u'width': 1280, u'height': 962}, {u'url': u'http://41.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_500.jpg', u'width': 500, u'height': 376}, {u'url': u'http://41.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_400.jpg', u'width': 400, u'height': 301}, {u'url': u'http://36.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_250.jpg', u'width': 250, u'height': 188}, {u'url': u'http://36.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_100.jpg', u'width': 100, u'height': 75}, {u'url': u'http://40.media.tumblr.com/3a23e75b564f5d790bb440ba2ba6140c/tumblr_n6csptiJ5u1rzato1o10_75sq.jpg', u'width': 75, u'height': 75}]}], u'id': 87231460597L, u'post_url': u'http://zaggatar.tumblr.com/post/87231460597/i-thought-i-would-upload-some-of-what-i-think-is', u'caption': u'<p><span>I thought I would upload s</span>ome of what I think is best of my older stuff.</p>\n<p>As you can see, I am guilty for liking horsegirls with big dicks.</p>\n<p>Enjoy.</p>', u'state': u'published', u'short_url': u'http://tmblr.co/Zlxuxu1HFPdJr', u'date': u'2014-05-29 20:53:00 GMT', u'type': u'photo', u'slug': u'i-thought-i-would-upload-some-of-what-i-think-is', u'photoset_layout': u'1111111111', u'blog_name': u'zaggatar'}
    #print flatten(image_post_dict)
    #new_post_dict = save_media(session,image_post_dict)
    #download_image_link(session,"https://derpicdn.net/spns/W1siZiIsIjIwMTQvMDEvMTAvMDJfNDBfMjhfNjUyX2RlcnBpYm9vcnVfYmFubmVyLnBuZyJdXQ.png")

    # Debug audio
    logging.debug("Debug audio")
    soundcloud_post_dict = {u'reblog_key': u'S6VWj0Cb', u'reblog': {u'comment': u'', u'tree_html': u'<p><a class="tumblr_blog" href="http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre">waltzforluma</a>:</p><blockquote><p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p></blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'regular', u'header_full_height': 262, u'title_color': u'#444444', u'header_bounds': u'0,623,262,157', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/ZrTn5ivly/tumblr_static_tumblr_static_57wsbbc6rz0g0gk4ww8k884wk_focused_v3.png', u'show_description': True, u'header_full_width': 898, u'avatar_shape': u'circle', u'header_focus_width': 466, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'header_image_scaled': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/g9cn5ivlx/tumblr_static_57wsbbc6rz0g0gk4ww8k884wk_2048_v2.png', u'show_avatar': True, u'header_focus_height': 262, u'title_font': u'Garamond Classic FS', u'header_image': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/g9cn5ivlx/tumblr_static_57wsbbc6rz0g0gk4ww8k884wk.png'}, u'name': u'waltzforluma'}, u'comment': u'<p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p>', u'post': {u'id': u'111622677961'}}]}, u'player': u'<iframe src="https://w.soundcloud.com/player/?url=https%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F192213990&amp;visual=true&amp;liking=false&amp;sharing=false&amp;auto_play=false&amp;show_comments=false&amp;continuous_play=false&amp;origin=tumblr" frameborder="0" allowtransparency="true" class="soundcloud_audio_player" width="500" height="500"></iframe>', u'id': 113020390888L, u'post_url': u'http://doscoon.tumblr.com/post/113020390888/waltzforluma-or-your-computer-could-overheat', u'source_title': u'waltzforluma', u'format': u'html', u'highlighted': [], u'state': u'published', u'track_name': u'Steven Universe - Death Rag', u'short_url': u'http://tmblr.co/ZlYOqv1fGYate', u'type': u'audio', u'tags': [], u'timestamp': 1425776404, u'note_count': 1014, u'source_url': u'http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre', u'date': u'2015-03-08 01:00:04 GMT', u'plays': 38933, u'slug': u'waltzforluma-or-your-computer-could-overheat', u'album_art': u'http://38.media.tumblr.com/tumblr_nk3re1A1Cf1qzqb72_1424489834_cover.jpg', u'blog_name': u'doscoon', u'is_external': True, u'audio_url': u'https://api.soundcloud.com/tracks/192213990/stream?client_id=3cQaPshpEeLqMsNFAUw1Q', u'caption': u'<p><a class="tumblr_blog" href="http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre">waltzforluma</a>:</p><blockquote><p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p></blockquote>', u'audio_type': u'soundcloud', u'audio_source_url': u'https://soundcloud.com/aivisura/steven-universe-death-rag', u'embed': u'<iframe src="https://w.soundcloud.com/player/?url=https%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F192213990&amp;visual=true&amp;liking=false&amp;sharing=false&amp;auto_play=false&amp;show_comments=false&amp;continuous_play=false&amp;origin=tumblr" frameborder="0" allowtransparency="true" class="soundcloud_audio_player" width="500" height="500"></iframe>'}
    #audio_handlers.handle_soundcloud_audio(session,soundcloud_post_dict)

    # Debug video
    logging.debug("Debug video")
    tumblr_video_post_dict = {u'reblog_key': u'3bqfxHgy', u'short_url': u'http://tmblr.co/Z_sLQw1eYTSqS', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}], u'id': 112247295260L, u'post_url': u'http://tsitra360.tumblr.com/post/112247295260/my-latest-art-timelapse-is-up-see-how-i-drew', u'tags': [], u'highlighted': [], u'state': u'published', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1425068852, u'note_count': 79, u'video_type': u'youtube', u'date': u'2015-02-27 20:27:32 GMT', u'thumbnail_height': 360, u'permalink_url': u'https://www.youtube.com/watch?v=tT5pifkZzEk', u'slug': u'my-latest-art-timelapse-is-up-see-how-i-drew', u'blog_name': u'tsitra360', u'caption': u'<p>My latest art timelapse is up! See how I drew Berry Swirl on my youtube channel.</p>', u'thumbnail_url': u'https://i.ytimg.com/vi/tT5pifkZzEk/hqdefault.jpg'}
    youtube_video_post_dict = {u'reblog_key': u'HfjckfH7', u'short_url': u'http://tmblr.co/ZUGffq1cfuHuJ', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}], u'id': 110224285203L, u'post_url': u'http://askbuttonsmom.tumblr.com/post/110224285203/throwback-can-you-believe-its-been-almost-2yrs', u'tags': [u"button's mom", u'hardcopy', u'song', u'shadyvox'], u'highlighted': [], u'state': u'published', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1423197599, u'note_count': 145, u'video_type': u'youtube', u'date': u'2015-02-06 04:39:59 GMT', u'thumbnail_height': 360, u'permalink_url': u'https://www.youtube.com/watch?v=lGIEmH3BoyA', u'slug': u'throwback-can-you-believe-its-been-almost-2yrs', u'blog_name': u'askbuttonsmom', u'caption': u'<p>Throwback! Can you believe it&#8217;s been almost 2yrs since this came out? Mommy&#8217;s getting old&#8230;</p>', u'thumbnail_url': u'https://i.ytimg.com/vi/lGIEmH3BoyA/hqdefault.jpg'}
    youtube_dict_two = {u'highlighted': [], u'reblog_key': u'qO3JnfS7', u'player': [{u'width': 250, u'embed_code': False}, {u'width': 400, u'embed_code': False}, {u'width': 500, u'embed_code': False}], u'format': u'html', u'timestamp': 1390412461, u'note_count': 4282, u'tags': [], u'video_type': u'youtube', u'id': 74184911379L, u'post_url': u'http://askbuttonsmom.tumblr.com/post/74184911379/ask-thecrusaders-bar-buddies-dont-worry', u'caption': u'<p><a class="tumblr_blog" href="http://ask-thecrusaders.tumblr.com/post/74162414750/bar-buddies-dont-worry-neon-you-will-have-your">ask-thecrusaders</a>:</p>\n<blockquote>\n<p><strong>"Bar Buddies"</strong><br/><br/>Dont\u2019 worry Neon, you will have your music video soon enough.</p>\n</blockquote>\n<p>Honestly, that Neon Lights is a TERRIBLE influence!! No son of mine will grow up to be a drunken drug-shooting bass dropping hipster! :C</p>', u'state': u'published', u'html5_capable': False, u'reblog': {u'comment': u'<p>Honestly, that Neon Lights is a TERRIBLE influence!! No son of mine will grow up to be a drunken drug-shooting bass dropping hipster! :C</p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://ask-thecrusaders.tumblr.com/post/74162414750/bar-buddies-dont-worry-neon-you-will-have-your">ask-thecrusaders</a>:</p><blockquote>\n<p><strong>"Bar Buddies"</strong><br/><br/>Dont\u2019 worry Neon, you will have your music video soon enough.</p>\n</blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'title_font': u'Helvetica Neue', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'avatar_shape': u'circle', u'show_avatar': True, u'background_color': u'#F6F6F6', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f'}, u'name': u'ask-thecrusaders'}, u'comment': u'<p><strong>"Bar Buddies"</strong><br><br>Dont\u2019 worry Neon, you will have your music video soon enough.</p>', u'post': {u'id': u'74162414750'}}]}, u'short_url': u'http://tmblr.co/ZUGffq155m_eJ', u'date': u'2014-01-22 17:41:01 GMT', u'type': u'video', u'slug': u'ask-thecrusaders-bar-buddies-dont-worry', u'blog_name': u'askbuttonsmom'}
    vine_dict = {u'reblog_key': u'A5DhHt28', u'reblog': {u'comment': u'<p>Have a nice weekend, Tumblr.&nbsp;</p>', u'tree_html': u'', u'trail': []}, u'placement_id': u'{"i":"mF4avY6GyshXjaQmfk0v","v":4,"t":1427193020,"c":{"p":"113540981790","b":"staff"},"d":{"v":{"e":"hjWIUFOYD31"}},"h":"3291f1aa07"}', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="250" height="250" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}, {u'width': 400, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="400" height="400" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}, {u'width': 500, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="500" height="500" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}], u'id': 113540981790L, u'post_url': u'http://staff.tumblr.com/post/113540981790/have-a-nice-weekend-tumblr', u'source_title': u'weloveshortvideos.com', u'tags': [], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZE5Fby1flaUGU', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1426282797, u'note_count': 48309, u'video_type': u'vine', u'source_url': u'http://weloveshortvideos.com', u'date': u'2015-03-13 21:39:57 GMT', u'thumbnail_height': 480, u'permalink_url': u'https://vine.co/v/hjWIUFOYD31', u'slug': u'have-a-nice-weekend-tumblr', u'blog_name': u'staff', u'caption': u'<p>Have a nice weekend, Tumblr.\xa0</p>', u'thumbnail_url': u'http://v.cdn.vine.co/r/thumbs/FE4C8DC8781008139866036658176_1c16044fdd3.3.4.mp4_l_pAXVyCckNVnk2OzdadqNB_6bq4mYoBHpBFRIF8Hi3OdOW1vmjP1TR075G1ZegT.jpg?versionId=abawWSw4Y_QFv2TKPWz6j8N5y7.6LOGq'}
    #video_handlers.handle_tumblr_videos(session,tumblr_video_post_dict)
    #video_handlers.handle_youtube_video(session,youtube_video_post_dict)
    #video_handlers.handle_youtube_video(session,youtube_dict_two)
    video_handlers.handle_video_posts(session,vine_dict)


    logging.debug("Closing DB session")
    session.commit()
    return


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","media-handlers-log.txt"))
        debug()
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
