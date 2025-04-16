import ast
import json
import re
from pathlib import Path

import openreview

from core.__base_spider import BaseSpider
from core.log_config import print_log
from core.path_config import cache_dir, data_dir
from module.data_module import DownlaodModule
from module.params_module import Params


class OpenReviewSpider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.client_v2 = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net",  # https://api.openreview.net
            username="Ming.Hu@mbzuai.ac.ae",
            password="N-U74PKzf7y#T,q",
        )
        self.client_v1 = openreview.Client(
            baseurl="https://api.openreview.net",  # https://api.openreview.net
            username="Ming.Hu@mbzuai.ac.ae",
            password="N-U74PKzf7y#T,q",
        )

    def get_all_venues(self) -> list:
        """获取所有的会议id列表

        Returns:
            list: id列表
        """
        file_path = cache_dir / "venues.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                venues = json.load(f)
                return venues["members"]
        venues = self.client_v2.get_group(id="venues")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(venues.to_json(), f, ensure_ascii=False, indent=4)
        return venues.to_json()["members"]

    # def get_paper_list(self, cache_file_path: Path, params_list):
    def get_paper_list(self, params_module: Params):
        """获取所有论文列表"""
        if params_module.cache_file_path.exists():
            with open(params_module.cache_file_path, "r", encoding="utf-8") as f:
                paper_list = json.load(f)
        else:
            paper_list = []
            for params in params_module.params_list:
                # params.pop("domain", None)
                if "domain" in params:
                    offset = 0
                    while True:
                        params["offset"] = offset
                        paper_list_ = self.client_v2.get_notes(**params)
                        if not paper_list_:
                            break
                        paper_list.extend(paper_list_)
                        offset += 1000
                else:
                    paper_list.extend(self.client_v1.get_all_notes(**params))
            paper_list = [i.to_json() for i in paper_list]
            if paper_list:
                with open(params_module.cache_file_path, "w", encoding="utf-8") as f:
                    json.dump(paper_list, f, ensure_ascii=False, indent=4)
        print_log.info(f"{params_module.venue_id}: 共{len(paper_list)}个论文")
        return paper_list

    def get_review(self, paper_id: str) -> list:
        """获取论文详情页的信息以及评审信息，官方API

        Args:
            paper_id (str): 文章id
        Returns:
            list: 论文详情页的信息以及评审信息
        """
        review = self.client_v1.get_notes(forum=paper_id, trash=True)
        if not review:
            review = self.client_v2.get_notes(forum=paper_id, trash=True)
        review = [i.to_json() for i in review]
        return review


class PaperDownload(BaseSpider):

    def __init__(
        self,
        download_info: DownlaodModule,
    ):
        super().__init__()
        self.download_info = download_info

    def __generate_save_path(self):
        venue_id = re.sub(r'[<>:"/\\|?*]', "-", self.download_info.venue_id)
        paper_title = re.sub(
            r'[<>:"/\\|?*]', "-", self.download_info.paper_title
        ).replace("\x08", "")
        paper_save_dir = data_dir / f"{venue_id}/{self.download_info.paper_year}"
        paper_save_dir.mkdir(parents=True, exist_ok=True)
        self.paper_save_path = paper_save_dir / f"{paper_title}.pdf"
        if self.paper_save_path.exists():
            print_log.info(f"已下载过: {self.download_info.paper_id}")
            return True
        self.paper_supplement_save_path = (
            paper_save_dir / f"{paper_title}_supplement.pdf"
        )
        self.paper_review_save_path = paper_save_dir / f"{paper_title}.json"

    def download_paper(self):
        url = f"https://openreview.net/pdf?id={self.download_info.paper_id}"
        response = self._request(url)
        with open(self.paper_save_path, "wb") as f:
            f.write(response.content)
        print_log.info(f"论文下载成功: {self.download_info.paper_id}")

    def download_paper_supplement(self):
        url = f"https://openreview.net/attachment?id={self.download_info.paper_id}&name=supplementary_material"
        response = self._request(url)
        if response.status_code == 404:
            print_log.info(f"支撑文件不存在: {self.download_info.paper_id}")
            return
        with open(self.paper_supplement_save_path, "wb") as f:
            f.write(response.content)
        print_log.info(f"支撑下载成功: {self.download_info.paper_id}")

    def download_paper_review(self):
        with open(self.paper_review_save_path, "w", encoding="utf-8") as f:
            json.dump(self.download_info.review_info, f, ensure_ascii=False, indent=4)
        print_log.info(f"评审下载成功: {self.download_info.paper_id}")

    def __call__(self):
        if self.__generate_save_path():
            return
        self.download_paper()
        self.download_paper_supplement()
        self.download_paper_review()
