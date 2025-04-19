import ast
import json
import re
import time
from pathlib import Path

import openreview
from openreview.openreview import OpenReviewException

from core.__base_spider import BaseSpider
from core.log_config import print_log
from core.path_config import cache_dir, data_dir
from module.data_module import DownlaodModule
from module.params_module import Params

while True:
    try:
        client_v1 = openreview.Client(
            baseurl="https://api.openreview.net",  # https://api.openreview.net
            username="Ming.Hu@mbzuai.ac.ae",
            password="N-U74PKzf7y#T,q",
        )
        client_v2 = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net",  # https://api.openreview.net
            username="Ming.Hu@mbzuai.ac.ae",
            password="N-U74PKzf7y#T,q",
        )
        break
    except OpenReviewException as e:
        print_log.warning(f"链接过多, 30秒后重试: {e.args[0]['message']}")
        time.sleep(30)


def get_all_venues() -> list:
    """获取所有的会议id列表

    Returns:
        list: id列表
    """
    file_path = cache_dir / "venues.json"
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            venues = json.load(f)
            return venues["members"]
    venues = client_v2.get_group(id="venues")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(venues.to_json(), f, ensure_ascii=False, indent=4)
    return venues.to_json()["members"]


class OpenReviewSpider(BaseSpider):
    def __init__(self, venue_id: str):
        super().__init__()
        print_log.debug(f"获取venue_id: {venue_id}")
        self.venue_id = venue_id
        self.cache_file_path = cache_dir / f'{venue_id.replace("/", "_")}.json'

    def check_api_version(self) -> bool:
        """检查API版本"""
        try:
            group_data = client_v2.get_group(self.venue_id)
        except OpenReviewException as e:
            print_log.error(f'{self.venue_id}: {e.args[0]["message"]}')
            return False
        self.group_data = group_data
        domain = group_data.domain
        if domain:  # 存在domain,是V2版本
            print_log.info(f"{self.venue_id}: API版本为V2")
            self.version = 2
        else:  # 否则是V1版本
            print_log.info(f"{self.venue_id}: API版本为V1")
            self.version = 1
        return True

    def parse_submitions(self):
        """解析获取所有论文时需要的invitation参数"""
        if self.version == 1:
            web_code = self.group_data.web
            pattern = "SUBMISSION_ID = '(.*?)'"
            submition_id_list = re.findall(pattern, web_code)
            return submition_id_list
        content = self.group_data.content
        submition_id_list = [
            content[i]["value"] for i in content.keys() if i.endswith("submission_id")
        ]
        return submition_id_list

    def get_paper_list(self, submition_id_list: list):
        """获取所有论文列表"""

        def get_papers_v1():
            papers = []
            for submission_id in submition_id_list:
                notes = client_v1.get_all_notes(invitation=submission_id)
                for i in notes:
                    pdf = i.content.get("pdf", "")
                    if not pdf:
                        continue
                    year = time.strftime("%Y", time.localtime(i.tcdate // 1000))
                    id_ = i.id
                    title = i.content["title"]
                    supplementary = i.content.get("supplementary_material", "")
                    if supplementary:
                        supplementary_type = supplementary.split(".")[-1]
                    else:
                        supplementary_type = ""
                    papers.append(
                        {
                            "year": year,
                            "id": id_,
                            "title": title,
                            "api_version": 1,
                            "supplementary_type": supplementary_type,
                        }
                    )
            return papers

        def get_papers_v2():
            papers = []
            for submission_id in submition_id_list:
                notes = client_v2.get_all_notes(invitation=submission_id)
                for i in notes:
                    year = time.strftime("%Y", time.localtime(i.tcdate // 1000))
                    id_ = i.id
                    title = i.content["title"]["value"]
                    supplementary = i.content.get("supplementary_material", "")
                    if supplementary:
                        supplementary_type = supplementary["value"].split(".")[-1]
                    else:
                        supplementary_type = ""
                    papers.append(
                        {
                            "year": year,
                            "id": id_,
                            "title": title,
                            "api_version": 2,
                            "supplementary_type": supplementary_type,
                        }
                    )
            return papers

        if self.version == 1:
            paper_list = get_papers_v1()
        else:
            paper_list = get_papers_v2()
        with open(self.cache_file_path, "w", encoding="utf-8") as f:
            json.dump(paper_list, f, ensure_ascii=False, indent=4)
        print_log.info(f"{self.venue_id}: 共{len(paper_list)}个论文")
        return paper_list

    def __call__(self):
        if self.cache_file_path.exists():
            with open(self.cache_file_path, "r", encoding="utf-8") as f:
                paper_list = json.load(f)
            return paper_list
        if self.check_api_version():
            submition_id_list = self.parse_submitions()
            paper_list = self.get_paper_list(submition_id_list)
            return paper_list
        return False


class PaperDownload(BaseSpider):

    def __init__(self, venue_id: str, paper_info: dict):
        super().__init__()
        print_log.debug(f"获取文章: {paper_info}")
        self.venue_id = venue_id
        self.paper_id = paper_info["id"]
        self.paper_title = paper_info["title"]
        self.paper_year = paper_info["year"]
        self.api_version = paper_info["api_version"]
        self.supplementary_type = paper_info["supplementary_type"]

    def __generate_save_path(self):
        venue_id = re.sub(r'[<>:"/\\|?*]', "-", self.venue_id)
        paper_title = re.sub(r'[<>:"/\\|?*]', "-", self.paper_title).replace("\x08", "")
        paper_save_dir = data_dir / f"{venue_id}/{self.paper_year}"
        paper_save_dir.mkdir(parents=True, exist_ok=True)
        self.paper_save_path = paper_save_dir / f"{paper_title}.pdf"
        if self.paper_save_path.exists():
            print_log.info(f"已下载过: {self.paper_id}")
            return True
        if self.supplementary_type:
            self.paper_supplement_save_path = (
                paper_save_dir / f"{paper_title}_supplement.{self.supplementary_type}"
            )
        self.paper_review_save_path = paper_save_dir / f"{paper_title}.json"

    def download_paper(self):
        # url = f"https://openreview.net/pdf?id={self.paper_id}"
        # response = self._request(url)
        if self.api_version == 1:
            pdf_data = client_v1.get_attachment(id=self.paper_id, field_name="pdf")
        else:
            pdf_data = client_v2.get_attachment(id=self.paper_id, field_name="pdf")
        with open(self.paper_save_path, "wb") as f:
            f.write(pdf_data)
        print_log.info(f"论文下载成功: {self.paper_id}")

    def download_paper_supplement(self):
        # url = f"https://openreview.net/attachment?id={self.paper_id}&name=supplementary_material"
        # response = self._request(url)
        # if response.status_code == 404:
        #     print_log.info(f"支撑文件不存在: {self.paper_id}")
        #     return
        if not self.supplementary_type:
            return
        if self.api_version == 1:
            data = client_v1.get_attachment(
                id=self.paper_id, field_name="supplementary_material"
            )
        else:
            data = client_v2.get_attachment(
                id=self.paper_id, field_name="supplementary_material"
            )
        with open(self.paper_supplement_save_path, "wb") as f:
            f.write(data)
        print_log.info(f"支撑下载成功: {self.paper_id}")

    def download_paper_review(self):
        if self.api_version == 1:
            review = client_v1.get_notes(forum=self.paper_id, trash=True)
        else:
            review = client_v2.get_notes(forum=self.paper_id, trash=True)
        review = [i.to_json() for i in review]
        with open(self.paper_review_save_path, "w", encoding="utf-8") as f:
            json.dump(review, f, ensure_ascii=False, indent=4)
        print_log.info(f"评审下载成功: {self.paper_id}")

    def __call__(self):
        if self.__generate_save_path():
            return
        self.download_paper()
        self.download_paper_supplement()
        self.download_paper_review()


if __name__ == "__main__":
    venue_id = "ICLR.cc/2021/Conference"
    ors = OpenReviewSpider(venue_id)
    paper_list = ors()
