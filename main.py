import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.log_config import print_log
from core.openreview_spider import OpenReviewSpider, PaperDownload
from module.data_module import DownlaodModule
from module.params_module import params_module_list

# 获取所有会议的venue_id
openreview_spider = OpenReviewSpider()
venue_list = openreview_spider.get_all_venues()
venue_count = len(venue_list)
print_log.info(f"全部共{venue_count}个会议, 保存在./cache/venues.json中的members字段")
# 指定要获取的venue_id
venue_list = venue_list = [
    # "ICLR.cc/2020/Conference",
    # "ICLR.cc/2021/Conference",
    # "ICLR.cc/2022/Conference",
    "ICLR.cc/2023/Conference",
    "ICLR.cc/2025/Conference",
]

venue_count = len(venue_list)
print_log.info(f"指定需要获取{venue_count}个会议")
# 线程数设置
thread_num = 4


def main():
    for venue_index, venue_id in enumerate(venue_list, 1):
        print_log.info(f"开始: 第{venue_index}/{venue_count}个会议: {venue_id}")
        # 检查参数模型
        params_module = None
        for params_module_ in params_module_list:
            if params_module_.venue_id == venue_id:
                params_module = params_module_
        if params_module is None:
            print_log.error(f"没有找到匹配的参数模型, 需要维护: {venue_id}")
            continue
        paper_list = openreview_spider.get_paper_list(params_module)
        paper_count = len(paper_list)
        futures = []
        with ThreadPoolExecutor(
            max_workers=thread_num, thread_name_prefix="下载"
        ) as executor:
            for paper_index, paper in enumerate(paper_list, 1):
                task = executor.submit(
                    multi_task,
                    venue_index,
                    paper_index,
                    paper_count,
                    paper,
                    venue_id,
                )
                futures.append(task)
            for future in as_completed(futures):
                future.result()
        print_log.info(f"结束: 第{venue_index}/{venue_count}个会议: {venue_id}")


def parse_title(paper: dict):
    # 标题
    try:
        paper_title = paper["content"]["title"]["value"]
    except (KeyError, TypeError):
        paper_title = paper.get("content", {}).get("title", "")
        if isinstance(paper_title, dict):
            paper_title = paper_title.get("value", "")
    paper_title = (
        str(paper_title).replace("\n", "").replace("\r", "").replace("  ", " ").strip()
    )
    return paper_title


def parse_year(paper):
    # 年份
    date_key_list = ["pdate", "cdate", "tcdate"]
    target_date = None
    for i in date_key_list:
        if i in paper and paper[i]:  # 直接检查键是否存在
            target_date = paper[i]
            break
    if target_date is None:
        raise ValueError(f"没有匹配到日期信息, {paper}")
    paper_year = time.strftime("%Y", time.localtime(target_date // 1000))
    return paper_year


def multi_task(
    venue_index,
    paper_index,
    paper_count,
    paper,
    venue_id,
):
    print_log.info(
        f"开始: 第{venue_index}/{venue_count}个会议, 第{paper_index}/{paper_count}个论文"
    )
    # 论文信息
    paper_title = parse_title(paper)
    paper_year = parse_year(paper)
    paper_id = paper["id"]
    # 评审内容
    review_info = openreview_spider.get_review(paper_id)
    # 构建数据对象
    downlaod_info = DownlaodModule(
        venue_id, paper_year, paper_title, paper_id, review_info
    )
    # 下载
    PaperDownload(downlaod_info)()
    print_log.info(
        f"结束: 第{venue_index}/{venue_count}个会议, 第{paper_index}/{paper_count}个论文"
    )
    return True


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_log.exception(e)
