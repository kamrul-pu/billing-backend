from django.core.management.base import BaseCommand
from customer.models import Customer, Package, Payment

from django.db import transaction

import requests
from django.conf import settings

# MikroTik Router API Settings
MIKROTIK_URL = "http://103.146.16.148"  # Use http:// or https://
MIKROTIK_USER = "kamrul"
MIKROTIK_PASS = "kamrul#2025"


def get_users_from_server():
    try:
        response = requests.get(
            f"{MIKROTIK_URL}/rest/ppp/secret",
            auth=(MIKROTIK_USER, MIKROTIK_PASS),
            verify=False,  # Use CA in production
        )
        if response.status_code != 200:
            print("Failed to fetch users from server: ", response.status_code)
            return []

        users = response.json()
        return users
    except Exception as e:
        print("Error fetching users from server: ", str(e))
        return []


PACKAGE_DETAIL = {
    5: {"name": "Basic", "price": 500},
    10: {"name": "Standard", "price": 750},
    15: {"name": "Premium", "price": 1000},
    20: {"name": "Package 20 Mbps", "price": 2000},
    30: {"name": "Package 30 Mbps", "price": 3000},
    50: {"name": "Package 50 Mbps", "price": 5000},
}


class Command(BaseCommand):
    help = "Get customer data from server and update local database"

    def handle(self, *args, **kwargs):
        packages = Package.objects.filter()
        package_dict = {pkg.speed_mbps: pkg for pkg in packages}
        users = get_users_from_server()
        db_customers = Customer.objects.filter().only("username")
        db_customers_set = {customer.username: customer for customer in db_customers}
        customers_to_create = []
        for i in range(len(users)):
            # print("customer secert_id", users[i].get(".id", ""))
            username = users[i].get("name", "")
            if username in db_customers_set:
                # print("customer already exists in db: ", username)
                continue
            name = ""
            if username:
                name = username.split(".")[1] if "." in username else username
            disabled = users[i].get("disabled", "false").lower() == "true"
            profile: str = users[i].get("profile", "")
            package_speed = ""
            i: int = 0
            while i < len(profile):
                if not profile[i].isdigit():
                    break
                package_speed += profile[i]
                i += 1
            package_speed = int(package_speed) if package_speed else 0
            package = package_dict.get(package_speed, None)
            if not package:
                package = Package.objects.create(
                    name=PACKAGE_DETAIL.get(package_speed, {}).get(
                        "name", f"Package {package_speed} Mbps"
                    ),
                    speed_mbps=package_speed,
                    price=PACKAGE_DETAIL.get(package_speed, {}).get(
                        "price", 0.0
                    ),  # Default price, can be updated later
                )
                package_dict[package_speed] = package

            service = users[i].get("service", "DHCP")
            if service == "pppoe":
                service = "PPPoE"
            else:
                service = "DHCP"
            customers_to_create.append(
                Customer(
                    name=name.capitalize(),
                    secret_id=users[i].get(".id", ""),
                    username=username,
                    package_id=package.id or None,
                    password=users[i].get("password", ""),
                    mac_address=users[i].get("last-caller-id", ""),
                    is_active=not disabled,
                    address=users[i].get("comment", ""),
                    connection_type=service,
                )
            )
            if len(customers_to_create) % 100 == 0:
                print("adding customers in db")
                with transaction.atomic():
                    Customer.objects.bulk_create(customers_to_create)
                    customers_to_create = []
        # Adding remaing customers if any
        if customers_to_create:
            print("adding remaining customers in db")
            with transaction.atomic():
                Customer.objects.bulk_create(customers_to_create)

        print("Customers updated successfully.")
        self.stdout.write(self.style.SUCCESS("Customers updated successfully."))
