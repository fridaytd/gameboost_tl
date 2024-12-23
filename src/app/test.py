import requests

print(
    requests.get(
        "https://api.gameboost.com/wow-classic-era/gold/67767404-b342-4bc0-aab1-6adbac1404b8"
    ).text
)
