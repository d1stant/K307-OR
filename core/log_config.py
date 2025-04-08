import os
import sys
from pathlib import Path

from loguru import logger as print_log

__max_old_log_num = 10  # 只保存10个日志
__log_directory = Path(Path.cwd() / "./logs")
Path.mkdir(__log_directory, exist_ok=True)  # 创建日志文件夹

# 删除多余的日志
__old_log_list = sorted(__log_directory.glob("*.log"))
__total_log_num = len(__old_log_list)
if __total_log_num > __max_old_log_num:
    __difference_num = __total_log_num - __max_old_log_num
    for log in __old_log_list[: __difference_num + 1]:
        os.remove(log)


print_log.remove()  # 移除默认日志处理器

# 为每个日志级别设置颜色
print_log.level("DEBUG", color="<fg #8B658B>")
print_log.level("INFO", color="<fg #228B22>")
print_log.level("WARNING", color="<fg #FFD700>")
print_log.level("ERROR", color="<fg #ff00cc>")
print_log.level("CRITICAL", color="<fg #CD0000><bold>")

# 日志格式
__console_log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:^8}</level> : <level>{message}</level>"
__file_log_format = "{time:YYYY-MM-DD HH:mm:ss} | {process.name} | {thread.name} | {file:>10}:{line}:{function}() | {level} : {message}"

# 添加文件日志处理器
print_log.add(
    sink=__log_directory / "log_{time:YYYY-MM-DD HH-mm-ss}.log",
    # sink=sys.stdout,
    level="DEBUG",  # 级别
    format=__file_log_format,
    rotation="20 MB",  # 设置大小
    retention=20,
    encoding="utf-8",
    enqueue=True,
    backtrace=True,  # 记录堆栈
    diagnose=True,  # 堆栈跟踪
)

# 添加控制台日志处理器
print_log.add(
    sink=sys.stdout,
    level="INFO",
    # level="DEBUG",
    format=__console_log_format,
    colorize=True,
    enqueue=True,
)
# print_log.debug("test")
# print_log.info("test")
# print_log.warning("test")
# print_log.error("test")
# print_log.critical("test")
