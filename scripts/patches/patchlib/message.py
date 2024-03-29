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

from email.header import decode_header
from email.utils import parseaddr

from patchlib import config


def escape_message_id(mid):
    """Escape a Message-ID so it is safe for filenames"""
    return mid.replace('%', '%%').replace('/', '%2F')


def parse_email_address(value):
    name, mail = parseaddr(value)
    return {'name': name, 'email': mail}


def parse_email_addresses(value):
    if value:
        if value.find(', ') == -1:
            return [parse_email_address(value)]
        else:
            return list(map(parse_email_address, value.split(', ')))
    return []


def get_header(msg, name):
    value = ''

    # notmuch's Message.get_header() doesn't handle chunked encoded headers
    # correctly so we fix it here.
    header = msg.get_header(name)
    if header.find('=?') != -1:
        for chunk, encoding in decode_header(header):
            value += str(chunk, encoding or 'ascii')
    else:
        value = str(header)

    return value


def get_subject(msg):
    list_tag = '[%s] ' % config.get_list_tag()
    subject = get_header(msg, 'Subject')
    if subject.startswith(list_tag):
        subject = subject[len(list_tag):].strip()
    return subject


def find_and_split(haystack, needle):
    index = haystack.find(needle)
    if index == -1:
        return haystack, ''
    else:
        return haystack[0:index], haystack[index + len(needle):]


def is_digit(ch):
    return ch in '0123456789'


def parse_subject(msg):
    ret = decode_subject(msg)
    return ret['n'], ret['m'], ret['version'], ret['subject']


def decode_subject(msg):
    subject = get_header(msg, 'Subject')
    return decode_subject_text(subject)


def decode_subject_text(subject):
    ret = {'n': 1, 'm': 1, 'version': 1,
           'patch': False, 'rfc': False}
    patch_tags = []

    while subject and subject[0] == '[':
        bracket, subject = find_and_split(subject[1:], ']')
        subject = subject.lstrip()

        if bracket:
            words = list(map(str.upper, bracket.split(' ')))

            for word in words:
                if not word:
                    continue

                if word.startswith('PATCH') and word != 'PATCH':
                    # It's pretty common for people to do PATCHv2 or
                    # other silly things.  Try our best to handle that.
                    word = word[5:]
                    ret['patch'] = True

                index = word.find('/')
                if index != -1 and is_digit(word[0]) and is_digit(word[index + 1]):
                    try:
                        ret['n'], ret['m'] = list(map(int, word.split('/', 1)))
                    except ValueError:
                        pass
                elif word[0] == 'V' and is_digit(word[1]):
                    try:
                        ret['version'] = int(word[1:])
                    except:
                        pass
                elif word.startswith('FOR-') and is_digit(word[4]):
                    ret['for-release'] = word[4:]
                elif is_digit(word[0]) and word.find('.') != -1:
                    ret['for-release'] = word
                elif word in ['RFC', '/RFC']:
                    ret['rfc'] = True
                elif word in ['PATCH']:
                    ret['patch'] = True
                elif word in ['PULL']:
                    ret['pull-request'] = True
                    ret['patch'] = True
                elif word == config.get_list_tag().upper():
                    pass
                else:
                    patch_tags.append(word)

    if patch_tags:
        ret['tags'] = patch_tags

    ret['subject'] = subject

    return ret


def format_tag_name(key):
    return key[0].upper() + key[1:].lower()


def parse_tag(line, extra_tags=None):
    if not line:
        return None
    if extra_tags is None:
        extra_tags = []

    i = 0
    if not line[i].isupper():
        return None

    i += 1
    while i < len(line) and (line[i].isupper() or
                             line[i].islower() or
                             line[i] == '-'):
        i += 1

    if i == len(line) or line[i] != ':':
        return None

    key = format_tag_name(line[0:i])
    value = line[i + 1:].strip()

    if key not in (config.get_email_tags() + extra_tags) or not value:
        return None

    return {key: [value]}


def merge_tags(lhs, rhs):
    val = {}
    for key in lhs:
        if key in ['Message-id']:
            continue
        val[key] = lhs[key]

    for key in rhs:
        if key in ['Message-id']:
            continue
        if key not in val:
            val[key] = []
        for tag in rhs[key]:
            if tag not in val[key]:
                val[key].append(tag)

    return val


def isin(needle, lst):
    for item in lst:
        if needle['name'] == item['name'] and needle['email'] == item['email']:
            return True
    return False


def dedup(lst):
    new_lst = []
    for item in lst:
        if not isin(item, new_lst):
            new_lst.append(item)
    return new_lst


def get_payload(msg):
    parts = msg.get_message_parts()
    charset = parts[0].get_content_charset('utf-8')
    try:
        return parts[0].get_payload(decode=True).decode(charset)
    except:
        # Emails with bogus charset names have been known to exist
        return parts[0].get_payload(decode=True).decode('latin1')


def find_extra_tags(msg, leader):
    extra_tags = {}

    for line in get_payload(msg).split('\n'):
        if line == '---' or line.startswith('diff '):
            break

        tag = parse_tag(line)
        if tag:
            extra_tags = merge_tags(extra_tags, tag)

    to_addrs = parse_email_addresses(get_header(msg, 'To'))
    cc_addrs = parse_email_addresses(get_header(msg, 'Cc'))

    if not leader:
        for reply in msg.get_replies():
            new_tags, new_to, new_cc = find_extra_tags(reply, leader)
            extra_tags = merge_tags(extra_tags, new_tags)
            to_addrs += new_to
            cc_addrs += new_cc

    return extra_tags, dedup(to_addrs), dedup(cc_addrs)


def is_thanks_applied(msg):
    for line in get_payload(msg).split('\n'):
        for pattern in ('Thanks, applied',
                        'Applied to ',
                        'Applied, thanks'):
            if line.startswith(pattern):
                return True
    return False


def is_cover(msg):
    return msg.get('cover')


def is_patch(msg):
    ret = decode_subject(msg)
    return ret['patch']
