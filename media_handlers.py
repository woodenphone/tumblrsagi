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

#import mysql.connector
import sqlalchemy


import subprocess# For video and some audio downloads
import urllib# For encoding audio urls
import re
import logging
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


def download_image_link(session,media_url):
    """Load an image link and hash the data recieved,
    then add an entry to the DB for the URL
    and if no match is found for the hash, save the file to disk"""
    media_already_saved = None # Init var to unknown
    logging.debug("Processing image: "+repr(media_url))
    # Check if URL is in the DB already, if so return hash.
    url_check_row_dict = sql_functions.check_if_media_url_in_DB(session,media_url)
    if url_check_row_dict:
        media_already_saved = True
        return url_check_row_dict["sha512base64_hash"]
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
    hash_check_row_dict = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
    if hash_check_row_dict:
        media_already_saved = True
        image_filename = hash_check_row_dict["filename"]

    # Add new row
    new_media_row = Media(
    media_url=media_url,
    sha512base64_hash=sha512base64_hash,
    filename=image_filename,
    date_added=time_of_retreival,
    extractor_used="image_link",
    )
    session.add(new_media_row)

    # If hash was already in DB, don't bother saving file
    if media_already_saved:
        logging.debug("Hash already in DB, no need to save file to disk")
    else:
        # Save file to disk, using the hash as a filename
        logging.debug("Hash was not in DB, saving file: "+repr(file_path))
        save_file(filenamein=file_path,data=file_data,force_save=False)
    session.commit()
    return sha512base64_hash


def download_image_links(session,media_urls):
    # Save image links
    media_urls = uniquify(media_urls)
    link_hash_dict = {}# {link:hash}
    for media_urls in media_urls:
        sha512base64_hash =  download_image_link(session,media_urls)
        link_hash_dict[media_urls] = sha512base64_hash# {link:hash}
        continue
    return link_hash_dict# {link:hash}


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
        photo_url_list.append(original_size_url)
        if config.save_all_photo_sizes:
            # Grab alt size urls
            alt_sizes_list = photo_dict["alt_sizes"]
            for alt_size_dict in alt_sizes_list:
                alt_size_url = alt_size_dict["url"]
                photo_url_list.append(alt_size_url)
    logging.debug("photo_url_list: "+repr(photo_url_list))
    # Check the photo links against the DB to see if they have already been saved
    photo_urls_to_save = []
    for photo_link in photo_url_list:
        # Check if URL is in the DB
        link_already_saved = sql_functions.check_if_media_url_in_DB(session,photo_link)
        if link_already_saved:
            photo_urls_to_save.append(photo_link)
    # Save new photo links
    link_hash_dict = download_image_links(session,photo_urls_to_save)
    return link_hash_dict# {link:hash}


