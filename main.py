from const import (
    FONARTO_REGULAR_PATH,
    FONARTO_REGULAR_URL,
    FONARTO_XT_PATH,
    FONARTO_XT_URL,
)
from functions import download_file


def main():
    download_file(FONARTO_REGULAR_URL, FONARTO_REGULAR_PATH)
    download_file(FONARTO_XT_URL, FONARTO_XT_PATH)


if __name__ == "__main__":
    main()
