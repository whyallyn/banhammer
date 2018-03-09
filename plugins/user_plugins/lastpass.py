"""Define all LastPass actions."""
import json
import requests

from plugins.exceptions import PluginError
from plugins.interfaces import User
from plugins.utils import convert_str_tolist, get_plugin_config_options


class LastPass(User):
    """LastPass user object for interacting with the Provisioning API."""
    def __init__(self, username, reason):
        self.username = username
        self.reason = reason
        self._setup_plugins_config()

    def _setup_plugins_config(self):
        """Setup values from plugins.ini configuration."""
        option = get_plugin_config_options('lastpass')
        try:
            self.cid = option['cid']
            self.provhash = option['provhash']
            self.domains = convert_str_tolist(option['domains'])
        except KeyError as err:
            raise PluginError('No "%s" option in plugins.ini' % err.message)

    def _call_api(self, cmd, data):
        """Make a call to the LastPass Provisioning API."""
        api_url = 'https://lastpass.com/enterpriseapi.php'
        post_data = {
            'cid': self.cid,
            'provhash': self.provhash,
            'cmd': cmd,
            'data': data,
        }
        response = requests.post(api_url, data=json.dumps(post_data))
        if response.status_code == requests.codes.ok:
            try:
                json_response = response.json()
            except ValueError:
                raise PluginError('API is not configured correctly.')
            if 'error' in json_response:
                raise PluginError(json_response['error'][0])
            return json_response
        else:
            raise PluginError('HTTP %s' % response.status_code)

    def _delete_user_api(self, email, delete_action):
        """Deactivate, remove, or delete a LastPass user."""
        data = {
            'username': email,
            'deleteaction': '%s' % delete_action,
        }
        self._call_api('deluser', data)

    def _get_user_api(self, email):
        """Get user data for a LastPass user."""
        data = {
            'username': email,
        }
        return self._call_api('getuserdata', data)

    def deactivate_user(self):
        """Deactivate LastPass user.

        Blocks logins but retains data and enterprise membership.
        """
        num_users_disabled = 0
        users_unverified = []
        for domain in self.domains:
            email = '%s@%s' % (self.username, domain)
            # get user
            try:
                user = self._get_user_api(email)
            except PluginError as err:
                # user not found, go to next domain in list
                if err.message == '%s is not a valid user.' % email:
                    continue
                else:
                    raise
            # validate data
            if 'Users' not in user or len(user['Users']) < 1:
                continue
            try:
                uid = user['Users'].keys()[0]
                if not user['Users'][uid]['disabled']:
                    # disable user
                    self._delete_user_api(email, 0)
                    # verification
                    user = self._get_user_api(email)
                    if user['Users'][uid]['disabled']:
                        num_users_disabled += 1
                    else:
                        users_unverified.append(email)
                # user already disabled
                else:
                    num_users_disabled += 1
            except KeyError:
                raise PluginError('Received unexpected response from server.')
        if users_unverified:
            users = ' and '.join(users_unverified)
            raise PluginError(
                'Deactivating user - Verification failed for %s.' % users)
        if not num_users_disabled:
            domains = ' or '.join(self.domains)
            raise PluginError(
                'Deactivating user - no users found for %s.' % domains)
