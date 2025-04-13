1. 启动后会创建cache，data文件夹，cache文件夹用于缓存数据，data文件夹是下载的pdf以及审稿意见
2. 获取到全部的venue_id保存在cache/venue_id.json文件的members字段中
3. 指定下载数据范围，在main.py中修改venue_list的值即可
4. 默认线程池数量在main.py中修改thread_num的值即可，不建议太大，官方API有限制