import time
from app.crwl.crwl import currencies_extract, items_extract, accounts_extract
from seleniumbase import SB
from app.shared.paths import SRC_PATH


with SB(
    uc=True,
    headless=True,
    disable_js=False,
    # user_data_dir=str(SRC_PATH / "data" / "user_data"),
) as sb:
    sb.activate_cdp_mode("https://google.com")

    sb.cdp.get("https://gameboost.com")

    # button = sb.cdp.find_element_by_text("Change language and currency")
    # button.click()

    sb.click('span:contains("Change language and currency")')

    # sb.cdp.select_option_by_value("label:contains('Currency') ~ select", "EUR")

    # print(sb.cdp.locator("label:contains('Currency') ~ select").attrs)

    sb.cdp.mouse_click('label:contains("Currency") ~ button')
    # sp.click()
    # print(sp.text)
    # sb.cdp.select_option_by_value("EUR")

    sb.cdp.mouse_click('span:contains("Euro")')

    sb.cdp.mouse_click("button i.mr-2.fa-solid.fa-check")

    sb.sleep(5)

    sb.cdp.save_cookies(SRC_PATH / "data" / "cookies.json")

    # select = sb.cdp.
    # print(select)

    # time.sleep(10)

# print(
#     currencies_extract(
#         sb,
#         "https://gameboost.com/genshin-impact/top-up/1f1f6e83-46f8-4092-b82c-5592e3f23265",
#     )
# )


with SB(
    uc=True,
    headless=True,
    disable_js=True,
    # user_data_dir=str(SRC_PATH / "data" / "user_data"),
) as sb:
    sb.activate_cdp_mode("https://google.com")

    sb.cdp.load_cookies(SRC_PATH / "data" / "cookies.json")

    print(
        currencies_extract(
            sb,
            "https://gameboost.com/genshin-impact/top-up/1f1f6e83-46f8-4092-b82c-5592e3f23265",
        )
    )
