import time

from core.log_config import print_log
from core.openreview_spider import OpenReviewSpider, PaperDownload


def main():
    openreview_spider = OpenReviewSpider()
    # 获取所有会议列表
    venue_list = openreview_spider.get_all_venues()
    venue_count = len(venue_list)
    print_log.info(f"共{venue_count}个会议")
    for venue_index, venue_id in enumerate(venue_list, 1):
        venue_id = "ICLR.cc/2024/Conference"
        print_log.info(f"开始: 第{venue_index}/{venue_count}个会议")
        # 获取会议下的板块
        tab_list = openreview_spider.get_tab_list(venue_id)
        tab_mode = tab_list[0]
        tab_list = tab_list[1]
        tab_count = len(tab_list)
        if tab_mode == "mode_1":
            pass
        elif tab_mode == "mode_2":
            pass
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
            for paper_index, paper in enumerate(paper_list, 1):
                print_log.info(
                    f"开始: 第{venue_index}/{venue_count}个会议, 第{tab_index}/{tab_count}个板块, 第{paper_index}/{paper_count}个论文"
                )
                try:
                    paper_title = paper["content"]["title"]["value"]
                    paper_year = time.strftime(
                        "%Y", time.localtime(paper["pdate"] // 1000)
                    )
                except TypeError:
                    paper_title = (
                        paper["content"]["title"]
                        .replace("\n", "")
                        .replace("\r", "")
                        .replace("  ", "")
                    )
                    paper_year = time.strftime(
                        "%Y", time.localtime(paper["tmdate"] // 1000)
                    )

                paper_id = paper["id"]
                # 下载论文
                paper_download = PaperDownload(
                    venue_id, tab_name, paper_year, paper_title
                )
                paper_download.download_paper(paper_id)
                # 下载论文附件
                paper_download.download_paper_supplement(paper_id)
                # 下载评审信息
                if tab_mode == "mode_1":
                    review_info = openreview_spider.get_paper_review_1(paper_id)
                elif tab_mode == "mode_2":
                    review_info = openreview_spider.get_paper_review_2(paper_id)
                paper_download.download_paper_review(paper_id, review_info)
                print_log.info(
                    f"结束: 第{venue_index}/{venue_count}个会议, 第{tab_index}/{tab_count}个板块, 第{paper_index}/{paper_count}个论文"
                )
            print_log.info(
                f"结束: 第{venue_index}/{venue_count}个会议, 第{tab_index}/{tab_count}个板块"
            )
        print_log.info(f"结束: 第{venue_index}/{venue_count}个会议")
        return


if __name__ == "__main__":
    main()