def handle_tumblr_videos(session,post_dict):
    """Download tumblr-hosted videos from video posts
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    logging.debug("Processing tumblr video")
    video_page = post_dict["post_url"]
    logging.debug("post_dict"+repr(post_dict))
    post_id = str(post_dict["id"])
    logging.debug("video_page: "+repr(video_page))
    logging.debug("post_id: "+repr(post_id))
    # Check if video is already saved

    video_page_query = sqlalchemy.select([Media]).where(Media.media_url == video_page)
    video_page_rows = session.execute(video_page_query)
    video_page_row = video_page_rows.fetchone()
    if video_page_row:
        preexisting_filename = video_page_row["filename"]
        sha512base64_hash = video_page_row["sha512base64_hash"]
        return {"tumblr_video_embed":sha512base64_hash}

    # Load video
    # Form command to run
    # Define arguments. see this url for help
    # https://github.com/rg3/youtube-dl
    program_path = os.path.join("youtube-dl","youtube-dl.exe")
    assert(os.path.exists(program_path))
    ignore_errors = "-i"
    safe_filenames = "--restrict-filenames"
    output_arg = "-o"
    info_json_arg = "--write-info-json"
    description_arg ="--write-description"
    output_dir = os.path.join(config.root_path,"temp")
    output_template = os.path.join(output_dir, post_id+".%(ext)s")
    # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
    command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, video_page]
    logging.debug("command: "+repr(command))
    # Call youtube-dl
    command_result = subprocess.call(command)
    logging.debug("command_result: "+repr(command_result))
    # Fail if bad exit code
    if command_result != 0:
        logging.error("Command did not return correct exit code! (Normal exit is 0)")
        return {}
    time_of_retreival = get_current_unix_time()
    # Verify download worked
    # Read info JSON file
    expected_info_path = os.path.join(output_dir, post_id+".info.json")
    info_json = read_file(expected_info_path)
    yt_dl_info_dict = json.loads(info_json)
    logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
    # Grab file path
    media_temp_filepath = yt_dl_info_dict["_filename"]
    media_temp_filename = os.path.basename(media_temp_filepath)
    logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
    # Check that video file given in info JSON exists
    assert(os.path.exists(media_temp_filepath))
    # Generate hash for media file
    file_data = read_file(media_temp_filepath)
    sha512base64_hash = hash_file_data(file_data)
    # Decide where to put the file

    # Check if hash is in media DB
    hash_check_row_dict = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
    if hash_check_row_dict:
        media_already_saved = True
        preexisting_filename = hash_check_row_dict["filename"]
    else:
        preexisting_filename = None

    # Deal with temp file (Move or delete)
    if preexisting_filename:
        # Delete duplicate file if media is already saved
        logging.info("Deleting duplicate video file")
        logging.warning("CODE VIDEO DUPLICATE DELETE STUFF")# TODO FIXME
        final_media_filepath = preexisting_filename
    else:
        # Move file to media DL location
        logging.info("Moving video to final location")
        # Generate output filepath
        file_ext = media_temp_filename.split(".")[-1]
        filename = str(time_of_retreival)+file_ext
        final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
        # Move file to final location
        move_file(media_temp_filepath,final_media_filepath)
        assert(os.path.exists(final_media_filepath))

    # Add video to DB
    new_media_row = Media(
    media_url=video_page,
    sha512base64_hash=sha512base64_hash,
    filename=filename,
    date_added=time_of_retreival,
    extractor_used="tumblr_video_embed",
    tumblrvideo_yt_dl_info_json=info_json
    )
    session.add(new_media_row)
    return {"tumblr_video_embed":sha512base64_hash}


def crop_youube_id(url):
    video_id_regex ="""youtube.com/(?:embed/)?(?:watch\?v=)?([a-zA-Z0-9]+)"""
    video_id_search = re.search(video_id_regex, url, re.IGNORECASE|re.DOTALL)
    if video_id_search:
        video_id = video_id_search.group(1)
        logging.debug("Extracted id: "+repr(video_id)+" from url: "+repr(url))
        return video_id
    else:
        return


def handle_youtube_video(session,post_dict):
    """Download youtube videos from video posts
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    logging.debug("Processing youtube video")
    logging.debug("post_dict"+repr(post_dict))
    assert(post_dict["type"] == u"video")# Ensure calling code isn't broken
    assert(post_dict["video_type"] == u"youtube")# Ensure calling code isn't broken
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
    new_youtube_urls = []
    for youtube_url in youtube_urls:
        youtube_video_id = crop_youube_id(youtube_url)
        # Look up ID in DB
        video_page_query = sqlalchemy.select([Media]).where(Media.youtube_video_id == youtube_video_id)
        video_page_rows = session.execute(video_page_query)
        video_page_row = video_page_rows.fetchone()
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
        else:
            new_youtube_urls.append(youtube_url)
        continue

    # Prevent duplicates from the same post
    new_youtube_urls = uniquify(new_youtube_urls)

    # Download videos if there are any
    if len(new_youtube_urls) > 0:
        # Download each new video
        for new_youtube_url in new_youtube_urls:
            logging.debug("new_youtube_url: "+repr(new_youtube_url))
            # Form command to run
            # Define arguments. see this url for help
            # https://github.com/rg3/youtube-dl
            program_path = os.path.join("youtube-dl","youtube-dl.exe")
            assert(os.path.exists(program_path))
            ignore_errors = "-i"
            safe_filenames = "--restrict-filenames"
            output_arg = "-o"
            info_json_arg = "--write-info-json"
            description_arg ="--write-description"
            output_dir = os.path.join(config.root_path,"temp")
            output_template = os.path.join(output_dir, post_id+".%(ext)s")
            # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
            command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, new_youtube_url]
            logging.debug("command: "+repr(command))
            # Call youtube-dl
            command_result = subprocess.call(command)
            logging.debug("command_result: "+repr(command_result))
            time_of_retreival = get_current_unix_time()
            # Verify download worked
            # Read info JSON file
            expected_info_path = os.path.join(output_dir, post_id+".info.json")
            info_exists = os.path.exists(expected_info_path)
            if not info_exists:
                logging.error("Info file not found!")
                logging.error(repr(locals()))
            info_json = read_file(expected_info_path)
            yt_dl_info_dict = json.loads(info_json)
            logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
            # Grab file path
            media_temp_filepath = yt_dl_info_dict["_filename"]
            media_temp_filename = os.path.basename(media_temp_filepath)
            logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
            # Check that video file given in info JSON exists
            assert(os.path.exists(media_temp_filepath))
            # Generate hash for media file
            file_data = read_file(media_temp_filepath)
            sha512base64_hash = hash_file_data(file_data)
            # Decide where to put the file

            # Check if hash is in media DB
            video_page_query = sqlalchemy.select([Media]).where(Media.youtube_video_id == youtube_video_id)
            video_page_rows = session.execute(video_page_query)
            video_page_row = video_page_rows.fetchone()
            if video_page_row:
                # If media already saved, delete temp file and use old entry's data
                filename = video_page_row["media_filename"]
                logging.debug("Skipping previously saved video: "+repr(video_page_row))
                # Delete duplicate file if media is already saved
                logging.info("Deleting duplicate video file")
                logging.warning("CODE VIDEO DUPLICATE DELETE STUFF")# TODO FIXME
                continue
            else:
                # If media not in DB, move temp file to permanent location
                # Move file to media DL location
                logging.info("Moving video to final location")
                # Generate output filepath
                file_ext = media_temp_filename.split(".")[-1]
                filename = str(time_of_retreival)+"."+file_ext
                final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
                # Move file to final location
                move_file(media_temp_filepath,final_media_filepath)
                assert(os.path.exists(final_media_filepath))

            # Add video to DB
            new_media_row = Media(
            media_url=new_youtube_url,
            sha512base64_hash=sha512base64_hash,
            filename=filename,
            date_added=time_of_retreival,
            extractor_used="youtube_embed",
            youtube_yt_dl_info_json=info_json
            )
            session.add(new_media_row)
            continue

        logging.debug("Finished downloading youtube embeds")
        return {"youtube_embed":sha512base64_hash}
    else:
        return {}


