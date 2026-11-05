# Thanks https://stackoverflow.com/questions/62741559/how-to-get-all-comments-in-youtube-with-selenium
# NOTE: LEARN TO UNDERSTAND THE CODE FULLY.
# TO-DO: EXTRACT THE FILES IN A JSON FILE. ONE FOR LIVE CHAT AND ONE FOR COMMENT SECTION AND OTHER STUFF
#        THEN LANGUAGE DETECTION THOSE THINGS. ALSO INCLUDE EXCEPTIONS.
#        TRY TO INCORPORATE THE LIVE CHAT EXTRACTORS SO THAT YOU CAN DO BOTH AT THE SAME TIME.
#        ALSO, EXTRACT THE COMMENTS OUT OF THE LIVECHAT'S LIST OF DICTIONARIES AND PUT THEM
#        INTO A SEPARATE LIVE_CHAT_COMMENT_LIST
# Put those comments with only emojis in the OTHER section
# The code is kinda garbage tho. The accuracy of this is not 100%, but it should do the job most of the time
# Note: Try to use major ticks as years, and minor ticks as months...
import time
import json

from chat_replay_downloader.chat_replay_downloader import get_chat_replay

from selenium.common.exceptions import StaleElementReferenceException
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm

vid_no = 0  # Hard-coded, I know
streamer_names = ["watame"]
streamer_backup = ["kiara", "pekora", "aqua", "watame"]


def load_streamer_url_list(index, video_number):
    """Load the URL containing links to the streamers"""
    filename = f"streamer_url_list/{streamer_names[index]}_url"
    name = streamer_names[index]
    video_index = video_number
    f = open(filename, mode="r")
    url_list = json.loads(f.read())

    # Save time man...
    # The thing is the code does not extract all live chat 100% of the time, so this is the
    # the stopgap measure to reextract the live chat.
    # So basically, run this file, then detection.
    if name == "kiara":
        # For kiara: Remember to use the change the filename of 17 to position 0
        # THere is another that uses this URL https://www.youtube.com/watch?v=wyjvTl8FMVE, change that to pos 1
        video_index = 12
        # Kiara: vid_index 3 needs to reextract the live chat.
        # Pekora: check vid_index 11
        #while video_index < len(url_list):
        scrape_comments(url_list[video_index], video_index, name)
        # extracting_live_chat(url_list[video_index], video_index, name)
        print(f"\n---------FINISHED {streamer_names[index].upper()}'S VID {video_index + 1}---------\n")
        video_index += 1
    else:
        while video_index < len(url_list):
            scrape_comments(url_list[video_index], video_index, name)
            # extracting_live_chat(url_list[video_index], video_index, name)
            print(f"\n---------FINISHED {streamer_names[index].upper()}'S VID {video_index + 1}---------\n")
            video_index += 1
    f.close()


def scrape_comments(url: str, vid_index, streamer_name):
    print("Now extracting the comment sections...")
    options = webdriver.ChromeOptions()
    options.timeouts = {"script": 5000}
    driver = Chrome(options=options)
    driver.fullscreen_window()

    driver.get(url)
    driver.execute_script("window.scrollTo(0, 750)")
    # WOW THIS THING IS MUCH SHORTER THAN XPATH.
    # From 2024 Huy: mf Youtube changed their CSS names.
    VIEW_CSS_SELECTOR = "#count > yt-view-count-renderer > span.view-count.yt-view-count-renderer"
    NAME_CSS_SELECTOR = "yt-formatted-string.ytd-video-primary-info-renderer:nth-child(1)"
    NUM_COMMENTS_CSS_SELECTOR = "#header > ytd-comments-header-renderer > #title > #count > .count-text"

    # Wait for a few seconds so that the Youtube comments can load before the script is executed
    wait_man = WebDriverWait(driver, 10)
    time.sleep(5) 
    view_count = driver.find_element(By.CSS_SELECTOR, VIEW_CSS_SELECTOR)
    vid_name = driver.find_element(By.CSS_SELECTOR, NAME_CSS_SELECTOR)
    vid_name_y_location = vid_name.location['y']
    # prevent error from not finding the total number of recorded comments (including deleted or
    # shadowbanned ones)
    driver.execute_script(f"scrollTo(0, {vid_name_y_location})")
    time.sleep(5)
    total_com = driver.find_element(By.CSS_SELECTOR, NUM_COMMENTS_CSS_SELECTOR)

    # get the last comment
    wait_man.until(EC.visibility_of_element_located((By.XPATH, "//*[@id='content-text']")))

    # load all comments
    load_all_comments(driver)

    # open all replies, including "Show more replies"
    for reply in driver.find_elements_by_xpath(
            "//*[@id='replies']//paper-button[@class='style-scope ytd-button-renderer'][contains(.,'View')]"):
        # It's for to scroll the screen to see the reply button and then click on it.
        # reply.location_once_scrolled_into_view
        driver.execute_script("arguments[0].scrollIntoView()", reply)
        driver.execute_script("arguments[0].click()", reply)

        for more_reply in driver.find_elements_by_xpath(
                "//*[@id='replies']//paper-button[@class='style-scope yt-next-continuation'][contains(., 'Show more replies')]"):
            try:
                driver.execute_script("arguments[0].scrollIntoView()", more_reply)
                driver.execute_script("arguments[0].click()", more_reply)
            except StaleElementReferenceException:
                pass
    time.sleep(5)

    comments_list = driver.find_elements_by_xpath("//*[@id='content-text']")

    # Print the comments. Comments with nothing in it is filled with custom emojis
    print(view_count.text)
    print(vid_name.text)
    print(f"{len(comments_list)} extracted comments / {total_com.text}")
    collecting_parameters(list_comment=comments_list,
                          view_count=view_count,
                          video_index=vid_index,
                          video_title=vid_name,
                          total_comments=total_com,
                          streamer_name=streamer_name)
    print("Finished extracting comment sections")
    driver.quit()


