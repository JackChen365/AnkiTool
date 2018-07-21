import os
import shutil
from concurrent import futures

from anki.data.dict_service import DictService
from mdict_query import IndexBuilder


class CobuildService(DictService):
    def __init__(self):
        super(CobuildService, self).__init__()
        self.dict_name = 'Cobuild.mdx'
        (self.name, _) = os.path.splitext(self.dict_name)

    def is_alive(self, config):
        return os.path.exists(config.cobuild)

    def process_data(self, config, data):
        """"获取柯思林，高阶英汉双解词典信息"""
        # 获得所有数据
        # Cobuild词典信息
        print("Cobuild词典服务开始处理数据！")
        file_name = self.name
        dict_builder = IndexBuilder(config.cobuild)
        # 1：查询到所有单词的字典html信息
        (doc_items, invalid_items) = self._query_word_items(file_name, dict_builder, data)
        # 2：记录扫描无效信息
        print("\t检索字典：%s检索完毕！\n\t开始写入无效数据" % file_name)
        self.write_invalid_items(config, file_name + "_invalid", invalid_items)
        print("\t开始写入正常数据")
        # 3：扫描文本内资源信息
        print("\t开始写入资源数据")
        self.save_resource(config, dict_builder, doc_items, file_name)
        # 4：记录扫描结果
        self.write_items(config, file_name, doc_items)
        # 返回doc信息
        self.result = doc_items

    def _query_word_items(self, file_name, dict_builder, data):
        """查询Macmillan词典内单词信息"""
        items = {}
        invalid_items = []
        future_items = []
        # 添加查询任务
        for name in data:
            future_items.append(self.executor.submit(self._query_dict_item, dict_builder, name))
        # 轮询所有任务
        for future in futures.as_completed(future_items):
            (name, rs) = future.result()
            rs = dict_builder.mdx_lookup(name)
            if 0 == len(rs):
                invalid_items.append(name)
            elif 1 == len(rs):
                # 只有一个词条
                items[name] = rs[0].replace(",", "&#44;").strip()
            elif 1 < len(rs):
                print("单词:%s 文档个数超过1个" % name)
        print("%s 字典内共查询%d 条结果，无效：%d" % (file_name, len(items), len(invalid_items)))
        return items, invalid_items

    def import_resources(self, config):
        path = os.path.join(config.app_dir, self.name) + "/resources"
        if not os.path.exists(path):
            print("资源目录:%s不存在！" % path)
        else:
            for file_name in os.listdir(path):
                abs_path = os.path.join(path, file_name)
                # 拷贝文件
                shutil.copyfile(abs_path, os.path.join(config.anki_user_dir, file_name))
                # 移除原资源文件
                os.remove(abs_path)

    def get_write_data(self, name):
        return [self.result.get(name, " ")]