def handle_vine_video(session,post_dict):
    """Handle downloading of vine videos"""
    #TODO FIXME!
    assert(False)# Get on this


def handle_video_posts(session,post_dict):
    """Decide which video functions to run"""
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
    else:
        logging.error("Unknown video type!")
        logging.error("locals(): "+repr(locals()))
        assert(False)
    return {}


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
    track_id = re.search("""api\.soundcloud\.com/tracks/(\d+)/stream""", soundcloud_link, re.IGNORECASE|re.DOTALL).group(1)
    soundcloud_id = track_id

    # Check if audio has been saved, and return if it has
    id_query = sqlalchemy.select([Media]).where(Media.soundcloud_id == soundcloud_id)
    id_rows = session.execute(id_query)
    id_row = id_rows.fetchone()
    logging.debug("id_row: "+repr(id_row))
    if id_row:
        logging.debug("Soundcloud audio with this ID has already been saved, skipping")
        sha512base64_hash = id_row["sha512base64_hash"]
        return {"soundcloud_audio_embed":sha512base64_hash}

    # Grab url to send to youtube-dl
    soundcloud_url = post_dict["audio_url"]
    logging.debug("soundcloud_url: "+repr(soundcloud_url))
    # Form command to run
    # Define arguments. see this url for help
    # https://github.com/rg3/youtube-dl
    program_path = os.path.join("youtube-dl","youtube-dl.exe")
    assert(os.path.exists(program_path))
    ignore_errors = "-i"
    safe_filenames = "--restrict-filenames"
    output_arg = "-o"
    info_json_arg = "--write-info-json"
    description_arg ="--write-description"
    output_dir = os.path.join(config.root_path,"temp")
    output_template = os.path.join(output_dir, post_id+".%(ext)s")
    command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, soundcloud_url]
    logging.debug("command: "+repr(command))
    # Call youtube-dl
    command_result = subprocess.call(command)
    logging.debug("command_result: "+repr(command_result))
    time_of_retreival = get_current_unix_time()
    # Verify download worked
    # Read info JSON file
    expected_info_path = os.path.join(output_dir, post_id+".info.json")
    info_exists = os.path.exists(expected_info_path)
    if not info_exists:
        logging.error("Info file not found!")
        logging.error(repr(locals()))
    info_json = read_file(expected_info_path)
    yt_dl_info_dict = json.loads(info_json)
    logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
    # Grab file path
    media_temp_filepath = yt_dl_info_dict["_filename"]
    media_temp_filename = os.path.basename(media_temp_filepath)
    logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
    # Check that video file given in info JSON exists
    assert(os.path.exists(media_temp_filepath))
    # Generate hash for media file
    file_data = read_file(media_temp_filepath)
    sha512base64_hash = hash_file_data(file_data)
    # Decide where to put the file

    # Check if hash is in media DB
    hash_check_row_dict = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
    if hash_check_row_dict:
        preexisting_filename = hash_check_row_dict["filename"]
    else:
        preexisting_filename = None

    if preexisting_filename:
        # Delete temp file if media is already saved
        logging.info("Deleting duplicate video file")
        os.remove(media_temp_filepath)
        os.remove(expected_info_path)
        filename = preexisting_filename
        final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
    else:
        # Move file to media DL location
        logging.info("Moving video to final location")
        # Generate output filepath
        file_ext = media_temp_filename.split(".")[-1]
        filename = str(time_of_retreival)+"."+file_ext
        final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
        # Move file to final location
        move_file(media_temp_filepath,final_media_filepath)
    assert(os.path.exists(final_media_filepath))

    # Add video to DB
    new_media_row = Media(
    media_url=soundcloud_link,
    sha512base64_hash=sha512base64_hash,
    filename=filename,
    date_added=time_of_retreival,
    extractor_used="soundcloud_audio_embed",
    soundcloud_yt_dl_info_json=info_json,
    soundcloud_id = soundcloud_id
    )
    session.add(new_media_row)

    logging.debug("Finished downloading soundcloud embed")
    return {"soundcloud_audio_embed":sha512base64_hash}


