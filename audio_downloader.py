#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:  python translation of audio_downloader.js
#
# Author:      User
#
# Created:     12/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import random

from utils import *

API_KEY = "fuiKNFp9vQFvjLNvx4sUwti4Yb5yGutBN4Xh10LXZhhRKjWlV4"






def download(post_id,username):# ln 54
    # Load api JSON for page
    api_url = "https://api.tumblr.com/v2/blog/" + username + ".tumblr.com/posts" + "?api_key=" + API_KEY + "&id=" + post_id#ln 56
    logging.debug("api_url: "+repr(api_url))
    api_json = get(api_url)# ln 58-62
    api_dict = json.loads(api_json)
    logging.debug("api_dict: "+repr(api_dict))

    # Verify API data
    assert("posts" in api_dict.keys())# ln 67-68
    assert(len(api_dict["posts"]) >= 1)# ln 67-68

    if api_dict["posts"][0]["audio_type"] == "tumblr":# ln 72-75
        m_url = api_dict["posts"][0]["audio_url"]
        if "https://www.tumblr.com/audio_file/" in m_url:
            m_url = "http://a.tumblr.com/" + m_url.split("/")[-1] + "o1.mp3"

    m_id = "audio_" + make_id()# ln 79

    if "track_name" in api_dict["posts"][0].keys():# ln 88
        audio_name = api_dict["posts"][0]["track_name"]# ln 81
    else:
        audio_name = ""

    if "artist" not in api_dict["posts"][0].keys():# ln84-85
        audio_author = "unknown"# ln84-85
    else:
        audio_author = api_dict["posts"][0]["artist"]# ln 82

    # if (typeof audio_name !== "undefined" && audio_name !== "") {
    if (audio_name != ""):# ln 88
        # m_id = audio_name.replace(/\W/g, '') + "__" + audio_author.replace(/\W/g, '')
        m_id = re.sub('\w/g', '', audio_name) + "__" + re.sub('\w/g', '', audio_author)# ln 89
    # http://www.xkit.info/seven/helpers/audioget.php?fln=" + m_url + "&id=" + m_id + "\"
    download_link = "http://www.xkit.info/seven/helpers/audioget.php?fln=" + m_url + "&id=" + m_id + "\\"# ln 97-98
    media_file_data = get(download_link)
    file_path = os.path.join("download", "test", "test.mp3")
    save_file(filenamein=file_path,data=media_file_data,force_save=True)








def make_id():
    text = ""
    possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    i = 0
    while i < 15:
        i += 1
        text += random.choice(possible)
    logging.debug("text: "+repr(text))
    return text














def main():
    download(post_id="111911672818",username="askbuttonsmom")

if __name__ == '__main__':
    main()
