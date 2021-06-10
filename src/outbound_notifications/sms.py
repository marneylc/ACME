import smtplib


def alt_send_message(msg):
    target_email = "luke.email.ryan.here@gmail.com"
    bad_practice = "oferoyrtvimlhqdd"
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(target_email, bad_practice)
    from_mail = 'petersryan84@gmail.com'
    to = '95096707927@tmomail.net'
    body = msg
    message = ("From: %s\r\n" % from_mail + "To: %s\r\n" % to + "Subject: %s\r\n" % '' + "\r\n" + body)
    server.sendmail(from_mail, to, message)

def send_message(msg):
    target_email = "luke.email.ryan.here@gmail.com"
    # ToDo: HIGH PRIORITY --
    #   Instead of saving the password inside the file, we should required the user to enter the password correctly
    #   within some limited number of attempts.
    bad_practice = "oferoyrtvimlhqdd"
    # Establish a secure session with gmail's outgoing SMTP server using your gmail account
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(target_email, bad_practice)
    # Send text message through SMS gateway of destination number
    server.sendmail( "Your friendly neighborhood Python script", '5096707927@tmomail.net', msg)


if __name__ == '__main__':
    alt_send_message("test message")