def handle_tumblr_audio(session,post_dict):
    """Download tumblr-hosted audio from audio posts
    see this link for a reference implimentation
    https://github.com/atesh/XKit
    https://github.com/atesh/XKit/blob/master/Extensions/audio_downloader.js"""
    assert(post_dict["audio_type"] == u"tumblr")
    logging.debug("post_dict: "+repr(post_dict))
    # Generate a link to the audio file
    api_media_url = post_dict["audio_url"]
    # This is basically check if url starts with this string
    if "https://www.tumblr.com/audio_file/" in api_media_url:
        # and here it sets the de-facto URL for downloading
        media_url = "http://a.tumblr.com/" + urllib.quote(api_media_url.split("/")[-1]) + "o1.mp3"
    else:
        media_url = api_media_url
    logging.debug("media_url: "+repr(media_url))

    # Check the DB to see if media is already saved
    url_check_row_dict = sql_functions.check_if_media_url_in_DB(session,media_url)
    if url_check_row_dict:
        media_already_saved = True
        sha512base64_hash = row_dict["sha512base64_hash"]
        existing_filename = row_dict["filename"]
        logging.debug("URL is already in DB, no need to save file.")
        return {"tumblr_audio":sha512base64_hash}

    # Load the media file
    file_data = get(media_url)
    time_of_retreival = get_current_unix_time()
    # Check if file is saved already using file hash
    sha512base64_hash = hash_file_data(file_data)
    logging.debug("sha512base64_hash: "+repr(sha512base64_hash))

    # Check if hash is in media DB
    hash_check_row_dict = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
    if hash_check_row_dict:
        media_already_saved = True
        preexisting_filename = hash_check_row_dict["filename"]
    else:
        logging.debug("Hash is already in DB, no need to save file.")
        return {"tumblr_audio":sha512base64_hash}

    if media_already_saved:
        # Use filename from DB
        audio_filename = existing_filename
    else:
        # Generate filename
        audio_filename = str(time_of_retreival)+".mp3"
        logging.debug("audio_filename: "+repr(audio_filename))
        file_path = generate_media_file_path_timestamp(root_path=config.root_path,filename=audio_filename)
        # Save media to disk
        save_file(filenamein=file_path,data=file_data,force_save=False)

    # Add new row to DB
    new_media_row = Media(
    media_url = media_url,
    sha512base64_hash = sha512base64_hash,
    media_filename = audio_filename,
    date_added = time_of_retreival,
    extractor_used = "tumblr_audio"
    )
    session.add(new_media_row)

    return {"tumblr_audio":sha512base64_hash}


