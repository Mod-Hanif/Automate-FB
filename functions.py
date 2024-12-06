import pickle
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from typing import Any, Dict, List, Literal, Tuple, Union

import requests
from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageDraw, ImageFont
from selenium import webdriver
from stem import Signal
from stem.control import Controller

from const import (EMAIL_DEST, GMAIL_PASSWORD, GMAIL_USERNAME,
                   TOR_CONTROL_PORT, TOR_PASSWORD)
from logger import logger


def get_ip(proxies: Union[Dict[str, str], None] = None) -> Union[str, None]:
    response = requests.get("https://api.ipify.org?format=json", proxies=proxies)
    if response.status_code == 200:
        data = response.json()
        return data.get("ip")


def renew_ip(proxies: Union[Dict[str, str], None] = None) -> Union[str, None]:
    current_ip = get_ip(proxies)
    with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
        controller.authenticate(password=TOR_PASSWORD)
        controller.signal(Signal.NEWNYM)

    new_ip = get_ip(proxies)
    if new_ip and current_ip != new_ip:
        logger.success(
            f"A new IP address (<b><c>{new_ip}</c></b>)  was  <b><g>successfully</g></b>"
            " assigned by the Tor network.  The  current circuit has been refreshed, and"
            "traffic will now be routed  through a  new  exit node to ensure anonymity. "
            "The <b>change</b> was <b><g>completed</g></b> without <b><r>errors</r></b>."
        )

        return new_ip

    logger.error(
        "<b><r>Failed</r></b> to assign a new IP address through the Tor network. The attempt to "
        "refresh the current circuit and  obtain a new exit node was unsuccessfully. Please check"
        " the Tor service, control port  settings, or network connectivity for potential  issues."
    )


def send_email(
    subject: str,
    cols: List[str],
    rows: List[List[Any]],
    dest: str = EMAIL_DEST,
) -> bool:
    try:
        # Set up the Jinja2 environment
        env = Environment(loader=FileSystemLoader("./templates/"))
        template = env.get_template("base.html")

        # Render the HTML template with the provided data
        html_content = template.render(title=subject, cols=cols, rows=rows)

        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USERNAME
        msg["To"] = dest
        msg["Subject"] = subject

        # Attach the message body
        msg.attach(MIMEText(html_content, "html"))

        # Set up the SMTP server
        s = smtplib.SMTP("smtp.gmail.com", 587)
        s.starttls()
        s.login(GMAIL_USERNAME, GMAIL_PASSWORD)

        # Send the email
        s.send_message(msg)
        s.quit()

        logger.success(
            f"Email sent <green>successfully</green> to <bold>{dest!r}</bold>."
        )

        return True
    except Exception as e:
        logger.error(f"<r><b>ERROR</b></r>: <b><i>{e}</i></b>")

    return False


def get_comments() -> Union[List[str], None]:
    comments: Union[List[str], None] = None
    with open("comments.txt", "rt", encoding="UTF-8") as f:
        comments = [line.strip() for line in f.readlines()]
    random.shuffle(comments)

    return comments


def save_cookies(driver: webdriver.Chrome, filename: str) -> None:
    """
    Static method to save cookies from the current browser session after a successful login.

    Parameters:
    -----------
    driver : webdriver.Chrome
        The Selenium Chrome WebDriver instance from which cookies will be saved.

    Returns:
    --------
    None :
        Saves the cookies to a `.pkl` file in the 'pkl' directory with a unique filename.
    """
    # Save cookies after successful login
    pickle.dump(
        driver.get_cookies(),
        open(f"pkl/{filename}.pkl", "wb"),
    )


def load_cookies(driver: webdriver.Chrome, cookie_file: str) -> None:
    """
    Load cookies from a specified .pkl file into the Selenium WebDriver.

    Parameters:
    -----------
    driver : webdriver.Chrome
        The Selenium Chrome WebDriver instance into which cookies will be loaded.
    cookie_file : str
        The path to the .pkl file containing the cookies to be loaded.

    Returns:
    --------
    None
    """
    # Info: Starting cookie management process
    logger.info("Starting the process to load and add cookies (file: {cookie_file}).")

    # Remove all current cookies
    driver.delete_all_cookies()
    logger.info("All existing cookies have been deleted from the driver.")

    # Load cookies from the .pkl file
    with open(cookie_file, "rb") as f:
        cookies = pickle.load(f)
        logger.success(f"Cookie file successfully loaded (<b>{cookie_file!r}</b>)!")
        for cookie in cookies:
            driver.add_cookie(cookie)

    # Success: Cookies have been loaded and added
    logger.success(
        "Cookies have been <g>successfully</g> loaded from the file and added to the driver."
    )


def download_file(url, save_path):
    """
    Download a file from the specified URL and save it to the given path.

    Parameters:
    - url (str): The URL of the file to download.
    - save_path (str): The local path where the file should be saved.
    """
    try:
        # Send a GET request to the server
        response = requests.get(url, stream=True)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Open the file in write-binary mode and save the content
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(
                    chunk_size=1024
                ):  # Download in chunks
                    if chunk:
                        file.write(chunk)
            logger.success(f"File downloaded successfully and saved to {save_path}")
        else:
            logger.error(
                f"Failed to download the file. Status code: {response.status_code}"
            )

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")


def edit_image(
    image: bytes,
    text: str,
    font_path: str,
    size: int,
    position: Tuple[int, int],
    text_color: Tuple[int, int, int],
    format: Literal["PNG", "JPEG"] = "PNG",
) -> bytes:
    # Open the image
    img = Image.open(BytesIO(image))

    # Create an ImageDraw object to draw on the image
    draw = ImageDraw.Draw(img)

    # Define the font (using a custom bold font at 128px size)
    font = ImageFont.truetype(font_path, size=size)

    # Add text to the image
    draw.text(position, text, font=font, fill=text_color)

    # Create a BytesIO object to hold the binary data
    img_bytes = BytesIO()

    # Save the image to the BytesIO object in a specific format (e.g., PNG, JPEG)
    img.save(img_bytes, format=format)

    # Get the binary data from the BytesIO object
    img_bytes = img_bytes.getvalue()

    return img_bytes
