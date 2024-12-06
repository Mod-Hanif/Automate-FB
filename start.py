import os
import re
import threading
from typing import Any, Dict, List

import account
from facebook import Facebook

users: List[Dict[str, Any]] = [
    {
        "page_url": "https://www.facebook.com/CityComputerStore",
        "username": "aliabdullah.nasiri",
        "credentials": None,
        "groups": ["Math"],
        "share_count": 100,
        "comment_count": 50,
        "like_count": 0,
        "friend_request_count": 0,
        "send_invites": True,
        "telegram_id": 5906633627,
    },
    {
        "page_url": "https://www.facebook.com/profile.php?id=61554947310688",
        "username": "mohammad.hanif.nasiri.1967",
        "credentials": {
            "username": "mohammad.hanif.nasiri.1967",
            "password": "info@123",
        },
        "groups": ["Math"],
        "share_count": 100,
        "comment_count": 50,
        "like_count": 0,
        "friend_request_count": 0,
        "send_invites": False,
        "telegram_id": 5906633627,
    },
    {
        "page_url": "https://www.facebook.com/profile.php?id=100063642170837",
        "username": "hanif.nasiri.1967",
        "credentials": {
            "username": "hanif.nasiri.1967",
            "password": "info@123",
        },
        "groups": ["Math"],
        "share_count": 100,
        "comment_count": 50,
        "like_count": 0,
        "friend_request_count": 0,
        "send_invites": False,
        "telegram_id": 5906633627,
    },
    {
        "page_url": "https://www.facebook.com/PaytakhtMobile",
        "username": "ali.nasiri.20050727",
        "credentials": {
            "username": "ali.nasiri.20050727",
            "password": "info@123",
        },
        "groups": ["Math"],
        "share_count": 100,
        "comment_count": 50,
        "like_count": 0,
        "friend_request_count": 0,
        "send_invites": False,
        "telegram_id": 5906633627,
    },
    {
        "page_url": "https://www.facebook.com/CityComputerStore",
        "username": "mustafa.joya.123456789",
        "credentials": {
            "username": "mustafa.joya.123456789",
            "password": "milad123456789123456789",
        },
        "groups": ["Math"],
        "share_count": 100,
        "comment_count": 50,
        "like_count": 0,
        "friend_request_count": 0,
        "send_invites": True,
        "telegram_id": None,
    },
    {
        "page_url": "https://www.facebook.com/profile.php?id=61563882952139",
        "username": "milad.noori.7860",
        "credentials": {
            "username": "milad.noori.7860",
            "password": "milad0731161624",
        },
        "groups": ["Math"],
        "share_count": 100,
        "comment_count": 50,
        "like_count": 0,
        "friend_request_count": 0,
        "send_invites": True,
        "telegram_id": None,
    },
]

files: List[str] = os.listdir("pkl/")
threads: List[threading.Thread] = []

for index, user in enumerate(users):
    for file in files:
        if re.match(f"^{user['username']}.*", file):
            threads.append(
                threading.Thread(
                    target=account.start,
                    kwargs=dict(
                        cookie_file=f"pkl/{file}",
                        credentials=user["credentials"],
                        page_url=user["page_url"],
                        username=user["username"],
                        groups=user["groups"],
                        like_count=user["like_count"],
                        comment_count=user["comment_count"],
                        share_count=user["share_count"],
                        friend_request_count=user["friend_request_count"],
                        telegram_id=user["telegram_id"],
                        **dict(
                            headless=True,
                            disable_gpu=True,
                            disable_extensions=True,
                            disable_infobars=True,
                            start_maximized=True,
                            no_sandbox=True,
                            incognito=True,
                            block_notifications=True,
                        ),
                    ),
                )
            )

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

Facebook.send_report()
