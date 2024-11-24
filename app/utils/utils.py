import random
import string

def generate_custom_id():
    """Generate a custom 12-byte alphanumeric ID."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=12))