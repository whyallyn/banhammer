"""Define all Duo actions."""
import duo_client

from plugins.exceptions import PluginError
from plugins.interfaces import User
from plugins.utils import get_plugin_config_options


class Duo(User):
    """Duo user object for interacting with the Admin API."""
    def __init__(self, username, reason):
        self.username = username
        self.reason = reason
        # setup Admin API settings
        self._setup_plugins_config()
        self._get_user_result()

    def _setup_plugins_config(self):
        """Setup values from plugins.ini configuration."""
        option = get_plugin_config_options('duo')
        try:
            self.admin_api = duo_client.Admin(
                ikey=option['integration_key'],
                skey=option['secret_key'],
                host=option['api_hostname'],
            )
        except KeyError as err:
            raise PluginError('No "%s" option in plugins.ini' % err.message)

    def _get_user_result(self):
        """"Lookup Duo user by name and store result."""
        self.user_result = None
        try:
            result = self.admin_api.get_users_by_name(self.username)
        except RuntimeError as err:
            raise PluginError('Duo API error - %s' % err.message)
        if not result:
            raise PluginError('User could not be found.')
        # check that response contains everything expected
        if (isinstance(result, list) and len(result) == 1 and
                isinstance(result[0], dict) and
                set(['user_id', 'phones', 'tokens']) <= set(result[0]) and
                isinstance(result[0]['phones'], list) and
                isinstance(result[0]['tokens'], list)):
            self.user_result = result[0]
        else:
            raise PluginError('Received unexpected response from server.')

    @property
    def user_id(self):
        """Duo user ID."""
        return self.user_result['user_id']

    @property
    def phone_ids(self):
        """List of Duo user's phones by ID."""
        phones = []
        for phone in self.user_result['phones']:
            if 'phone_id' in phone:
                phones.append(phone['phone_id'])
        return phones

    @property
    def token_ids(self):
        """List of Duo user's tokens by ID."""
        tokens = []
        for token in self.user_result['tokens']:
            if 'token_id' in token:
                tokens.append(token['token_id'])
        return tokens

    def delete_phones(self):
        """Delete all phones for a Duo user account."""
        for phone in self.phone_ids:
            try:
                self.admin_api.delete_user_phone(self.user_id, phone)
            except RuntimeError as err:
                raise PluginError('Duo API error - %s' % err.message)
        # verify deletion
        self._get_user_result()
        if self.phone_ids:
            raise PluginError('Deleting phones - Verification failed')

    def delete_tokens(self):
        """Delete all tokens for a Duo user account."""
        for token in self.token_ids:
            try:
                self.admin_api.delete_user_token(self.user_id, token)
            except RuntimeError as err:
                raise PluginError('Duo API error - %s' % err.message)
        # verify deletion
        self._get_user_result()
        if self.token_ids:
            raise PluginError('Deleting tokens - Verification failed')
