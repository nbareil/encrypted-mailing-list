#! /usr/bin/env python

import email, email.message, email.mime.message, email.mime.multipart, email.mime.application
import smtplib
import gnupg
import quopri

smtp_from = 'toto@example.com'
smtp_rcpt = 'toto@example.com'

masqueraded_to = 'XXX@example.com'
masqueraded_from = 'XXX@example.com'
masqueraded_subject = 'XXX2'
encryptedbody = ''.join(open('t.gpg').readlines())
cleartext = ''.join(open('mail').readlines())

outermsg = email.message.Message()
outer = email.mime.multipart.MIMEMultipart('encrypted; protocol="application/pgp-encrypted"')
outer.attach(outermsg)
outer.add_header('Subject', masqueraded_subject)
outer.add_header('To', masqueraded_to)
outer.add_header('From', masqueraded_from)
#outer.add_header('Content-Type', 'multipart/encrypted', protocol='application/pgp-encrypted')
#print outer.as_string()

controlpartmsg = email.message.Message()
controlpart = email.mime.application.MIMEApplication(controlpartmsg, 'pgp-encrypted')
del controlpart['Content-Transfer-Encoding']
controlpart.set_payload('blabla')

ciphermsg = email.message.Message()
ciphermsg.set_payload(encryptedbody)
cipher = email.mime.message.MIMEMessage(ciphermsg)
cipher.add_header('Content-Transfer-Encoding', 'quoted-printable')
cipher.add_header('Content-Disposition', 'inline')
cipher.set_payload(quopri.encodestring(cleartext))

innermsg = email.message.Message()
innermsg.set_payload(encryptedbody)
inner = email.mime.application.MIMEApplication(innermsg, 'octet-stream')

gpg = gnupg.GPG()
encryptedmsg = gpg.encrypt(cipher.as_string(), [smtp_rcpt], armor=False).data

inner.set_payload(encryptedmsg.encode('base64'))


outer.attach(controlpart)
outer.attach(inner)
print outer.as_string()


s = smtplib.SMTP('localhost')
s.sendmail(smtp_from, [smtp_rcpt], outer.as_string())
s.quit()

