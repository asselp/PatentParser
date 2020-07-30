from typing import List

import requests
from lxml.html import fromstring

from src.conf import HEADERS, KP_MAIN
from src.models import Patent

r = 'aidana'
q = 34


class KazPatentCrawler:

    def __init__(self):
        self.headers = HEADERS
        self.view_id = None
        self.session_id = None

    def _prepare(self, response) -> None:
        tree = fromstring(response.text)
        self.view_id: str = tree.xpath('.//input[@id="view:_id1__VUID"]/@value')[0]
        self.session_id = response.cookies.get('SessionID')

    def _get_preloaded_page(self) -> bytes:
        """
            1. Get session_id and view_id
            2. Return the preloaded table with 35 patents
        """
        response = requests.get(
            url=KP_MAIN,
            headers=self.headers,
            timeout=20
        )
        # Todo: handle request exceptions
        self._prepare(response)
        return response.content

    def _scroll(self) -> List[Patent]:
        # self.view_id
        # self.session_id
        return []

    def _get_first_patents(self) -> List[Patent]:
        _patents = []
        preloaded_page: bytes = self._get_preloaded_page()
        tree = fromstring(preloaded_page)
        rows: List = tree.xpath('//table[@id="gridDataTablet"]//tr[@class="itsFeedHover"]')
        for row in rows:
            td: list = row.xpath('./td//text()')
            _patents.append(
                Patent(
                    id=td[0],
                    registration_date=td[1],
                    receipt_date=td[2],
                    full_name=td[3],
                    type=td[4],
                    name_of_work=td[5],
                    work_creation_date=td[6],
                    status=td[7]
                )
            )
        return _patents

    def get_patents(self, count: int = 200):
        _patents: List[Patent] = self._get_first_patents()
        """Get the remaining patents by scrolling"""
        finished = False
        while not finished:
            patents_batch: List[Patent] = self._scroll()
            _patents.extend(patents_batch)
            finished = True
        return _patents


if __name__ == '__main__':
    crawler = KazPatentCrawler()
    patents = crawler.get_patents()
    for patent in patents:
        print(patent.dict())
