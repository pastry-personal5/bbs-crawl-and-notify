import asyncio
import queue
from threading import Thread

import dc_api
from loguru import logger

from global_config_controller import GlobalConfigIR


class _AsyncTimedIterator:

    __slots__ = ("_iterator", "_timeout", "_sentinel")

    def __init__(self, iterable, timeout, sentinel):
        self._iterator = iterable.__aiter__()
        self._timeout = timeout
        self._sentinel = sentinel

    async def __anext__(self):
        try:
            return await asyncio.wait_for(self._iterator.__anext__(), self._timeout)
        except asyncio.TimeoutError:
            return self._sentinel


class AsyncTimedIterable:

    __slots__ = ("_factory",)

    def __init__(self, iterable, timeout=None, sentinel=None):
        self._factory = lambda: _AsyncTimedIterator(iterable, timeout, sentinel)

    def __aiter__(self):
        return self._factory()


def run_thread_to_fetch(q: queue.Queue, board_id: str, max_of_id: int, global_control_context: dict) -> str:
    future = asyncio.run_coroutine_threadsafe(crawl(board_id, max_of_id, global_control_context), global_control_context["asyncio_loop"])
    try:
        result = future.result()  # Wait for and get the result
        print("Thread received:", result)
    except Exception as e:
        print("Exception in coroutine:", e)

    q.put(result)


async def crawl(board_id: str, max_of_id: int, global_control_context: dict) -> None:

    CONST_TIMEOUT_IN_SEC = 8
    CONST_TIME_TO_SLEEP_IN_SEC = 8
    CONST_NUM_FIRST_FETCH = 16
    CONST_NUM_NORMAL_FETCH = 16


    api = dc_api.API()
    logger.info("Trying to fetch board messages...")

    logger.info(f"For now, only {board_id} is crawled.")
    index_generator = None
    if max_of_id != 0:
        index_generator = api.board(
            board_id,
            start_page=1,
            num=CONST_NUM_NORMAL_FETCH,
            document_id_lower_limit=max_of_id,
        )
    else:
        index_generator = api.board(
            board_id, start_page=1, num=CONST_NUM_FIRST_FETCH
        )
    logger.info("Done!")
    message = ""
    cnt = 0
    timed_index_generator = AsyncTimedIterable(
        iterable=index_generator, timeout=CONST_TIMEOUT_IN_SEC
    )
    async for index in timed_index_generator:
        if index:
            logger.info(" ... index.id " + index.id)
            if int(index.id) > max_of_id:
                max_of_id = int(index.id)
            message += index.title + "\n"
            cnt += 1
    logger.info(message)

    await api.close()
    return message


class CrawlerForDCInside:

    def __init__(self):
        self.visited_item_recorder = None
        self.board_ids = None
        self.max_of_id = 0

    def prepare(self, global_config: GlobalConfigIR) -> None:
        self.board_ids = global_config.config["crawler"]["dc_inside"]["config"]["board_ids"]
        logger.info(self.board_ids)

    def get_message_to_send(self, global_control_context: dict) -> None:
        logger.info("Starting DCInside crawler...")
        q = queue.Queue()  # Thread-safe queue for results
        board_id = self.board_ids[0]

        t = Thread(target=run_thread_to_fetch, args=(q, board_id, self.max_of_id, global_control_context,), daemon=True)
        t.start()

        # Wait for result from thread
        result = q.get()  # This blocks until something is put in the queue
        print("Main received:", result)

        t.join()

        return result
