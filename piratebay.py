import re
import time
import aiohttp
from bs4 import BeautifulSoup
from htmlscrapper import Scraper
from constants import PIRATEBAY_URL


class PirateBay:
    _name = "Pirate Bay"
    def __init__(self):
        self.BASE_URL = PIRATEBAY_URL
        self.LIMIT = None

    def _parser(self, htmls):
        try:
            for html in htmls:
                soup = BeautifulSoup(html, "html.parser")

                my_dict = {"data": []}
                for tr in soup.find_all("tr")[1:]:
                    td = tr.find_all("td")
                    try:
                        name = td[1].find("a").text # type: ignore
                    except:
                        name = None
                    if name:
                        url = td[1].find("a")["href"] # type: ignore
                        magnet = td[3].find_all("a")[0]["href"]
                        size = td[4].text.strip()
                        seeders = td[5].text
                        leechers = td[6].text
                        category = td[0].find_all("a")[0].text
                        uploader = td[7].text
                        dateUploaded = td[2].text
                           
                        my_dict["data"].append(
                            {
                                "name": name,
                                "size": size,
                                "seeders": seeders,
                                "leechers": leechers,
                                "category": category,
                                "uploader": uploader,
                                "url": url,
                                "date": dateUploaded,
                                "hash": re.search(
                                    r"([{a-f\d,A-F\d}]{32,40})\b", magnet # type: ignore
                                ).group(0), # type: ignore
                                "magnet": magnet,
                            }
                        )
                    if len(my_dict["data"]) == self.LIMIT:
                        break
                last_tr = soup.find_all("tr")[-1]
                potential_page_link = last_tr.find("td").find("a").href # type: ignore
                check_if_pagination_available = potential_page_link is not None and potential_page_link[:len("/search/")] == "/search/" # type: ignore
                if check_if_pagination_available:
                    current_page = last_tr.find("td").find("b").text # type: ignore
                    my_dict["current_page"] = int(current_page) # type: ignore
                    my_dict["total_pages"] = int( # type: ignore
                        last_tr.find("td").find_all("a")[-2].text # type: ignore
                    )
                return my_dict
        except:
            return None

    async def search(self, query, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            print(query)
            url = self.BASE_URL + "/search/{}/{}/99/0".format(query, page)
            return await self.parser_result(start_time, url, session)

    async def parser_result(self, start_time, url, session):
        html = await Scraper().get_all_results(session, url)
        results = self._parser(html)
        if results is not None:
            results["time"] = time.time() - start_time
            results["total"] = len(results["data"])
            return results
        return results

    async def trending(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            url = self.BASE_URL + "/top/all"
            return await self.parser_result(start_time, url, session)

    async def recent(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            if not category:
                url = self.BASE_URL + "/recent"
            else:
                url = self.BASE_URL + "/{}/latest/".format(category)
            return await self.parser_result(start_time, url, session)
    async def getContentIMDBId(self, url):
        result = ''
        async with aiohttp.ClientSession() as session:
            html = await Scraper().get_all_results(session, url)
            if html:
                soup = BeautifulSoup(html[0], "html.parser") # type: ignore
                print("----- soup")
                print(soup)
                
                for dd in soup.find_all("dd"):
                    for child in dd.children:
                        if child.text == "IMDB":
                            result = child["href"] # type: ignore
            return result
