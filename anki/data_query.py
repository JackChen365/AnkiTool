import collections
import os
import time
import csv

from command_tool import open_file

from anki.data.baicizhan_service import BaicizhanSercice
from anki.data.cobuild_service import CobuildService
from anki.data.dict_service import DictService
from anki.data.macmillan_service import MacmillanService


class DataQuery(object):

    def __init__(self):
        # 百斩词服务对象，Macmillan服务对象，柯思林高阶英汉词典对象
        # BaicizhanSercice.__class__: BaicizhanSercice(),
        self.service_items = collections.OrderedDict()
        self.service_items[MacmillanService.__name__] = MacmillanService()
        self.service_items[CobuildService.__name__] = CobuildService()
        self.service_items[BaicizhanSercice.__name__] = BaicizhanSercice()

    def get_service(self, cls):
        return self.service_items[cls]

    def process(self, config, data):
        print("\t开始操作！")
        for name, item in self.service_items.items():
            st = int(time.time())
            if item.is_alive(config):
                item.process_data(config, data)
            else:
                print("\t%s 字典文件不存在！" + name)
            print("\t服务:%s 任务处理完成，耗时：%d秒" % (name, (int(time.time()) - st)))
        # 导入资源文件
        self.import_resources(config)
        # 准备写入数据
        result_file = config.app_dir + "result_" + str(time.time()) + ".csv"
        with open(result_file, "w", newline='', encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            # 先写入columns_name
            for name in data:
                rows_items = []
                for service in self.service_items.values():
                    # 检测服务是否正常
                    if item.is_alive(config):
                        # 获取每个服务每一列的写入数据
                        write_items = service.get_write_data(name)
                        rows_items.extend(write_items)
                # print("name:%s len:%d" % (name, len(rows_items)))
                writer.writerow(rows_items)
        # 弹出文件夹
        open_file(config.app_dir.replace("/", os.path.sep))
        print("\t操作完成！")

    def import_resources(self, config):
        print("Warning! Import all dict resource files(y/n)")
        s = input("> ")
        if "yes" == s.lower().strip() or 'y' == s.lower().strip():
            if os.path.exists(config.anki_user_dir):
                for name, item in self.service_items.items():
                    item.import_resources(config)
                print("Import completed!")
            else:
                print("Import user folder failure! %s does not existed!" % config.anki_user_dir)
        else:
            print("User doesn't want import resource files,you can use command \"anki import\" import next time!")
