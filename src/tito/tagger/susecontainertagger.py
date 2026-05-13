# Copyright (c) 2022 SUSE Linux Products GmbH
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
"""
Code for tagging containers in SUSE Style.
"""
import os
import re
import shutil

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from tito.tagger import SUSETagger

from tito.common import (error_out, get_latest_tagged_version,
                         increase_version, reset_release, increase_zstream, info_out, get_spec_version_and_release)


class SUSEContainerTagger(SUSETagger):
    def __init__(self, config=None, keep_version=False, offline=False, user_config=None):
        SUSETagger.__init__(self, config=config, keep_version=keep_version, offline=offline, user_config=user_config)
        self.changes_file_name = f"{self.project_name}.changes"
        self.changes_file = os.path.join(self.full_project_dir, self.changes_file_name)

    def _bump_version(self, release=False, zstream=False):
        """
        Bump up the package version in the spec file.

        Set release to True to bump the package release instead.

        Checks for the keep version option and if found, won't actually
        bump the version or release.
        """
        old_version = get_latest_tagged_version(self.project_name)
        if old_version is None:
            old_version = "untagged"
        if not self.keep_version:

            version_prefix = ""
            if os.path.split(self.spec_file_name)[-1] == "Chart.yaml":
                version_prefix = "version:"
                version_release_regex = re.compile(rf"^({version_prefix}\s*)(.+)$", re.IGNORECASE)
            elif os.path.split(self.spec_file_name)[-1] == "Dockerfile":
                version_prefix = "LABEL org.opencontainers.image.version="
                version_release_regex = re.compile(rf"^({version_prefix}\s*)(.+)$", re.IGNORECASE)
            elif os.path.split(self.spec_file_name)[-1].endswith(".kiwi"):
                version_release_regex = re.compile(r'^\s*<label name="org\.opencontainers\.image\.version" value="(.+)"/>\s*$')


            in_f = open(self.spec_file, 'r')
            out_f = open(self.spec_file + ".new", 'w')
            new_version = None
            old_version = None
            lines = []

            for line in in_f.readlines():
                version_match = re.match(version_release_regex, line)

                if version_match and not zstream and not release:
                    current_version = version_match.group(2)
                    old_version = current_version
                    release = None
                    if len(current_version.split("-")) >= 2:
                        (current_version, release) = current_version.split("-")

                    if hasattr(self, '_use_version'):
                        new_version = self._use_version
                    else:
                        new_version = increase_version(current_version)

                    if release:
                        new_version = f"{new_version}-{release}"
                    line = "".join([version_match.group(1), new_version, "\n"])

                lines.append(line)

            new_file_content = "".join(lines)

            out_f.write(new_file_content)

            in_f.close()
            out_f.close()
            shutil.move(self.spec_file + ".new", self.spec_file)

        new_version = get_spec_version_and_release(self.full_project_dir, self.spec_file_name)
        if new_version.strip() == "":
            msg = "Error getting bumped package version"
            error_out(msg)
        info_out("Tagging new version of %s: %s -> %s" % (self.project_name, old_version, new_version))
        return new_version
