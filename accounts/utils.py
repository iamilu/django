import pyotp
from datetime import datetime, timedelta

def send_otp(request):
    totp = pyotp.TOTP(pyotp.random_base32(), interval=60) # otp will become invalid or expired after 60 secs
    otp = totp.now() # to get the otp value
    request.session['otp_secret_key'] = totp.secret # store otp secret key in the user session
    valid_date = datetime.now() + timedelta(minutes=1) # adding 1 minute to the current time
    request.session['otp_valid_until'] = str(valid_date) # setting the expiration time of 1 minute in user session

    # code to send otp by sms or email

    print('your OTP is ' + otp)
