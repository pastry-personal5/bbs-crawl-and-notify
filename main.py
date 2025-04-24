"""
This module get contents from the web site,
then send that content to a telegram chat room with a bot.
"""

import datetime
import signal
import sys
from threading import Event, Thread

from loguru import logger

from notifier_for_telegram import NotifierForTelegram
from crawler_for_fm_korea import CrawlerForFMKorea
from visited_item_recorder import VisitedItemRecorder
from global_config_controller import GlobalConfigController, GlobalConfigIR


def quit_application(signo, _frame, global_signal_context: dict):
    # `_frame` and `context` are not used. It's intentional.
    logger.info(f"Interrupted by signal number {signo}, shutting down...")
    global_signal_context["exit_event"].set()
    logger.info(_frame)
    logger.info(global_signal_context)
    logger.info(global_signal_context["exit_event"])
    sys.exit(-1)


def init_signal_functions(global_signal_context: dict) -> None:
    """
    This function set up signal handlers.
    Also it sets `global_signal_context`'s key, value.
    """
    global_signal_context["exit_event"] = Event()
    signal.signal(
        signal.SIGTERM, lambda signo, frame: quit_application(signo, frame, global_signal_context)
    )
    signal.signal(
        signal.SIGINT, lambda signo, frame: quit_application(signo, frame, global_signal_context)
    )


class ChildController:
    def __init__(self):
        self.crawler = None
        self.visited_item_recorder = None
        self.notifier = None

    def prepare(self, global_config: GlobalConfigIR) -> None:
        pass

    def start(self, global_signal_context: dict):
        def run_loop_with_context(context: dict):
            const_time_to_sleep_between_req = 60
            max_count = 120
            for _ in range(max_count):
                logger.info("Trying to fetch content...")
                message_to_send = self.crawler.get_message_to_send(context)
                if len(message_to_send) > 0:
                    self.notifier.notify(message_to_send)
                logger.info(datetime.datetime.now())
                logger.info("Now sleep...")
                for _ in range(const_time_to_sleep_between_req):
                    if context["exit_event"].is_set():
                        logger.info("Exit event is set. Exiting loop.")
                        return
                    context["exit_event"].wait(1)
                logger.info(datetime.datetime.now())

        t = Thread(target = run_loop_with_context, args = (global_signal_context,))
        t.start()
        t.join()


class MainController:

    def __init__(self):
        self.global_config_controller = GlobalConfigController()
        self.global_config = None
        self.controllers = None

    def start(self) -> None:
        logger.info("MainController started.")
        global_config = self.global_config
        self.controllers = self._build_controllers(global_config)
        global_signal_context = {}
        init_signal_functions(global_signal_context)
        self.run_loop_with_context(global_signal_context)

    def run_loop_with_context(self, global_signal_context: dict) -> None:
        for controller in self.controllers:
            controller.prepare(self.global_config)
            controller.start(global_signal_context)

    def read_global_config_and_validate(self) -> None:
        """
        This function reads the global config file and validates it.
        """
        global_config_controller = GlobalConfigController()
        self.global_config = global_config_controller.read_global_config()
        if not global_config_controller.validate(self.global_config):
            logger.error("Global config validation failed.")
            sys.exit(-1)

    def _build_controllers(self, global_config: GlobalConfigIR) -> list:
        """
        This function builds controllers based on the global config.
        """
        controllers = []

        # For now, we only have one controller.
        # In the future, we can add more controllers based on the global config as pipelines.
        child_controller = ChildController()
        crawler_for_fm_korea = CrawlerForFMKorea()
        child_controller.crawler = crawler_for_fm_korea
        child_controller.crawler.visited_item_recorder = VisitedItemRecorder([])
        notifier_for_telegram = NotifierForTelegram()
        notifier_for_telegram.prepare(global_config)
        child_controller.notifier = notifier_for_telegram

        controllers.append(child_controller)

        return controllers


def load_config_and_run_loop():
    main_controller = MainController()
    main_controller.read_global_config_and_validate()
    main_controller.start()


def main():
    load_config_and_run_loop()


if __name__ == "__main__":
    main()
