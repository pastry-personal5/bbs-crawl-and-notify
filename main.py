"""
This module get contents from the web site,
then send that content to a telegram chat room with a bot.
You cannot use requests and BeautifulSoup only. Use of selenium is required to get the content from the web site - "fmkorea.com."
"""

import datetime
import re
import signal
import sys
from threading import Event


from bs4 import BeautifulSoup
from loguru import logger
import requests
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
import selenium
import yaml


class VisitedItemRecorder:

    def __init__(self, tags: list):
        """This function initializes the object.

        Args:
            tags (list): |tags| is optional. |tags| is shallow-copied using `copy()` call.
        """
        self.tags = tags.copy()
        self.visited_items = set()

    def is_visited(self, item: str):
        return item in self.visited_items

    def add_item(self, item: str):
        self.visited_items.add(item)

    def get_visited_items(self):
        return self.visited_items


class LinkVisitorClientContext:
    driver = None  # It's a Selenium driver.

    def __init__(self):
        self.driver = None

    def clean_up(self):
        if self.driver:
            self.driver.quit()


def visit_page(driver: Chrome, url: str) -> None:
    try:
        driver.get(url)
    except selenium.common.exceptions.WebDriverException as e:
        logger.error(f"Error visiting {url}")
        logger.error(e)
        sys.exit(-1)


def create_client_context_with_selenium() -> LinkVisitorClientContext:
    driver = webdriver.Chrome()
    driver.implicitly_wait(0.5)

    client_context = LinkVisitorClientContext()
    client_context.driver = driver
    return client_context


def visit_with_selenium(client_context: LinkVisitorClientContext, url: str) -> None:
    visit_page(client_context.driver, url)


def remove_video_tag_message(text: str) -> str:
    return text.replace("Video 태그를 지원하지 않는 브라우저입니다.", "")


def remove_urls(text: str) -> str:
    url_pattern = r"https?://\S+|www\.\S+"
    return re.sub(url_pattern, "", text)


def remove_any_unused_text(text: str) -> str:
    text = remove_video_tag_message(text)
    text = remove_urls(text)
    return text


def visit_article_link(
    context: dict, client_context: LinkVisitorClientContext, href: str
) -> tuple[bool, str]:
    flag_continue = False
    text = None

    if href:
        if context["visited_item_recorder"].is_visited(href):
            logger.info(f"Already visited: ({href}). Skip it.")
            flag_continue = True
        else:
            context["visited_item_recorder"].add_item(href)
            url_for_href = f"https://www.fmkorea.com{href}"
            const_time_to_sleep_after_visit_using_selenium = 2
            const_time_to_sleep_between_req_for_href_in_sec = 1
            const_timeout_for_requests_get_in_sec = 16

            try:
                visit_with_selenium(client_context, url_for_href)
                context["exit_event"].wait(
                    const_time_to_sleep_after_visit_using_selenium
                )
                req_for_href = requests.get(
                    url_for_href, timeout=const_timeout_for_requests_get_in_sec
                )
                context["exit_event"].wait(
                    const_time_to_sleep_between_req_for_href_in_sec
                )
                soup_for_href = BeautifulSoup(
                    req_for_href.content, "html.parser", from_encoding="cp949"
                )
                if div_tags := soup_for_href.find_all("div", "xe_content"):
                    if div_tags[0] and div_tags[0].text:
                        text = div_tags[0].text.strip()
                        text = remove_any_unused_text(text)
            except Exception:
                context["exit_event"].wait(
                    const_time_to_sleep_between_req_for_href_in_sec
                )

    return (flag_continue, text)