def handle_audio_posts(session,post_dict):
    """Download audio from audio posts"""
    # Determing if post is tumblr audio
    if post_dict["type"] != u"audio":
        return {}
    # Tumblr hosted audio
    if post_dict["audio_type"] == u"tumblr":
        logging.debug("Post is tumblr audio")
        return handle_tumblr_audio(session,post_dict)
    if post_dict["audio_type"] == u"soundcloud":
        logging.debug("Post is tumblr audio")
        return handle_soundcloud_audio(session,post_dict)
    return {}


def save_media(session,post_dict):
    """ Main function for saving a posts media"""
    #logging.info("Saving post media")
    #logging.debug("post_dict"+repr(post_dict))
    logging.debug('post_dict["type"] '+repr(post_dict["type"] ))
    # Get list of links
    all_post_links = extract_post_links(post_dict)
    logging.debug("all_post_links"+repr(all_post_links))
    # Remove links already in DB
    logging.warning("Preexisting link check is disabled.")
    preexisting_link_dict = {}# {link:hash}# TODO FIXME
    logging.debug("preexisting_link_dict: "+repr(preexisting_link_dict))
    new_links = []
    preexisting_links = preexisting_link_dict.keys()
    for post_link in all_post_links:
        if post_link in preexisting_links:
            continue
        else:
            new_links.append(post_link)
    new_links = uniquify(new_links)
    logging.debug("new_links: "+repr(new_links))
    # Save image links (Remote) ex. http://foo.com/image.jpg
    if config.save_images:
        image_link_dict={}# = handle_image_links(session,new_links)# {link:hash}
    else:
        image_link_dict = {}
    # Save photos sections (Tumblr)
    if config.save_photos:
        tumblr_photos_link_dict = handle_tumblr_photos(session,post_dict)# {link:hash}
    else:
        tumblr_photos_link_dict = {}
    # Save videos, both tumblr and youtube (Tumblr & Youtube)
    if config.save_videos:
        video_embed_dict = handle_video_posts(session,post_dict)
    # Saved linked videos
    # TODO FIXME
    # Save audio
    if config.save_audio:
        audio_embed_dict = handle_audio_posts(session,post_dict)
    # Join mapping dicts # {link:hash}
    link_to_hash_dict = merge_dicts(
    preexisting_link_dict,
    image_link_dict,
    tumblr_photos_link_dict,
    video_embed_dict,
    audio_embed_dict,
    )
    logging.debug("link_to_hash_dict: "+repr(link_to_hash_dict))
    # Replace links with marker string
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
    handle_soundcloud_audio(session,soundcloud_post_dict)

    # Debug video
    logging.debug("Debug video")
    tumblr_video_post_dict = {u'reblog_key': u'3bqfxHgy', u'short_url': u'http://tmblr.co/Z_sLQw1eYTSqS', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}], u'id': 112247295260L, u'post_url': u'http://tsitra360.tumblr.com/post/112247295260/my-latest-art-timelapse-is-up-see-how-i-drew', u'tags': [], u'highlighted': [], u'state': u'published', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1425068852, u'note_count': 79, u'video_type': u'youtube', u'date': u'2015-02-27 20:27:32 GMT', u'thumbnail_height': 360, u'permalink_url': u'https://www.youtube.com/watch?v=tT5pifkZzEk', u'slug': u'my-latest-art-timelapse-is-up-see-how-i-drew', u'blog_name': u'tsitra360', u'caption': u'<p>My latest art timelapse is up! See how I drew Berry Swirl on my youtube channel.</p>', u'thumbnail_url': u'https://i.ytimg.com/vi/tT5pifkZzEk/hqdefault.jpg'}
    youtube_video_post_dict = {u'reblog_key': u'HfjckfH7', u'short_url': u'http://tmblr.co/ZUGffq1cfuHuJ', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}], u'id': 110224285203L, u'post_url': u'http://askbuttonsmom.tumblr.com/post/110224285203/throwback-can-you-believe-its-been-almost-2yrs', u'tags': [u"button's mom", u'hardcopy', u'song', u'shadyvox'], u'highlighted': [], u'state': u'published', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1423197599, u'note_count': 145, u'video_type': u'youtube', u'date': u'2015-02-06 04:39:59 GMT', u'thumbnail_height': 360, u'permalink_url': u'https://www.youtube.com/watch?v=lGIEmH3BoyA', u'slug': u'throwback-can-you-believe-its-been-almost-2yrs', u'blog_name': u'askbuttonsmom', u'caption': u'<p>Throwback! Can you believe it&#8217;s been almost 2yrs since this came out? Mommy&#8217;s getting old&#8230;</p>', u'thumbnail_url': u'https://i.ytimg.com/vi/lGIEmH3BoyA/hqdefault.jpg'}
    youtube_dict_two = {u'highlighted': [], u'reblog_key': u'qO3JnfS7', u'player': [{u'width': 250, u'embed_code': False}, {u'width': 400, u'embed_code': False}, {u'width': 500, u'embed_code': False}], u'format': u'html', u'timestamp': 1390412461, u'note_count': 4282, u'tags': [], u'video_type': u'youtube', u'id': 74184911379L, u'post_url': u'http://askbuttonsmom.tumblr.com/post/74184911379/ask-thecrusaders-bar-buddies-dont-worry', u'caption': u'<p><a class="tumblr_blog" href="http://ask-thecrusaders.tumblr.com/post/74162414750/bar-buddies-dont-worry-neon-you-will-have-your">ask-thecrusaders</a>:</p>\n<blockquote>\n<p><strong>"Bar Buddies"</strong><br/><br/>Dont\u2019 worry Neon, you will have your music video soon enough.</p>\n</blockquote>\n<p>Honestly, that Neon Lights is a TERRIBLE influence!! No son of mine will grow up to be a drunken drug-shooting bass dropping hipster! :C</p>', u'state': u'published', u'html5_capable': False, u'reblog': {u'comment': u'<p>Honestly, that Neon Lights is a TERRIBLE influence!! No son of mine will grow up to be a drunken drug-shooting bass dropping hipster! :C</p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://ask-thecrusaders.tumblr.com/post/74162414750/bar-buddies-dont-worry-neon-you-will-have-your">ask-thecrusaders</a>:</p><blockquote>\n<p><strong>"Bar Buddies"</strong><br/><br/>Dont\u2019 worry Neon, you will have your music video soon enough.</p>\n</blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'title_font': u'Helvetica Neue', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'avatar_shape': u'circle', u'show_avatar': True, u'background_color': u'#F6F6F6', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f'}, u'name': u'ask-thecrusaders'}, u'comment': u'<p><strong>"Bar Buddies"</strong><br><br>Dont\u2019 worry Neon, you will have your music video soon enough.</p>', u'post': {u'id': u'74162414750'}}]}, u'short_url': u'http://tmblr.co/ZUGffq155m_eJ', u'date': u'2014-01-22 17:41:01 GMT', u'type': u'video', u'slug': u'ask-thecrusaders-bar-buddies-dont-worry', u'blog_name': u'askbuttonsmom'}
    #handle_tumblr_videos(session,tumblr_video_post_dict)
    #handle_youtube_video(session,youtube_video_post_dict)
    #handle_youtube_video(session,youtube_dict_two)


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
