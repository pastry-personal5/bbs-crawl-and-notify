import unittest
from bbs_crawl_and_notify.global_config_controller import (
    TelegramNotifierConfigValidator,
    GlobalConfigIR,
)


class TestTelegramNotifierConfigValidator(unittest.TestCase):
    def setUp(self):
        self.validator = TelegramNotifierConfigValidator()

    def test_valid_config(self):
        global_config = GlobalConfigIR()
        global_config.config = {
            "notifier": {
                "telegram": {
                    "config": {
                        "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
                        "bot_chat_id": "123456789",
                    }
                }
            }
        }
        self.assertTrue(self.validator.validate(global_config))

    def test_missing_bot_token(self):
        global_config = GlobalConfigIR()
        global_config.config = {
            "notifier": {
                "telegram": {
                    "config": {
                        "bot_chat_id": "123456789",
                    }
                }
            }
        }
        self.assertFalse(self.validator.validate(global_config))

    def test_missing_bot_chat_id(self):
        global_config = GlobalConfigIR()
        global_config.config = {
            "notifier": {
                "telegram": {
                    "config": {
                        "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
                    }
                }
            }
        }
        self.assertFalse(self.validator.validate(global_config))

    def test_default_bot_token(self):
        global_config = GlobalConfigIR()
        global_config.config = {
            "notifier": {
                "telegram": {
                    "config": {
                        "bot_token": "12345:YOUR FULL BOT TOKEN",
                        "bot_chat_id": "123456789",
                    }
                }
            }
        }
        self.assertFalse(self.validator.validate(global_config))

    def test_missing_telegram_config(self):
        global_config = GlobalConfigIR()
        global_config.config = {
            "notifier": {
                "telegram": {}
            }
        }
        self.assertFalse(self.validator.validate(global_config))

    def test_missing_notifier_config(self):
        global_config = GlobalConfigIR()
        global_config.config = {}
        self.assertFalse(self.validator.validate(global_config))


if __name__ == "__main__":
    unittest.main()
