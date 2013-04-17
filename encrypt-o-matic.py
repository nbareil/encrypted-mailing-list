#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import email, email.message, email.mime.message, email.mime.multipart, email.mime.application
import smtplib
import socket
import gnupg
import md5
import string
import re

my_hostname = '%s.%s' % ('encrypted', socket.gethostname())

def h(s):
    return md5.new(s).hexdigest()

def hash_ref_if_needed(ref):
    if not ref.endswith(my_hostname):
        ref = h(ref)
    return ref

def clean_subject(s):
    r = re.compile(r'^(\s*(Re|Aw|TR|FW)\s*:\s*)*', re.IGNORECASE)
    return r.sub('', s)
    

smtp_from = 'toto@example.com'
smtp_rcpt = 'toto@example.com'

cleartext = ''.join(open('mail').readlines())
original = email.message_from_string(cleartext)
original_subject = original['Subject']
original_to      = original['To']
original_from    = original['From']
original_msgid   = original['Message-ID']
original_ref     = original['References']

masqueraded_to      = h(original_to)
masqueraded_from    = h(original_from)
masqueraded_subject = h(clean_subject(original_subject))
masqueraded_msgid   = '<%s@%s>' % (h(original_msgid), my_hostname)
if original_ref:
    masqueraded_ref     = map(hash_ref_if_needed,
                              map(string.strip,
                                  original_ref.split(',')))


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
if original_ref:
    outer.add_header('References', masqueraded_ref)

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
encryptedmsg = str(gpg.encrypt(cipher.as_string(), [smtp_rcpt]))

inner.set_payload(encryptedmsg)


outer.attach(controlpart)
outer.attach(inner)

s = smtplib.SMTP('localhost')
s.sendmail(smtp_from, [smtp_rcpt], outer.as_string())
s.quit()

