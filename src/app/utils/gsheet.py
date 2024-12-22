import os


from gspread.auth import service_account

from app.utils.paths import ROOT_PATH


g_client = service_account(ROOT_PATH.joinpath(os.environ["KEYS_PATH"]))

spreadsheet = g_client.open_by_url(os.environ["SPREADSHEET_URL"])

worksheet = spreadsheet.worksheet(os.environ["SHEET_NAME"])
