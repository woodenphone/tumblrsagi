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
from sql_functions import Media
import sql_functions
import config # User settings
from tables import *# This module only has the table classes


def handle_soundcloud_audio(session,post_dict):
    """Save soundcloud audio ect from a post
    Use youtube-dl to save audio
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    # Send album art image link off to be checked
    logging.debug("post_dict: "+repr(post_dict))
    post_id = str(post_dict["id"])
    # Grab "track id"?
    # u'https://api.soundcloud.com/tracks/192213990/stream?client_id=3cQaPshpEeLqMsNFAUw1Q' to '192213990'
    soundcloud_link = post_dict["audio_url"]
    if soundcloud_link is None:# Handle missing link
        logging.error("handle_soundcloud_audio() audio_url is None! Can't save!")
        logging.error("handle_soundcloud_audio(post_dict) :"+repr(post_dict))
        return []
    soundcloud_id_search = re.search("""api\.soundcloud\.com/tracks/(\d+)/stream""", soundcloud_link, re.IGNORECASE|re.DOTALL)
    soundcloud_id = soundcloud_id_search.group(1)
    cleaned_soundcloud_link = re.search("""([^?]+)""", soundcloud_link, re.IGNORECASE|re.DOTALL).group(1)
    logging.debug("cleaned_soundcloud_link"+repr(cleaned_soundcloud_link))

    # Check if audio has been saved, and return if it has
    id_query = sqlalchemy.select([Media]).where(Media.audio_id == soundcloud_id)
    id_rows = session.execute(id_query)
    id_row = id_rows.fetchone()
    logging.debug("id_row: "+repr(id_row))
    if id_row:
        logging.debug("Soundcloud audio with this ID has already been saved, skipping")
        media_id = id_row["media_id"]
        media_id_list = [media_id]
        return media_id_list
    else:
        # Grab url to send to youtube-dl
        download_urls = [cleaned_soundcloud_link]

        # Download videos if there are any
        media_id_list = run_yt_dl_multiple(
            session = session,
            download_urls = download_urls,
            extractor_used="audio_handlers.handle_soundcloud_audio()",
            audio_id = soundcloud_id
            )
        logging.debug("Finished downloading soundcloud embeds")
        return media_id_list


def handle_bandcamp_audio(session,post_dict):#WIP
    """Save bandcamp audio ect from a post
    Use youtube-dl to save audio
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    # Send album art image link off to be checked
    logging.debug("post_dict: "+repr(post_dict))

    bandcamp_link = post_dict["audio_url"]

    # u'http://popplers5.bandcamp.com/download/track?enc=mp3-128&fsig=ca33bbe78b527483940c050bd627a33d&id=2851867171&nl=1&stream=1&ts=1428792368.0'
    # u'id=2851867171'
    # u'2851867171'
    bandcamp_id = re.search("""id=(\d+)""", bandcamp_link, re.IGNORECASE|re.DOTALL).group(1)

    # Check if audio has been saved, and return if it has
    id_query = sqlalchemy.select([Media]).where(Media.audio_id == bandcamp_id)
    id_rows = session.execute(id_query)
    id_row = id_rows.fetchone()
    logging.debug("id_row: "+repr(id_row))
    if id_row:
        logging.debug("bandcamp audio with this ID has already been saved, skipping")
        media_id = id_row["media_id"]
        media_id_list = [media_id]
        return media_id_list

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = [bandcamp_link],
        extractor_used="audio_handlers.handle_bandcamp_audio()",
        audio_id = bandcamp_id
        )
    logging.debug("Finished downloading bandcamp embeds")
    return media_id_list



