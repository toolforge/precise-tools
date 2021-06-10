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

import datetime

import requests

from . import utils

CACHE = utils.Cache()


def tools_from_accounting(remove_migrated=True, cached=False):
    """Get a list of (tool, job name, count, last) tuples for jobs running on
    trusty exec nodes in the last 7 days."""
    p = {'purge': 1} if not cached else None
    r = requests.get('https://sge-jobs.toolforge.org/json', params=p)

    tools = {}

    for tool, data in r.json()['tools'].items():
        jobs = {}
        for job_name, job in data['jobs'].items():
            if 'default' in job['per_release'].keys() or 'stretch' in job['per_release'].keys():
                if (not remove_migrated) or ('buster' not in job['per_release'].keys()):
                    jobs[job_name] = {
                        'count': job['count'],
                        'last': job['last'],
                    }
        if len(jobs) != 0:
            tools[tool] = {
                'jobs': jobs,
                'members': data['members']
            }

    return tools


def gridengine_status(url, cached=False):
    """Get a list of (tool, job name, host, release) tuples for jobs currently running
    on the given grid."""
    p = {'purge': 1} if not cached else None
    r = requests.get(url,  params=p)
    grid_info = r.json()['data']['attributes']

    tools = []
    for host, info in grid_info.items():
        if info['jobs']:
            tools.extend([
                (
                    normalize_toolname(job['job_owner']),
                    job['job_name'],
                    host,
                    job.get('release', 'default')
                )
                for job in info['jobs'].values()
            ])

    return tools


def normalize_toolname(name):
    if name.startswith('tools.'):
        return name[6:]
    # else None -- we ignore non-tool accounts like 'root'


def tools_members(tools):
    """
    Return a dict that has members of a tool associated with each tool
    Ex:
    {'musikbot': ['musikanimal'],
     'ifttt': ['slaporte', 'mahmoud', 'madhuvishy', 'ori']}
    """
    members = {}
    with utils.ldap_conn() as conn:
        for tool in tools:
            members[tool] = utils.find_members(conn, tool, [])
    return members


def get_view_data(days=7, cached=True, remove_migrated=True):
    """Get a structured collection of data about tools that are running on
    precise grid nodes.

    Return value will be a structure something like:
        {
            'generated': datetime,
            'tools': {
                'tool A': {
                    'jobs': {
                        'job X': {
                            'count': N,
                            'last': datetime,
                        },
                        'job Y': {
                            'count': N,
                            'last': datetime,
                        },
                        ...
                    },
                    'members': [
                        'user A',
                        'user B',
                        ...
                    ]
                },
                ...
            },
        }
    """

    cache_key = 'maindict:days={}:remove_migrated={}'.format(
        days, remove_migrated)
    ctx = CACHE.load(cache_key) if cached else None
    if ctx is None:
        date_fmt = '%Y-%m-%d %H:%M'
        tools = tools_from_accounting(remove_migrated, cached)

        grid_jobs = gridengine_status('https://sge-status.toolforge.org/api/v1', cached)
        fetch_maintainers_from_ldap = []

        for tool, name, host, release in grid_jobs:
            if release != 'buster':
                continue
            if tool in tools and name in tools[tool]['jobs']:
                del tools[tool]['jobs'][name]
                if not tools[tool]['jobs']:
                    del tools[tool]

        for tool, name, host, release in grid_jobs:
            if release == 'buster':
                # Oldest jobs do not have a release set, new ones have it as 'stretch'
                # Skipping everything that is not buster is easiest
                continue
            if not tool:
                print('Discarding user job: {}@{}'.format(name, host))
                continue

            if tool not in tools:
                tools[tool] = {
                    'jobs': {},
                    'members': [],
                }
                fetch_maintainers_from_ldap.append(tool)
            if name not in tools[tool]['jobs']:
                tools[tool]['jobs'][name] = {
                    'count': 0,
                    'last': '',
                }
            tools[tool]['jobs'][name]['count'] += 1
            tools[tool]['jobs'][name]['last'] = 'Currently running'

        for key, val in tools_members(fetch_maintainers_from_ldap).items():
            tools[key]['members'] = list(val)

        ctx = {
            'generated': datetime.datetime.now().strftime(date_fmt),
            'tools': tools,
        }
        CACHE.save(cache_key, ctx)
    return ctx
