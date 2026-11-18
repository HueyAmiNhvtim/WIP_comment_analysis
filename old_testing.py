import time
import json

from chat_replay_downloader.chat_replay_downloader import get_chat_replay

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_comments(url: str):
    driver = Chrome(executable_path="/usr/local/bin/chromedriver")

    driver.get(url)
    driver.execute_script("window.scrollTo(0, 750)")
    # WOW THIS THING IS MUCH SHORTER THAN XPATH.
    NUM_COMMENTS_CSS_SELECTOR = "#header > ytd-comments-header-renderer > #title > #count > .count-text"

    # Wait for a few seconds so that the Youtube comments can load before the script is executed
    wait_man = WebDriverWait(driver, 10)
    time.sleep(10)
    time.sleep(1)
    wait_man.until(EC.visibility_of_element_located((By.CSS_SELECTOR, NUM_COMMENTS_CSS_SELECTOR)))
    total_com = driver.find_element(By.CSS_SELECTOR, NUM_COMMENTS_CSS_SELECTOR)
    wait_man.until(EC.visibility_of_element_located((By.XPATH, "//*[@id='content-text']")))

    # wait until the comments loading is done
    WebDriverWait(driver, 30).until(
        EC.invisibility_of_element((By.CSS_SELECTOR, "div.active.style-scope.paper-spinner")))

    # load all comments
    load_all_comments(driver)
    # open all replies
    for reply in driver.find_elements_by_xpath(
            "//*[@id='replies']//paper-button[@class='style-scope ytd-button-renderer'][contains(.,'View')]"):
        reply.location_once_scrolled_into_view
        driver.execute_script("arguments[0].click()", reply)
        for more_reply in driver.find_elements_by_xpath(
                "//*[@id='replies']//paper-button[@class='style-scope yt-next-continuation'][contains(., 'Show more replies')]"):
            try:
                more_reply.location_once_scrolled_into_view
                driver.execute_script("arguments[0].click()", more_reply)
            except StaleElementReferenceException:
                pass
    comments_list = driver.find_elements_by_xpath("//*[@id='content-text']")

    # Print the comments. Comments with nothing in it is filled with custom emojis
    for i in range(len(comments_list)):
        print(f"Comment {i+1} {comments_list[i].text}")
    print(f"{len(comments_list)} extracted comments / {total_com.text}")
    driver.quit()


def load_all_comments(web_driver):
    """WHY IS IT SO SIMPLE? WHY CAN'T I THINK OF THAT?"""
    """Code extracted from https://github.com/SodakDoubleD/youtube-comment-scraper/blob/master/youtube_comment_scraper.py#L32"""
    """Thank you so much SodakDoubleD"""
    time.sleep(5)

    get_scroll_height_command = (
        "return (document.documentElement || document.body).scrollHeight;"
    )
    scroll_to_command = "scrollTo(0, {});"

    # Set y origin and grab the initial scroll height
    y_position = 0
    scroll_height = web_driver.execute_script(get_scroll_height_command)

    print("Opened url, scrolling to bottom of page...")
    # While the scrollbar can still scroll further down, keep scrolling
    # and asking for the scroll height to check again
    # scrollTo makes the driver scroll to a particular coordinate, making that point appear
    # at the top left of the page it seems. (0,0) coordinate is the top left-most of the entire
    # webpage, scrollTo(x, y) make the coordinate of the visible top-left of the webpage be (x, y)
    while y_position != scroll_height:
        y_position = scroll_height
        web_driver.execute_script(scroll_to_command.format(scroll_height))

        # Page needs to load yet again otherwise the scroll height matches the y position
        # and it breaks out of the loop
        time.sleep(4)
        scroll_height = web_driver.execute_script(get_scroll_height_command)



scrape_comments("https://www.youtube.com/watch?v=Pak5J1sk6fc")