def handle_tumblr_audio(session,post_dict):
    """Download tumblr-hosted audio from audio posts
    see this link for a reference implimentation
    https://github.com/atesh/XKit
    https://github.com/atesh/XKit/blob/master/Extensions/audio_downloader.js"""
    media_already_saved = None
    assert(post_dict["audio_type"] == u"tumblr")
    logging.debug("handle_tumblr_audio() post_dict: "+repr(post_dict))
    # Generate a link to the audio file
    api_media_url = post_dict["audio_url"]
    # This is basically check if url starts with this string
    if "https://www.tumblr.com/audio_file/" in api_media_url:
        # and here it sets the de-facto URL for downloading
        media_url = "http://a.tumblr.com/" + urllib.quote(api_media_url.split("/")[-1]) + "o1.mp3"
    else:
        media_url = api_media_url
    logging.debug("handle_tumblr_audio() media_url: "+repr(media_url))

    # Check the DB to see if media is already saved
    url_check_row_dict = sql_functions.check_if_media_url_in_DB(
        session,
        media_url=media_url
        )
    if url_check_row_dict:
        media_already_saved = True
        media_id = url_check_row_dict["media_id"]
        logging.debug("audio_handlers.handle_tumblr_audio()  URL is already in DB, no need to save file.")
        return [media_id]

    # Load the media file
    file_data = get_url(media_url)
    if not file_data:
        logging.error("handle_tumblr_audio() Could not load data for"+repr(media_url))
        return []

    time_of_retreival = get_current_unix_time()

    # Check if file is saved already using file hash
    sha512base16_hash = hash_file_data(file_data)# Used for filenames and dedupe
    md5base64_hash = generate_md5b64_for_memory(file_data)# For comparison only
    logging.debug("handle_tumblr_audio() sha512base16_hash: "+repr(sha512base16_hash))

    # Check if hash is in DB
    hash_check_row_dict = sql_functions.check_if_hash_in_db(
        session,
        sha512base16_hash=sha512base16_hash
        )
    if hash_check_row_dict:
        media_already_saved = True
        media_id = hash_check_row_dict["media_id"]
        existing_filename = hash_check_row_dict["local_filename"]
    else:
        logging.debug("handle_tumblr_audio() Hash is already in DB, no need to save file.")
    if media_already_saved:
        # Use filename from DB
        local_filename = existing_filename
        file_path = generate_path(
            root_path=config.root_path,
            filename=local_filename
            )
    else:
        # Generate filename
        local_filename = generate_filename(
            ext="mp3",
            sha512base16_hash=sha512base16_hash
            )
        logging.debug("handle_tumblr_audio() local_filename: "+repr(local_filename))
        file_path = generate_path(
            root_path=config.root_path,
            filename=local_filename
            )
        # Save media to disk
        save_file(
            file_path=file_path,
            data=file_data,
            force_save=False
            )
    
    # Get size of file
    file_size_in_bytes = find_file_size(file_path)

    # Add new row to DB
    new_media_row = Media(
        media_url = media_url,
        sha512base16_hash = sha512base16_hash,
        local_filename = local_filename,
        date_added = time_of_retreival,
        file_extention = "mp3",
        extractor_used="audio_handlers.handle_tumblr_audio()",
        md5base64_hash=md5base64_hash,
        file_size_in_bytes=file_size_in_bytes,
        )
    session.add(new_media_row)
    session.commit()

    # Get the id back
    get_id_row = sql_functions.check_if_hash_in_db(session,sha512base16_hash)
    media_id = get_id_row["media_id"]
    media_id_list = [media_id]
    return media_id_list


def handle_audio_posts(session,post_dict):
    """Download audio from audio posts"""
    # Determing if post is tumblr audio
    if post_dict["type"] != u"audio":
        return {}
    logging.debug("Audio post! post_dict: "+repr(post_dict))# Find audio post dicts for debugging
    # Tumblr hosted audio
    if post_dict["audio_type"] == u"tumblr":
        logging.debug("Post is tumblr audio")
        return handle_tumblr_audio(session,post_dict)
    # Soundcloud
    elif post_dict["audio_type"] == u"soundcloud":
        logging.debug("Post is soundcloud audio")
        return handle_soundcloud_audio(session,post_dict)
    # Bandcamp
    elif post_dict["audio_type"] == u"bandcamp":
        logging.debug("Post is bandcamp audio")
        return handle_bandcamp_audio(session,post_dict)
    # Spotify
    elif post_dict["audio_type"] == u"spotify":
        logging.debug("Post is spotify audio")
        logging.warning("Spotify is unsupported")# TODO FIXME
        return {}
    # Unknown
    else:
        logging.error("Unknown audio type!")
        logging.error("locals(): "+repr(locals()))
        assert(False)


