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

from patchlib import (
    config,
    data,
    message,
    query,
)

def search_subseries(patches, query_str):
    sub_series = []

    tokens = query.tokenize_query(query_str)
    q, _ = query.parse_query(tokens)

    for series in patches:
        if not query.eval_query(series, q):
            continue

        sub_series.append(series)

    return sub_series

def find_subseries(patches, args):
    return search_subseries(patches, ' '.join(args.query))

def dump_notmuch_query(patches, args):
    import notmuch

    sub_series = find_subseries(patches, args)
    if not sub_series:
        return

    def fn(series):
        return 'id:"%s"' % series['messages'][0]['message-id']

    query_str = ' or '.join(map(fn, sub_series))

    db = notmuch.Database(config.get_notmuch_dir())
    q = notmuch.Query(db, query_str)

    tids = []
    for thread in q.search_threads():
        tids.append('thread:%s' % thread.get_thread_id())

    print(' or '.join(tids))

def dump_oneline_query(patches, args):
    for series in find_subseries(patches, args):
        msg = series['messages'][0]
        print("{:s} {:s}".format(
            msg['message-id'],
            msg['subject']))

def dump_commits(patches, args):
    for series in find_subseries(patches, args):
        for msg in series['messages']:
            if 'commit' in msg:
                print(msg['commit'])

def dump_full_query(patches, args):
    for series in find_subseries(patches, args):
        msg = series['messages'][0]
        print("Message-id: {:s}".format(msg['message-id']))
        print("From: {:s} <{:s}>".format(msg['from']['name'],
                                         msg['from']['email']))
        print("Date: {:s}".format(msg['date']))
        ret = message.decode_subject_text(msg['subject'])
        tags = []
        if ret['rfc']:
            tags.append("RFC")
        if 'pull-request' in ret and ret['pull-request']:
            tags.append("PULL")
        if 'for-release' in ret:
            tags.append("for-" + ret['for-release'])
        if ret['version'] != 1:
            tags.append('v' + str(ret['version']))
        if tags:
            print("Tags: {:s}".format(", ".join(tags)))

        for msg in series['messages']:
            ret = message.decode_subject_text(msg['subject'])
            print("   [{:d}/{:d}] {:s}".format(
                ret['n'], ret['m'], ret['subject']))
        print()

def main(args):
    with open(config.get_json_path(), 'rb') as fp:
        patches = data.parse_json(fp.read())

    if args.format == 'notmuch':
        dump_notmuch_query(patches, args)
    elif args.format == 'oneline':
        dump_oneline_query(patches, args)
    elif args.format == 'full':
        dump_full_query(patches, args)
    elif args.format == 'commits':
        dump_commits(patches, args)
    else:
        raise Exception('unknown format %s' % args.format)

    return 0
