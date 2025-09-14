import requests
from django.conf import settings

# Load from Django settings
MIKROTIK_URL = settings.MIKROTIK_URL
MIKROTIK_USER = settings.MIKROTIK_USER
MIKROTIK_PASS = settings.MIKROTIK_PASS
MIKROTIK_VERIFY_SSL = getattr(
    settings, "MIKROTIK_VERIFY_SSL", False
)  # Default: False for dev
REQUEST_TIMEOUT = getattr(settings, "MIKROTIK_REQUEST_TIMEOUT", 10)  # Seconds


class Mikrotik:
    """
    Utility class to interact with MikroTik router via REST API.
    Supports: create, read, update, disable, delete PPP users and manage active sessions.
    """

    @staticmethod
    def get_user_by_username(username):
        """
        Fetch a PPP secret by username.
        :param username: str
        :return: tuple(success: bool, data_or_error: dict/str)
        """
        if not username:
            return False, "Username is required"

        try:
            query_url = f"{MIKROTIK_URL}/rest/ppp/secret/print"
            response = requests.post(
                query_url,
                json={".query": [f"name={username}"]},
                auth=(MIKROTIK_USER, MIKROTIK_PASS),
                verify=False,
                # verify=MIKROTIK_VERIFY_SSL,
                # timeout=REQUEST_TIMEOUT,
            )

            if response.status_code != 200:
                return False, f"HTTP {response.status_code}: {response.text}"

            data = response.json()
            if not data:
                return False, "User not found in PPP secrets"

            return True, data[0]

        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def get_users_from_server():
        """
        Fetch all PPP users (secrets).
        :return: tuple(success: bool, users_list_or_error: list/str)
        """
        try:
            url = f"{MIKROTIK_URL}/rest/ppp/secret"
            response = requests.get(
                url,
                auth=(MIKROTIK_USER, MIKROTIK_PASS),
                # verify=MIKROTIK_VERIFY_SSL,
                # timeout=REQUEST_TIMEOUT,
                verify=False,
            )

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"HTTP {response.status_code}: {response.text}"

        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def get_user_sessions(organization):
        """
        Get all active PPP sessions.
        :return: tuple(success: bool, sessions_list_or_error: list/str)
        """
        try:
            url = f"{organization.router_ip}/rest/ppp/active"
            response = requests.get(
                url,
                auth=(organization.router_username, organization.router_password),
                # verify=MIKROTIK_VERIFY_SSL,
                # timeout=REQUEST_TIMEOUT,
                verify=False,
            )
            print("RRRRR: ", response)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"HTTP {response.status_code}: {response.text}"

        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def delete_user_session(session_id):
        """
        Terminate an active PPP session by ID.
        :param session_id: str (.id from session)
        :return: bool
        """
        try:
            url = f"{MIKROTIK_URL}/rest/ppp/active/{session_id}"
            response = requests.delete(
                url,
                auth=(MIKROTIK_USER, MIKROTIK_PASS),
                # verify=MIKROTIK_VERIFY_SSL,
                # timeout=REQUEST_TIMEOUT,
                verify=False,
            )

            if response.status_code == 200:
                return True
            else:
                print(
                    f"[Mikrotik] Failed to delete session {session_id}: {response.text}"
                )
                return False

        except Exception as e:
            print(f"[Mikrotik] Exception deleting session {session_id}: {str(e)}")
            return False

    @staticmethod
    def toggle_ppp_user(username, disable=True):
        """
        Enable or disable a PPP user.
        If disabling, also terminate active session.
        :param username: str
        :param disable: bool (True to disable, False to enable)
        :return: tuple(success: bool, message: str)
        """
        if not username:
            return False, "Username is required"

        try:
            # Step 1: Get user
            success, user = Mikrotik.get_user_by_username(username)
            if not success:
                return False, f"User not found: {user}"

            secret_id = user[".id"]
            disabled_str = "true" if disable else "false"

            # Step 2: Update disabled status
            patch_url = f"{MIKROTIK_URL}/rest/ppp/secret/{secret_id}"
            response = requests.patch(
                patch_url,
                json={"disabled": disabled_str},
                auth=(MIKROTIK_USER, MIKROTIK_PASS),
                # verify=MIKROTIK_VERIFY_SSL,
                # timeout=REQUEST_TIMEOUT,
                verify=False,
            )

            if response.status_code != 200:
                try:
                    error_msg = response.json().get("message", response.text)
                except:
                    error_msg = response.text
                return False, f"Update failed: {error_msg}"

            # Step 3: If disabling, terminate active session
            if disable:
                success, sessions = Mikrotik.get_user_sessions()
                if success:
                    for session in sessions:
                        if session.get("name") == username:
                            session_id = session[".id"]
                            if Mikrotik.delete_user_session(session_id):
                                print(f"[Mikrotik] Terminated session for '{username}'")
                            else:
                                print(
                                    f"[Mikrotik] Warning: Could not terminate session for '{username}'"
                                )
                    print("sessions not available for the user")
                else:
                    print(
                        f"[Mikrotik] Warning: Could not fetch active sessions: {sessions}"
                    )

            action = "disabled" if disable else "enabled"
            return True, f"User '{username}' {action} successfully"

        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def create_ppp_user(user):
        username = user.get("username", "")
        password = user.get("password", "")
        if not username or not password:
            return False, "Username and password are required"

        payload = {
            "name": username,
            "password": password,
            "service": user.get("service", "pppoe"),  # Default to pppoe
            "profile": user.get("profile", "5Mbps"),  # Default profile
            "disabled": "false",
            "comment": user.get("comment", "Test Comment"),
        }

        try:
            url = f"{MIKROTIK_URL}/rest/ppp/secret"
            response = requests.put(  # MikroTik uses PUT to CREATE
                url,
                json=payload,
                auth=(MIKROTIK_USER, MIKROTIK_PASS),
                verify=False,
                # verify=MIKROTIK_VERIFY_SSL,
                # timeout=REQUEST_TIMEOUT,
            )
            print("RRRRR: ", response)
            if response.status_code == 201:
                return True, "PPP user created successfully"
            else:
                try:
                    error_msg = response.json().get("message", response.text)
                except:
                    error_msg = response.text
                return False, f"Create failed [{response.status_code}]: {error_msg}"

        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def delete_ppp_user(username):
        """
        Delete a PPP user (ppp secret) by username.
        :param username: str
        :return: tuple(success: bool, message: str)
        """
        success, user = Mikrotik.get_user_by_username(username)
        if not success:
            return False, f"User not found: {user}"

        try:
            url = f"{MIKROTIK_URL}/rest/ppp/secret/{user['.id']}"
            response = requests.delete(
                url,
                auth=(MIKROTIK_USER, MIKROTIK_PASS),
                verify=False,
                # verify=MIKROTIK_VERIFY_SSL,
                # timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                return True, "User deleted successfully"
            else:
                return False, f"Delete failed: {response.text}"

        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
