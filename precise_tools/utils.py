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

from __future__ import division

import os
import datetime


def lines_in_last_n_bytes(filename, nbytes):
    """Get lines from last n bytes from the filename as an iterator."""
    with open(filename, 'r') as f:
        f.seek(-nbytes, os.SEEK_END)

        # Ignore first line as it may be only part of a line
        f.readline()

        # We can't simply `return f` as the returned f will be closed
        # Do all the IO within this function
        for line in f:
            yield line


def totimestamp(dt, epoch=None):
    """Convert a datetime to unix epoch seconds."""
    # From http://stackoverflow.com/a/8778548/8171
    if epoch is None:
        epoch = datetime.datetime(1970, 1, 1)
    td = dt - epoch
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6
