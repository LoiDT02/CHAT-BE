import string
import random


def generate_password(min_char: int = 15, max_char: int = 20):
    password_length = random.randint(min_char, max_char)
    password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(password_length))
    return password
