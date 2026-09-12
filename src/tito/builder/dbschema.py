# Copyright (c) 2026 SUSE LLC
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
"""
Builder for the Uyuni/SUSE Manager database schema packages.

These packages (susemanager-schema, uyuni-reportdb-schema) collect new,
unreleased migration scripts in an "upgrade/next" directory while a schema
version is under development, instead of a versioned upgrade directory.
"""
import os
import re

from tito.common import run_command
from tito.exception import TitoException

VERSION_REGEX = re.compile(r"^Version:\s*(\S+)", re.IGNORECASE)


class DatabaseSchemaBuilder(object):
    """
    Moves the SQL scripts pending in upgrade/next into a new, properly
    named upgrade/<project>-<old-version>-to-<project>-<new-version>
    directory, staging the move in git.
    """

    NEXT_DIR_NAME = "next"

    def __init__(self, project_dir, project_name):
        self.project_dir = project_dir
        self.project_name = project_name
        self.upgrade_dir = os.path.join(project_dir, "upgrade")
        self.next_dir = os.path.join(self.upgrade_dir, self.NEXT_DIR_NAME)

    def read_spec_version(self, spec_file):
        """ Read the (plain) Version field straight out of a spec file. """
        with open(spec_file) as f:
            for line in f:
                match = VERSION_REGEX.match(line)
                if match:
                    return match.group(1)
        raise TitoException("Could not find a Version in %s" % spec_file)

    def pending_migrations(self):
        """ Return the names of the migration scripts sitting in upgrade/next. """
        if not os.path.isdir(self.next_dir):
            return []
        return sorted(
            name for name in os.listdir(self.next_dir)
            if name != "README.md"
            and os.path.isfile(os.path.join(self.next_dir, name))
        )

    def move_pending_migrations(self, old_version, new_version):
        """
        Move the pending migration scripts out of upgrade/next into a new
        upgrade/<project>-<old-version>-to-<project>-<new-version>
        directory, git-staged so they end up in the tagger's commit.

        Does nothing if the version did not change or there is nothing
        pending in upgrade/next.
        """
        if old_version == new_version:
            return

        migrations = self.pending_migrations()
        if not migrations:
            return

        target_dir_name = "%s-%s-to-%s-%s" % (
            self.project_name, old_version, self.project_name, new_version)
        target_dir = os.path.join(self.upgrade_dir, target_dir_name)
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)

        for name in migrations:
            if os.path.exists(os.path.join(target_dir, name)):
                raise TitoException("Schema migration already exists: %s" os.path.join(target_dir, name))
            run_command("git mv %s %s" % (
                os.path.join(self.next_dir, name),
                os.path.join(target_dir, name)))
