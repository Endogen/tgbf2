import json
import logging

from pathlib import Path


class ConfigManager:

    # JSON content
    _cfg = dict()
    # Config file path
    _cfg_file = None

    def __init__(self, config_file):
        """ This class takes a JSON config file and makes it available
         so that if you provide a key, you will get the value back.
         Values can also bet set or removed from the config. Setting
         and removing values will be written to the initial config file.
         """

        if config_file:
            self._cfg_file = config_file
            self._read_cfg()
        else:
            logging.error("ERROR: No config file provided")

    def _read_cfg(self):
        """ Read the JSON content of a given configuration file """

        try:
            if Path(self._cfg_file).is_file():
                with open(self._cfg_file) as config_file:
                    self._cfg = json.load(config_file)
            else:
                self._cfg = {}
        except Exception as e:
            err = f"Can't read '{self._cfg_file}'"
            logging.error(f"{repr(e)} - {err}")

    def _write_cfg(self):
        """ Write the JSON dictionary into the given configuration file """

        try:
            Path(self._cfg_file).parent.mkdir(parents=True, exist_ok=True)

            with open(self._cfg_file, "w") as config_file:
                json.dump(self._cfg, config_file, indent=4)
        except Exception as e:
            err = f"Can't write '{self._cfg_file}'"
            logging.error(f"{repr(e)} - {err}")

    def get(self, *keys):
        """ Return the value of the given key(s) from a configuration file """

        if not self._cfg:
            self._read_cfg()

        if not keys:
            return self._cfg

        value = self._cfg

        try:
            for key in keys:
                value = value[key]
        except Exception as e:
            err = f"Can't get '{keys}' from '{self._cfg_file}'"
            logging.debug(f"{repr(e)} - {err}")
            return None

        return value

    def set(self, value, *keys):
        """ Set a new value for the given key(s) in the configuration file.
        Will also execute the callback method if there is one """

        if not self._cfg:
            self._read_cfg()

        if not keys:
            return

        tmp_cfg = self._cfg

        try:
            for key in keys[:-1]:
                tmp_cfg = tmp_cfg.setdefault(key, {})
            tmp_cfg[keys[-1]] = value

            self._write_cfg()
        except Exception as e:
            err = f"Can't set '{keys}' in '{self._cfg_file}'"
            logging.debug(f"{repr(e)} - {err}")

    def remove(self, *keys):
        """ Remove given key(s) from the configuration file.
        Will also execute the callback method if there is one """

        if not self._cfg:
            self._read_cfg()

        if not keys:
            return

        tmp_cfg = self._cfg

        try:
            for key in keys[:-1]:
                tmp_cfg = tmp_cfg.setdefault(key, {})
            del tmp_cfg[keys[-1]]

            self._write_cfg()
        except KeyError as e:
            err = f"Can't remove key '{keys}' from '{self._cfg_file}'"
            logging.debug(f"{repr(e)} - {err}")
