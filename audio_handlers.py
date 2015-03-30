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
    program_path = config.youtube_dl_path
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
        logging.info("Deleting duplicate audio file")
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
    session.commit()
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
    session.commit()
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




def main():
    pass

if __name__ == '__main__':
    main()
