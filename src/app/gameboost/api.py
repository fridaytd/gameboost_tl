import os
from typing import Final
import requests

from . import logger
from .models import OfferResponse, CurrencyOffer, AccountOffer, ItemOffer

from app.shared.decorators import retry_on_fail

GAMEBOOST_API_BASE_URL: Final[str] = "https://api.gameboost.com/v2"


class GameboostClient:
    def __init__(self) -> None:
        self.base_url: str = GAMEBOOST_API_BASE_URL
        self.api_key: str = os.environ["GAMEBOOST_API_KEY"]

    @retry_on_fail(max_retries=3, sleep_interval=2, exceptions=(requests.HTTPError,))
    def get_currency_offer(
        self,
        currency_offer_id: str,
    ) -> OfferResponse[CurrencyOffer]:
        path: str = f"{self.base_url}/currency-offers/{currency_offer_id}"

        headers: dict = {"Authorization": f"Bearer {self.api_key}"}

        res = requests.get(url=path, headers=headers)
        try:
            res.raise_for_status()
        except requests.HTTPError as e:
            logger.exception(f"Error getting currency offer: {res.text}")
            raise e

        return OfferResponse[CurrencyOffer].model_validate(res.json())

    @retry_on_fail(max_retries=3, sleep_interval=2, exceptions=(requests.HTTPError,))
    def update_currency_offer(
        self,
        currency_offer_id: str,
        price: float,
        stock: int,
    ) -> dict:
        payload = {
            "price": f"{price:f}",
            "stock": stock,
        }

        path: str = f"{self.base_url}/currency-offers/{currency_offer_id}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        res = requests.patch(url=path, json=payload, headers=headers)
        try:
            res.raise_for_status()
        except requests.HTTPError as e:
            logger.exception(f"Error updating currency offer: {res.text}")
            raise e

        return res.json()

    @retry_on_fail(max_retries=3, sleep_interval=2, exceptions=(requests.HTTPError,))
    def get_account_offer(
        self,
        account_offer_id: str,
    ) -> OfferResponse[AccountOffer]:
        path: str = f"{self.base_url}/account-offers/{account_offer_id}"

        headers: dict = {"Authorization": f"Bearer {self.api_key}"}

        res = requests.get(url=path, headers=headers)
        try:
            res.raise_for_status()
            # print(res.json())
        except requests.HTTPError as e:
            logger.exception(f"Error getting account offer: {res.text}")
            raise e

        return OfferResponse[AccountOffer].model_validate(res.json())

    @retry_on_fail(max_retries=3, sleep_interval=2, exceptions=(requests.HTTPError,))
    def update_account_offer(
        self,
        account_offer_id: str,
        price: float,
    ) -> dict:
        payload = {
            "price": f"{price:f}",
        }

        path: str = f"{self.base_url}/account-offers/{account_offer_id}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        res = requests.patch(url=path, json=payload, headers=headers)
        try:
            res.raise_for_status()
        except requests.HTTPError as e:
            logger.exception(f"Error updating account offer: {res.text}")
            raise e

        return res.json()

    @retry_on_fail(max_retries=3, sleep_interval=2, exceptions=(requests.HTTPError,))
    def get_item_offer(
        self,
        item_offer_id: str,
    ) -> OfferResponse[ItemOffer]:
        path: str = f"{self.base_url}/item-offers/{item_offer_id}"

        headers: dict = {"Authorization": f"Bearer {self.api_key}"}

        res = requests.get(url=path, headers=headers)
        try:
            res.raise_for_status()
        except requests.HTTPError as e:
            logger.exception(f"Error getting item offer: {res.text}")
            raise e

        return OfferResponse[ItemOffer].model_validate(res.json())

    @retry_on_fail(max_retries=3, sleep_interval=2, exceptions=(requests.HTTPError,))
    def update_item_offer(
        self,
        item_offer_id: str,
        price: float,
        stock: int,
    ) -> dict:
        payload = {
            "price": f"{price:f}",
            "stock": stock,
        }

        path: str = f"{self.base_url}/item-offers/{item_offer_id}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        res = requests.patch(url=path, json=payload, headers=headers)
        try:
            res.raise_for_status()
        except requests.HTTPError as e:
            logger.exception(f"Error updating item offer: {res.text}")
            raise e

        return res.json()

    def get_balance(self) -> dict:
        path: str = f"{self.base_url}/payments/balance"

        headers: dict = {"Authorization": f"Bearer {self.api_key}"}

        res = requests.get(url=path, headers=headers)
        try:
            res.raise_for_status()
        except requests.HTTPError as e:
            logger.exception(f"Error getting balance: {res.text}")
            raise e

        return res.json()


gameboost_api_client = GameboostClient()
