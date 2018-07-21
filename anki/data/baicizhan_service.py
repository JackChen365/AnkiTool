import json
import os
import re
import shutil

from anki.data.data_service import DataService
from anki.service.baicizhan import Baicizhan
from concurrent import futures


class BaicizhanItem(object):
    """"百词斩返回信息"""

    def __init__(self):
        self.word = ""
        self.accent = None
        self.img = None
        self.df = None
        self.mean_cn = None
        self.errorCode = -1
        self.tv = None


class BaicizhanSercice(DataService):
    """百词斩数据服务对象"""

    def is_alive(self, config):
        return True

    def __init__(self):
        super(BaicizhanSercice, self).__init__()
        self.name = "Baicizhan"
        self.service = Baicizhan()

    def process_data(self, config, data):
        """百词斩数据处理"""
        # 获得所有数据
        print("百词斩服务开始处理数据！")
        cache_path = config.app_dir + self.name + "/"
        if not os.path.exists(cache_path): os.makedirs(cache_path)
        # 从网络获取
        future_items = []
        for d in data:
            future_items.append(self.executor.submit(self.service.request, d, cache_path, True))
        index = 0
        results = {}
        for future in futures.as_completed(future_items):
            item = future.result()
            if item.result is not None:
                results[item.word] = json.loads(item.result)
                if 0 != index and 0 == index % 100:
                    print("\t己获取:%d 个单词！" % index)
            else:
                print("\t单词：%s获取失败" % item.word)
            index += 1
        self.result = results
        print("\t单词信息获取完成！")
        # 下载所有资源信息
        print("是否下载百词斩所有在线资源！(y/n)")
        input_str = input("> ")
        if "yes" == input_str.lower() or 'y' == input_str.lower():
            print("\t开始下载资源文件！")
            self.download_resources(cache_path)

    def download_resources(self, cache_path):
        future_items = []
        cache_resource = cache_path + "resources/"
        if not os.path.exists(cache_resource): os.makedirs(cache_resource)
        for _, items in self.result.items():
            # 下载图片
            self.download_file(future_items, items.get("img", None), cache_resource)
            # 下载象形文本
            self.download_file(future_items, items.get("df", None), cache_resource)
            # 下载tv
            self.download_file(future_items, items.get("tv", None), cache_resource)
        index = 0
        failure_items = []
        for future in futures.as_completed(future_items):
            item = future.result()
            if item.result is not None:
                if 0 != index and 0 == index % 100:
                    print("\t\t己下载:%d 个资源文件！" % index)
            else:
                failure_items.append(item.url)
                print("\t%s 下载失败！" % item.url)
            index += 1
        print("\t所有下载任务完成,共计：%d" % index)
        print("\t失败：%d" % len(failure_items))

    def download_file(self, future_items, url, path):
        """下载一个文件"""
        if url is not None and 0 < len(url.strip()):
            file_name = os.path.basename(url)
            if not os.path.exists(path + file_name):
                future_items.append(
                    self.executor.submit(self.service.download, url, path, True))

    def import_resources(self, config):
        """导入百词斩所有资源文件"""
        path = os.path.join(config.app_dir, self.name) + "/resources"
        user_dir = config.anki_user_dir
        if not os.path.exists(path):
            print("资源目录:%s不存在！" % path)
        else:
            for file_name in os.listdir(path):
                abs_path = os.path.join(path, file_name)
                # 拷贝文件
                shutil.copyfile(abs_path, os.path.join(user_dir, file_name))
                # 移除原资源文件
                os.remove(abs_path)

    def get_write_data(self, name):
        dict_item = self.result.get(name, None)
        if dict_item is None:
            return list(map(lambda i: "", range(0, 4)))
        else:
            img = dict_item.get("img")
            df = dict_item.get("df")
            tv = dict_item.get("tv")
            items = ["" if img is None else ("<img src=\"%s\"/>" % os.path.basename(img)),
                     "" if df is None else ("<img src=\"%s\"/>" % os.path.basename(df)),
                     "" if tv is None else ("[sound:\"%s\"]" % os.path.basename(tv)),
                     dict_item.get("mean_cn", " ")]
            return items