def debug():
    """For WIP, debug, ect function calls"""
    session = sql_functions.connect_to_db()

    # tumblr
    tumblr_post_dict = {u'reblog_key': u'fZE1iow1', u'reblog': {u'comment': u'', u'tree_html': u'<p><a href="http://asklalalexxi.tumblr.com/post/115588359781/i-normally-dont-like-yogurt-because-of-the" class="tumblr_blog">asklalalexxi</a>:</p><blockquote><p>I normally dont like yogurt because of the consistency. but omg\u2026.ive been starving~ Since the infections gone, I can eat dairy now, and this ironically doesn\u2019t make my stomach upset.\xa0</p></blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_08.png?_v=f0f055039bb6136b9661cf2227b535c2', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_08.png?_v=f0f055039bb6136b9661cf2227b535c2', u'avatar_shape': u'square', u'show_avatar': True, u'background_color': u'#FAFAFA', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_08.png?_v=f0f055039bb6136b9661cf2227b535c2'}, u'name': u'asklalalexxi'}, u'comment': u'<p>I normally dont like yogurt because of the consistency. but omg\u2026.ive been starving~ Since the infections gone, I can eat dairy now, and this ironically doesn\u2019t make my stomach upset.\xa0</p>', u'post': {u'id': u'115588359781'}}]}, u'player': u'<embed type="application/x-shockwave-flash" src="http://assets.tumblr.com/swf/audio_player.swf?audio_file=https%3A%2F%2Fwww.tumblr.com%2Faudio_file%2Faskbuttonsmom%2F115588501253%2Ftumblr_nmcidl4oPW1sl74rq&color=FFFFFF" height="27" width="207" quality="best" wmode="opaque"></embed>', u'id': 115588501253L, u'post_url': u'http://askbuttonsmom.tumblr.com/post/115588501253/asklalalexxi-i-normally-dont-like-yogurt-because', u'plays': 1550, u'tags': [], u'highlighted': [], u'state': u'published', u'track_name': u'When you havent eaten in a while...', u'short_url': u'http://tmblr.co/ZUGffq1hfd8y5', u'type': u'audio', u'format': u'html', u'timestamp': 1428257396, u'note_count': 67, u'date': u'2015-04-05 18:09:56 GMT', u'slug': u'asklalalexxi-i-normally-dont-like-yogurt-because', u'album_art': u'http://31.media.tumblr.com/tumblr_nmcidl4oPW1sl74rqo1_1428257289_cover.png', u'blog_name': u'askbuttonsmom', u'audio_url': u'https://www.tumblr.com/audio_file/askbuttonsmom/115588501253/tumblr_nmcidl4oPW1sl74rq', u'caption': u'<p><a href="http://asklalalexxi.tumblr.com/post/115588359781/i-normally-dont-like-yogurt-because-of-the" class="tumblr_blog">asklalalexxi</a>:</p><blockquote><p>I normally dont like yogurt because of the consistency. but omg\u2026.ive been starving~ Since the infections gone, I can eat dairy now, and this ironically doesn\u2019t make my stomach upset.\xa0</p></blockquote>', u'audio_type': u'tumblr', u'audio_source_url': u'https://www.tumblr.com/audio_file/askbuttonsmom/115588501253/tumblr_nmcidl4oPW1sl74rq', u'embed': u'<iframe class="tumblr_audio_player tumblr_audio_player_115588501253" src="http://askbuttonsmom.tumblr.com/post/115588501253/audio_player_iframe/askbuttonsmom/tumblr_nmcidl4oPW1sl74rq?audio_file=https%3A%2F%2Fwww.tumblr.com%2Faudio_file%2Faskbuttonsmom%2F115588501253%2Ftumblr_nmcidl4oPW1sl74rq" frameborder="0" allowtransparency="true" scrolling="no" width="500" height="169"></iframe>'}
    #tumblr_result = handle_audio_posts(session,tumblr_post_dict)

    # soundcloud
    soundcloud_post_dict_1 = {u'reblog_key': u'S6VWj0Cb', u'reblog': {u'comment': u'', u'tree_html': u'<p><a class="tumblr_blog" href="http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre">waltzforluma</a>:</p><blockquote><p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p></blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'regular', u'header_full_height': 262, u'title_color': u'#444444', u'header_bounds': u'0,623,262,157', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/ZrTn5ivly/tumblr_static_tumblr_static_57wsbbc6rz0g0gk4ww8k884wk_focused_v3.png', u'show_description': True, u'header_full_width': 898, u'avatar_shape': u'circle', u'header_focus_width': 466, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'header_image_scaled': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/g9cn5ivlx/tumblr_static_57wsbbc6rz0g0gk4ww8k884wk_2048_v2.png', u'show_avatar': True, u'header_focus_height': 262, u'title_font': u'Garamond Classic FS', u'header_image': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/g9cn5ivlx/tumblr_static_57wsbbc6rz0g0gk4ww8k884wk.png'}, u'name': u'waltzforluma'}, u'comment': u'<p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p>', u'post': {u'id': u'111622677961'}}]}, u'player': u'<iframe src="https://w.soundcloud.com/player/?url=https%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F192213990&amp;visual=true&amp;liking=false&amp;sharing=false&amp;auto_play=false&amp;show_comments=false&amp;continuous_play=false&amp;origin=tumblr" frameborder="0" allowtransparency="true" class="soundcloud_audio_player" width="500" height="500"></iframe>', u'id': 113020390888L, u'post_url': u'http://doscoon.tumblr.com/post/113020390888/waltzforluma-or-your-computer-could-overheat', u'source_title': u'waltzforluma', u'format': u'html', u'highlighted': [], u'state': u'published', u'track_name': u'Steven Universe - Death Rag', u'short_url': u'http://tmblr.co/ZlYOqv1fGYate', u'type': u'audio', u'tags': [], u'timestamp': 1425776404, u'note_count': 1014, u'source_url': u'http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre', u'date': u'2015-03-08 01:00:04 GMT', u'plays': 38933, u'slug': u'waltzforluma-or-your-computer-could-overheat', u'album_art': u'http://38.media.tumblr.com/tumblr_nk3re1A1Cf1qzqb72_1424489834_cover.jpg', u'blog_name': u'doscoon', u'is_external': True, u'audio_url': u'https://api.soundcloud.com/tracks/192213990/stream?client_id=3cQaPshpEeLqMsNFAUw1Q', u'caption': u'<p><a class="tumblr_blog" href="http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre">waltzforluma</a>:</p><blockquote><p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p></blockquote>', u'audio_type': u'soundcloud', u'audio_source_url': u'https://soundcloud.com/aivisura/steven-universe-death-rag', u'embed': u'<iframe src="https://w.soundcloud.com/player/?url=https%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F192213990&amp;visual=true&amp;liking=false&amp;sharing=false&amp;auto_play=false&amp;show_comments=false&amp;continuous_play=false&amp;origin=tumblr" frameborder="0" allowtransparency="true" class="soundcloud_audio_player" width="500" height="500"></iframe>'}
    #soundcloud_result_1 = handle_audio_posts(session,soundcloud_post_dict_1)

    # soundcloud
    soundcloud_post_dict_2 = {u'reblog_key': u'S6VWj0Cb', u'reblog': {u'comment': u'', u'tree_html': u'<p><a class="tumblr_blog" href="http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre">waltzforluma</a>:</p><blockquote><p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p></blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'regular', u'header_full_height': 262, u'title_color': u'#444444', u'header_bounds': u'0,623,262,157', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/ZrTn5ivly/tumblr_static_tumblr_static_57wsbbc6rz0g0gk4ww8k884wk_focused_v3.png', u'show_description': True, u'header_full_width': 898, u'avatar_shape': u'circle', u'header_focus_width': 466, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'header_image_scaled': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/g9cn5ivlx/tumblr_static_57wsbbc6rz0g0gk4ww8k884wk_2048_v2.png', u'show_avatar': True, u'header_focus_height': 262, u'title_font': u'Garamond Classic FS', u'header_image': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/g9cn5ivlx/tumblr_static_57wsbbc6rz0g0gk4ww8k884wk.png'}, u'name': u'waltzforluma'}, u'comment': u'<p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p>', u'post': {u'id': u'111622677961'}}]}, u'player': u'<iframe src="https://w.soundcloud.com/player/?url=https%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F192213990&amp;visual=true&amp;liking=false&amp;sharing=false&amp;auto_play=false&amp;show_comments=false&amp;continuous_play=false&amp;origin=tumblr" frameborder="0" allowtransparency="true" class="soundcloud_audio_player" width="500" height="500"></iframe>', u'id': 113020390888L, u'post_url': u'http://doscoon.tumblr.com/post/113020390888/waltzforluma-or-your-computer-could-overheat', u'source_title': u'waltzforluma', u'format': u'html', u'highlighted': [], u'state': u'published', u'track_name': u'Steven Universe - Death Rag', u'short_url': u'http://tmblr.co/ZlYOqv1fGYate', u'type': u'audio', u'tags': [], u'timestamp': 1425776404, u'note_count': 1014, u'source_url': u'http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre', u'date': u'2015-03-08 01:00:04 GMT', u'plays': 38933, u'slug': u'waltzforluma-or-your-computer-could-overheat', u'album_art': u'http://38.media.tumblr.com/tumblr_nk3re1A1Cf1qzqb72_1424489834_cover.jpg', u'blog_name': u'doscoon', u'is_external': True, u'audio_url': u'https://api.soundcloud.com/tracks/192213990/stream?client_id=3cQaPshpEeLqMsNFAUw1Q', u'caption': u'<p><a class="tumblr_blog" href="http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre">waltzforluma</a>:</p><blockquote><p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p></blockquote>', u'audio_type': u'soundcloud', u'audio_source_url': u'https://soundcloud.com/aivisura/steven-universe-death-rag', u'embed': u'<iframe src="https://w.soundcloud.com/player/?url=https%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F192213990&amp;visual=true&amp;liking=false&amp;sharing=false&amp;auto_play=false&amp;show_comments=false&amp;continuous_play=false&amp;origin=tumblr" frameborder="0" allowtransparency="true" class="soundcloud_audio_player" width="500" height="500"></iframe>'}
    soundcloud_result_2 = handle_audio_posts(session,soundcloud_post_dict_2)
    logging.info("soundcloud_result_2:"+repr(soundcloud_result_2))

    # Dead soundcloud
    soundcloud_post_dict_3 =  {u'reblog_key': u'UygtqfHO', u'reblog': {u'comment': u'', u'tree_html': u''}, u'audio_url': None, u'id': 96589998856L, u'album': u'Pure Heroine - EP', u'highlighted': [], u'plays': 463291, u'format': u'html', u'post_url': u'http://tepidtwisted.tumblr.com/post/96589998856', u'recommended_source': None, u'state': u'published', u'track_name': u'Everybody Wants To Rule The World', u'short_url': u'http://tmblr.co/ZrDCJw1PzDci8', u'type': u'audio', u'tags': [], u'timestamp': 1409799977, u'note_count': 62060, u'source_url': u'http://audio-trip.tumblr.com/post/84453352328', u'trail': [], u'player': u'<iframe src="https://w.soundcloud.com/player/?url=&amp;visual=true&amp;liking=false&amp;sharing=false&amp;auto_play=false&amp;show_comments=false&amp;continuous_play=false&amp;origin=tumblr" frameborder="0" allowtransparency="true" class="soundcloud_audio_player" width="500" height="500"></iframe>', u'date': u'2014-09-04 03:06:17 GMT', u'source_title': u'audio-trip', u'slug': u'', u'album_art': u'http://33.media.tumblr.com/tumblr_n4wy9ee6BY1rhgjr7o1_1398977906_cover.jpg', u'blog_name': u'tepidtwisted', u'is_external': True, u'artist': u'Lorde', u'caption': u'', u'audio_type': u'soundcloud', u'audio_source_url': None, u'embed': u'<iframe src="https://w.soundcloud.com/player/?url=&amp;visual=true&amp;liking=false&amp;sharing=false&amp;auto_play=false&amp;show_comments=false&amp;continuous_play=false&amp;origin=tumblr" frameborder="0" allowtransparency="true" class="soundcloud_audio_player" width="500" height="500"></iframe>'}
    soundcloud_result_3 = handle_audio_posts(session,soundcloud_post_dict_3)
    logging.info("soundcloud_result_3:"+repr(soundcloud_result_3))

    # bandcamp
    bandcamp_post_dict = {u'reblog_key': u'AbxPRz4A', u'short_url': u'http://tmblr.co/ZE5FbyhlEyOo', u'audio_url': u'http://popplers5.bandcamp.com/download/track?enc=mp3-128&fsig=ca33bbe78b527483940c050bd627a33d&id=2851867171&nl=1&stream=1&ts=1428792368.0', u'player': u'<iframe class="bandcamp_audio_player" width="500" height="120" src="http://bandcamp.com/EmbeddedPlayer/size=medium/bgcol=ffffff/linkcol=0687f5/notracklist=true/transparent=true/track=2851867171/" allowtransparency="true" frameborder="0"></iframe>', u'id': 46963344946, u'album': u'Hunter Hunted - EP', u'post_url': u'http://staff.tumblr.com/post/46963344946/listen-up-our-audio-player-just-got-super-rad', u'source_title': u'Bandcamp', u'tags': [u'hunter hunted', u'keep together', u'music on tumblr', u'bands on tumblr'], u'highlighted': [], u'state': u'published', u'track_name': u'Keep Together', u'type': u'audio', u'featured_in_tag': [u'Music', u'Design'], u'format': u'html', u'timestamp': 1364937324, u'note_count': 5105, u'source_url': u'http://hunterhuntedmusic.bandcamp.com/track/keep-together', u'date': u'2013-04-02 21:15:24 GMT', u'plays': 110209, u'slug': u'listen-up-our-audio-player-just-got-super-rad', u'album_art': u'http://31.media.tumblr.com/tumblr_mkn8sgrMDN1qz8q0h_dSDeaHscmUuv4sl8epf8mAC32IU_cover.jpg', u'blog_name': u'staff', u'is_external': True, u'artist': u'Hunter Hunted', u'caption': u'<p>Listen up: our audio player just got super rad!</p>\n<ul><li><span>Fancy new audio visualizer</span></li>\n<li><span>Bigger album art</span></li>\n<li><span>Click and drag to skip around</span></li>\n</ul><p>Hit play and happy listening!</p>', u'audio_type': u'bandcamp', u'audio_source_url': u'http://popplers5.bandcamp.com/download/track?enc=mp3-128&fsig=ca33bbe78b527483940c050bd627a33d&id=2851867171&nl=1&stream=1&ts=1428792368.0', u'embed': u'<iframe class="bandcamp_audio_player" width="100%" height="120" src="http://bandcamp.com/EmbeddedPlayer/size=medium/bgcol=ffffff/linkcol=0687f5/notracklist=true/transparent=true/track=2851867171/" allowtransparency="true" frameborder="0"></iframe>'}
    #bandcamp_result = handle_audio_posts(session,bandcamp_post_dict)

    # Spotify
    spotify_post_dict = {u'reblog_key': u'AbxPRz4A', u'short_url': u'http://tmblr.co/ZE5FbyhlEyOo', u'audio_url': u'http://popplers5.bandcamp.com/download/track?enc=mp3-128&fsig=ca33bbe78b527483940c050bd627a33d&id=2851867171&nl=1&stream=1&ts=1428792368.0', u'player': u'<iframe class="bandcamp_audio_player" width="500" height="120" src="http://bandcamp.com/EmbeddedPlayer/size=medium/bgcol=ffffff/linkcol=0687f5/notracklist=true/transparent=true/track=2851867171/" allowtransparency="true" frameborder="0"></iframe>', u'id': 46963344946, u'album': u'Hunter Hunted - EP', u'post_url': u'http://staff.tumblr.com/post/46963344946/listen-up-our-audio-player-just-got-super-rad', u'source_title': u'Bandcamp', u'tags': [u'hunter hunted', u'keep together', u'music on tumblr', u'bands on tumblr'], u'highlighted': [], u'state': u'published', u'track_name': u'Keep Together', u'type': u'audio', u'featured_in_tag': [u'Music', u'Design'], u'format': u'html', u'timestamp': 1364937324, u'note_count': 5105, u'source_url': u'http://hunterhuntedmusic.bandcamp.com/track/keep-together', u'date': u'2013-04-02 21:15:24 GMT', u'plays': 110209, u'slug': u'listen-up-our-audio-player-just-got-super-rad', u'album_art': u'http://31.media.tumblr.com/tumblr_mkn8sgrMDN1qz8q0h_dSDeaHscmUuv4sl8epf8mAC32IU_cover.jpg', u'blog_name': u'staff', u'is_external': True, u'artist': u'Hunter Hunted', u'caption': u'<p>Listen up: our audio player just got super rad!</p>\n<ul><li><span>Fancy new audio visualizer</span></li>\n<li><span>Bigger album art</span></li>\n<li><span>Click and drag to skip around</span></li>\n</ul><p>Hit play and happy listening!</p>', u'audio_type': u'bandcamp', u'audio_source_url': u'http://popplers5.bandcamp.com/download/track?enc=mp3-128&fsig=ca33bbe78b527483940c050bd627a33d&id=2851867171&nl=1&stream=1&ts=1428792368.0', u'embed': u'<iframe class="bandcamp_audio_player" width="100%" height="120" src="http://bandcamp.com/EmbeddedPlayer/size=medium/bgcol=ffffff/linkcol=0687f5/notracklist=true/transparent=true/track=2851867171/" allowtransparency="true" frameborder="0"></iframe>'}
    #spotify_result = handle_audio_posts(session,spotify_post_dict)

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
