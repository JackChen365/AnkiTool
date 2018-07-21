import re
from abc import abstractmethod
from concurrent import futures
from multiprocessing import cpu_count


class DataService(object):
    """数据处理服务"""

    def __init__(self):
        self.result = None
        # 初始化线程池
        self.executor = futures.ThreadPoolExecutor(cpu_count() + 1)
        self.pattern = re.compile(r"=\"(sound://)?([^\"\.]+\.(?:wav|gif|png|jpg))\"")

    @staticmethod
    def _query_dict_item(dict_builder, word):
        return word, dict_builder.mdx_lookup(word)

    @abstractmethod
    def process_data(self, config, data):
        pass

    @abstractmethod
    def is_alive(self, config):
        pass

    @abstractmethod
    def get_write_data(self, name):
        pass

    @abstractmethod
    def import_resources(self, config):
        pass
