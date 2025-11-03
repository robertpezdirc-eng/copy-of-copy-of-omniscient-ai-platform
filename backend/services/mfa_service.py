import pyotp
import random
import smtplib

class MFAService:
    def generate_totp(self, secret):
        totp = pyotp.TOTP(secret)
        return totp.now()

    def send_sms(self, phone_number, message):
        # SMS sending logic
        pass

    def send_email(self, email, message):
        # Email sending logic
        pass

    def generate_backup_codes(self):
        return [str(random.randint(100000, 999999)) for _ in range(10)]