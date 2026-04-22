import json
import random

from bs4 import BeautifulSoup

from app.shared.decorators import retry_on_fail

from .exceptions import CrwlError
from .models import Offer


@retry_on_fail(max_retries=3, sleep_interval=2)
def get_page_data(sb) -> dict:

    sb.solve_captcha()
    sb.cdp.sleep(random.uniform(3, 3.5))
    soup = BeautifulSoup(sb.cdp.get_page_source(), "html.parser")

    # New architecture: data is in an inline <script> tag starting with {"component":
    for script in soup.find_all("script"):
        text = script.get_text() or ""
        if text.startswith('{"component"'):
            return json.loads(text)

    # Fallback: old architecture with #app[data-page]
    app_tag = soup.select_one("#app")
    if app_tag:
        page_data = app_tag.attrs.get("data-page", None)
        if isinstance(page_data, str):
            return json.loads(page_data)
        elif page_data is not None:
            raise CrwlError(f"Unexpected data-page type: {type(page_data)}")

    raise CrwlError("Page data not found!!!")


@retry_on_fail(max_retries=2, sleep_interval=2)
def get_soup_and_page_data(
    sb,
    url: str,
) -> dict:
    sb.get(url)
    sb.cdp.sleep(random.uniform(3, 3.5))
    page_data = get_page_data(sb)
    return page_data


@retry_on_fail()
def currencies_extract(
    sb,
    url: str,
) -> list[Offer]:

    page_data = get_soup_and_page_data(sb, url)

    props = page_data.get("props", None)
    if not props:
        raise CrwlError("Props not found!!!")

    model = props.get("model", None)
    if not model:
        raise CrwlError("Model not found!!!")

    list_currencies_dict: list[dict] = []
    if "currency_offer" in model:
        list_currencies_dict.append(model["currency_offer"])

    if "currencies" in model and "data" in model["currencies"]:
        list_currencies_dict.extend(model["currencies"]["data"])

    return [
        Offer(
            seller=currency["seller"]["username"],
            price=currency["local_price"]["amount"],
            title=currency["title"],
            id=currency.get("id", None),
        )
        for currency in list_currencies_dict
    ]


def items_extract(
    sb,
    url: str,
) -> list[Offer]:
    page_data = get_soup_and_page_data(sb, url)

    props = page_data.get("props", None)
    if not props:
        raise CrwlError("Props not found!!!")

    model = props.get("model", None)
    if not model:
        raise CrwlError("Model not found!!!")

    list_items_dict = []

    if "items" in model and "data" in model["items"]:
        list_items_dict.extend(model["items"]["data"])

    return [
        Offer(
            seller=item["seller"]["username"],
            price=item["local_price"]["value"],
            title=item["title"],
            id=item.get("id", None),
        )
        for item in list_items_dict
    ]


def accounts_extract(
    sb,
    url: str,
) -> list[Offer]:
    page_data = get_soup_and_page_data(sb, url)

    props = page_data.get("props", None)
    if not props:
        raise CrwlError("Props not found!!!")

    model = props.get("model", None)
    if not model:
        raise CrwlError("Model not found!!!")

    list_accounts_dict = []

    if "accounts" in model and "data" in model["accounts"]:
        list_accounts_dict.extend(model["accounts"]["data"])

    return [
        Offer(
            seller=item["seller"]["username"],
            price=item["local_price"]["value"],
            title=item["title"],
            id=item.get("id", None),
        )
        for item in list_accounts_dict
    ]
