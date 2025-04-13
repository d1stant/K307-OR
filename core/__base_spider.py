import time

import requests
from fake_useragent import UserAgent

from core.log_config import print_log


class BaseSpider:
    def __init__(self):
        self.__ua = UserAgent()
        self.session = requests.Session()
        self.session.headers = {
            "accept": "application/json,text/*;q=0.99",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
            "cache-control": "no-cache",
            "connection": "close",
            "origin": "https://openreview.net",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://openreview.net/",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            # "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
        }

    def _request(self, url: str, params=None, data=None) -> requests.Response:
        while True:
            self.session.headers["user-agent"] = self.__ua.random
            try:
                if data:
                    response = self.session.post(url, params=params, data=data)
                else:
                    response = self.session.get(url, params=params)
                if response.status_code in [200, 404]:
                    return response
                elif response.status_code == 429:
                    print_log.warning(f"网站返回频繁,10sec后重试: {url}")
                    time.sleep(10)
                else:
                    print_log.warning(
                        f"请求{url}失败，状态码：{response.status_code}，返回内容：{response.text}"
                    )
            except requests.exceptions.ConnectionError:
                print_log.warning(f"ConnectionError: {url}")
            except Exception as e:
                print_log.error(f"请求{url}失败，错误信息：{e.__class__.__name__}：{e}")
