import time
import uuid
from typing import Self, Union

import click
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from chrome import Chrome
from console import console
from facebook import cli
from functions import save_cookies
from logger import logger


class Login(Chrome):
    def __init__(self: Self, **kwargs) -> None:
        super().__init__(**kwargs)

    @staticmethod
    def preform_automatically_login(
        driver: WebDriver,
        username: str,
        password: str,
    ) -> Union[None, bool]:
        # Open Facebook login page
        driver.get("https://www.facebook.com/login")

        try:
            # Locate email, password fields, and login button
            email_field = driver.find_element(By.ID, "email")
            password_field = driver.find_element(By.ID, "pass")
            login_button = driver.find_element(By.NAME, "login")

            # Enter login credentials
            email_field.send_keys(username)
            password_field.send_keys(password)

            # Submit login form
            login_button.click()
            time.sleep(5)
            # Check if there is an element that indicates successful login, e.g., Facebook home button
            try:
                driver.find_element(
                    By.XPATH, "//*[contains(@href, 'https://www.facebook.com/')]"
                )

                logger.success(
                    f"Login <b><g>successful</g></b> for user: <b>{username!r}</b>"
                )

                return True  # Login was successful
            except NoSuchElementException:
                logger.error(
                    f"Login <r><b>failed</b></r> for user: <b>{username!r}</b>"
                )
                return False  # Login failed (possibly due to wrong credentials)
        except (NoSuchElementException, TimeoutException):
            # Handle case where login page elements couldn't be found
            return False

    def login(
        self: Self,
        username: Union[None, str] = None,
        password: Union[None, str] = None,
    ) -> bool:
        # Open Facebook login page
        self.driver.get("https://www.facebook.com/login")

        if username and password:
            try:
                # Locate email, password fields, and login button
                email_field = self.driver.find_element(By.ID, "email")
                password_field = self.driver.find_element(By.ID, "pass")
                login_button = self.driver.find_element(By.NAME, "login")

                # Enter login credentials
                email_field.send_keys(username)
                password_field.send_keys(password)

                # Submit login form
                login_button.click()

                # Wait for page to load and check if login was successful
                time.sleep(
                    5
                )  # You can also use WebDriverWait for a more robust solution

                input("Press Enter to continue!")

                # Check if there is an element that indicates successful login, e.g., Facebook home button
                try:
                    self.driver.find_element(
                        By.XPATH, "//*[contains(@href, 'https://www.facebook.com/')]"
                    )

                    logger.success(
                        f"Login <b><g>successful</g></b> for user: <b>{username!r}</b>"
                    )

                    console.input(
                        "Press Enter to continue and save cookies as a .pkl file."
                    )

                    save_cookies(self.driver, f"{username}-{uuid.uuid4()}")

                    return True  # Login was successful
                except NoSuchElementException:
                    logger.error(
                        f"Login <r><b>failed</b></r> for user: <b>{username!r}</b>"
                    )
                    return False  # Login failed (possibly due to wrong credentials)
            except (NoSuchElementException, TimeoutException) as _:
                # Handle case where login page elements couldn't be found
                return False
        else:
            # If no username and password are provided, prompt for manual login
            logger.info("Please perform manual login in the browser.")

            console.input(
                "Press Enter to continue after you have manually logged in..."
            )

            # Check if login was successful after manual intervention
            try:
                self.driver.find_element(
                    By.XPATH, "//*[contains(@href, 'https://www.facebook.com/')]"
                )

                logger.success(
                    f"Login <b><g>successful</g></b> for user: <b>{username!r}</b>"
                )

                console.input(
                    "Press Enter to continue and save cookies as a .pkl file."
                )

                save_cookies(self.driver, f"{uuid.uuid4()}")

                return True  # Manual login was successful
            except NoSuchElementException:
                logger.error(
                    f"Login <r><b>failed</b></r> for user: <b>{username!r}</b>"
                )

                return False  # Manual login failed or not completed


@cli.command()
@click.option(
    "-U",
    "--username",
    type=str,
    help="The username or email address for Facebook login. [Optional]",
)
@click.option(
    "-P",
    "--password",
    type=str,
    help="The password associated with the Facebook account. [Optional]",
)
@click.pass_context
def login(
    ctx: click.core.Context,
    username: Union[None, str],
    password: Union[None, str],
) -> None:
    login: Login = Login(**ctx.parent.params if ctx.parent else {})

    login.login(username, password)


if __name__ == "__main__":
    cli()
