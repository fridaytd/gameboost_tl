from app.utils.logger import logger

from seleniumbase import SB
# from bs4 import BeautifulSoup
# import json

# from app.crwl import currencies_extract, items_extract, accounts_extract


# with SB(uc=True, headless=True) as sb:
#     items = accounts_extract(
#         sb,
#         url="https://gameboost.com/dragonball-legends/accounts?sort=price",
#     )

#     with open("data.json", "w") as f:
#         json.dump([item.model_dump() for item in items], f, indent=4)

# from app.gameboost_client import GameboostClient

# client = GameboostClient()

# print(client.get_currency_offer("3476"))

from app.models.gsheet_models import Product
from app.utils.gsheet import worksheet

product = Product.get(worksheet, 4)
# print(product.model_dump_json())

# # print(product.min_price())
# # print(product.max_price())
# # print(product.stock())
# print(product.blacklits())

from app.process import run


with SB(uc=True, headless=True) as sb:
    print(run(sb, product))