def get_message_to_send(context: dict) -> str:
    const_time_to_sleep_after_visit_using_selenium = 2
    const_timeout_for_requests_get_in_sec = 16

    to_return = ""
    page_number = 1
    url = f"https://www.fmkorea.com/index.php?mid=football_world&page={page_number}"
    client_context = create_client_context_with_selenium()
    visit_with_selenium(client_context, url)
    context["exit_event"].wait(const_time_to_sleep_after_visit_using_selenium)
    req = requests.get(url, timeout=const_timeout_for_requests_get_in_sec)
    soup = BeautifulSoup(req.content, "html.parser", from_encoding="cp949")
    td_tags = soup.find_all("td", "title hotdeal_var8")

    logger.info(f"Number of tags: ({len(td_tags)})")

    const_max_td_tags = 20
    limit_number = max(const_max_td_tags, len(td_tags))
    for i in range(limit_number - 1, -1, -1):
        td_tag = td_tags[i]

        # Let's look for a |category|.
        category = ""
        tr_tag_for_article_item = td_tag.parent
        td_tag_for_category = tr_tag_for_article_item.find("td", "cate")
        first_a_tag_for_category = td_tag_for_category.find("a")
        if first_a_tag_for_category is not None:
            category = first_a_tag_for_category.text.strip()

        # Let's look for a |title| and |text|.
        title = ""
        text = ""
        if td_tag is not None:
            a_tags = td_tag.find_all("a")
            first_a_tag = a_tags[0]
            if first_a_tag is not None:
                title = first_a_tag.text.strip()
                # print_message(str(title))
                href = first_a_tag["href"]
                (continue_flag, text) = visit_article_link(
                    context, client_context, href
                )
                if continue_flag:
                    continue

        # Let's pseudo-escape |title| and |text| to send them using an HTTP GET call.
        # Escaping is not perfect now.
        # TODO(pastry-personal5): Fix escaping. Also, fix the style of a telegram message.
        title = escape_text(title)
        if text:
            text = escape_text(text)
            logger.info(f"- [{category}]{title} ({text})")
            to_return = f"{to_return}- \\[{category}]{title} ({text})\n"
        else:
            logger.info(f"- [{category}]{title}")
            to_return = f"{to_return}- \\[{category}]{title}\n"

    client_context.clean_up()
    return to_return


def print_message(message: str):
    if message is not None:
        sys.stdout.buffer.write(message.encode("utf-8"))
        sys.stdout.buffer.write(("\n").encode("utf-8"))
        sys.stdout.buffer.flush()


def run_loop_with_context(context: dict):
    const_time_to_sleep_between_req = 60
    max_count = 120
    for _ in range(max_count):
        logger.info("Trying to fetch content...")
        message_to_send = get_message_to_send(context)
        if len(message_to_send) > 0:
            send_telegram_message(context, message_to_send)
        logger.info(datetime.datetime.now())
        logger.info("Now sleep...")
        for _ in range(const_time_to_sleep_between_req):
            context["exit_event"].wait(1)
        logger.info(datetime.datetime.now())


def quit_application(signo, _frame, context: dict):
    # `_frame` and `context` are not used. It's intentional.
    logger.info(f"Interrupted by signal number {signo}, shutting down...")
    logger.info(_frame)
    logger.info(context)
    logger.info(context["exit_event"])
    sys.exit(-1)


def init_context_with_global_config(context: dict, global_config: dict) -> None:
    context["bot_token"] = global_config["bot_token"]
    context["bot_chat_id"] = global_config["bot_chat_id"]

    context["visited_item_recorder"] = VisitedItemRecorder([])


def init_signal_functions(context: dict) -> None:
    """
    This function set up signal handlers.
    Also it sets `context`'s key, value.
    """
    context["exit_event"] = Event()
    signal.signal(
        signal.SIGTERM, lambda signo, frame: quit_application(signo, frame, context)
    )
    signal.signal(
        signal.SIGINT, lambda signo, frame: quit_application(signo, frame, context)
    )


def run_loop_with_global_config(global_config: dict) -> None:
    context = {}
    init_context_with_global_config(context, global_config)
    init_signal_functions(context)
    run_loop_with_context(context)


def escape_text(text: str) -> str:
    # const_regex_to_escape = r"(?<!\\)(_|\*|\[|\]|\(|\)|\~|`|>|#|\+|-|=|\||\{|\}|\.|\!)"
    const_regex_to_escape = r"(?<!\\)(_|\*|\[|\]|\(|\)|\~|`|>|#|\+|=|\||\{|\})"
    text = re.sub(const_regex_to_escape, lambda t: "\\" + t.group(), text)
    return text


def send_telegram_message(context, message: str) -> None:
    const_timeout_for_requests_get_in_sec = 16

    bot_token = context["bot_token"]
    bot_chat_id = context["bot_chat_id"]
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={bot_chat_id}&parse_mode=Markdown&text={message}"
    requests.get(url, timeout=const_timeout_for_requests_get_in_sec)


def validate_global_config(global_config: dict):
    if "bot_token" not in global_config:
        return False
    if "bot_chat_id" not in global_config:
        return False
    const_default_bot_token_for_template = "12345:YOUR FULL BOT TOKEN"
    return global_config["bot_token"] != const_default_bot_token_for_template


def load_config_and_run_loop():
    try:
        with open("global_config.yaml", "rb") as config_file_stream:
            global_config = yaml.safe_load(config_file_stream)
    except IOError as e:
        logger.error(f"An IOError has been occurred: {e}")
        sys.exit(-1)
    if not validate_global_config(global_config):
        logger.error("Error in the global configuration")
        sys.exit(-1)
    run_loop_with_global_config(global_config)


def main():
    load_config_and_run_loop()


if __name__ == "__main__":
    main()
