from core.path_config import cache_dir, data_dir


class Params:

    def __init__(self, venue_id: str, params_list: list):
        self.venue_id = venue_id
        self.__generate_path()
        self.params_list = params_list

    def __generate_path(self):
        if self.venue_id:
            file_name = self.venue_id.replace("/", "_")
            self.cache_file_path = cache_dir / f"{file_name}.json"
            self.paper_dir_path = data_dir / file_name


class ICLR2020Conference(Params):
    def __init__(self):
        venue_id = "ICLR.cc/2020/Conference"
        params_list = [
            {
                "invitation": "ICLR.cc/2020/Conference/-/Withdrawn_Submission",
                "details": "replyCount,invitation,original",
            },
            {
                "invitation": "ICLR.cc/2020/Conference/-/Desk_Rejected_Submission",
                "details": "replyCount,invitation,original",
            },
            {
                "invitation": "ICLR.cc/2020/Conference/-/Blind_Submission",
                "details": "replyCount,invitation,original,directReplies",
            },
        ]
        super().__init__(venue_id, params_list)


class ICLR2021Conference(Params):
    def __init__(self):
        venue_id = "ICLR.cc/2021/Conference"
        params_list = [
            {
                "invitation": "ICLR.cc/2021/Conference/-/Withdrawn_Submission",
                "details": "replyCount,invitation,original",
            },
            {
                "invitation": "ICLR.cc/2021/Conference/-/Blind_Submission",
                "details": "replyCount,invitation,original,directReplies",
            },
            {
                "invitation": "ICLR.cc/2021/Conference/-/Desk_Rejected_Submission",
                "details": "replyCount,invitation,original",
            },
        ]
        super().__init__(venue_id, params_list)


class ICLR2022Conference(Params):
    def __init__(self):
        venue_id = "ICLR.cc/2022/Conference"
        params_list = [
            {
                "content": {"venue": "ICLR 2022 Spotlight"},
                "invitation": "ICLR.cc/2022/Conference/-/Blind_Submission",
                "details": "replyCount",
            },
            {
                "content": {"venue": "ICLR 2022 Oral"},
                "invitation": "ICLR.cc/2022/Conference/-/Blind_Submission",
                "details": "replyCount",
            },
            {
                "content": {"venue": "ICLR 2022 Submitted"},
                "invitation": "ICLR.cc/2022/Conference/-/Blind_Submission",
                "details": "replyCount",
            },
            {
                "invitation": "ICLR.cc/2022/Conference/-/Withdrawn_Submission",
                "details": "replyCount",
            },
            {
                "content": {"venue": "ICLR 2022 Poster"},
                "invitation": "ICLR.cc/2022/Conference/-/Blind_Submission",
                "details": "replyCount",
            },
            {
                "invitation": "ICLR.cc/2022/Conference/-/Desk_Rejected_Submission",
                "details": "replyCount,invitation,original",
            },
        ]
        super().__init__(venue_id, params_list)


class ICLR2023Conference(Params):
    def __init__(self):
        venue_id = "ICLR.cc/2023/Conference"
        params_list = [
            {
                "content": {"venue": "ICLR 2023 poster"},
                "invitation": "ICLR.cc/2023/Conference/-/Blind_Submission",
                "details": "replyCount",
            },
            {
                "invitation": "ICLR.cc/2023/Conference/-/Desk_Rejected_Submission",
                "details": "replyCount,invitation,original",
            },
            {
                "content": {"venue": "ICLR 2023 notable top 5%"},
                "invitation": "ICLR.cc/2023/Conference/-/Blind_Submission",
                "details": "replyCount",
            },
            {
                "content": {"venue": "Submitted to ICLR 2023"},
                "invitation": "ICLR.cc/2023/Conference/-/Blind_Submission",
                "details": "replyCount",
            },
            {
                "content": {"venue": "ICLR 2023 notable top 25%"},
                "invitation": "ICLR.cc/2023/Conference/-/Blind_Submission",
                "details": "replyCount",
            },
            {
                "invitation": "ICLR.cc/2023/Conference/-/Withdrawn_Submission",
                "details": "replyCount",
            },
        ]
        super().__init__(venue_id, params_list)


class ICLR2025Conference(Params):
    def __init__(self):
        venue_id = "ICLR.cc/2025/Conference"
        params_list = [
            {
                "content": {"venue": "ICLR 2025 Oral"},
                "domain": "ICLR.cc/2025/Conference",
                "details": "replyCount,presentation,writable",
            },
            {
                "content": {"venue": "ICLR 2025 Spotlight"},
                "domain": "ICLR.cc/2025/Conference",
                "details": "replyCount,presentation,writable",
            },
            {
                "content": {"venue": "ICLR 2025 Poster"},
                "domain": "ICLR.cc/2025/Conference",
                "details": "replyCount,presentation,writable",
            },
            {
                "content": {"venue": "Submitted to ICLR 2025"},
                "domain": "ICLR.cc/2025/Conference",
                "details": "replyCount,presentation,writable",
            },
            {
                "content": {"venue": "ICLR.cc/2025/Conference/Withdrawn_Submission"},
                "domain": "ICLR.cc/2025/Conference",
                "details": "replyCount,presentation,writable",
            },
            {
                "content": {
                    "venue": "ICLR.cc/2025/Conference/Desk_Rejected_Submission"
                },
                "domain": "ICLR.cc/2025/Conference",
                "details": "replyCount,presentation,writable",
            },
        ]
        super().__init__(venue_id, params_list)


params_module_list = [
    ICLR2020Conference(),
    ICLR2021Conference(),
    ICLR2022Conference(),
    ICLR2023Conference(),
    ICLR2025Conference(),
]
