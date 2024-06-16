'''
This module get contents from the web site,
then send that content to a telegram chat room with a bot.
'''

import datetime
import signal
import sys
from threading import Event


from bs4 import BeautifulSoup
from loguru import logger
import re
import requests
from selenium import webdriver
import yaml


class VisitedItemRecorder:
    visited_items = set()
    tags = None

    # `tags` is optional.
    # `tags` is shallow-copied using `copy()` call.
    def __init__(self, tags: list):
        self.tags = tags.copy()

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


def visit_page(driver, url):
    driver.get(url)
    title = driver.title
    if title:
        logger.info(f'title ({title})')


def create_client_context_with_selenium() -> LinkVisitorClientContext:
    driver = webdriver.Chrome()
    driver.implicitly_wait(0.5)

    client_context = LinkVisitorClientContext()
    client_context.driver = driver
    return client_context


def visit_with_selenium(client_context, url) -> None:
    visit_page(client_context.driver, url)



def remove_any_unused_text(text: str) -> str:
    text = text.replace('Video 태그를 지원하지 않는 브라우저입니다.', '')
    return text


def get_message_to_send(context) -> str:
    const_time_to_sleep_between_req_for_href_in_sec = 1
    const_time_to_sleep_after_visit_using_selenium = 2
    to_return = ''
    page_number = 1
    url = f'https://www.fmkorea.com/index.php?mid=football_world&page={page_number}'
    client_context = create_client_context_with_selenium()
    visit_with_selenium(client_context, url)
    context['exit_event'].wait(const_time_to_sleep_after_visit_using_selenium)
    req = requests.get(url)
    soup = BeautifulSoup(req.content, "html.parser", from_encoding='cp949')
    td_tags = soup.find_all('td', 'title hotdeal_var8')

    logger.info(f'Number of tags: ({len(td_tags)})')

    const_max_td_tags = 20
    limit_number = max(const_max_td_tags, len(td_tags))
    for i in range(limit_number - 1, -1, -1):
        td_tag = td_tags[i]
        title = ''
        text = ''
        if td_tag is not None:
            a_tags = td_tag.find_all('a')
            first_a_tag = a_tags[0]
            if first_a_tag is not None:
                title = first_a_tag.text.strip()
                # print_message(str(title))
                href = first_a_tag['href']
                if href:
                    if context['visited_item_recorder'].is_visited(href):
                        logger.info(f'Already visited: ({href}). Skip it.')
                        continue
                    else:
                        context['visited_item_recorder'].add_item(href)
                    url_for_href = 'https://www.fmkorea.com%s' % href
                    try:
                        visit_with_selenium(client_context, url_for_href)
                        context['exit_event'].wait(const_time_to_sleep_after_visit_using_selenium)
                        req_for_href = requests.get(url_for_href)
                    except Exception:
                        context['exit_event'].wait(const_time_to_sleep_between_req_for_href_in_sec)
                        continue
                    context['exit_event'].wait(const_time_to_sleep_between_req_for_href_in_sec)
                    soup_for_href = BeautifulSoup(req_for_href.content, "html.parser", from_encoding='cp949')
                    div_tags = soup_for_href.find_all('div', 'xe_content')
                    # print_message(str(div_tags))
                    if div_tags:
                        if div_tags[0]:
                            if div_tags[0].text:
                                text = div_tags[0].text.strip()
                                text = remove_any_unused_text(text)
        if text:
            to_return = to_return + '- ' + title + ' / ' + text + '\n'
        else:
            to_return = to_return + '- ' + title + '\n'

    client_context.clean_up()
    return to_return





def print_message(message: str):
    if message is not None:
        sys.stdout.buffer.write(message.encode('utf-8'))
        sys.stdout.buffer.write(('\n').encode('utf-8'))
        sys.stdout.buffer.flush()


def run_loop_with_context(context):
    const_time_to_sleep_between_req = 60
    max_count = 120
    count = 0
    while count < max_count:
        logger.info('Trying to fetch content...')
        message_to_send = get_message_to_send(context)
        if len(message_to_send) > 0:
            send_telegram_message(context, message_to_send)
        logger.info(datetime.datetime.now())
        logger.info('Now sleep...')
        for _ in range(const_time_to_sleep_between_req):
            context['exit_event'].wait(1)
        logger.info(datetime.datetime.now())
        count += 1


def quit_application(signo, _frame, context):
    logger.info(f'Interrupted by {signo}, shutting down...')
    # context['exit_event'].set()
    sys.exit(-1)


def init_context_with_global_config(context: dict, global_config: dict) -> None:
    context['bot_token'] = global_config['bot_token']
    context['bot_chat_id'] = global_config['bot_chat_id']

    context['visited_item_recorder'] = VisitedItemRecorder([])


def init_signal_functions(context) -> None:
    '''
    This function set up signal handlers.
    Also it sets `context`'s key, value.
    '''
    context['exit_event'] = Event()
    signal.signal(signal.SIGTERM, lambda signo, frame: quit_application(signo, frame, context))
    signal.signal(signal.SIGINT, lambda signo, frame: quit_application(signo, frame, context))


def run_loop_with_global_config(global_config):
    context = {}
    init_context_with_global_config(context, global_config)
    init_signal_functions(context)
    # global_context = context.copy()  # Look for `quit_application.`
    run_loop_with_context(context)


def escape_text(text):
    # const_regex_to_escape = r"(?<!\\)(_|\*|\[|\]|\(|\)|\~|`|>|#|\+|-|=|\||\{|\}|\.|\!)"
    const_regex_to_escape = r"(?<!\\)(_|\*|\[|\]|\(|\)|\~|`|>|#|\+|=|\||\{|\})"
    text = re.sub(const_regex_to_escape, lambda t: "\\"+t.group(), text)
    return text


def send_telegram_message(context, message: str) -> None:
    bot_token = context['bot_token']
    bot_chat_id = context['bot_chat_id']
    message = escape_text(message)
    url = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chat_id + '&parse_mode=Markdown&text=' + message
    requests.get(url)


def validate_global_config(global_config):
    if not 'bot_token' in global_config:
        return False
    if not 'bot_chat_id' in global_config:
        return False
    default_bot_token_for_template = '12345:YOUR FULL BOT TOKEN'
    if global_config['bot_token'] == default_bot_token_for_template:
        return False
    return True


def load_config_and_run_loop():
    try:
        config_file_stream = open('global_config.yaml', 'rb')
        global_config = yaml.safe_load(config_file_stream)
        config_file_stream.close()
    except IOError as e:
        logger.error(f'An IOError has been occurred: {e}')
        sys.exit(-1)
    if not validate_global_config(global_config):
        logger.error('Error in the global configuration')
        sys.exit(-1)
    run_loop_with_global_config(global_config)


def main():
    load_config_and_run_loop()


if __name__ == '__main__':
    main()
