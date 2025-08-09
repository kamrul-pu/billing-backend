import factory
from django.contrib.auth import get_user_model
from faker import Faker

from core.choices import UserKind, UserGender


User = get_user_model()

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
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
