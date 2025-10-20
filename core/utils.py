"""Utils functions for core app."""


# Media File Prefixes
def get_user_media_path_prefix(instance, filename):
    return f"users/{instance.slug}/{filename}"


def generate_unique_otp(length=6) -> str:
    otp = "".join(random.choices("0123456789", k=length))

    return otp