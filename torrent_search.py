from enum import Enum
from json import loads

from flask import jsonify
from constants import OMDAPI_TOKEN, OMDBAPI_LINK
from requests import get
from piratebay import PirateBay

piratebay = PirateBay()


async def search(query: str):
    res = await piratebay.search(query, 1, 99)
    return res


async def getimdb(url):
    res = await piratebay.getContentIMDBId(url)
    if len(res) > 0:
        return res.split("tt")[2] # type: ignore
    else:
        return jsonify({"status": "Not Found", "message": "Unable to find ImdbId"}), 404


def get_content_info(imdbId: str):
    res = get(OMDBAPI_LINK, params={"apikey": OMDAPI_TOKEN, "i": "tt" + imdbId})
    return loads(res.text)


def get_content_by_name(name: str):
    res = get(OMDBAPI_LINK, params={"apikey": OMDAPI_TOKEN, "t": name})
    print(res.text)
    return loads(res.text)
