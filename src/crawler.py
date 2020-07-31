from typing import List, Optional

import requests
from lxml.html import fromstring

from src.utils import get_logger
from src.conf import HEADERS, KP_MAIN, SCROLL_HEADERS, PARAMS, KP_AJAX
from src.models import Patent


class KazPatentCrawler:

    def __init__(self, quantity):
        self.headers = HEADERS
        self.scroll_header = SCROLL_HEADERS
        self.params = PARAMS
        self.view_id = None
        self.session_id = None
        self.data = None
        self.quantity = quantity
        self.logger = get_logger('KazPatentCrawler')

    def _prepare(self, response) -> None:
        """
            Prepare crawler to make a post request
        """
        tree = fromstring(response.text)
        self.view_id: str = tree.xpath('.//input[@id="view:_id1__VUID"]/@value')[0]
        self.session_id = dict(SessionID=dict(response.cookies).get("SessionID"))
        self.data = f"%24%24viewid={self.view_id}&%24%24xspsubmitid=QueryLazyLoadHandlerRA_server&%24%24xspexecid=' \
                    '&%24%24xspsubmitvalue={self.quantity - 35}&%24%24xspsubmitscroll=0%7C0&view%3A_id1=view%3A_id1"
        self.logger.info('Parsing started')

    def _get_preloaded_page(self) -> Optional[bytes]:
        """
            1. Get session_id and view_id
            2. Return the preloaded table with 35 patents
        """
        try:
            response = requests.get(
                url=KP_MAIN,
                headers=self.headers,
                timeout=20
            )
            self._prepare(response)
            return response.content
        except requests.exceptions.Timeout as e:
            self.logger.error(f'Request exception: {e}')
            return
        except requests.exceptions.RequestException as e:
            self.logger.error(f'Request exception: {e}')
            return

    def _get_ajax_response(self) -> Optional[bytes]:
        """
            Return the AJAX response
        """
        try:
            response = requests.post(
                timeout=20,
                url=KP_AJAX,
                headers=SCROLL_HEADERS,
                params=self.params,
                cookies=self.session_id,
                data=self.data
            )
            return response.content
        except requests.exceptions.Timeout as e:
            self.logger.error(f'Request exception: {e}')
            return
        except requests.exceptions.RequestException as e:
            self.logger.error(f'Request exception: {e}')
            return

    def _parse_patents(self, page) -> List[Patent]:
        _patents = []
        tree = fromstring(page.decode('utf-8'))
        rows = tree.xpath('//table//tr[@class="itsFeedHover"]')
        for row in rows:
            td: List = row.xpath('./td//text()')
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

    def _get_first_patents(self) -> List[Patent]:
        _patents = []
        retries = 3
        while retries:
            retries -= 1
            preloaded_page: bytes = self._get_preloaded_page()
            self.logger.info('Got preloaded page')
            if not preloaded_page:
                continue
            return self._parse_patents(preloaded_page)

    def _get_ajax_patents(self) -> List[Patent]:
        _patents = []
        retries = 3
        while retries:
            retries -= 1
            ajax_page: bytes = self._get_ajax_response()
            self.logger.info('Got ajax response')
            if not ajax_page:
                continue
            return self._parse_patents(ajax_page)

    def get_patents(self) -> List[Patent]:
        _patents: List[Patent] = self._get_first_patents()
        if _patents:
            self.logger.info('Preloaded patents parsed')
            finished = False
            while not finished:
                patents_batch: List[Patent] = self._get_ajax_patents()
                if patents_batch:
                    self.logger.info('AJAX page patents parsed')
                    _patents.extend(patents_batch)
                    finished = True
                self.logger.info('Parsing is over')
                return _patents


if __name__ == '__main__':
    crawler = KazPatentCrawler(40)
    crawler.get_patents()