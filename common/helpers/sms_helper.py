"""
Docstring for common.helpers.sms_helper
"""

import json

import requests

from django.conf import settings

SMS_URL: str = settings.SMS_URL
SMS_API_KEY: str = settings.SMS_API_KEY
SMS_SENDER_ID: str = settings.SMS_SENDER_ID


class SMS:
    """SMS helper class"""

    @staticmethod
    def send_single_sms(to: str, message: str) -> bool:
        """Send SMS using BulkSMSBD API."""
        body = {
            "api_key": SMS_API_KEY,
            "senderid": SMS_SENDER_ID,
            "number": to,
            "message": message,
        }
        url: str = SMS_URL + "/smsapi"
        try:
            response = requests.post(url, data=body, timeout=60)
            response.raise_for_status()
            if response.status_code != 202:
                print(f"Failed to send SMS, {response.text}")
                return False
            return True

        except requests.RequestException as e:
            # Log the error
            print(f"Error sending SMS: {e}")
            return False

    @staticmethod
    def send_bulk_sms(messages) -> bool:
        """
        Docstring for send_bulk_sms

        :param messages: Description
        :return: Description
        :rtype: bool
        """
        body = {
            "api_key": SMS_API_KEY,
            "senderid": SMS_SENDER_ID,
            "messages": json.dumps(messages),
        }

        url: str = SMS_URL + "/smsapimany"
        try:
            response = requests.post(url, data=body, timeout=60)
            response.raise_for_status()
            if response.status_code not in [200, 202]:
                print(f"Failed to send SMS, {response.text}")
                return False
            return True

        except requests.RequestException as e:
            # Log the error
            print(f"Error sending SMS: {e}")
            return False


# {
#   type : "post",
#   url : "http://bulksmsbd.net/api/smsapimany",
#   data : {
#     "api_key" : "your api key",
#     "senderid" : "sender id",
#     "messages" :
#             [
#                   {
#                     "to" : "88016xxxxxxxx",
#                     "message" : "SMS text 1"
#                   },
#                   {
#                     "to" : "88019xxxxxxxx",
#                     "message" : "SMS Text 2"
#                   }
#             ]
#   }
# }
