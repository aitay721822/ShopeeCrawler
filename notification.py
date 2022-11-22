import logging
import smtplib

from email.mime.text import MIMEText
from email.header import Header


class Email:

    def __init__(self,
                 smtp_server: str,
                 smtp_port: int,
                 user: str,
                 pwd: str,
                 logger: logging.Logger = logging.getLogger("email")):
        self.logger = logger
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.user = user
        self.pwd = pwd

    def send(self, sender: str, receivers: list, title: str, content: str):
        return False

class DummyEmail(Email):

    def __init__(self, logger: logging.Logger = logging.getLogger("fake_email")):
        super().__init__('', '', '', '', logger)

    def send(self, sender: str, receivers: list, title: str, content: str):
        self.logger.info(f"send email to {', '.join(receivers)} by {sender}")
        self.logger.info(f"send status: ok. title: {title}, content: {content!s:5.5s}")
        return True

class GoogleEmail(Email):

    def __init__(self, username, password):
        super().__init__(
            'smtp.gmail.com',
            587,
            username,
            password
        )

    def send(self, sender, receivers, title, content):
        self.logger.info(f"send email to {', '.join(receivers)} by {sender}")
        message = MIMEText(content, 'html', 'utf-8')
        message['From'] = Header("提醒機器人", 'utf-8')
        message['To'] = Header("用戶", 'utf-8')
        message['Subject'] = Header(title, "utf-8")
        try:
            smtpObj = smtplib.SMTP(self.smtp_server, self.smtp_port)
            smtpObj.connect(self.smtp_server, self.smtp_port)
            smtpObj.ehlo()
            smtpObj.starttls()
            smtpObj.ehlo()
            smtpObj.login(self.user, self.pwd)
            smtpObj.sendmail(sender, receivers, message.as_string())
            self.logger.info(f"send status: ok. title: {title}, content: {content!s:5.5s}")
            return True
        except smtplib.SMTPException as e:
            self.logger.error(f"send status: error occurred: {e}")
            return False

