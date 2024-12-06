import asyncio
import os
import pickle
import random
import re
import threading
import time
import uuid
from typing import Callable, Dict, List, Literal, Self, Union

import click
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from telegram import InputMediaPhoto
from urllib3.exceptions import ReadTimeoutError

from chrome import Chrome
from console import console
from const import FONARTO_XT_PATH, TELEGRAM_BOT_API_TOKEN
from facebook import Facebook, cli
from functions import edit_image, get_comments
from logger import logger
from login import Login
from main import main as main_func
from telegram_bot import TelegramBot

# call the main function which imported from another module called `main.py`
main_func()


class Account(Facebook, Chrome):
    def __init__(
        self: Self,
        cookie_file: str,
        credentials: Union[Dict[Literal["username", "password"], str], None],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.cookie_file: str = cookie_file
        self.credentials: Union[Dict[Literal["username", "password"], str], None] = (
            credentials
        )
        self.telegram_bot: TelegramBot = TelegramBot(TELEGRAM_BOT_API_TOKEN)

    def __enter__(self: Self) -> Union[Self, None]:
        """
        Opens a Facebook session and loads stored cookies for authentication.

        This method loads the Facebook homepage, injects cookies for user login, and refreshes the page.
        If login is successful, it initializes the report for tracking user actions.

        Returns:
        --------
        Union[Self, None]
            Returns the bot instance if the login is successful; otherwise, None.
        """
        self.driver.get("https://facebook.com")
        time.sleep(5)

        cookies = pickle.load(open(self.cookie_file, "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)

        self.driver.refresh()

        if not (is_logged_in := self.is_logged_in) and self.credentials is not None:
            username: Union[str, None] = self.credentials.get(
                "username"
            )  # get username from credentials dictionary
            password: Union[str, None] = self.credentials.get(
                "password"
            )  # get password from credentials dictionary

            if username and password:  # validate username and password
                # Perform automatically login using the Login static method
                is_logged_in = Login.preform_automatically_login(
                    self.driver, username, password
                )

        if is_logged_in and self.username:
            Facebook.report.setdefault(
                f"{self.username}",
                {
                    "share": 0,
                    "like": 0,
                    "comment": 0,
                    "friend-requests": 0,
                },
            )

            return self

    def __exit__(self: Self, exc_type, exc_value, traceback) -> None:
        """
        Cleans up the session by deleting cookies and quitting the WebDriver.

        This method is called automatically when exiting the context. It deletes all cookies from
        the session and closes the browser.

        Parameters:
        -----------
        exc_type : Exception type
            The exception type if an error occurred during the session, otherwise None.

        exc_value : Exception value
            The exception value if an error occurred during the session, otherwise None.

        traceback : Traceback
            The traceback object if an error occurred during the session, otherwise None.

        Returns:
        --------
        None
        """
        self.driver.delete_all_cookies()
        self.driver.quit()

    def scroll_into_view(self: Self, element: WebElement) -> None:
        """
        Scrolls a specified WebElement into view within the browser window.

        This function leverages JavaScript to smoothly scroll the element into view.
        It centers the element vertically and aligns it horizontally based on its
        closest scrollable ancestor.

        Parameters:
        ----------
        element : WebElement
            The web element to be scrolled into view.

        Returns:
        -------
        None
            This function does not return any value.

        Example:
        -------
        ```python
        element = driver.find_element(By.ID, "targetElement")
        scroll_into_view(self, element)
        ```
        """
        self.driver.execute_script(
            """
            const element = arguments[0];

            element.scrollIntoView({
              behavior: 'smooth',
              block: 'center',
              inline: 'nearest'
            });
            """,
            element,
        )

        time.sleep(1)

    @property
    def is_logged_in(self: Self) -> bool:
        """
        Check if the user is logged into Facebook.

        This property accesses the Facebook homepage and checks for the presence of
        an element that indicates the user is logged in. It looks for the profile
        section of the page, which is only visible when a user is authenticated.

        Returns:
        -------
        bool
            True if the user is logged in (i.e., the profile element is found),
            False otherwise.
        """
        if (url := "https://www.facebook.com") != self.driver.current_url:
            self.driver.get(url)
            time.sleep(5)

        try:
            # Example: Check for the presence of the profile picture or the user's name
            self.driver.find_element(By.XPATH, "//div[@aria-label='Your profile']")
            logger.info("User is logged in.")

            return True
        except Exception:
            logger.info("User is not logged in.")

            return False

    @property
    def username(self: Self) -> Union[str, None]:
        """
        Retrieve the username of the logged-in Facebook user.

        This property accesses the Facebook homepage and attempts to locate the
        username by finding the link in the shortcuts section. If successful,
        it returns the username extracted from the link. If unsuccessful,
        it logs an error and returns None.

        Returns:
        -------
        Union[str, None]
            The username of the logged-in user if found; otherwise, None.
        """

        if hasattr(self, "_username"):
            return self._username

        self.driver.get("https://facebook.com")
        time.sleep(5)

        try:
            link = self.driver.find_element(
                By.XPATH, '//div[@aria-label="Shortcuts"]//a'
            )
            if href := link.get_dom_attribute("href"):
                username = href.split("/").pop()
                logger.info(
                    f"Successfully retrieved the user <b>{username!r}</b> information."
                )
                self._username = username
                return username

        except Exception:
            logger.error("<r>Unable</r> to retrieve username!")

        return None

    @property
    def facebook_element(self: Self) -> WebElement:
        """
        Retrieves the Facebook element by its unique ID.

        Returns:
            WebElement: The web element located by its ID, "facebook",
                        enabling interaction or further manipulation.
        """
        return self.driver.find_element(By.ID, "facebook")

    def get_screenshot(
        self: Self,
        url: str,
        callback_func: Union[None, Callable] = None,
        timeout: int = 5,
        /,
        **kwargs,
    ) -> Union[None, bytes]:
        self.driver.get(url)
        time.sleep(5)

        if callback_func:
            callback_func(**kwargs)

        try:
            return self.driver.get_screenshot_as_png()
        except Exception:
            if timeout > 0:
                time.sleep(5)
                return self.get_screenshot(url, callback_func, timeout - 1)

    def get_screenshot_as_file(
        self: Self,
        url: str,
        callback_fun: Union[None, Callable] = None,
        *args,
        **kwargs,
    ) -> str:
        with open(path := f"/tmp/{uuid.uuid4()}.png", mode="wb") as file:
            screenshot = self.get_screenshot(url, callback_fun, *args, **kwargs)
            if screenshot:
                file.write(screenshot)

        return path

    def get_last_post_url(
        self: Self, page_url: str, timeout: int = 5
    ) -> Union[str, None]:
        if self.driver.current_url != page_url:
            self.driver.get(page_url)
            self.infinite_scroll(scroll_limit=2, delay=2.5)
            time.sleep(5)

        self.driver.execute_script(
            """
            const facebookElement = document.querySelector('#facebook');

            facebookElement.addEventListener("copy", (event) => {
                let value = event.target.value;

                let postLinkElement = document.createElement("post-link");
                postLinkElement.innerHTML = value;

                facebookElement.append(postLinkElement);
            });
            """
        )

        try:
            try:
                copy_button = self.driver.find_element(
                    By.XPATH,
                    "//span[contains(text(), 'Copy')]/ancestor::*[@role='button']",
                )
                self.scroll_into_view(copy_button)
                copy_button.click()
                time.sleep(5)

            except Exception as _:
                # Find the first "Share" button on the page
                share_button = self.driver.find_element(
                    By.XPATH,
                    "//div[@aria-label='Send this to friends or post it on your profile.'][@role='button']",
                )
                self.scroll_into_view(share_button)
                share_button.click()
                time.sleep(5)

                copy_link_button = self.driver.find_element(
                    By.XPATH,
                    "//div[@role='dialog']//span[contains(text(), 'Copy link')]/ancestor::*[@role='button']",
                )
                copy_link_button.click()
                time.sleep(5)

            link = self.driver.find_element(
                By.TAG_NAME,
                "post-link",
            ).text

            if link:
                logger.success(
                    f"User <b>{self.username!r}</b> - Successfully the last post link ({link}) retrieved."
                )

                return link

        except Exception as _:
            pass

        logger.error(
            f"User <b>{self.username!r}</b> - <r>Unable</r> to get the last post link."
        )

        return self.get_last_post_url(page_url, timeout - 1) if timeout > 0 else None

    def share(
        self: Self, post_url: str, groups: List[str], count: int, timeout: int = 5
    ) -> None:
        self.driver.get(post_url)
        time.sleep(5)

        prefix: str = self.get_selectors_prefix()

        try:
            for group in groups:
                for _ in range(count // len(groups)):
                    share_count: int = 0
                    if self.username:
                        share_count = Facebook.report[self.username]["share"]

                    if share_count >= count:
                        logger.success(
                            f"User <b>{self.username!r}</b> - <g>Successfully</g> the sharing process completed!"
                        )
                        return

                    logger.info(
                        f"User <b>{self.username!r}</b> - Preparing to share the last post... (Attempt <c>{share_count+1}</c> of <c>{count}</c>)"
                    )

                    # Find the first "Share" button on the page
                    share_button = self.driver.find_element(
                        By.XPATH,
                        f"{prefix}//span[contains(text(), 'Share')]/ancestor::*[@role='button']",
                    )
                    self.scroll_into_view(share_button)
                    share_button.click()
                    time.sleep(2.5)

                    # Select the "Share to a Group" option
                    share_to_group_button = self.driver.find_element(
                        By.XPATH,
                        f"{prefix}//span[contains(text(), 'Group')]/ancestor::*[@role='button']",
                    )
                    share_to_group_button.click()
                    time.sleep(2.5)

                    search_input = self.driver.find_element(
                        By.XPATH,
                        f'{prefix}//input[@placeholder="Search for groups"]',
                    )
                    search_input.send_keys(group)
                    time.sleep(2.5)

                    group_elem = self.driver.find_element(
                        By.XPATH,
                        f"{prefix}//span[contains(text(), '{group}')]/ancestor::*[@role='button']",
                    )
                    group_elem.click()
                    time.sleep(2.5)

                    post_button = self.driver.find_element(
                        By.XPATH, f"{prefix}//div[@aria-label='Post']"
                    )
                    post_button.click()

                    for _ in range(15):
                        try:
                            self.driver.find_element(
                                By.XPATH,
                                "//span[contains(text(), 'Shared to your group.')]",
                            )
                            logger.success(
                                f"User <b>{self.username!r}</b> - The post was <b><g>successfully</g></b> shared in the group <b>{group!r}</b>."
                            )

                            if self.username:
                                # Increment share count in report
                                Facebook.report[self.username]["share"] += 1

                            break
                        except Exception as _:
                            try:
                                self.driver.find_element(
                                    By.XPATH,
                                    "//span[contains(text(), 'Something went wrong. Please try again.')]",
                                )

                                logger.warning(
                                    f"User <b>{self.username!r}</b> - You"
                                    " <r>can not</r> <b>share</b> the post right now!"
                                )

                                return
                            except Exception as _:
                                pass

                        time.sleep(0.512)

                    try:
                        spans = self.driver.find_elements(
                            By.XPATH,
                            "//div[@role='dialog']//span",
                        )

                        for span in spans:
                            if (
                                "You Can't Use This Feature Right Now" in span.text
                                or "You can't use this feature at the moment"
                                in span.text
                            ):
                                logger.warning(
                                    f"User <b>{self.username!r}</b> - You"
                                    " <r>can not</r> <b>share</b> the post right now!"
                                )

                                return

                    except Exception as _:
                        pass

        except Exception as _:
            logger.error(
                f"User <b>{self.username!r}</b> - An <r>error</r> occurred during sharing the post!"
            )
            logger.info(
                f"User <b>{self.username!r}</b> - <b>Retrying</b> to share the post."
            )

            if timeout > 0:
                return self.share(
                    post_url,
                    groups,
                    count,
                    timeout - 1,
                )

    def comment(self: Self, post_url: str, count: int = 50, timeout: int = 5) -> None:
        self.driver.get(post_url)
        time.sleep(5)

        # Retrieve comments random comments
        if comments := get_comments():
            try:
                prefix: str = self.get_selectors_prefix()

                textbox: WebElement = self.driver.find_element(
                    By.XPATH,
                    f'{prefix}//div[@aria-label="Write a comment…" or contains(@aria-label, "Comment as") and @role="textbox"]',
                )

                textbox.click()

                for _ in range(count):
                    comment_count: int = 0
                    if self.username:
                        comment_count = Facebook.report[self.username]["comment"]

                    if comment_count >= count:
                        logger.info(
                            f"User <b>{self.username!r}</b> - <b>Completed</b> commenting process."
                        )
                        return

                    textbox.send_keys(text := random.choice(comments))
                    time.sleep(random.random())

                    textbox.send_keys(Keys.ENTER)

                    while True:
                        try:
                            self.driver.find_element(
                                By.XPATH,
                                "//span[contains(text(), 'Posting...')]",
                            )
                            time.sleep(0.512)
                            continue

                        except Exception as _:
                            try:
                                self.driver.find_element(
                                    By.XPATH,
                                    "//span[contains(text(), 'Unable to post comment.')]",
                                )

                                logger.warning(
                                    f"User <b>{self.username!r}</b> - You <r>can not</r> write <b>comments</b> right now!"
                                )
                                return

                            except Exception as _:
                                logger.success(
                                    f"User <b>{self.username!r}</b> - <g>Successfully</g> posted comment {comment_count+1}/{count}: <b>{text!r}</b>"
                                )

                                if self.username:
                                    # Increment comment count in report
                                    Facebook.report[self.username]["comment"] += 1

                                break

                    time.sleep(1.5 + random.random())

                    try:
                        spans = self.driver.find_elements(
                            By.XPATH,
                            "//div[@role='dialog']//span",
                        )

                        for span in spans:
                            if (
                                "You Can't Use This Feature Right Now" in span.text
                                or "You can't use this feature at the moment"
                                in span.text
                            ):
                                logger.warning(
                                    f"User <b>{self.username!r}</b> - You <r>can not</r> write <b>comments</b> right now!"
                                )
                                return

                    except Exception as _:
                        pass

            except Exception as _:
                logger.error(
                    f"User <b>{self.username!r}</b> - <r>Failed</r> to locate or interact with comment textbox."
                )
                if timeout > 0:
                    return self.comment(post_url, count, timeout - 1)

        else:
            logger.error("<r>No</r> comments available to post.")

    def like(self: Self, page_url: str, timeout: int = 5) -> Union[bool, None]:
        pass

    def send_friend_request(self: Self, count: int = 100) -> None:
        self.driver.get("https://www.facebook.com/friends")
        time.sleep(5)

        def send_request():
            try:
                friends_element: WebElement = self.driver.find_element(
                    By.XPATH,
                    "//div[@aria-label='Friends' and @role='main']",
                )
                list_element: WebElement = friends_element.find_element(
                    By.XPATH,
                    "//div[@role='list']",
                )
                suggestions: List[WebElement] = list_element.find_elements(
                    By.XPATH,
                    "//div[@role='listitem']",
                )

                for suggestion in suggestions:
                    requests_count: Union[int, None] = None
                    if self.username:
                        requests_count = Facebook.report[self.username][
                            "friend-requests"
                        ]

                    if requests_count is not None:
                        if self.username:
                            if (
                                Facebook.report[self.username]["friend-requests"]
                                >= count
                            ):
                                logger.success(
                                    f"User <b>{self.username}</b> - The sending friend requests process completed!"
                                )
                                return True
                        try:
                            self.scroll_into_view(suggestion)

                            add_friend_button = suggestion.find_element(
                                By.XPATH,
                                "//div[@aria-label='Add friend' and @role='button']",
                            )
                            self.scroll_into_view(add_friend_button)
                            add_friend_button.click()
                            time.sleep(2.5)

                            try:
                                suggestion.find_element(
                                    By.XPATH, "//span[contains(text(), 'Request sent')]"
                                )

                                if self.username:
                                    Facebook.report[self.username][
                                        "friend-requests"
                                    ] += 1

                                logger.success(
                                    f"User <b>{self.username}</b> - Request <g>successfully</g> sent. [<c>{requests_count + 1}</c> of <c>{count}</c>]"
                                )

                            except Exception:
                                logger.warning(
                                    f"User <b>{self.username}</b> - The request <y>was not</y> sent successfully."
                                )

                            try:
                                spans = self.driver.find_elements(
                                    By.XPATH,
                                    "//div[@role='dialog']//span",
                                )

                                for span in spans:
                                    if (
                                        "You Can't Use This Feature Right Now"
                                        in span.text
                                        or "You can't use this feature at the moment"
                                        in span.text
                                    ):
                                        logger.warning(
                                            f"User <b>{self.username!r}</b> - You <r>can not</r> send friend requests right now!"
                                        )
                                        return False

                            except Exception:
                                pass

                        except Exception:
                            pass

                    else:
                        return False

            except Exception:
                logger.error(
                    f"User <b>{self.username}</b> - An error occurred during sending friend requests."
                )

        self.infinite_scroll(
            element=self.facebook_element,
            delay=2.5,
            callback=send_request,
        )

    def invite(self: Self, page_url: str, timeout: int = 5) -> None:
        self.driver.get(page_url)
        time.sleep(5)

        try:
            more_options_button: WebElement = self.driver.find_element(
                By.XPATH, "//div[@aria-label='See options' and @role='button']"
            )
            self.scroll_into_view(more_options_button)
            more_options_button.click()
            time.sleep(2.5)

            invite_friends_button: WebElement = self.driver.find_element(
                By.XPATH,
                "//span[contains(text(), 'Invite friends')]/ancestor::div[@role='menuitem']",
            )
            self.scroll_into_view(invite_friends_button)
            invite_friends_button.click()
            time.sleep(5)

            try:
                self.driver.find_element(
                    By.XPATH,
                    "//span[contains(text(), 'No Friends To Invite')]",
                )

                logger.warning(
                    f"User <b>{self.username}</b> - No <b>Friends</b> To Invite."
                )

                return
            except Exception:
                try:
                    select_all_button: WebElement = self.driver.find_element(
                        By.XPATH,
                        "//div[contains(@aria-label, 'Select All')][@role='button']",
                    )
                    select_all_button.click()
                    time.sleep(2.5)

                    send_invite_button: WebElement = self.driver.find_element(
                        By.XPATH,
                        "//div[@aria-label='Send Invites' and @role='button']",
                    )
                    send_invite_button.click()

                    for _ in range(10):
                        try:
                            self.driver.find_element(
                                By.XPATH, "//span[contains(text(), 'Invites sent')]"
                            )

                            logger.success(
                                f"User <b>{self.username}</b> - Invites <g>successfully</g> sent."
                            )

                            return
                        except Exception:
                            pass

                        time.sleep(0.512)
                    else:
                        logger.warning(
                            f"User <b>{self.username}</b> - Invites may have <y>failed</y> to send."
                        )

                except Exception:
                    logger.warning(
                        f"User <b>{self.username}</b> - The <b>'Select All'</b> button was not found!"
                    )

                    # Try another way

        except Exception:
            logger.error(
                f"User <b>{self.username}</b> - An error occurred while sending invites. Retrying (<c>{timeout}</c> remaining)."
            )

            if timeout > 0:
                return self.invite(page_url, timeout - 1)

    def get_selectors_prefix(self: Self, post_url: Union[str, None] = None) -> str:

        if post_url is not None:
            self.driver.get(post_url)
            time.sleep(5)

        try:
            self.driver.find_element(
                By.XPATH,
                "//div[@role='dialog']//span[contains(text(), 'Share')]/ancestor::*[@role='button']",
            )
            logger.info(f"User <b>{self.username}</b> - Dialog Found!")

            return "//div[@role='dialog']"
        except Exception as _:
            logger.warning(f"User <b>{self.username}</b> - Dialog Not Found!")

            return ""

    def start(
        self: Self,
        *,
        page_url: str,
        username: Union[None, str] = None,
        groups: Union[None, List[str]] = None,
        like_count: int = 50,
        comment_count: int = 50,
        share_count: int = 5,
        friend_request_count: int = 50,
        send_invites: bool = False,
        telegram_id: Union[int, None] = None,
    ):
        if username and username != self.username:
            return

        if post_url := self.get_last_post_url(page_url):
            prefix: str = self.get_selectors_prefix(post_url)

            def func():
                share_button = self.driver.find_element(
                    By.XPATH,
                    f"{prefix}//span[contains(text(), 'Share')]/ancestor::*[@role='button']",
                )
                self.scroll_into_view(share_button)
                logger.success(
                    f"User <b>{self.username}</b> has scrolled to the information section."
                )
                time.sleep(2.5)

            screenshots: List[bytes] = []

            if before_screenshot := self.get_screenshot(post_url, func):
                before = edit_image(
                    before_screenshot,
                    text="Before",
                    font_path=FONARTO_XT_PATH,
                    size=128,
                    position=(50, 25),
                    text_color=(255, 0, 0),
                )

                screenshots.append(before)

            if share_count > 0 and groups:
                self.share(post_url, groups, share_count)

            if comment_count > 0:
                self.comment(post_url, comment_count)

            if like_count > 0:
                pass

            if send_invites:
                self.invite(page_url)

            if friend_request_count > 0:
                self.send_friend_request(friend_request_count)

            like = comment = share = friend_requests = None
            if self.username:
                like = Facebook.report[self.username]["like"]
                comment = Facebook.report[self.username]["comment"]
                share = Facebook.report[self.username]["share"]
                friend_requests = Facebook.report[self.username]["friend-requests"]

            if after_screenshot := self.get_screenshot(post_url, func):
                after = edit_image(
                    after_screenshot,
                    text="After",
                    font_path=FONARTO_XT_PATH,
                    size=128,
                    position=(50, 25),
                    text_color=(255, 0, 0),
                )

                screenshots.append(after)

            caption: str = "\n".join(
                [
                    "Before and After Sharing the Facebook Post in Groups and Commenting.",
                    f"Username: {self.username}",
                    f"Page URL: {page_url}",
                    f"Post URL: {post_url}",
                    f"Like: {like}",
                    f"Comment: {comment}",
                    f"Share: {share}",
                    f"Friend Requests: {friend_requests}",
                ]
            )

            photos: List[InputMediaPhoto] = [
                InputMediaPhoto(photo, caption=caption if not index else None)
                for index, photo in enumerate(screenshots)
            ]

            asyncio.run(self.telegram_bot.send_photos(*photos, chat_id=telegram_id))

    def infinite_scroll(
        self: Self,
        element: Union[WebElement, None] = None,
        delay: float = 5,
        scroll_limit: Union[None, int] = None,
        callback: Union[Callable, None] = None,
        *args,
        **kwargs,
    ) -> None:
        """
        Scrolls down a specified web element to load additional content up to a specified limit.

        This method automatically scrolls to the bottom of the provided web element and waits
        for new content to load. It continues scrolling until either the specified number of
        scrolls is reached or no new content is detected.

        Parameters:
        -----------
        element: Union[WebElement, None], optional
            The specific web element to scroll. If not provided, the method defaults to
            finding the Facebook main element by its ID. This should be an instance of a
            Selenium WebElement that contains scrollable content.

        delay: float, optional
            The time to wait (in seconds) after each scroll before checking for new content.
            Default is 5 seconds.

        scroll_limit: Union[None, int], optional
            The maximum number of scrolls to perform. If set to None, the method will continue
            scrolling until no more new content is loaded. Default is None.

        callback: Union[Callable, None], optional
            A function to be executed after each successful scroll. This can be used to perform
            actions such as logging the number of items loaded or any other processing. Default is None.

        *args:
            Additional positional arguments to pass to the callback function.

        **kwargs:
            Additional keyword arguments to pass to the callback function.

        Returns:
        --------
        None
            This method does not return any value. It performs scrolling actions on the specified
            web element and may execute the provided callback function.

        Raises:
        -------
        WebDriverException
            If the Selenium WebDriver encounters an issue while executing the scrolling actions
            or JavaScript commands.

        Example:
        --------
        >>> def my_callback(arg1, kwarg1=None):
        >>>     print(f"Scrolled and loaded new content! Arg1: {arg1}, Kwarg1: {kwarg1}")
        >>>
        >>> element_to_scroll = driver.find_element(By.ID, "scrollable-element-id")  # Example element
        >>> infinite_scroll(element=element_to_scroll, scroll_limit=5, callback=my_callback, "Some value", kwarg1="Some keyword value")
        """

        if not element:
            element = self.facebook_element

        last_height = self.driver.execute_script(
            "return arguments[0].scrollHeight", element
        )

        count = 0  # Initialize scroll count
        while True:
            # Scroll to the bottom of the page
            self.driver.execute_script(
                "window.scrollTo(0, arguments[0].scrollHeight);", element
            )

            # Wait for new content to load
            time.sleep(delay)  # Adjust based on your needs

            # Calculate new height and compare with the last height
            new_height = self.driver.execute_script(
                "return arguments[0].scrollHeight", element
            )
            if new_height == last_height:
                break  # Break the loop if no new content has been loaded

            # Update the last height
            last_height = new_height

            # Execute the callback function
            if callback:
                if (
                    callback(*args, **kwargs) is not None
                ):  # Call the provided callback function
                    break

            # Increment the scroll count and check against the limit
            count += 1
            if scroll_limit is not None and count >= scroll_limit:
                break  # Exit if the scroll limit is reached


def start(
    cookie_file: str,
    page_url: str,
    username: Union[None, str] = None,
    groups: Union[None, List[str]] = None,
    like_count: int = 50,
    comment_count: int = 50,
    share_count: int = 5,
    friend_request_count: int = 50,
    send_invites: bool = False,
    timeout: int = 5,
    credentials: Union[Dict[Literal["username", "password"], str], None] = None,
    telegram_id: Union[int, None] = None,
    **kwarg,
) -> None:
    try:  # handle exceptions
        with Account(
            cookie_file=cookie_file, credentials=credentials, **kwarg
        ) as account:
            if account:
                account.start(
                    page_url=page_url,
                    username=username,
                    groups=groups,
                    like_count=like_count,
                    comment_count=comment_count,
                    share_count=share_count,
                    friend_request_count=friend_request_count,
                    send_invites=send_invites,
                    telegram_id=telegram_id,
                )
    except ReadTimeoutError as err:
        logger.error(f"Read timeout occurred: <r>{err}</r>")

        if timeout > 0:
            logger.info(
                f"<y>Retrying...</y> <c>{timeout}</c> attempt(s) remaining to start the process with URL: <c>{page_url}</c>"
            )
            return start(
                cookie_file,
                page_url,
                username,
                groups,
                like_count,
                comment_count,
                share_count,
                friend_request_count,
                send_invites,
                timeout - 1,
            )


@cli.command()
@click.option(
    "--page-url",
    type=str,
    help="The URL of the page where you want to like all posts and post comments. This option is required.",
    required=True,
)
@click.option(
    "--username",
    type=str,
    help="The username of the account to be used for the operation.",
)
@click.option(
    "--groups",
    type=str,
    callback=lambda ctx, param, value: value.split(",") if value else None,
    help="Comma-separated list of group names where the post will be shared.",
)
@click.option(
    "--share-count",
    type=int,
    default=5,
    help="Number of times to share the post in groups. Default is 5.",
)
@click.option(
    "--comment-count",
    type=int,
    default=10,
    help="Number of comments to post on each post. Default is 10.",
)
@click.option(
    "--like-count",
    type=int,
    default=50,
    help="Specify the number of posts to like. Default is 50.",
)
@click.option(
    "--friend-request-count",
    type=int,
    default=50,
    help="Specify the number of friend requests to send. Default is 50.",
)
@click.option(
    "--send-invites",
    is_flag=True,
    help="Send invites when this flag is used.",
)
@click.pass_context
def main(
    ctx: click.core.Context,
    page_url: str,
    username: Union[None, str] = None,
    groups: Union[None, List[str]] = None,
    share_count: int = 5,
    comment_count: int = 50,
    like_count: int = 50,
    friend_request_count: int = 50,
    send_invites: bool = False,
) -> None:

    threads: List[threading.Thread] = []

    if os.path.exists("pkl/"):
        for pkl in os.listdir("pkl"):
            if username and not re.match(f"^{username}.*", pkl):
                continue

            threads.append(
                threading.Thread(
                    target=start,
                    kwargs=dict(
                        cookie_file=f"pkl/{pkl}",
                        page_url=page_url,
                        username=username,
                        groups=groups,
                        like_count=like_count,
                        share_count=share_count,
                        comment_count=comment_count,
                        friend_request_count=friend_request_count,
                        send_invites=send_invites,
                        **ctx.parent.params if ctx.parent else {},
                    ),
                )
            )

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    Facebook.send_report()


if __name__ == "__main__":
    cli()
