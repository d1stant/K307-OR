import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.log_config import print_log
from core.module import DownlaodModule
from core.openreview_spider import OpenReviewSpider, PaperDownload

# 获取所有会议的venue_id
openreview_spider = OpenReviewSpider()
venue_list = openreview_spider.get_all_venues()
venue_count = len(venue_list)
print_log.info(f"全部共{venue_count}个会议, 保存在./cache/venues.json中的members字段")
# 指定要获取的venue_id
venue_list = ["ICLR.cc/2019/Workshop/DeepGenStruc", "ICLR.cc/2021/Workshop/NeuCAIR"]
venue_count = len(venue_list)
print_log.info(f"指定需要获取{venue_count}个会议")
# 线程数设置
thread_num = 4


def main():
    for venue_index, venue_id in enumerate(venue_list, 1):
        print_log.info(f"开始: 第{venue_index}/{venue_count}个会议")
        # 获取会议下的板块
        tab_list = openreview_spider.get_tab_list(venue_id)
        if not tab_list:
            continue
        tab_mode = tab_list[0]
        tab_list = tab_list[1]
        tab_count = len(tab_list)
        for tab_index, tab_info in enumerate(tab_list, 1):
            print_log.info(
                f"开始: 第{venue_index}/{venue_count}个会议, 第{tab_index}/{tab_count}个板块"
            )
            # 获取对应板块下的论文列表
            tab_name = tab_info["name"]
            if tab_mode == "mode_1":
                paper_list = openreview_spider.get_paper_list_1(venue_id, tab_info)
            elif tab_mode == "mode_2":
                paper_list = openreview_spider.get_paper_list_2(venue_id, tab_info)
            paper_count = len(paper_list)
            futures = []
            with ThreadPoolExecutor(
                max_workers=thread_num, thread_name_prefix="下载"
            ) as executor:
                for paper_index, paper in enumerate(paper_list, 1):
                    task = executor.submit(
                        multi_task,
                        venue_index,
                        tab_index,
                        tab_count,
                        paper_index,
                        paper_count,
                        paper,
                        tab_mode,
                        venue_id,
                        tab_name,
                    )
                    futures.append(task)
                for future in as_completed(futures):
                    future.result()
            print_log.info(
                f"结束: 第{venue_index}/{venue_count}个会议, 第{tab_index}/{tab_count}个板块"
            )
        print_log.info(f"结束: 第{venue_index}/{venue_count}个会议")


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
        if i in paper:  # 直接检查键是否存在
            target_date = paper[i]
            break
    if target_date is None:
        raise ValueError(f"没有匹配到日期信息, {paper}")
    paper_year = time.strftime("%Y", time.localtime(target_date // 1000))
    return paper_year


def multi_task(
    venue_index,
    tab_index,
    tab_count,
    paper_index,
    paper_count,
    paper,
    tab_mode,
    venue_id,
    tab_name,
):
    print_log.info(
        f"开始: 第{venue_index}/{venue_count}个会议, 第{tab_index}/{tab_count}个板块, 第{paper_index}/{paper_count}个论文"
    )
    # 论文信息
    paper_title = parse_title(paper)
    paper_year = parse_year(paper)
    paper_id = paper["id"]
    # 评审内容
    if tab_mode == "mode_1":
        review_info = openreview_spider.get_paper_review_1(paper_id)
    elif tab_mode == "mode_2":
        review_info = openreview_spider.get_paper_review_2(paper_id)
    # 构建数据对象
    downlaod_info = DownlaodModule(
        venue_id, tab_name, paper_year, paper_title, paper_id, review_info
    )
    # 下载
    PaperDownload(downlaod_info)()
    print_log.info(
        f"结束: 第{venue_index}/{venue_count}个会议, 第{tab_index}/{tab_count}个板第{paper_index}/{paper_count}个论文"
    )
    return True


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_log.exception(e)
