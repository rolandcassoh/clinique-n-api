import factory
from faker import Faker

from app.core.auth.password import hash_password
from app.modules.auth.infrastructure.models import UserModel

_fake = Faker("fr_FR")


class UserFactory(factory.Factory):
    class Meta:
        model = UserModel

    name = factory.LazyFunction(lambda: _fake.name())
    email = factory.LazyFunction(lambda: _fake.unique.email())
    password = factory.LazyFunction(lambda: hash_password("SecureP@ss123"))
    username = factory.LazyFunction(lambda: _fake.user_name())
    phone = factory.LazyFunction(lambda: _fake.phone_number()[:30])
    is_active = True
    email_verified_at = None
    otp_code = None
    totp_secret = None
    totp_enabled = False


class DoctorFactory(UserFactory):
    name = factory.LazyFunction(lambda: f"Dr. {_fake.last_name()}")
    email = factory.LazyFunction(lambda: f"doctor.{_fake.unique.last_name().lower()}@clinique.app")
