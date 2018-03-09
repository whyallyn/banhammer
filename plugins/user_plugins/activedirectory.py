"""Define all Active Directory actions."""
from datetime import datetime

import ldap
from pyldaplite import PyLDAPLite

from plugins.exceptions import PluginError
from plugins.interfaces import User
from plugins.utils import generate_random_string, get_plugin_config_options


class ActiveDirectory(User):
    """Active Directory user object for performing LDAP commands."""
    def __init__(self, username, reason):
        # create LDAP connection
        self._setup_plugins_config()
        self.ldapl = PyLDAPLite(
            server='ldaps://%s' % self.server, base_dn=self.base_dn)
        try:
            self.ldapl.connect(self.admin, self.password)
        except ldap.LDAPError as err:
            raise PluginError(
                'LDAP error while creating connection: %s' %
                self._get_ldap_errors(err))
        self.aduser = self._get(username)
        self.reason = reason

    def _setup_plugins_config(self):
        """Setup values from plugins.ini configuration."""
        option = get_plugin_config_options('activedirectory')
        try:
            self.server = option['server']
            self.base_dn = option['base_dn']
            self.admin = option['admin']
            self.password = option['password']
            self.reset_password_length = int(option['reset_password_length'])
            self.backup_dir = option['backup_dir']
            self.disabled_group = option['disabled_group']
            self.disabled_ou = option['disabled_ou']
        except KeyError as err:
            raise PluginError('No "%s" option in plugins.ini' % err.message)

    @staticmethod
    def _get_ldap_errors(err):
        """Get LDAP error by extracting message."""
        errors = []
        if 'info' in err.args[0]:
            errors.append(err.args[0]['info'])
        if 'desc' in err.args[0]:
            errors.append(err.args[0]['desc'])
        return ' '.join(errors)

    def _get(self, username):
        """Get one or more Active Directory user objects."""
        try:
            result = self.ldapl.search_name(username)
        except ldap.LDAPError:
            raise PluginError('LDAP error - Invalid Base DN')

        if len(result) == 0:
            raise PluginError('User "%s" does not exist.' % username)
        elif len(result) > 1:
            raise PluginError(
                'More than one result found for "%s".' % username)
        elif len(result) == 1:
            return result[0][0][1]

    def randomize_password(self):
        """Change an Active Directory user's password to a random value."""
        new_pwd = generate_random_string(self.reset_password_length)
        new_pwd = unicode('\"' + new_pwd + '\"').encode('utf-16-le')
        try:
            self.ldapl.conn.modify_s(
                self.aduser['distinguishedName'][0],
                [(ldap.MOD_REPLACE, 'unicodePwd', [new_pwd])])
        except ldap.LDAPError as err:
            raise PluginError(
                'LDAP error while randomizing AD password: %s' %
                self._get_ldap_errors(err))

    def _backup_group_memberships(self):
        """Backup a user's group memberships."""
        if 'memberOf' not in self.aduser:
            return
        backup_file = '%s_adgroups_%s.txt' % (
            self.aduser['sAMAccountName'][0],
            datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        try:
            with open('%s/%s' % (self.backup_dir, backup_file), 'w') as fil:
                for group in self.aduser['memberOf']:
                    fil.write("%s\n" % group)
        except IOError:
            raise IndentationError(
                'Error writing group memberships to backup file.')

    def remove_group_memberships(self):
        """Remove an Active Directory user from all groups."""
        if 'memberOf' not in self.aduser:
            return
        self._backup_group_memberships()
        try:
            for group in self.aduser['memberOf']:
                self.ldapl.conn.modify_s(
                    group,
                    [(
                        ldap.MOD_DELETE,
                        'member',
                        self.aduser['distinguishedName'])])
            self.aduser = self._get(self.aduser['sAMAccountName'][0])
            if 'memberOf' in self.aduser:
                raise PluginError(
                    'Removing group memberships - Verification failed.')
        except ldap.LDAPError as err:
            raise PluginError(
                'LDAP error while removing from groups: %s' %
                self._get_ldap_errors(err))

    def _add_group(self, group_dn):
        """Add a user object to an Active Directory group."""
        try:
            self.ldapl.conn.modify_s(
                group_dn,  # distinguishedName
                [(ldap.MOD_ADD, 'member', self.aduser['distinguishedName'])]
            )
            self.aduser = self._get(self.aduser['sAMAccountName'][0])
            if ('memberOf' not in self.aduser or
                    group_dn not in self.aduser['memberOf']):
                raise PluginError(
                    'Adding to group "%s" - Verification failed.' % group_dn)
        except ldap.LDAPError as err:
            raise PluginError(
                'LDAP error while adding user to group: %s' %
                self._get_ldap_errors(err))

    def add_to_disabled_group(self):
        """Add an Active Directory user to the configured disabled group."""
        self._add_group(self.disabled_group)

    def disable(self):
        """Disables an Active Directory user account."""
        new_uac = str(int(self.aduser['userAccountControl'][0]) | 0x00000002)
        try:
            self.ldapl.conn.modify_s(
                self.aduser['distinguishedName'][0],
                [(ldap.MOD_REPLACE, 'userAccountControl', [new_uac])])
            self.aduser = self._get(self.aduser['sAMAccountName'][0])
            if not int(self.aduser['userAccountControl'][0]) & 0x00000002:
                raise PluginError(
                    'Disabling account - Verification failed.')
        except ldap.LDAPError as err:
            raise PluginError(
                'LDAP error while disabling AD account: %s' %
                self._get_ldap_errors(err))

    def _move(self, newsuperior):
        """Move an Active Directory user to another organizational unit."""
        try:
            self.ldapl.conn.rename_s(
                self.aduser['distinguishedName'][0],
                'cn=%s' % self.aduser['cn'][0],
                newsuperior)
            self.aduser = self._get(self.aduser['sAMAccountName'][0])
            superior = self.aduser['distinguishedName'][0].split(
                ',', 1)[1]
            if newsuperior.lower() != superior.lower():
                raise PluginError(
                    'Moving to "%s" - Verification failed.' % newsuperior)
        except ldap.LDAPError as err:
            raise PluginError(
                'LDAP error while moving AD object: %s' %
                self._get_ldap_errors(err))

    def move_to_disabled_ou(self):
        """Move an Active Directory user to the configured disabled OU."""
        self._move(self.disabled_ou)
