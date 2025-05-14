import asyncio
import queue
from threading import Thread

import dc_api
from loguru import logger

from bbs_crawl_and_notify.global_config_controller import GlobalConfigIR


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


def run_coroutine_to_fetch(q: queue.Queue, board_id: str, max_of_id: int, global_control_context: dict) -> None:
    """
    Runs the coroutine to fetch data in a separate thread.
    Checks for the exit_event to terminate gracefully.
    """
    logger.info(f"Starting coroutine... with max_of_id({max_of_id})")
    try:
        future = asyncio.run_coroutine_threadsafe(
            fetch(board_id, max_of_id, global_control_context),
            global_control_context["asyncio_loop"]
        )
        while not global_control_context["exit_event"].is_set():
            try:
                result_from_call = future.result(timeout=1)  # Check periodically
                logger.info(f"Thread received: {result_from_call}")
                q.put(result_from_call)
                return
            except asyncio.TimeoutError:
                continue  # Keep waiting if no result yet
    except Exception as e:
        logger.error("Exception in coroutine:", e)
        q.put(None)  # Signal failure
    finally:
        logger.info("Exiting coroutine thread.")


async def fetch(board_id: str, max_of_id: int, global_control_context: dict) -> dict:
    """
    Fetches data from the DCInside API asynchronously.
    """
    const_time_in_sec = 8
    const_num_first_fetch = 16
    const_num_normal_fetch = 16


    api = dc_api.API()
    logger.info("Trying to fetch board messages...")
    logger.info(f"Board ID: {board_id}")
    logger.info(f"Max of ID: {max_of_id}")

    try:
        index_generator = None
        if max_of_id != 0:
            index_generator = api.board(
                board_id,
                start_page=1,
                num=const_num_normal_fetch,
                document_id_lower_limit=max_of_id,
            )
        else:
            index_generator = api.board(
                board_id, start_page=1, num=const_num_first_fetch
            )
        logger.info("Done!")
        message = ""
        cnt = 0
        timed_index_generator = AsyncTimedIterable(
            iterable=index_generator, timeout=const_time_in_sec
        )
        async for index in timed_index_generator:
            if index:
                if int(index.id) > max_of_id:
                    max_of_id = int(index.id)
                message += index.title + "\n"
                cnt += 1
        logger.info(message)

        await api.close()

        result_to_return = {}
        result_to_return["board_id"] = board_id
        result_to_return["message"] = board_id + '\n' + message
        result_to_return["max_of_id"] = max_of_id

        logger.info(result_to_return)
        return result_to_return

    except asyncio.CancelledError:
        logger.info("Fetch coroutine was cancelled.")
        await api.close()
        return {"message": "", "max_of_id": max_of_id, "board_id": board_id}
    except Exception as e:
        logger.error(f"Exception in fetch coroutine: {e}")
        await api.close()
        return {"message": "", "max_of_id": max_of_id, "board_id": board_id}


class CrawlerForDCInside:

    def __init__(self):
        self.visited_item_recorder = None
        self.boards = None
        self.max_of_id_dict = {}
        self.child_threads = []
        self.controller_message_queue = None  # This is a shared object. The lifecycle of this queue is managed by the parent.

    def prepare(self, global_config: GlobalConfigIR) -> None:
        self.boards = global_config.config["crawler"]["dc_inside"]["config"]["boards"]
        logger.info(self.boards)

    def set_controller_message_queue(self, controller_message_queue: queue.Queue) -> None:
        self.controller_message_queue = controller_message_queue

    def start(self, global_control_context: dict) -> None:
        """
        Starts the crawler for DCInside.
        This method creates threads to fetch data from the DCInside API.
        It uses a queue to communicate results back to the main thread.
        """

        q = queue.Queue()  # Thread-safe queue for results

        for board in self.boards:
            board_id = board["id"]
            if board_id == "":
                logger.warning("Board ID is empty. Continue...")
                continue
            self.max_of_id_dict[board_id] = 0

            t = Thread(target=run_coroutine_to_fetch, args=(q, board_id, self.max_of_id_dict[board_id], global_control_context,), daemon=True)
            self.child_threads.append(t)
            logger.info(f"Starting DCInside crawler thread for Board ID {board_id}...")
            t.start()


        # Wait for result from thread or exit event
        while not global_control_context["exit_event"].is_set():
            try:
                result = q.get(timeout=1)  # Check periodically
                if result is not None:
                    logger.info(f"Main received: {result}")
                    board_id = result["board_id"]
                    max_of_id = result["max_of_id"]
                    if board_id not in self.max_of_id_dict:
                        logger.warning(f"Board ID {board_id} not found in max_of_id_dict.")
                        continue
                    self.max_of_id_dict[board_id] = max_of_id
                    logger.info(f"Updated max_of_id_dict: {self.max_of_id_dict}")
                    self.controller_message_queue.put(result)
            except queue.Empty:
                continue  # Keep waiting if no result yet

        logger.info("Exit event set. Exiting...")
        for t in self.child_threads:
            t.join(timeout=1)
