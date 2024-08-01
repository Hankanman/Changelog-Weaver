""" This module provides a custom logger for the application. """

import logging

module_aliases = {
    "__main__": "Main",
    "changelog_weaver.changelog": "Changelog",
    "changelog_weaver.work": "Work",
    "changelog_weaver.configuration.config": "Config",
    "changelog_weaver.configuration.base_config": "Config",
    "changelog_weaver.configuration.model": "AI Model",
    "changelog_weaver.configuration.output": "Output",
    "changelog_weaver.configuration.prompts": "Prompts",
    "changelog_weaver.platforms.platform_client": "Platform Client",
    "changelog_weaver.platforms.devops_client": "Azure DevOps",
    "changelog_weaver.platforms.github_client": "GitHub",
    "changelog_weaver.platforms.devops_api": "Azure DevOps",
    "changelog_weaver.platforms.github_api": "GitHub",
    "changelog_weaver.utilities.utils": "Utilities",
    "changelog_weaver.utilities.heirarchy": "Utilities",
    "changelog_weaver.typings": "Typings",
}

# Define the target length for the module alias
TARGET_ALIAS_LENGTH = 15


class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.levelname == "INFO":
            record.levelname = ""
        else:
            record.levelname = f"[{record.levelname}] "
        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    # Get alias or the last part of the module name
    alias = module_aliases.get(name, name.split(".")[-1])

    # Pad or truncate the alias to ensure consistent length
    if len(alias) > TARGET_ALIAS_LENGTH:
        alias = alias[:TARGET_ALIAS_LENGTH]
    else:
        alias = alias.ljust(TARGET_ALIAS_LENGTH)

    logger = logging.getLogger(alias)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = CustomFormatter(
            "%(asctime)s | %(name)s | %(levelname)s%(message)s", datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
