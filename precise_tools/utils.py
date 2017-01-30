# -*- coding: utf-8 -*-
#
# This file is part of precise-tools
# Copyright (C) 2017 Bryan Davis and contributors
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess


def tail(filename, lines):
    """Get last n lines from the filename as an iterator."""
    # Inspired by http://stackoverflow.com/a/4418193/8171
    cmd = ['tail', '-%d' % lines, filename]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        line = proc.stdout.readline()
        if line == '' and proc.poll() is not None:
            break
        yield line

    if proc.returncode == 0:
        raise StopIteration
    else:
        raise subprocess.CalledProcessError(
            returncode=proc.returncode,
            command=' '.join(cmd)
        )
