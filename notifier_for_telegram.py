from global_config_controller import GlobalConfigIR


import requests


class NotifierForTelegram:
    def __init__(self):
        self.bot_token = None
        self.bot_chat_id = None

    def prepare(self, global_config: GlobalConfigIR) -> None:
        self.bot_token = global_config.config["notifier"]["telegram"]["config"]["bot_token"]
        self.bot_chat_id = global_config.config["notifier"]["telegram"]["config"]["bot_chat_id"]

    def notify(self, message: str) -> None:
        const_timeout_for_requests_get_in_sec = 16

        bot_token = self.bot_token
        bot_chat_id = self.bot_chat_id
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={bot_chat_id}&parse_mode=Markdown&text={message}"
        requests.get(url, timeout=const_timeout_for_requests_get_in_sec)
