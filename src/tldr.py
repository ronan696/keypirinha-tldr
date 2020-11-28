# Keypirinha launcher (keypirinha.com)

import datetime
import os
import re
import json
import urllib
import getopt
import locale
import zipfile
import shutil

import keypirinha as kp
import keypirinha_util as kpu


class tldr(kp.Plugin):
    """
    tldr pages client

    A Keypirinha plugin for tldr pages.
    More information: https://tldr.sh/

    Plugin URL: https://github.com/ronan696/keypirinha-tldr
    """

    config = {}
    commands = []
    cache_path = ""

    ITEMCAT_COMMAND = kp.ItemCategory.USER_BASE + 1
    DEFAULT_PLATFORM = "windows"
    DEFAULT_LANGUAGE = "en"
    DEFAULT_INFO_URL = "https://google.com/search?q={query}"
    DEFAULT_UPDATE_AFTER = 7
    COMMON_PLATFORM = "common"
    PLATFORM_LIST = ["linux", "osx", "windows", "sunos"]
    LANGUAGE_LIST = [
        "en",
        "bs",
        "da",
        "de",
        "es",
        "fr",
        "hbs",
        "hi",
        "id",
        "it",
        "ja",
        "ko",
        "ml",
        "nl",
        "no",
        "pl",
        "pt_BR",
        "pt_PT",
        "ru",
        "sv",
        "ta",
        "th",
        "tr",
        "zh",
        "zh_TW",
    ]
    TLDR_ZIP_LINK = (
        "https://raw.githubusercontent.com/tldr-pages/tldr-pages.github.io/master/assets/tldr.zip"
    )
    TRANSLATION_URL = "https://github.com/tldr-pages/tldr/blob/master/CONTRIBUTING.md#translations"
    ISSUE_URL = "https://github.com/tldr-pages/tldr/issues/new?title=page%20request:%20{}"

    def __init__(self):
        super().__init__()

    def on_start(self):
        self.commands = []
        actions = [
            self.create_action(
                name="copy", label="Copy", short_desc="Copy the command to clipboard"
            )
        ]

        self.cache_path = self.get_package_cache_path(create=True)
        self._read_config()
        self._update_cache()
        self.set_actions(self.ITEMCAT_COMMAND, actions)

    def on_catalog(self):
        catalog = []
        catalog.append(
            self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label="{}: {}".format(self.friendly_name(), "Search"),
                short_desc="Search for console commands in tldr pages",
                target="search",
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.NOARGS,
            )
        )
        catalog.append(
            self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label="{}: {}".format(self.friendly_name(), "Update Page Cache"),
                short_desc="Update local page cache from tldr.sh",
                target="update",
                args_hint=kp.ItemArgsHint.FORBIDDEN,
                hit_hint=kp.ItemHitHint.NOARGS,
            )
        )
        self.set_catalog(catalog)

    def on_suggest(self, user_input, items_chain):
        command = ""
        if not items_chain or items_chain[-1].category() != kp.ItemCategory.KEYWORD:
            return

        if not user_input:
            command = ""

        if self.should_terminate(0.3):
            return

        optlist = []
        args = []
        try:
            optlist, args = getopt.getopt(kpu.cmdline_split(user_input), "L:p:command:")
            optlist = dict(optlist)
            if "-p" in optlist.keys() and optlist["-p"].lower() not in self.PLATFORM_LIST:
                raise getopt.GetoptError(
                    "The platform entered is either incorrect or not yet supported."
                )
            if "-L" in optlist.keys() and optlist["-L"] not in self.LANGUAGE_LIST:
                raise getopt.GetoptError(
                    "The language entered is either incorrect or not yet supported."
                )
            command = "-".join(args)
        except getopt.GetoptError as options_error:
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Invalid input format",
                        short_desc=str(options_error),
                        target="error",
                    )
                ],
                kp.Match.ANY,
                kp.Sort.NONE,
            )
            return

        # If command list is empty, notify the user that there was
        # an error while saving tldr pages to local cache.
        if len(self.commands) == 0:
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="The command index is empty.",
                        short_desc="Retry updating page cache as there may have been a problem during the operation.",
                    )
                ],
                kp.Match.ANY,
                kp.Sort.NONE,
            )
            return

        if command in self.commands:
            language_list = self.config["language"] + (
                ["en"] if "en" not in self.config["language"] else []
            )
            if "-L" in optlist.keys():
                language_list = [optlist["-L"]]

            platform = optlist["-p"].lower() if "-p" in optlist.keys() else self.config["platform"]
            platform_list = [platform, "common"] + [p for p in self.PLATFORM_LIST if p != platform]

            suggestions = []
            found_in_host = True
            found_in_platform = ""
            break_from_loop = False
            for platform in platform_list:
                platform_dir_path = os.path.join(platform, command + ".md")
                for language in language_list:
                    language_dir_path = "pages" + ("" if language == "en" else ("." + language))
                    command_path = os.path.join(
                        self.cache_path, language_dir_path, platform_dir_path
                    )
                    if os.path.exists(command_path):
                        suggestions = self._parse_page(command_path)

                        # Check if the command is not found in the host platform
                        if platform not in (platform_list[0], "common"):
                            found_in_host = False
                            found_in_platform = platform
                        break_from_loop = True
                        break
                if break_from_loop:
                    break

            if len(suggestions) == 0:
                language_dir = os.path.join(
                    self.cache_path,
                    "pages" + ("" if language_list[-1] == "en" else ("." + language_list[-1])),
                )
                # If language directory exists and the user overrides the language at runtime,
                # it means that the command is not available in that particular language
                if os.path.exists(language_dir) and "-L" in optlist.keys():
                    suggestions = [
                        self.create_error_item(
                            label="No results found for '{}' command in '{}'.".format(
                                command.replace("-", " "), language_list[-1]
                            ),
                            short_desc="tldr page for '{}' command is not yet available for the specified language.".format(
                                command.replace("-", " ")
                            ),
                        ),
                        self.create_item(
                            category=kp.ItemCategory.URL,
                            label="Contribute tldr page for '{}' command in '{}'.".format(
                                command.replace("-", " "), language_list[-1]
                            ),
                            short_desc="URL: " + self.TRANSLATION_URL,
                            target=self.TRANSLATION_URL,
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        ),
                    ]

                # If the language directory does not exist, then possibly
                # the local cache for the language is not available
                else:
                    suggestions = [
                        self.create_error_item(
                            label="Locally cached tldr pages for '{}' not found.".format(
                                language_list[-1]
                            ),
                            short_desc="Try adding '{}' to the language option in the config file or updating the page cache.".format(
                                language_list[-1]
                            ),
                        )
                    ]

            # If suggestions are returned and the command is not
            # available for host platform, notify the user
            elif not found_in_host:
                suggestions = [
                    self.create_error_item(
                        label="'{}' command not found for {}.".format(
                            command.replace("-", " "), platform_list[0]
                        ),
                        short_desc="Showing results for {}.".format(found_in_platform),
                    )
                ] + suggestions
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

        # Notify user that the command is not yet available in tldr pages
        elif user_input and len(args) != 0:
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="'{}' command not found. Ensure that the command is correct.".format(
                            command.replace("-", " ")
                        ),
                        short_desc="If the command is correct, it may not yet be available in tldr pages.",
                    ),
                    self.create_item(
                        category=kp.ItemCategory.URL,
                        label="Request tldr page for '{}' command.".format(command.replace("-", " ")),
                        short_desc="URL: " + self.ISSUE_URL.format(command.replace("-", " ")),
                        target=self.ISSUE_URL.format(command),
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                    ),
                ],
                kp.Match.ANY,
                kp.Sort.NONE,
            )

    def on_execute(self, item, action):
        if item:
            is_private = action and action.name() == "browse_private"
            is_url_copy = (
                item.category() == kp.ItemCategory.URL and action and action.name() == "copy"
            )
            is_browse_action = action is None or action.name().find("browse") != -1

            if item.target() == "update":
                self._update_cache(force=True)
            elif item.category() == self.ITEMCAT_COMMAND or is_url_copy:
                kpu.set_clipboard(item.target())
            elif is_browse_action:
                kpu.web_browser_command(private_mode=is_private, url=item.target(), execute=True)

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            old_language = set(self.config["language"])
            self._read_config()
            new_language = set(self.config["language"])
            language_changed = old_language != new_language
            self._update_cache(force=language_changed)

    def _read_config(self):
        """Reads the configuration from the package configuration file"""
        settings = self.load_settings()

        # Platform Configuration
        platform = settings.get("platform", section="main", fallback=self.DEFAULT_PLATFORM).strip()
        self.config["platform"] = (
            platform if platform in self.PLATFORM_LIST else self.DEFAULT_PLATFORM
        )

        # Language Configuration
        locale_str = locale.getdefaultlocale()[0]
        language = ""
        if locale_str not in self.LANGUAGE_LIST:
            language = locale_str.split("_")[0]
            if language not in self.LANGUAGE_LIST:
                language = "en"
        else:
            language = locale_str
        self.DEFAULT_LANGUAGE = language
        language = settings.get("language", section="main", fallback=self.DEFAULT_LANGUAGE).split(
            ","
        )
        language = [l.strip() for l in language if l.strip() in self.LANGUAGE_LIST]
        self.config["language"] = language if len(language) != 0 else [self.DEFAULT_LANGUAGE]

        # URL Configuration
        info_url = settings.get("info_url", section="main", fallback=self.DEFAULT_INFO_URL).strip()
        self.config["info_url"] = info_url

        # Cache Update Interval Configuration
        cache_update_after = settings.get(
            "cache_update_after",
            section="main",
            fallback=self.DEFAULT_UPDATE_AFTER,
        )
        try:
            self.config["cache_update_after"] = int(cache_update_after)
        except ValueError:
            self.config["cache_update_after"] = self.DEFAULT_UPDATE_AFTER

    def _parse_page(self, page_path):
        """Gets a list of commands from the tldr page

        Parameters
        ----------
        page_path : str
            The file location of the tldr page

        Returns
        -------
        suggestions
            a list of suggestions representing the commands in the tldr page
        """
        # Read MD page
        lines = []
        with open(page_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        command_suggestion_list = []
        command_item = {}
        command = ""
        command_desc = ""
        command_url = ""
        url_regex = (
            r"(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)>"
        )
        for line in lines:
            if line.startswith("#"):
                command = line.replace("#", "").strip()
            elif line.startswith(">"):
                url_search_result = re.search(url_regex, line)
                if url_search_result:
                    command_url = url_search_result.group(1)
                else:
                    command_desc += line.replace(">", "").strip() + " "
            elif line.startswith("-"):
                command_item = {}
                command_item["info"] = (
                    line.replace("-", "", 1)
                    .replace("{{", "{")
                    .replace("}}", "}")
                    .replace(":", "")
                    .strip()
                )
            elif line.startswith("`"):
                command_item["command_str"] = (
                    line.replace("`", "").replace("{{", "{").replace("}}", "}").strip()
                )
                command_suggestion_list.append(
                    self.create_item(
                        category=self.ITEMCAT_COMMAND,
                        label=command_item["command_str"],
                        short_desc=command_item["info"],
                        target=command_item["command_str"],
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                    )
                )

        if command_url == "":
            command_url = self.config["info_url"].format(
                query=urllib.parse.quote(command + " command")
            )

        command_url_desc = "URL: " + command_url

        command_name_item = self.create_item(
            category=kp.ItemCategory.URL,
            label=command_desc,
            short_desc=command_url_desc,
            target=command_url,
            args_hint=kp.ItemArgsHint.FORBIDDEN,
            hit_hint=kp.ItemHitHint.IGNORE,
        )

        return [command_name_item] + command_suggestion_list

    def _update_cache(self, force=False):
        """Updates the local tldr page cache in the package cache directory

        Parameters
        ----------
        force : bool, optional
            A flag used to force the cache update even if the set conditions are not met (default is False)
        """
        try:
            tldr_zip_exists = False
            download_time = datetime.datetime.now()
            tldr_zip = ""
            tldr_zip_path = os.path.join(self.cache_path, "tldr.zip")
            if os.path.exists(tldr_zip_path):
                tldr_zip_exists = True
                download_time = datetime.datetime.fromtimestamp(os.path.getmtime(tldr_zip_path))

            days_to_update_cache = datetime.timedelta(days=self.config["cache_update_after"])
            should_update_cache = download_time + days_to_update_cache < datetime.datetime.now()

            if should_update_cache or not tldr_zip_exists or force:
                self.commands = []
                self._delete_old_pages()
                urllib.request.urlretrieve(
                    self.TLDR_ZIP_LINK,
                    os.path.join(self.cache_path, "tldr.zip"),
                )

                tldr_zip = zipfile.ZipFile(tldr_zip_path, "r")
                required_pages = [
                    ("pages." + language_name + "/")
                    for language_name in self.config["language"]
                    if language_name != "en"
                ] + ["pages/", "index.json"]
                required_page_files = []
                for rpfn in required_pages:
                    required_page_files += [f for f in tldr_zip.namelist() if rpfn in f]
                tldr_zip.extractall(members=required_page_files, path=self.cache_path)

                tldr_zip.close()

            # Build a command index from index.json
            index_str = []
            with open(os.path.join(self.cache_path, "index.json")) as index_file:
                index_str = index_file.readlines()[0]
            index = json.loads(index_str)
            self.commands = [command["name"] for command in index["commands"]]

        except Exception as ex:
            self.err("An error occurred while updating page cache. " + str(ex))

    def _delete_old_pages(self):
        """Deletes the existing page directories"""
        files_to_delete = [
            file for file in os.listdir(path=self.cache_path) if file.find("pages") != -1
        ]

        for file in files_to_delete:
            shutil.rmtree(os.path.join(self.cache_path, file))
