from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your Account SID from twilio.com/console
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
# Your Auth Token from twilio.com/console
auth_token  = os.getenv('TWILIO_AUTH_TOKEN')

# Print environment variables to verify
print(f"Account SID: {account_sid}")
print(f"Auth Token: {auth_token}")

client = Client(account_sid, auth_token)

message = client.messages.create(
    to="+919655612306", 
    from_="+17722962741",  # Replace with your Twilio-provided phone number
    body="Hello from Python!")

print(message.sid)