def load_all_comments(web_driver):
    """WHY IS IT SO SIMPLE? WHY CAN'T I THINK OF THAT?"""
    """Code extracted from https://github.com/SodakDoubleD/youtube-comment-scraper/blob/master/youtube_comment_scraper.py#L32"""
    """Thank you so much SodakDoubleD"""
    # wait until the comments loading is done
    time.sleep(5)  # I suppose that waiting for the loading selector to disappear is not always 100% reliable.
    WebDriverWait(web_driver, 30).until(
        EC.invisibility_of_element((By.CSS_SELECTOR, "div.active.style-scope.paper-spinner")))
    # Javascript ||: Logical OR
    get_current_scroll_height_command = (
        "return (document.documentElement || document.body).scrollHeight;"
    )
    scroll_to_command = "scrollTo(0, {})"

    # Set the origin of y-position.
    # While the scrollbar can still scroll further down, keep scrolling
    # and asking for the scroll height to check again.

    # scrollTo makes the driver scroll to a particular coordinate, making that point appear
    # at the top left of the page it seems. (0,0) coordinate is the top left-most of the entire
    # webpage, scrollTo(x, y) make the coordinate of the visible top-left of the webpage be (x, y)
    y_position = 0
    scroll_height = web_driver.execute_script(get_current_scroll_height_command)
    while y_position != scroll_height:
        y_position = scroll_height
        web_driver.execute_script(scroll_to_command.format(y_position))

        # Allows the page to load, otherwise the y_postion would be equal to scrollHeight,
        # making it break out of the loop.
        time.sleep(4)
        scroll_height = web_driver.execute_script(get_current_scroll_height_command)


def extract_text(var):
    # list for lists of comment, else for the viewcount and such.
    if isinstance(var, list):
        var = [comment.text for comment in var]
        return var
    else:
        var = var.text
        return var


def collecting_parameters(list_comment, view_count, video_index, video_title, total_comments, streamer_name):
    """The video_index will be used to add counter to files"""
    list_comment = extract_text(list_comment)
    view_count = extract_text(view_count)
    video_title = extract_text(video_title)
    total_comments = extract_text(total_comments)
    vid_neccessary_info = [video_index, video_title, view_count, total_comments]
    load_into_streamer_JSON(streamer_name, vid_neccessary_info, list_comment)


def load_into_streamer_JSON(streamer_name, vid_info, comment_list):
    video_index = vid_info[0]
    yeet = f"streamer_comments/{streamer_name}/post_live/{streamer_name}_post_stream_#{4}.json"
    vids_info_file = f"streamer_comments/{streamer_name}/vid_info/{streamer_name}_stream_#{4}.json"
    with open(yeet, mode="w") as file:
        json.dump(comment_list, file)
    with open(vids_info_file, mode="w") as file:
        json.dump(vid_info, file)
    return


def extracting_live_chat(url: str, vid_index, streamer_name):
    print("Now extracting live chat...")
    try:
        youtube_messages = get_chat_replay(url)
        live_messages_stream_time_stamp = []
        for msg_i in tqdm(len(youtube_messages)):
            full_info = youtube_messages[msg_i]
        # for full_info in youtube_messages:
            LMST = {full_info["message"]: full_info["time_in_seconds"]}
            live_messages_stream_time_stamp.append(LMST)
        live_chat_file_path = f"streamer_comments/{streamer_name}/live/{streamer_name}_LC_#{4}.json"
        with open(live_chat_file_path, mode="w") as file:
            json.dump(live_messages_stream_time_stamp, file)
        print(f"{len(live_messages_stream_time_stamp)} messages extracted in the livechat replay.")
        print("Finished extracting live chat")
    except json.decoder.JSONDecodeError:  # From 2024 Huy: hmm, why did we decide to rerun this function???
        extracting_live_chat(url, vid_index, streamer_name)


if __name__ == "__main__":
    for streamer_index in range(len(streamer_names)):
        print(f"[INFO] EXTRACTING {streamer_names[streamer_index].upper()}'S STREAMS NOW")
        load_streamer_url_list(streamer_index, vid_no)
        print(f"[INFO] FINISHED EXTRACTING {streamer_names[streamer_index].upper()}'S STREAMS ")


