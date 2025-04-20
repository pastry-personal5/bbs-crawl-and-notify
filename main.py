"""
This module get contents from the web site,
then send that content to a telegram chat room with a bot.
"""

import datetime
import re
import signal
import sys
from threading import Event

from loguru import logger
import requests

from link_visitor_client_context import LinkVisitorClientContext
from crawler_for_fm_korea import CrawlerForFMKorea
from visited_item_recorder import VisitedItemRecorder
from global_config_controller import GlobalConfigController


def run_loop_with_context(context: dict):
    cralwer_for_fm_korea = CrawlerForFMKorea()
    const_time_to_sleep_between_req = 60
    max_count = 120
    for _ in range(max_count):
        logger.info("Trying to fetch content...")
        message_to_send = cralwer_for_fm_korea.get_message_to_send(context)
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
    context["bot_token"] = global_config.config["notifier"]["telegram"]["config"]["bot_token"]
    context["bot_chat_id"] = global_config.config["notifier"]["telegram"]["config"]["bot_chat_id"]

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


def send_telegram_message(context, message: str) -> None:
    const_timeout_for_requests_get_in_sec = 16

    bot_token = context["bot_token"]
    bot_chat_id = context["bot_chat_id"]
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={bot_chat_id}&parse_mode=Markdown&text={message}"
    requests.get(url, timeout=const_timeout_for_requests_get_in_sec)


def load_config_and_run_loop():
    global_config_controller = GlobalConfigController()
    global_config = global_config_controller.read_global_config()
    if not global_config_controller.validate(global_config):
        logger.error("Global config validation failed.")
        sys.exit(-1)
    run_loop_with_global_config(global_config)


def main():
    load_config_and_run_loop()


if __name__ == "__main__":
    main()
