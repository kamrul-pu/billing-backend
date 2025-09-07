import factory
from django.contrib.auth import get_user_model
from faker import Faker

from core.choices import UserKind, UserGender, SubscriptionType, SubscriptionStatus

from core.models import Organization, Subscription

User = get_user_model()

fake = Faker()


class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "core.Subscription"

    name = factory.Faker("name")
    description = factory.Faker("text", max_nb_chars=100)
    plan = factory.Faker(
        "random_element", elements=[choice.value for choice in SubscriptionType]
    )
    price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    max_customers = factory.Faker("random_int", min=10, max=1000)


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "core.Organization"

    name = factory.Faker("company")
    description = factory.Faker("text", max_nb_chars=100)
    address = factory.Faker("address")
    phone = factory.Faker("phone_number")
    email = factory.Faker("company_email")
    website = factory.Faker("url")
    subscription = factory.Iterator(Subscription().get_all_actives())
    subscription_status = factory.Faker(
        "random_element", elements=[choice.value for choice in SubscriptionStatus]
    )
    router_ip = factory.Faker("ipv4")
    router_username = factory.Faker("user_name")
    router_password = factory.Faker("password")
    router_port = 8728
    router_secret = factory.Faker("word")
    router_ssl = False
    allowed_customer = 100
    total_customer = 0


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    organization = factory.Iterator(Organization().get_all_actives())
    # phone = factory.Sequence(lambda n: f"987654321{n % 10}")
    phone = factory.LazyAttribute(lambda _: fake.unique.phone_number())
    email = factory.LazyAttribute(
        lambda o: f"{o.first_name.lower()}.{o.last_name.lower()}@example.com"
    )
    gender = factory.Faker(
        "random_element", elements=[choice.value for choice in UserGender]
    )
    kind = factory.Faker(
        "random_element", elements=[choice.value for choice in UserKind]
    )
    password = factory.PostGenerationMethodCall("set_password", "defaultpassword")
    is_staff = False
    is_active = True
