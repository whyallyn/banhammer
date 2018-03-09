"""Define all Google actions."""
from datetime import datetime

from plugins.exceptions import PluginError
from plugins.interfaces import User
from plugins.utils import (
    capture_stdout, generate_random_string, get_plugin_config_options)


class Google(User):
    """Google user object for performing Google API commands."""
    def __init__(self, username, reason):
        self._setup_plugins_config()
        self.username = username
        self.reason = reason
        # Load GAM
        try:
            import sys
            sys.path.append(self.gam_location)
            import gam
            self.gam = gam.ProcessGAMCommand
        except IOError:
            raise PluginError('Failed locate GAM.')
        except ImportError:
            raise PluginError('Failed to import GAM.')

    def _setup_plugins_config(self):
        """Setup values from plugins.ini configuration."""
        option = get_plugin_config_options('google')
        try:
            self.domain = option['domain']
            self.reset_password_length = int(option['reset_password_length'])
            self.gam_location = option['gam_location']
            self.backup_dir = option['backup_dir']
        except KeyError as err:
            raise PluginError('No "%s" option in plugins.ini' % err.message)

    def _run_gam(self, gam_cmd):
        """Take a GAM command string and run it."""
        with capture_stdout() as out:
            self.gam(gam_cmd.split())
        if out[1]:
            if '403' in out[1]:
                raise PluginError(
                    'GAM error - Not authorized to access this resource/API.')
        return out

    @property
    def info(self):
        """Get Google user account information."""
        out = self._run_gam('gam info user %s' % self.username)[0]
        if not out:
            raise PluginError('GAM error - User could not be found.')
        return out

    def _update(self, arguments):
        """Update a Google user."""
        return self._run_gam(
            'gam update user %s %s' % (self.username, arguments))[0]

    def randomize_password(self):
        """Changes a Google user's password to a random value."""
        out = self.info
        new_pwd = generate_random_string(
            self.reset_password_length)
        out = self._update('password \'%s\'' % new_pwd)
        if out != 'updating user %s@%s...\n' % (self.username, self.domain):
            raise PluginError(
                'Randomizing password - Verification failed.')

    def _remove_group(self, group):
        """Remove Google user from group."""
        out = self._run_gam('gam update group %s remove user %s' % (
            group, self.username))[1]
        if out != ' removing %s@%s\n' % (self.username, self.domain):
            raise PluginError(
                'Removing user from group - Verification failed.')

    @property
    def groups(self):
        """Get Google groups for a user."""
        out = self.info
        if '\nGroups: (' not in out:
            return
        add_group = False
        groups = []
        for line in out.split('\n'):
            if not line.startswith('   '):
                add_group = False
            if add_group:
                groups.append(line.split('<')[1].strip('>'))
            if line.startswith('Groups: ('):
                add_group = True
        return groups

    def _backup_group_memberships(self):
        """Backup a user's group memberships."""
        groups = self.groups
        if not groups:
            return
        backup_file = '%s_googlegroups_%s.txt' % (
            self.username, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        try:
            with open('%s/%s' % (self.backup_dir, backup_file), 'w') as fil:
                for grp in groups:
                    fil.write("%s\n" % grp)
        except IOError:
            raise PluginError(
                'Error writing group memberships to backup file.')

    def remove_group_memberships(self):
        """Remove a Google user from all groups."""
        self._backup_group_memberships()
        groups = self.groups
        if groups:
            for grp in groups:
                self._remove_group(grp)

    def remove_from_gal(self):
        """Remove a Google user from the Global Address List."""
        self._update('gal off')
        out = self.info
        for line in out.split('\n'):
            if line.startswith('Included in GAL:'):
                result = line.split(':')[1].strip()
                if result == 'False':
                    return
        raise PluginError('Removing from GAL - Verification failed.')

    def suspend(self):
        """Suspend a Google user account."""
        self._update('suspended on')
        out = self.info
        for line in out.split('\n'):
            if line.startswith('Account Suspended:'):
                result = line.split(':')[1].strip()
                if result == 'True':
                    return
        raise PluginError('Suspending account - Verification failed.')
