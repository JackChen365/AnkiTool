import os
import re
from abc import abstractmethod
from concurrent import futures

from anki.data.data_service import DataService


class DictService(DataService):
    """字典数据处理服务"""

    def __init__(self):
        super(DictService, self).__init__()

    def import_resources(self, config):
        pass

    def is_alive(self, config):
        pass

    def process_data(self, config, data):
        pass

    def get_write_data(self, name):
        pass

    @staticmethod
    def write_invalid_items(config, file_name, items):
        """写入操作无效数据"""
        # 写入文件
        fh = open(config.app_dir + file_name + ".txt", 'w', encoding='utf-8')
        try:
            for i in items:
                fh.write(i + "\n")
        finally:
            fh.close()

    def write_items(self, config, file_name, items):
        """写入操作成功数据"""
        file_path = config.app_dir + file_name
        if not os.path.exists(file_path): os.makedirs(file_path)
        # 写入文件
        future_items = []
        for (key, item) in items.items():
            if not os.path.exists(file_path + "/" + "_" + key):
                # 加_线的原因是区别关键字
                future_items.append(self.executor.submit(self._write_file, file_path + "/" + "_" + key, key, item))
        total = 0
        for future in futures.as_completed(future_items):
            word = future.result()
            if word:
                total += 1
            else:
                print("\t单词:%s 文本保存失败！" % word)
            if 0 != total and 0 == total % 100:
                print("\t己保存:%d 个单词文本！" % total)

    @staticmethod
    def _write_file(file_path, word, text):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return word

    @staticmethod
    def reset_html_res(items):
        """重置html内资源信息"""
        for (key, item) in items.items():
            pattern = re.compile(r"=\"(sound://)?([^\"\.]+\.(?:wav|gif|png|jpg))\"")
            matcher = pattern.findall(item)
            for host, res in matcher:
                # 重置资源索引路径,将多级的img/xx.jpg,置为1级的
                base_name = os.path.basename(res)
                if base_name != res:
                    item = item.replace(host + res, host + base_name)
            # 替换音频信息，从<a href=xx> 替换为[sound://xx]
            for v in re.compile("(?P<path><a href=\"sound://(?P<res>[^\\.]+\\.wav)\">)").findall(item):
                item = item.replace(v[0], "[sound:%s]" % v[1])
            # 重置信息
            items[key] = item

    def save_resource(self, config, dict_builder, items, name):
        """保存字典内资源文件"""
        path = config.app_dir + name + "/resources"
        if not os.path.exists(path): os.makedirs(path)
        total = 0
        future_items = []
        for (key, item) in items.items():
            pattern = re.compile(r"=\"(sound://)?([^\"\.]+\.(?:wav|gif|png|jpg))\"")
            matcher = pattern.findall(item)
            for host, res in matcher:
                file_path = os.path.join(path, os.path.basename(res))
                # 文件不存在时才进行操作
                if not os.path.exists(file_path):
                    # 添加查询任务
                    future_items.append(self.executor.submit(self._query_file, dict_builder, file_path, res))
        # 轮询所有任务,任务添加后，开始轮询
        for future in futures.as_completed(future_items):
            (res, result) = future.result()
            if result:
                total += 1
            else:
                print("\t资源:%s 下载失败！" % res)
            # 输出信息
            if 0 != total and 0 == total % 100:
                print("\t\t己保存:%d 个资源文件!" % total)
        print("\t共保存：%d 个资源文件" % total)

    @staticmethod
    def _query_file(dict_builder, file_path, res):
        # 数据索引内格式为\分隔，所有必须转，否则查找数据时会失效
        result = True
        bytes_list = dict_builder.mdd_lookup("\\" + res.replace("/", "\\"))
        if 0 == len(bytes_list):
            result = False
            print("\t资源:%s查询失败!" % res)
        else:
            # 因为部分资源为img/xx.jpg 所有需要取具体名称
            f = open(file_path, 'wb')
            f.write(bytes_list[0])
            f.close()
        return res, result
