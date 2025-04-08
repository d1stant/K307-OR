import ast
import json
import re
from pathlib import Path

import openreview
from jsonpath import jsonpath
from lxml import etree

from core.__base_spider import BaseSpider
from core.log_config import print_log
from core.path_config import cache_dir, data_dir


class OpenReviewSpider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.client = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net",
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
        venues = self.client.get_group(id="venues")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(venues.to_json(), f, ensure_ascii=False, indent=4)
        return venues.to_json()["members"]

    def get_tab_list(self, venue_id: str) -> list:
        """获取会议分板块的名称和查询参数

        Args:
            venue_id (str): 会议id

        Returns:
            list: 会议下面板块名称，查询参数['mode_1',[{"name":"","query":{}}]]
        """
        url = f"https://openreview.net/group?id={venue_id}"
        response = self._request(url)
        print_log.debug(f"HTML DATA: {response.text}")
        tree = etree.HTML(response.text)
        next_data = tree.xpath('.//*[@id="__NEXT_DATA__"]/text()')
        next_data = json.loads(next_data[0])
        tabs = self.__parse_tab_1(next_data)
        tabs_1 = jsonpath(next_data, "$..tabs")
        if tabs_1:
            return ["mode_1", tabs]
        tabs_2 = self.__parse_tab_2(next_data)
        if tabs_2:
            return ["mode_2", tabs_2]

    def __parse_tab_1(self, next_data: dict) -> list:
        """解析tab信息情况1，符合使用官方API的情况"""
        tabs = jsonpath(next_data, "$..tabs")
        if tabs:
            tabs = [i for i in tabs[0] if "query" in i]
            return tabs
        return []

    def __parse_tab_2(self, next_data: dict) -> list:
        """解析tab信息情况2，符合使用网页API的情况"""
        js_code = jsonpath(next_data, "$..webfieldCode")
        if js_code:
            invitation = re.findall("BLIND_SUBMISSION_ID = '(.*?)';", js_code[0], re.S)
            tab_info = re.findall("DECISION_HEADING_MAP = (.*?);", js_code[0], re.S)
            tab_info = tab_info[0].replace("\n", "").replace(" ", "").strip()
            tab_info = ast.literal_eval(tab_info)
            tabs = [
                {
                    "name": i[1],
                    "decision": i[0],
                    "invitation": invitation[0],
                }
                for i in tab_info.items()
            ]
            return tabs
        return []

    def get_paper_list_1(self, venue_id: str, tab_info: dict):
        """获取这个会议下某一个板块的所有论文,模式1,官方API

        Args:
            venue_id (str): 会议id
            tab_info (dict): 板块信息 {"name":"","query":{}}
        """
        tab_name = tab_info["name"]
        file_path = cache_dir / f"{venue_id.replace('/','-')}_{tab_name}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                paper_list = json.load(f)
                print_log.info(f"{venue_id}-{tab_name}: 共{len(paper_list)}个论文")
                return paper_list
        tab_query = tab_info["query"]
        query_params = self.__parse_query(tab_query)
        paper_list = self.client.get_all_notes(**query_params)
        paper_list = [i.to_json() for i in paper_list]
        print_log.info(f"{venue_id}-{tab_name}: 共{len(paper_list)}个论文")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(paper_list, f, ensure_ascii=False, indent=4)
        return paper_list

    def get_paper_list_2(self, venue_id: str, tab_info: dict):
        """获取这个会议下某一个板块的所有论文,模式1,网页API"""
        tab_name = tab_info["name"]
        file_path = cache_dir / f"{venue_id.replace('/','-')}_{tab_name}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                paper_list = json.load(f)
                print_log.info(f"{venue_id}-{tab_name}: 共{len(paper_list)}个论文")
                return paper_list
        invitation = tab_info["invitation"]
        decision = tab_info["decision"]
        offset = 0
        papers = []
        url = f"https://api.openreview.net/notes?invitation={invitation}&details=replyCount,invitation,original&limit=1000&offset={1000*offset}"
        response = self._request(url)
        response_body = response.json()
        data_count = response_body["count"]
        papers.extend(response_body["notes"])
        while len(papers) < data_count:
            offset += 1
            url = f"https://api.openreview.net/notes?invitation={invitation}details=replyCount%2Cinvitation%2Coriginal&limit=1000&offset={1000*offset}"
            response = self._request(url)
            response_body = response.json()
            papers.extend(response_body["notes"])
        tagget_paper = [i for i in papers if i["content"]["decision"] == decision]
        print_log.info(f"{venue_id}-{tab_name}: 共{len(tagget_paper)}个论文")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tagget_paper, f, ensure_ascii=False, indent=4)
        return tagget_paper

    def __parse_query(self, query_info: dict):
        result = {"content": {}}
        for key, value in query_info.items():
            if key.startswith("content."):
                result["content"][key.split(".")[1]] = value
            else:
                result[key] = value
        return result

    def get_paper_review_1(self, paper_id: str) -> list:
        """获取论文详情页的信息以及评审信息，官方API

        Args:
            paper_id (str): 文章id
        Returns:
            list: 论文详情页的信息以及评审信息
        """
        paper_detail = self.client.get_notes(forum=paper_id, trash=True)
        paper_detail = [i.to_json() for i in paper_detail]
        return paper_detail

    def get_paper_review_2(self, paper_id: str) -> list:
        """获取论文详情页的信息以及评审信息，网页API"""
        url = f"https://api.openreview.net/notes?forum={paper_id}&trash=true&details=replyCount%2Cwritable%2Crevisions%2Coriginal%2Coverwriting%2Cinvitation%2Ctags&limit=1000&offset=0"
        response = self._request(url)
        response_body = response.json()
        return response_body["notes"]


