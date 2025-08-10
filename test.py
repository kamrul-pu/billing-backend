# # utils.py
# import requests
# from django.conf import settings

# MIKROTIK_URL = "http://103.146.16.148"
# MIKROTIK_USER = "kamrul"
# MIKROTIK_PASS = "kamrul#2025"


# def toggle_ppp_user(username, disable=True):
#     try:
#         # First, get the secret by name
#         response = requests.post(
#             f"{MIKROTIK_URL}/rest/ppp/secret/print",
#             json={".query": [f"name={username}"]},
#             auth=(MIKROTIK_USER, MIKROTIK_PASS),
#             verify=False,  # because of self-signed cert; use CA in prod
#         )
#         if response.status_code != 200:
#             return False, "User not found or API error"

#         data = response.json()
#         # if not data:
#         #     return False, "No such user"
#         print("data: ", data)

#         secret_id = data[0][".id"]
#         disabled_str = "true" if disable else "false"

#         # Update disabled status
#         patch_resp = requests.patch(
#             f"{MIKROTIK_URL}/rest/ppp/secret/{secret_id}",
#             json={"disabled": disabled_str},
#             auth=(MIKROTIK_USER, MIKROTIK_PASS),
#             verify=False,
#         )

#         if patch_resp.status_code == 200:
#             # Step 3: Terminate active session
#             # active_sessions = requests.get(
#             #     f"{MIKROTIK_URL}/rest/ppp/active",
#             #     auth=(MIKROTIK_USER, MIKROTIK_PASS),
#             #     verify=False,
#             # ).json()

#             # for session in active_sessions:
#             #     if session.get("name") == username:
#             #         requests.delete(
#             #             f"{MIKROTIK_URL}/rest/ppp/active/{session['.id']}",
#             #             auth=(MIKROTIK_USER, MIKROTIK_PASS),
#             #             verify=False,
#             #         )
#             #         break
#             return True, "User updated"
#         else:
#             return False, patch_resp.json().get("message", "Unknown error")

#     except Exception as e:
#         return False, str(e)


# toggle_ppp_user("AKHI", False)


# utils.py
import requests
from django.conf import settings

# MikroTik Router API Settings
MIKROTIK_URL = "http://103.146.16.148"  # Use http:// or https://
MIKROTIK_USER = "kamrul"
MIKROTIK_PASS = "kamrul#2025"


def toggle_ppp_user(username, disable=True):
    """
    Enable or disable a PPP user on MikroTik and optionally terminate their active session.

    Args:
        username (str): The PPP username (name field in /ppp secret)
        disable (bool): If True, disables the user. If False, enables them.

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Step 1: Find the PPP secret by username
        query_url = f"{MIKROTIK_URL}/rest/ppp/secret/print"
        response = requests.post(
            query_url,
            json={".query": [f"name={username}"]},
            auth=(MIKROTIK_USER, MIKROTIK_PASS),
            verify=False,  # Set to True in production with valid CA
        )

        if response.status_code != 200:
            return False, f"Failed to query user: HTTP {response.status_code}"

        data = response.json()

        if not data:
            return False, "User not found in PPP secrets"

        secret = data[0]
        secret_id = secret[".id"]
        disabled_str = "true" if disable else "false"

        # Step 2: Update the 'disabled' status of the PPP secret
        patch_url = f"{MIKROTIK_URL}/rest/ppp/secret/{secret_id}"
        patch_resp = requests.patch(
            patch_url,
            json={"disabled": disabled_str},
            auth=(MIKROTIK_USER, MIKROTIK_PASS),
            verify=False,
        )

        if patch_resp.status_code != 200:
            error_detail = patch_resp.json().get("message", "Unknown error")
            return False, f"Failed to update user: {error_detail}"

        # Step 3: If disabling, check and terminate active session
        if disable:
            active_sessions_url = f"{MIKROTIK_URL}/rest/ppp/active"
            active_resp = requests.get(
                active_sessions_url,
                auth=(MIKROTIK_USER, MIKROTIK_PASS),
                verify=False,
            )

            if active_resp.status_code == 200:
                active_sessions = active_resp.json()
                for session in active_sessions:
                    if session.get("name") == username:
                        session_id = session[".id"]
                        delete_url = f"{MIKROTIK_URL}/rest/ppp/active/{session_id}"
                        delete_resp = requests.delete(
                            delete_url,
                            auth=(MIKROTIK_USER, MIKROTIK_PASS),
                            verify=False,
                        )
                        if delete_resp.status_code == 200:
                            print(f"Terminated active session for {username}")
                        else:
                            print(
                                f"Failed to terminate session {session_id}: {delete_resp.text}"
                            )
                        break  # Only one session per user typically
            else:
                print("Warning: Could not fetch active sessions")

        return True, "User updated successfully"

    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


# Test the function
if __name__ == "__main__":
    # Example: Enable user 'AKHI'
    success, msg = toggle_ppp_user("AKHI", disable=False)
    print("Success:" if success else "Error:", msg)

    # Example: Disable user 'AKHI'
    # success, msg = toggle_ppp_user("AKHI", disable=True)
    # print("Success:" if success else "Error:", msg)
