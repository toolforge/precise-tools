#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of precise-tools
# Copyright (C) 2019 Bryan Davis and contributors
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

import collections
import email.message
import smtplib
import ssl

import requests


EXCLUDED_TOOLS = (
    'gridengine-status',
)
SERVER = 'mail.tools.wmflabs.org'
REPLY_TO = 'Bryan Davis <bd808@tools.wmflabs.org>'
SUBJECT = '[Toolforge] Tools you maintain are running on Trusty job grid'
MESSAGE = """\
Hello {maintainer},

This email is a reminder that the tools listed below have run jobs and/or
webservices using the Ubuntu Trusty job grid in the past 7 days. This job grid
will be shutdown on or before the week of 2019-03-25 as the final step in the
removal of Ubuntu Trusty from Toolforge and the larger Cloud VPS environment.

{tools}

See <https://tools.wmflabs.org/trusty-tools/u/{maintainer}> for more details
on these tools and the jobs that have been seen.

Please see the migration instructions on Wikitech [0] for more information on
how to move your tools to either the new Debian Stretch job grid or the
Kubernetes cluster.

[0]: https://wikitech.wikimedia.org/wiki/News/Toolforge_Trusty_deprecation

Thanks,
The Toolforge admin team
"""


def get_maintainer_info():
    maintainers = collections.defaultdict(set)
    r = requests.get('https://tools.wmflabs.org/trusty-tools/json')
    trusty_tools = r.json()
    for tool, data in trusty_tools['tools'].items():
        if tool in EXCLUDED_TOOLS:
            continue
        for member in data['members']:
            maintainers[member].add(tool)
    return maintainers


def send_message(server, maintainer, tools):
    body = MESSAGE.format(
        maintainer=maintainer,
        tools='\n'.join(['  * {}'.format(tool) for tool in sorted(tools)]),
    )
    msg = email.message.EmailMessage()
    msg.set_content(body)
    msg['Sender'] = '<tools.trusty-tools@tools.wmflabs.org>'
    msg['From'] = 'Toolforge admins <tools.admin@tools.wmflabs.org>'
    msg['To'] = '<{}@tools.wmflabs.org>'.format(maintainer)
    msg['Reply-To'] = REPLY_TO
    msg['Subject'] = SUBJECT
    server.send_message(msg)


def main():
    maintainers = get_maintainer_info()
    ctx = ssl.create_default_context()
    with smtplib.SMTP(host=SERVER, port=25, timeout=5) as server:
        server.starttls(context=ctx)
        for maintainer, tools in maintainers.items():
            send_message(server, maintainer, tools)


if __name__ == '__main__':
    main()

# vim:sw=4:ts=4:sts=4:et:
