# -*- coding: utf-8 -*-
# This is a Python script for crawling FM Korea website and extracting football-related articles.
# It uses BeautifulSoup for HTML parsing and requests for HTTP requests.
# It also uses loguru for logging and a custom VisitedItemRecorder to keep track of visited articles.
# You cannot use requests and BeautifulSoup only. Use of selenium is required to get the content from the web site - "fmkorea.com."

import re
import sys

import requests
from bs4 import BeautifulSoup
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
import selenium

from link_visitor_client_context import LinkVisitorClientContext


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


def print_message(message: str):
    if message is not None:
        sys.stdout.buffer.write(message.encode("utf-8"))
        sys.stdout.buffer.write(("\n").encode("utf-8"))
        sys.stdout.buffer.flush()


def escape_text(text: str) -> str:
    # const_regex_to_escape = r"(?<!\\)(_|\*|\[|\]|\(|\)|\~|`|>|#|\+|-|=|\||\{|\}|\.|\!)"
    const_regex_to_escape = r"(?<!\\)(_|\*|\[|\]|\(|\)|\~|`|>|#|\+|=|\||\{|\})"
    text = re.sub(const_regex_to_escape, lambda t: "\\" + t.group(), text)
    return text


class CrawlerForFMKorea:
    def __init__(self):
        pass

    def visit_article_link(
        self,
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

    def get_message_to_send(self, context: dict) -> str:
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
                    (continue_flag, text) = self.visit_article_link(
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
