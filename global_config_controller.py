import sys

from loguru import logger
import yaml


class GlobalConfigIR:

    def __init__(self):
        self.config = {}

class GlobalConfigController:

    def __init__(self):
        self.config_validators = [
            TelegramNotifierConfigValidator(),
        ]

    def validate(self, global_config: GlobalConfigIR) -> bool:
        for validator in self.config_validators:
            if not validator.validate(global_config):
                logger.error(f"Validation failed for {validator.__class__.__name__}. Please check the configuration file and ensure all required fields are correctly set.")
                return False
        return True

    def read_global_config(self) -> GlobalConfigIR:
        # An object of GlobalConfigIR is created and returned.
        # The object is initialized with the content of the global_config.yaml file.
        try:
            with open("global_config.yaml", "rb") as config_file_stream:
                global_config_dict = yaml.safe_load(config_file_stream)
                global_config = GlobalConfigIR()
                global_config.config = global_config_dict
                return global_config
        except FileNotFoundError:
            logger.error("The global_config.yaml file was not found. Please ensure the file exists in the project root directory.")
            sys.exit(-1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing the global_config.yaml file: {e}. Please ensure the file is properly formatted YAML.")
            sys.exit(-1)
        except IOError as e:
            logger.error(f"An IOError occurred while reading the global_config.yaml file: {e}. Please check file permissions and try again.")
            sys.exit(-1)


class ConfigValidatorBase:

    def __init__(self):
        pass

    def validate(self, global_config: GlobalConfigIR) -> bool:
        raise NotImplementedError("Subclasses should implement this method.")


class TelegramNotifierConfigValidator(ConfigValidatorBase):

    def __init__(self):
        super().__init__()
        self.config = {}

    def validate(self, global_config: GlobalConfigIR) -> bool:
        try:
            local_config = global_config.config['notifier']['telegram']['config']
        except KeyError:
            logger.error("Telegram notifier configuration not found.")
            return False
        if "bot_token" not in local_config:
            logger.error("bot_token not found.")
            return False
        if "bot_chat_id" not in local_config:
            logger.error("bot_chat_id not found.")
            return False
        const_default_bot_token_for_template = "12345:YOUR FULL BOT TOKEN"
        if local_config["bot_token"] == const_default_bot_token_for_template:
            logger.error(
                f"Please change the default bot_token: {const_default_bot_token_for_template}"
            )
            return False
        return True
