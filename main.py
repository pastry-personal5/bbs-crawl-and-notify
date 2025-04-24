"""
This module get contents from the web site,
then send that content to a telegram chat room with a bot.

To use "dcinside," it's mixing threads and asyncio.
"""

from abc import ABC, abstractmethod
import asyncio
import datetime
import signal
import sys
from threading import Event, Thread

from loguru import logger

from notifier_for_telegram import NotifierForTelegram
from crawler_for_fm_korea import CrawlerForFMKorea
from crawler_for_dc_inside import CrawlerForDCInside
from visited_item_recorder import VisitedItemRecorder
from global_config_controller import GlobalConfigController, GlobalConfigIR


def quit_application(signo, _frame, global_control_context: dict):
    # `_frame` and `context` are not used. It's intentional.
    logger.info(f"Interrupted by signal number {signo}, shutting down...")
    global_control_context["exit_event"].set()
    logger.info(_frame)
    logger.info(global_control_context)
    logger.info(global_control_context["exit_event"])
    sys.exit(-1)


def init_signal_functions(global_control_context: dict) -> None:
    """
    This function set up signal handlers.
    Also it sets `global_control_context`'s key, value.
    """
    global_control_context["exit_event"] = Event()
    signal.signal(
        signal.SIGTERM, lambda signo, frame: quit_application(signo, frame, global_control_context)
    )
    signal.signal(
        signal.SIGINT, lambda signo, frame: quit_application(signo, frame, global_control_context)
    )





class ChildControllerBase(ABC):
    def __init__(self):
        self.crawler = None
        self.visited_item_recorder = None
        self.notifier = None

    @abstractmethod
    def prepare(self, global_config: GlobalConfigIR) -> None:
        pass

    @abstractmethod
    def start(self, global_control_context: dict) -> None:
        pass


class ChildControllerForBlockingIO(ChildControllerBase):

    def __init__(self):
        super().__init__()

    def prepare(self, global_config: GlobalConfigIR) -> None:
        self.crawler.prepare(global_config)
        self.notifier.prepare(global_config)

    def start(self, global_control_context: dict) -> None:
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

        t = Thread(target = run_loop_with_context, args = (global_control_context,))
        t.start()
        t.join()


class ChildControllerForAsyncIO(ChildControllerBase):

    def __init__(self):
        super().__init__()

    def prepare(self, global_config: GlobalConfigIR) -> None:
        self.crawler.prepare(global_config)
        self.notifier.prepare(global_config)

    def start(self, global_control_context: dict) -> None:

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

        t = Thread(target = run_loop_with_context, args = (global_control_context,))
        t.start()
        t.join()


class MainController:

    def __init__(self):
        self.global_config_controller = GlobalConfigController()
        self.global_config = None
        self.controllers = None

        self.loop = None
        self.loop_thread = None

    def run(self) -> None:
        logger.info("Starting MainController...")
        global_config = self.global_config
        self.controllers = self._build_controllers(global_config)
        global_control_context = {}
        init_signal_functions(global_control_context)
        self._init_asyncio_loop(global_control_context)
        self.run_loop_with_global_control_context(global_control_context)

        # Stop.
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.loop_thread.join()

    def run_loop_with_global_control_context(self, global_control_context: dict) -> None:
        for controller in self.controllers:
            controller.prepare(self.global_config)
            controller.start(global_control_context)

    def read_global_config_and_validate(self) -> None:
        """
        This function reads the global config file and validates it.
        """
        global_config_controller = GlobalConfigController()
        self.global_config = global_config_controller.read_global_config()
        if not global_config_controller.validate(self.global_config):
            logger.error("Global config validation failed.")
            sys.exit(-1)

    def _init_asyncio_loop(self, global_control_context: dict) -> None:
        """
        This function initializes the asyncio loop.
        It sets `global_control_context`'s key, value.
        Later, it is used to create a worker thread.
        e.g. Thread(target=worker, args=(global_control_context["asyncio_loop"],), daemon=True).start()
        """
        self.loop = asyncio.new_event_loop()
        self.loop_thread = Thread(target=self.loop.run_forever, daemon=True)
        self.loop_thread.start()

        global_control_context["asyncio_loop"] = self.loop

    def _build_controllers(self, global_config: GlobalConfigIR) -> list:
        """
        This function builds controllers based on the global config.
        """
        controllers = []

        # For now, we have two controllers.
        # In the future, we can add more controllers based on the global config as pipelines.
        if True:
            child_controller_for_fm_korea = ChildControllerForBlockingIO()
            crawler_for_fm_korea = CrawlerForFMKorea()
            child_controller_for_fm_korea.crawler = crawler_for_fm_korea
            child_controller_for_fm_korea.crawler.visited_item_recorder = VisitedItemRecorder([])
            notifier_for_telegram = NotifierForTelegram()
            notifier_for_telegram.prepare(global_config)
            child_controller_for_fm_korea.notifier = notifier_for_telegram
            controllers.append(child_controller_for_fm_korea)

        if True:
            child_controller_for_dc_inside = ChildControllerForAsyncIO()
            crawler_for_dc_inside = CrawlerForDCInside()
            child_controller_for_dc_inside.crawler = crawler_for_dc_inside
            child_controller_for_dc_inside.crawler.visited_item_recorder = VisitedItemRecorder([])
            notifier_for_telegram = NotifierForTelegram()
            notifier_for_telegram.prepare(global_config)
            child_controller_for_dc_inside.notifier = notifier_for_telegram
            controllers.append(child_controller_for_dc_inside)

        return controllers


def load_config_and_run_loop():
    main_controller = MainController()
    main_controller.read_global_config_and_validate()
    main_controller.run()


def main():
    load_config_and_run_loop()


if __name__ == "__main__":
    main()
