#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import email, email.message, email.mime.message, email.mime.multipart, email.mime.application
import smtplib
import socket
import gnupg
import hashlib
import string
import re
import sys

SECRET_FILE = 'secretkey'
RCPTS_LIST_FILE = 'recipients.txt' # one email address per line
FROM_ADDR_FILE  = 'from.txt'       # one line containing FROM address
reply_to = string.strip(open('replyto.txt').readline())

try:
    SECRET_KEY = string.strip(open(SECRET_FILE).readline())
except:
    SECRET_KEY = open('/dev/urandom').read(64)
    open(SECRET_FILE, 'w+').write(SECRET_KEY)
    

my_hostname = '%s.%s' % ('encrypted', socket.gethostname())


def h(s):
    return hashlib.md5(SECRET_KEY + s).hexdigest()


def clean_subject(s):
    r = re.compile(r'^(\s*(Re|Aw|TR|FW)\s*:\s*)*', re.IGNORECASE)
    return r.sub('', s)


smtp_from = open(FROM_ADDR_FILE).readline()
smtp_rcpt = map(string.strip, open(RCPTS_LIST_FILE).readlines())

cleartext = ''.join(sys.stdin.readlines())
original = email.message_from_string(cleartext)
original_subject = original['Subject']
original_to      = original['To']
original_from    = original['From']
original_msgid   = original['Message-ID']
original_ref     = original.get('References', None)
original_irt     = original.get('In-Reply-To', None)

masqueraded_to      = h(original_to)
masqueraded_from    = h(original_from)
if not my_hostname in original_irt:
    masqueraded_subject = h(clean_subject(original_subject))
else:
    masqueraded_subject = original_subject
masqueraded_msgid   = '<%s@%s>' % (h(original_msgid), my_hostname)

# Mail structure
# ==============
#
#     outer
#     ├── controlpart
#     └── inner
#         └── ciphered
#             └── rfc1822 (original)
#


outermsg = email.message.Message()
outer = email.mime.multipart.MIMEMultipart('encrypted; protocol="application/pgp-encrypted"')
outer.attach(outermsg)
outer.add_header('Subject', masqueraded_subject)
outer.add_header('To', masqueraded_to)
outer.add_header('From', masqueraded_from)
outer.add_header('Message-ID', masqueraded_msgid)
outer.add_header('Mail-Followup-To', reply_to)
if original_ref:
    outer.add_header('References', original_ref)
if original_irt:
    outer.add_header('In-Reply-To', original_irt)
outer.add_header('Mail-Reply-To', reply_to)
outer.add_header('Reply-To', reply_to)

controlpartmsg = email.message.Message()
controlpart = email.mime.application.MIMEApplication(controlpartmsg, 'pgp-encrypted')
del controlpart['Content-Transfer-Encoding']
controlpart.set_payload('blabla')

ciphermsg = email.message.Message()
cipher = email.mime.message.MIMEMessage(ciphermsg)
cipher.add_header('Content-Disposition', 'inline')
cipher.set_payload(cleartext)

innermsg = email.message.Message()
inner = email.mime.application.MIMEApplication(innermsg, 'octet-stream')
del inner['Content-Transfer-Encoding']

gpg = gnupg.GPG()
result = gpg.encrypt(cipher.as_string(), smtp_rcpt)
encryptedmsg = str(result)

inner.set_payload(encryptedmsg)


outer.attach(controlpart)
outer.attach(inner)

s = smtplib.SMTP('localhost')
s.sendmail(smtp_from, [smtp_rcpt], outer.as_string())
s.quit()

