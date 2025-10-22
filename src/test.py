from app.crwl.crwl import currencies_extract, items_extract, accounts_extract
from seleniumbase import SB
from app import config
from app.gameboost.api import gameboost_api_client

# with SB(uc=True, headless=False, disable_js=True) as sb:
#     sb.activate_cdp_mode("https://google.com")

#     print(
#         currencies_extract(
#             sb,
#             "https://gameboost.com/wow-classic-era/gold/67767404-b342-4bc0-aab1-6adbac1404b8",
#         )
#     )


# print(gameboost_api_client.get_currency_offer("3475"))
print(gameboost_api_client.get_account_offer("2351937"))
# print(gameboost_api_client.get_item_offer("10217"))
# print(gameboost_api_client.get_item
