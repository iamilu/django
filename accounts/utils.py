from .models import Account

import pyotp
from datetime import datetime, timedelta

from twilio.rest import Client

from django.conf import settings

def send_sms(request, otp):

    account_sid = settings.ACCOUNT_SID
    auth_token = settings.AUTH_TOKEN

    email = request.session['email']
    try:
        user = Account.objects.get(email__exact=email)
    except  Account.DoesNotExist:
        user = None
    print(user.phone)

    client = Client(account_sid, auth_token)

    message = client.messages \
                    .create(
                        body = f"Please enter OTP {otp} to login to the website",
                        from_ = f"{settings.SEND_SMS_FROM}",
                        to = f"{user.phone}",
                    )

    print(message)

def send_otp(request):
    totp = pyotp.TOTP(pyotp.random_base32(), interval=60) # otp will become invalid or expired after 60 secs
    
    # get otp value
    otp = totp.now()

    # get otp secret key value
    otp_secret_key = totp.secret

    request.session['otp_secret_key'] = otp_secret_key

    # add 1 minute to the current time
    valid_date = datetime.now() + timedelta(minutes=1)
    # set the expiration time of OTP 1 minute in user session
    request.session['otp_valid_until'] = str(valid_date)

    print('your OTP is ' + otp)
    
    # code to send otp by sms using twilio
    send_sms(request, otp)
