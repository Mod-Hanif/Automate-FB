import asyncio
import random
from typing import Self, Set, Tuple, Union

from telegram import Bot, PhotoSize, Update
from telegram._files.inputmedia import InputMediaPhoto
from telegram._utils.types import FileInput

from logger import logger


class TelegramBot:

    def __init__(self, token: str):

        self.token: str = token
        self.updates: Union[Tuple[Update, ...], None] = None

    async def send_message(
        self: Self, text: str, chat_id: Union[int, None] = None
    ) -> None:
        logger.info("Attempting to send message to all chat IDs.")  # Start of method

        for _chat_id in await self.chat_ids:
            if chat_id is not None and _chat_id != chat_id:
                continue

            try:
                logger.info(
                    f"Sending message to chat ID: {_chat_id}"
                )  # Info about specific chat_id
                await self.bot.send_message(_chat_id, text)  # Send the message
                logger.success(
                    f"<b>Message</b> sent <g>successfully</g> to chat ID: <c>{_chat_id}</c>"
                )  # Success
                await asyncio.sleep(2.5 + random.random())  # Throttle the requests
            except Exception as err:
                logger.error(
                    f"<r><b>Failed</b></r> to send message to chat ID: <c>{_chat_id}</c>. Error: <r><b>{err}</b></r>"
                )  # Log error
                logger.error(
                    "<y>Skipping</y> this chat ID and continuing with the next."
                )  # Info about fallback

    async def send_photo(
        self: Self,
        photo: Union[FileInput, PhotoSize],
        caption: Union[str, None] = None,
        chat_id: Union[int, None] = None,
    ) -> None:
        logger.info("Attempting to send photo to all chat IDs.")  # Start of method

        for _chat_id in await self.chat_ids:
            if chat_id is not None and _chat_id != chat_id:
                continue

            try:
                logger.info(
                    f"<b>Sending</b> photo to chat ID: <c>{_chat_id}</c>"
                )  # Info about specific chat_id
                await self.bot.send_photo(_chat_id, photo, caption)
                logger.success(
                    f"<b>Photo</b> sent <g>successfully</g> to chat ID: <c>{_chat_id}</c>"
                )  # Success
                await asyncio.sleep(2.5 + random.random())  # Throttle the requests
            except Exception as err:
                logger.error(
                    f"<r><b>Failed</b></r> to send <b>photo</b> to chat ID: <c>{_chat_id}</c>. Error: <r><b>{err}</b></r>"
                )  # Log error
                logger.error(
                    "<y>Skipping</y> this chat ID and continuing with the next."
                )  # Info about fallback

    async def send_photos(
        self: Self, *photos: InputMediaPhoto, chat_id: Union[int, None] = None
    ) -> None:
        logger.info("Attempting to send all photos to all chat IDs.")

        for _chat_id in await self.chat_ids:
            if chat_id is not None and _chat_id != chat_id:
                continue

            try:
                logger.info(
                    f"<b>Sending</b> photos to chat ID: <c>{_chat_id}</c>"
                )  # info about specific chat_id

                await self.bot.send_media_group(_chat_id, photos)

                logger.success(
                    f"<b>Photos</b> sent <g>successfully</g> to chat ID: <c>{_chat_id}</c>"
                )  # Success
                await asyncio.sleep(2.5 + random.random())  # Throttle the requests
            except Exception as err:
                logger.error(
                    f"<r><b>Failed</b></r> to send <b>photos</b> to chat ID: <c>{_chat_id}</c>. Error: <r><b>{err}</b></r>"
                )  # Log error
                logger.error(
                    "<y>Skipping</y> this chat ID and continuing with the next."
                )  # Info about fallback

    async def get_updates(
        self: Self, timeout: int = 5
    ) -> Union[Tuple[Update, ...], None]:

        if self.updates:
            return self.updates

        try:
            updates = self.updates = await self.bot.get_updates()
            logger.success("<g>Successfully</g> updates retrieved.")

            if len(updates) > 0:
                logger.info(f"<b>{len(updates)}</b> update(s) retrieved and processed.")
            else:
                logger.warning("<r>No</r> updates retrieved.")

            return updates

        except Exception as _:
            logger.error("<r>Failed</r> to get updates!")

            if timeout > 0:
                await asyncio.sleep(5 + random.random())
                return await self.get_updates(timeout - 1)

    @property
    async def chat_ids(self: Self) -> Set[Union[str, int]]:
        ids: Set[Union[str, int]] = set()
        updates = await self.get_updates()

        if updates:
            for update in updates:
                if update.message and update.message.chat_id:
                    ids.add(update.message.chat_id)

        return ids

    @property
    def bot(self: Self):
        """The bot property."""
        return Bot(self.token)


def main(): ...


if __name__ == "__main__":
    main()  # call the main function
