"""Define all Bit9 actions."""
import json

import requests

from plugins.exceptions import PluginError
from plugins.interfaces import Hash
import plugins.utils


class Bit9(Hash):
    """Bit9 hash object."""
    def __init__(self, hashcode, reason):
        self.hashcode = hashcode
        self.reason = reason
        self._setup_plugins_config()

    def _setup_plugins_config(self):
        """Setup values from plugins.ini configuration."""
        option = plugins.utils.get_plugin_config_options('bit9')
        try:
            self.token = option['token']
            self.url = option['url']
            self.strong_cert = True
            if option['strong_cert'].lower() == 'false':
                self.strong_cert = False
        except KeyError as err:
            raise PluginError('No "%s" option in plugins.ini' % err.message)

    def _update_file_state(self, fstate):
        """Updates file state by hash for all Bit9 policies."""
        # disable warnings when not verifying certificate
        if not self.strong_cert:
            requests.packages.urllib3.disable_warnings()

        auth_json = {
            'X-Auth-Token': self.token,
            'content-type': 'application/json',
        }
        data = {
            'hash': self.hashcode,
            'name': self.reason,
            'fileState': fstate,  # 1 means 'unapproved', 3 means 'banned'
        }

        # make request to Bit9
        try:
            bit9_request = requests.post(
                self.url,
                json.dumps(data),
                headers=auth_json,
                verify=self.strong_cert,
                timeout=60,
            )
            bit9_request.raise_for_status()
        except requests.exceptions.RequestException as err:
            raise PluginError('Bit9 server failed to respond - %s.' % err)

    def unapprove_file(self):
        """Mark a file as unapproved in Bit9."""
        self._update_file_state(1)

    def ban_file(self):
        """Ban a file in Bit9."""
        self._update_file_state(3)
