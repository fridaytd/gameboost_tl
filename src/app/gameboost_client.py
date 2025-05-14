import os

import requests

from .shared.consts import GAMEBOOST_API_BASE_URL


class GameboostClient:
    def __init__(self) -> None:
        self.base_url: str = GAMEBOOST_API_BASE_URL
        self.api_key: str = os.environ["GAMEBOOST_API_KEY"]

    def get_currency_offer(
        self,
        currency_offer_id: str,
    ) -> dict:
        path: str = f"{self.base_url}/currency-offers/{currency_offer_id}"

        headers: dict = {"Authorization": f"Bearer {self.api_key}"}

        res = requests.get(url=path, headers=headers)
        res.raise_for_status()

        return res.json()["data"]

    def update_currency_offer(
        self,
        currency_offer_id: str,
        payload: dict,
    ) -> dict:
        payload["price"] = f"{payload['price']:f}"

        path: str = f"{self.base_url}/currency-offers/{currency_offer_id}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        res = requests.patch(url=path, json=payload, headers=headers)
        res.raise_for_status()

        return res.json()
