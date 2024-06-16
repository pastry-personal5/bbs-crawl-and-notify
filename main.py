'''
This module get contents from the web site,
then send that content to a telegram chat room with a bot.
'''


from threading import Event
import signal
import sys


from bs4 import BeautifulSoup
from loguru import logger
import requests
from selenium import webdriver
import yaml


# global_context = None


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
    logger.info(f'title ({title})')


def create_client_context_with_selenium() -> LinkVisitorClientContext:
    driver = webdriver.Chrome()
    driver.implicitly_wait(0.5)

    client_context = LinkVisitorClientContext()
    client_context.driver = driver
    return client_context


def visit_with_selenium(client_context, url) -> None:
    visit_page(client_context.driver, url)


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

    max_count = 20

    count = 0
    for td_tag in td_tags:
        count += 1
        if count > max_count:
            break
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
                    url_for_href = 'https://www.fmkorea.com%s' % href
                    try:
                        visit_with_selenium(client_context, url_for_href)
                        context['exit_event'].wait(const_time_to_sleep_after_visit_using_selenium)
                        req_for_href = requests.get(url_for_href)
                    except:
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
        if text:
            to_return = to_return + '- ' + title + '/' + text + '\n'
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
        logger.info('Now sleep...')
        for _ in range(const_time_to_sleep_between_req):
            context['exit_event'].wait(1)
        count += 1


def quit_application(signo, _frame):
    logger.info(f'Interrupted by {signo}, shutting down...')
    # global_context['exit_event'].set()
    sys.exit(-1)


def build_context_from_global_config(context: dict, global_config: dict) -> None:
    context['bot_token'] = global_config['bot_token']
    context['bot_chat_id'] = global_config['bot_chat_id']


def init_signal_functions(context) -> None:
    '''
    This function set up signal handlers.
    Also it sets `context`'s key, value.
    '''
    context['exit_event'] = Event()
    signal.signal(signal.SIGTERM, quit_application)
    signal.signal(signal.SIGINT, quit_application)


def run_loop_with_global_config(global_config):
    context = {}
    build_context_from_global_config(context, global_config)
    init_signal_functions(context)
    # global_context = context.copy()  # Look for `quit_application.`
    run_loop_with_context(context)


def send_telegram_message(context, message: str) -> None:
    bot_token = context['bot_token']
    bot_chat_id = context['bot_chat_id']
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
        print(global_config)
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
