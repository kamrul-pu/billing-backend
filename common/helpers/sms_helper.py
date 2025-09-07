import requests
import json

SMS_URL: str = "http://bulksmsbd.net/api"
SMS_API_KEY: str = "REaJMMMxbc00PNs9N9xH"
SMS_SENDER_ID: str = "Random"  # Replace with your sender ID


class SMS:
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
            response = requests.post(url, data=body)
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
        body = {
            "api_key": SMS_API_KEY,
            "senderid": SMS_SENDER_ID,
            "messages": messages,
        }
        url: str = SMS_URL + "/smsapimany"
        try:
            response = requests.post(url, data=json.dumps(body))
            response.raise_for_status()
            if response.status_code != 202:
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