class PaperDownload(BaseSpider):

    def __init__(self, venue_id: str, tab_name: str, paper_year, paper_title: str):
        super().__init__()
        self.__generate_save_path(venue_id, tab_name, paper_year, paper_title)

    def __generate_save_path(
        self, venue_id: str, tab_name: str, paper_year: str, paper_title: str
    ):
        venue_id = re.sub(r'[<>:"/\\|?*]', "-", venue_id)
        tab_name = re.sub(r'[<>:"/\\|?*]', "-", tab_name)
        paper_title = re.sub(r'[<>:"/\\|?*]', "-", paper_title)
        paper_save_dir = data_dir / f"{venue_id}/{tab_name}/{paper_year}"
        paper_save_dir.mkdir(parents=True, exist_ok=True)
        self.paper_save_path = paper_save_dir / f"{paper_title}.pdf"
        self.paper_supplement_save_path = (
            paper_save_dir / f"{paper_title}_supplement.pdf"
        )
        self.paper_review_save_path = paper_save_dir / f"{paper_title}.json"

    def download_paper(self, paper_id: str):
        if self.paper_save_path.exists():
            print_log.info(f"论文已下载: {paper_id}")
            return
        url = f"https://openreview.net/pdf?id={paper_id}"
        response = self._request(url)
        with open(self.paper_save_path, "wb") as f:
            f.write(response.content)
        print_log.info(f"下载论文成功: {paper_id}")

    def download_paper_supplement(self, paper_id: str):
        if self.paper_supplement_save_path.exists():
            print_log.info(f"支撑文件已下载")
            return
        url = f"https://openreview.net/attachment?id={paper_id}&name=supplementary_material"
        response = self._request(url)
        if response.status_code == 404:
            print_log.info(f"{paper_id}无支撑文件: {paper_id}")
            return
        with open(self.paper_supplement_save_path, "wb") as f:
            f.write(response.content)
        print_log.info(f"下载支撑文件成功: {paper_id}")

    def download_paper_review(self, paper_id: str, review_info: list):
        if self.paper_review_save_path.exists():
            print_log.info(f"评审已下载: {paper_id}")
            return
        with open(self.paper_review_save_path, "w", encoding="utf-8") as f:
            json.dump(review_info, f, ensure_ascii=False, indent=4)
        print_log.info(f"下载评审成功: {paper_id}")


if __name__ == "__main__":
    ops = OpenReviewSpider()
    # venues = ops.get_all_venues()
    # print(len(venues))
    # tabs = ops.get_tab_list("TMLR")
    ops.get_paper_review_2("ZhGJ9KQlXi9jk")
