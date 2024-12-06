from typing import Any, Dict, List

import click

from functions import send_email
from logger import logger
from console import console

from rich.table import Table


class Facebook:
    report: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def print_report() -> None:
        table: Table = Table(style="cyan bold")

        cols: List[str] = [
            "#",
            "Username",
            "Like",
            "Comment",
            "Share",
            "Friend Requests",
        ]

        for col in cols:
            table.add_column(col)

        rows: List[List[Any]] = []

        for index, (username, data) in enumerate(Facebook.report.items()):
            comment = data.get("comment")
            share = data.get("share")
            like = data.get("like")
            friend_requests = data.get("friend-requests")

            row: List[Any] = []

            row.append(index + 1)
            row.append(username)
            row.append(like)
            row.append(comment)
            row.append(share)
            row.append(friend_requests)

            rows.append(list(map(str, row)))

        for row in rows:
            table.add_row(*row)

        console.print(table)

    @staticmethod
    def send_report():
        if Facebook.report:
            cols: List[str] = [
                "#",
                "Username",
                "Like",
                "Comment",
                "Share",
                "Friend Requests",
            ]
            rows: List[List[Any]] = []

            for index, (username, data) in enumerate(Facebook.report.items()):
                comment = data.get("comment")
                share = data.get("share")
                like = data.get("like")
                friend_requests = data.get("friend-requests")

                row = [
                    index + 1,
                    username,
                    like,
                    comment,
                    share,
                    friend_requests,
                ]
                rows.append(row)

            send_email("Automate - Facebook", cols=cols, rows=rows)


@click.group()
@click.option(
    "--headless",
    is_flag=True,
    help="Run Chrome in headless mode (without a UI).",
)
@click.option(
    "--disable-gpu",
    is_flag=True,
    help="Disable GPU hardware acceleration.",
)
@click.option(
    "--disable-infobars",
    is_flag=True,
    help="Prevent Chrome from showing infobars.",
)
@click.option(
    "--disable-extensions",
    is_flag=True,
    help="Disable all Chrome extensions.",
)
@click.option(
    "--start-maximized",
    is_flag=True,
    help="Start Chrome with the window maximized.",
)
@click.option(
    "--block-notifications",
    is_flag=True,
    help="Block browser notifications from appearing.",
)
@click.option(
    "--no-sandbox",
    is_flag=True,
    help="Disable the sandbox for all running processes. This is useful when running Chrome in environments that do not support sandboxing, such as certain CI/CD systems or containerized environments.",
)
@click.option(
    "--incognito",
    is_flag=True,
    help="Open in incognito mode.",
)
@click.option(
    "--tor",
    is_flag=True,
    help="Use Tor anonymity network.",
)
def cli(
    headless: bool,
    disable_gpu: bool,
    disable_infobars: bool,
    disable_extensions: bool,
    start_maximized: bool,
    block_notifications: bool,
    no_sandbox: bool,
    incognito: bool,
    tor: bool,
):
    # Log the values of each parameter
    logger.info(f"Headless mode: {headless}")
    logger.info(f"Disable GPU: {disable_gpu}")
    logger.info(f"Disable infobars: {disable_infobars}")
    logger.info(f"Disable extensions: {disable_extensions}")
    logger.info(f"Start maximized: {start_maximized}")
    logger.info(f"Block notifications: {block_notifications}")
    logger.info(f"Sandbox: {no_sandbox}")
    logger.info(f"Incognito: {incognito}")
    logger.info(f"Tor: {tor}")


if __name__ == "__main__":
    cli()
