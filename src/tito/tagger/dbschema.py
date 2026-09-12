# Copyright (c) 2026 SUSE LLC
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
"""
Tagger for the Uyuni/SUSE Manager database schema packages.

These packages (susemanager-schema, uyuni-reportdb-schema) collect new,
unreleased migration scripts in an "upgrade/next" directory while a schema
version is under development, instead of a versioned upgrade directory.
"""
from tito.builder.dbschema import DatabaseSchemaBuilder
from tito.tagger.susetagger import SUSETagger


class DatabaseSchemaTagger(SUSETagger):
    """
    SUSETagger variant for the Uyuni/SUSE Manager database schema
    packages (susemanager-schema, uyuni-reportdb-schema).

    When tagging a new version, moves the migration scripts collected in
    upgrade/next into a proper <old-version>-to-<new-version> upgrade
    directory. The move is staged in git, so it is picked up by the
    commit the tagger creates while tagging.

    If you want it put in tito.props (locally in the package directory):
    [buildconfig]
    tagger = tito.tagger.DatabaseSchemaTagger
    """

    def _bump_version(self, release=False, zstream=False):
        builder = DatabaseSchemaBuilder(self.full_project_dir, self.project_name)
        old_version = builder.read_spec_version(self.spec_file)

        new_version = SUSETagger._bump_version(self, release=release, zstream=zstream)

        new_plain_version = builder.read_spec_version(self.spec_file)
        builder.move_pending_migrations(old_version, new_plain_version)

        return new_version
