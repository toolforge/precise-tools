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
import collections

import requests

from . import kubernetes, utils

CACHE = utils.Cache()
KUBERNETES = kubernetes.KubernetesClient.create_inside_cluster()


def get_k8s_workloads():
    """Gets a list of all workloads running on Kubernetes"""
    tools = collections.defaultdict(list)

    deployments = KUBERNETES.get(
        "/apis/apps/v1/deployments",
        params={"limit": 5000},
    )["items"]

    for deployment in deployments:
        namespace: str = deployment["metadata"]["namespace"]
        if not namespace.startswith("tool-"):
            continue
        namespace = namespace[5:]
        tools[namespace].append(deployment["metadata"]["name"])

    cronjobs = KUBERNETES.get(
        "/apis/batch/v1beta1/cronjobs",
        params={"limit": 5000},
    )["items"]

    for cronjob in cronjobs:
        namespace: str = cronjob["metadata"]["namespace"]
        if not namespace.startswith("tool-"):
            continue
        namespace = namespace[5:]
        tools[namespace].append(cronjob["metadata"]["name"])

    return tools

def is_migrated(tool_name, job_name, job, k8s_jobs):
    if (
        job["queue"] == ["webgrid-lighttpd"] or job["queue"] == ["webgrid-generic"]
        and tool_name in k8s_jobs
    ):
        return True

    return job_name in k8s_jobs

def tools_from_accounting(remove_migrated=True, cached=False):
    """Get a list of (tool, job name, count, last) tuples for jobs running on
    trusty exec nodes in the last 7 days."""
    p = {'purge': 1} if not cached else None
    r = requests.get('https://sge-jobs.toolforge.org/json', params=p)

    if remove_migrated:
        k8s_workloads = get_k8s_workloads()
    else:
        k8s_workloads = {}

    tools = {}

    for tool, data in r.json()['tools'].items():
        jobs = {}
        for job_name, job in data['jobs'].items():
            if not is_migrated(tool, job_name, job, k8s_workloads.get(tool, [])):
                jobs[job_name] = {
                    'count': job['count'],
                    'last': job['last'],
                }

        if len(jobs) != 0:
            tools[tool] = {
                'jobs': jobs,
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

        for tool, name, host, release in grid_jobs:
            if not tool:
                print('Discarding user job: {}@{}'.format(name, host))
                continue

            if tool not in tools:
                tools[tool] = {
                    'jobs': {},
                }

            if name not in tools[tool]['jobs']:
                tools[tool]['jobs'][name] = {
                    'count': 0,
                    'last': '',
                }

            tools[tool]['jobs'][name]['count'] += 1
            tools[tool]['jobs'][name]['last'] = 'Currently running'

        for key, val in tools_members(tools.keys()).items():
            tools[key]['members'] = list(val)

        ctx = {
            'generated': datetime.datetime.now().strftime(date_fmt),
            'tools': tools,
        }
        CACHE.save(cache_key, ctx)
    return ctx
