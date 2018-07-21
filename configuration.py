# 操作目录信息,可以配置自定义操作输出目录
import os
import platform
from configparser import ConfigParser


class Configuration(object):
    """应用配置"""

    def __init__(self):
        user_dir = os.path.expanduser('~')
        sys_str = platform.system().strip()
        if sys_str == "windows":
            roaming_data = os.path.join(user_dir, "AppData/Roaming/")
            self.app_dir = os.path.join(roaming_data, "Anki_Tool/")
            if not os.path.exists(self.app_dir): os.makedirs(self.app_dir)
            self.app_config_file = os.path.join(self.app_dir, "app_config.ini")  # 工具配置信息
            self.baizhanci = "http://mall.baicizhan.com/ws/search?w={word}"
            self.macmillan = "E:\Dicts\Macmillan English Dictionary for Advanced Learners\Macmillan English " \
                             "Dictionary for Advanced Learners.mdx"
            self.cobuild = "E:\Dicts\柯林斯COBUILD高阶英汉双解学习词典.mdx"
            self.anki_user_dir = roaming_data + "Anki2/User 1/collection.media"  # anki media根目录
        elif sys_str == "darwin":
            # os x
            self.app_dir = os.path.join(user_dir, "Anki_Tool/")
            if not os.path.exists(self.app_dir): os.makedirs(self.app_dir)
            self.app_config_file = os.path.join(self.app_dir, "app_config.ini")  # 工具配置信息
            self.baizhanci = "http://mall.baicizhan.com/ws/search?w={word}"
            self.macmillan = ""
            self.cobuild = ""
            self.anki_user_dir = os.path.join(user_dir, "Anki2/User 1/collection.media")  # anki media根目录
        # 如果配置信息不存在或更改，保存新的配置文件
        section = "app"
        if not os.path.exists(self.app_config_file):
            """初次配置信息不存在，取默认"""
            config = ConfigParser()
            # 词典位置
            config.add_section(section)
            config.set(section, "baizhanci", self.baizhanci)
            config.set(section, "macmillan", self.macmillan)
            config.set(section, "cobuild", self.cobuild)
            # anki软件的应用媒体文件目录
            config.set(section, "anki_user_dir", self.anki_user_dir)
            # 写入配置
            config.write(open(self.app_config_file, "w", encoding="gbk"))
            config.write(open(os.path.join(self.app_dir, ".backup.ini"), "w", encoding="gbk"))
        else:
            # 读取配置
            try:
                config = ConfigParser()
                config.read(self.app_config_file)
            except Exception as e:
                print("\t配置文件异常！")
                print(e)
            else:
                # 词典位置
                self.baizhanci = config.get(section, "baizhanci")
                self.macmillan = config.get(section, "macmillan")
                self.cobuild = config.get(section, "cobuild")
                # anki软件的应用媒体文件目录
                self.anki_user_dir = config.get(section, "anki_user_dir")

    def write_last_file(self, args):
        """写入使用的文件"""
        config = ConfigParser()
        config.read(self.app_config_file)
        # 移除section
        section = "files"
        config.remove_section(section)
        # 添加分类
        index = 0
        config.add_section(section)
        for arg in args:
            config.set(section, ("last%d" % index), arg)
            index += 1
        config.write(open(self.app_config_file, "w", encoding="gbk"))

    def read_last_file(self):
        """读取最后使用文件"""
        try:
            config = ConfigParser()
            config.read(self.app_config_file)
        except Exception:
            print("\t配置文件异常！")
            return []
        else:
            # 词典位置
            section = "files"
            if config.has_section(section):
                return list(map(lambda i: i[-1], config.items(section)))
            else:
                return []
