import os

from dotenv import load_dotenv
load_dotenv()
from pwn import *
from yachalk import chalk

DOMAIN = os.environ.get("DOMAIN")
USER_ID = os.environ.get("COOKIE_VALUE")

START_TRIGGER = "abc123"
NEXT_TRIGGER = b"whiz??\n"
FLAG_TRIGGER = b"Aww yeah!\n"

WORD_MATCH = "-"
BINARY_MATCH = "0b"
HEX_MATCH = "0x"


def binary_to_decimal(binary):
    return int(binary, 2)


def hex_to_decimal(hex):
    return int(hex, 16)


def handleWord(wordNumber):
    if WORD_MATCH in wordNumber:
        wordNumbers = wordNumber.split("-")
        words = [
            "ZERO",
            "ONE",
            "TWO",
            "THREE",
            "FOUR",
            "FIVE",
            "SIX",
            "SEVEN",
            "EIGHT",
            "NINE",
            "TEN",
        ]

        for i, v in enumerate(wordNumbers):
            for j in words:
                wordNumbers[i] = wordNumbers[i].replace(j, str(words.index(j)))
        print(wordNumbers)
        return int("".join(map(str, wordNumbers)))
    elif wordNumber.startswith(BINARY_MATCH):
        return binary_to_decimal(wordNumber)
    elif wordNumber.startswith(HEX_MATCH):
        return hex_to_decimal(wordNumber)
    return wordNumber


def calculate():
    line = target.recvline()
    string = line.decode("utf-8")

    print("Original:", string)

    if "flag{" not in string:
        # Parse equation
        equation = string[: string.index("=")]

        # Parse "components" of equation
        components = equation.split()
        x = handleWord(components[0])
        operand = components[1]
        y = handleWord(components[2])

        answer = eval(f"{x}{operand}{y}")
        target.send(f"{answer}\n")

        print(chalk.black("Solve     \t"), chalk.cyan(equation))
        print(chalk.black("x:        \t"), chalk.bold.yellow(x))
        print(chalk.black("Operation:\t"), chalk.blue_bright(operand))
        print(chalk.black("y:        \t"), chalk.bold.yellow(y))
        print(chalk.black("Answer:   \t"), chalk.bold.green(answer))
    else:
        flag = re.search("flag{.*", string).group(0)
        print(chalk.bold("Flag =     \t"), chalk.green(flag))


target = remote(DOMAIN, 1236)
target.recvuntil(START_TRIGGER)
target.send(f"{USER_ID}\n")
target.recvuntil(NEXT_TRIGGER)

calculate()

while target.recvline() == FLAG_TRIGGER:
    calculate()
