#
# patches - QEMU Patch Tracking System
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Anthony Liguori <aliguori@us.ibm.com>
#
# This work is licensed under the terms of the GNU GPLv2 or later.
# See the COPYING file in the top-level directory.
#

from patchlib import config


def any_committed(series):
    for message in series['messages']:
        if 'commit' in message:
            return True
    return False


def is_applied(series):
    return 'applied-by' in series['messages'][0]


def is_committed(series):
    committed = False

    if is_pull_request(series):
        if 'commit' in series['messages'][0]['pull-request']:
            return True
        elif is_committed_in_branch(series, config.get_master_branch()):
            return True
        return False

    for message in series['messages']:
        if message.get('cover'):
            continue

        if 'commit' not in message:
            return False
        else:
            committed = True

    return committed


def is_committed_in_branch(series, branch):
    committed = False

    for message in series['messages']:
        if message.get('cover'):
            continue

        if 'commit' not in message:
            return False
        elif message['tree'] != branch:
            return False
        else:
            committed = True

    return committed


def is_reviewed(series):
    found = False

    for message in series['messages']:
        if message.get('cover'):
            if 'Reviewed-by' in message['tags']:
                return True
            continue

        if 'Reviewed-by' not in message['tags']:
            return False

        found = True

    return found


def is_pull_request(series):
    if 'pull-request' in series['messages'][0]:
        return series['messages'][0]['pull-request']
    return False


def is_obsolete(series):
    if 'obsolete' in series['messages'][0]:
        return series['messages'][0]['obsolete']
    return False


def is_broken(series):
    if series.get('broken'):
        return True
    return False


def is_rfc(series):
    return "rfc" in series['messages'][0] and series['messages'][0]['rfc']


def has_subject_tags(series):
    return bool(series['messages'][0].get('subject-tags'))
