#-------------------------------------------------------------------------------
# Name:        yt_dl_wrapper
# Purpose:
#
# Author:      User
#
# Created:     08/04/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sqlalchemy
import subprocess# For video and some audio downloads

# This project
from utils import *
from tables import *# This module only has the table classes
import sql_functions
import config # User settings




def run_yt_dl_multiple(session,download_urls,extractor_used,audio_id=None,video_id=None):
    """Run yt-dl for n >= 0 videos
    Return joined dicts passed back from run_yt_dl_single()
    """
    assert(type(download_urls) is type([]))
    # Prevent duplicate downloads
    download_urls = uniquify(download_urls)
    # Download videos if there are any
    media_id_list = []
    for download_url in download_urls:
        media_id_list += run_yt_dl_single(
            session=session,
            download_url=download_url,
            extractor_used=extractor_used,
            audio_id=audio_id,
            video_id=video_id,
            )
        continue
    return media_id_list


def run_yt_dl_single(session,download_url,extractor_used,audio_id=None,video_id=None):
    """Run youtube-dl for extractors, adding row to the table whose ORM class is given
    return """
    logging.debug("download_url: "+repr(download_url))

    temp_id_timestamp = str(get_current_unix_time())# For filenames in the temp dir
    sanitized_download_url_for_hash = download_url.encode("ascii","ignore")
    temp_id_hash = hash_file_data(sanitized_download_url_for_hash)# For filenames in the temp dir
    temp_id = temp_id_timestamp+"."+temp_id_hash

    # Check that URL is not already saved
    video_page_row = sql_functions.check_if_media_url_in_DB(
        session=session,
        media_url=download_url
        )
    if video_page_row:
        logging.debug("Skipping previously saved video: "+repr(video_page_row))
        return [video_page_row["media_id"]]

    # Form command to run
    # Define arguments. see this url for help
    # https://github.com/rg3/youtube-dl
    program_path = config.youtube_dl_path
    assert(os.path.exists(program_path))
    ignore_errors = "-i"
    safe_filenames = "--restrict-filenames"
    output_arg = "-o"
    info_json_arg = "--write-info-json"
    description_arg ="--write-annotations"
    max_filesise_arg = "--max-filesize"#+config.youtube_dl_max_filesize
    output_dir = os.path.join(config.root_path,"temp")
    output_template = os.path.join(output_dir, temp_id+".%(ext)s")# CHECK THIS! Will multiple videos in a link be an issue?

    # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
    command = [
        program_path,
        ignore_errors,
        safe_filenames,
        max_filesise_arg, config.youtube_dl_max_filesize,
        info_json_arg,
        description_arg,
        output_arg, output_template,
        download_url
        ]
    logging.debug("command: "+repr(command))
    # Call youtube-dl
    command_result = subprocess.call(command)
    logging.debug("command_result: "+repr(command_result))
    time_of_retreival = get_current_unix_time()

    # Verify download worked
    if command_result != 0:
        logging.error("Command did not return 0, this means something went wrong.")
        logging.error("Failed to save media: "+repr(download_url))
        logging.error(repr(locals()))
        return {}

    # Read info JSON file
    expected_info_path = os.path.join(output_dir, temp_id+".info.json")
    info_exists = os.path.exists(expected_info_path)
    if not info_exists:
        logging.error("Info file not found!")
        logging.error(repr(locals()))
        return {}
    info_json = read_file(expected_info_path)
    yt_dl_info_dict = json.loads(info_json)
    logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))

    # Grab file path
    media_temp_filepath = yt_dl_info_dict["_filename"]
    media_temp_filename = os.path.basename(media_temp_filepath)
    file_ext = media_temp_filename.split(".")[-1]
    logging.debug("media_temp_filepath: "+repr(media_temp_filepath))

    # Check that video file given in info JSON exists
    if not os.path.exists(media_temp_filepath):
        logging.error("Video file not found!")
        logging.error("Failed to save media: "+repr(download_url))
        logging.error(repr(locals()))
        return {}

    # Generate hash for media file
    sha512base16_hash = hash_file(media_temp_filepath)
    md5base64_hash = generate_md5b64_for_file(file_path)

    # Get size of file
    file_size_in_bytes = find_file_size(file_path)
    
    # Pause to make sure file is not in use
    time.sleep(10)

    # Decide where to put the file
    # Check if hash is in media DB
    video_page_row = sql_functions.check_if_hash_in_db(session,sha512base16_hash)
    if video_page_row:
        # If media already saved, delete temp file and use old entry's data
        filename = video_page_row["local_filename"]
        logging.debug("Skipping previously saved video: "+repr(video_page_row))
        # Delete duplicate file if media is already saved
        logging.info("Deleting duplicate video file: "+repr(media_temp_filepath))
        delete_file(media_temp_filepath)
    else:
        # If media not in DB, move temp file to permanent location
        # Move file to media DL location
        logging.info("Moving video to final location")
        # Generate output filepath
        filename = generate_filename(ext=file_ext,sha512base16_hash=sha512base16_hash)
        final_media_filepath = generate_path(root_path=config.root_path,filename=filename)
        # Move file to final location
        move_file(media_temp_filepath,final_media_filepath)
        assert(os.path.exists(final_media_filepath))

    # Remove info file
    delete_file(expected_info_path)

    # Add video to DB
    # Build as dict to allow name differences
    row_dict = {}
    # Mandantory values
    row_dict["media_url"] = download_url
    row_dict["sha512base16_hash"] = sha512base16_hash
    row_dict["local_filename"] = filename
    row_dict["file_extention"] = file_ext
    row_dict["date_added"] = time_of_retreival
    row_dict["extractor_used"] = extractor_used
    row_dict["yt_dl_info_json"] = info_json
    row_dict["md5base64_hash"] = md5base64_hash
    row_dict["file_size_in_bytes"] = file_size_in_bytes
    # Optional values
    if audio_id:
        row_dict["audio_id"] = audio_id
    if video_id:
        row_dict["video_id"] = video_id

    new_db_row = Media(**row_dict)# Create a row by instantiating the table's class using the dict as arguments
    session.add(new_db_row)
    session.commit()

    logging.debug("Finished downloading "+repr(download_url)+" using yt-dl")
    # Get the id back
    get_id_row = sql_functions.check_if_hash_in_db(session,sha512base16_hash)
    media_id = get_id_row["media_id"]
    media_id_list = [media_id]
    return media_id_list


def update_yt_dl():# TODO
    """Update youtube-dl to the latest version"""



def debug():
    """For WIP, debug, ect function calls"""
    session = sql_functions.connect_to_db()

    # gfycat
    gfycat_result = run_yt_dl_single(
        session,
        download_url = "http://gfycat.com/MerryAdolescentAlaskankleekai",
        extractor_used = "DEBUG:linked_gfycat",
        audio_id=None,
        video_id=None
        )
    logging.debug("gfycat_result: "+repr(gfycat_result))
    # youtube https://www.youtube.com/embed/JIQ_jjfDsw0
    youtube_result = run_yt_dl_single(
        session,
        download_url = "https://www.youtube.com/embed/JIQ_jjfDsw0",
        extractor_used = "DEBUG:youtube",
        audio_id=None,
        video_id=None
        )






def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","yt_dl_common_log.txt"))
        debug()
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
