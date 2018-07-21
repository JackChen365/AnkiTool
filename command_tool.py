import os
import re
import subprocess
import platform
from sys import argv
from anki.data_query import DataQuery
from configuration import Configuration
from anki import __version__


def main():
    help_info = "-w                            - default input word mode,word from command.\n" \
                "-f                            - word from disk file.\n" \
                "-lf                           - import last file!\n" \
                "-v                            - application version.\n" \
                "-h                            - get help.\n" \
                "--import                      - import all resource files.\n" \
                "--config                      - dict path,or generate file path..."
    if 1 == len(argv):
        print(help_info)
    else:
        command = argv[1]
        if command == "-w":
            import_data(argv[2:])
        elif command == "-f":
            import_file(argv[2:])
        elif command == "-lf":
            import_last_file()
        elif command == "-v":
            print("current version is %s" % __version__)
        elif command == "-h":
            print(help_info)
        elif command == "--import":
            import_resources()
        elif command == "--config":
            open_config()
        else:
            # 检测是否为单词，如果是的话，以单词处理
            if not import_args(argv[1:]):
                print(help_info)


def open_file(file_path):
    """打开文件，支持wins与osx系统打开"""
    if not os.path.exists(file_path):
        print("File:%s does not existed!" % file_path)
    else:
        sys_str = platform.system().strip()
        if sys_str == "windows":
            # subprocess.check_call(["explorer", "--", file_path.replace("/", os.path.sep)])
            os.startfile(file_path.replace("/", os.path.sep))
        elif sys_str == "darwin":
            subprocess.check_call(['open', '--', file_path])
        else:
            print("not support os!")


def import_args(param):
    """导入参数"""
    result = True
    pattern = re.compile(r"([\w\-\s]+)")
    for arg in param:
        result &= (re.fullmatch(pattern, arg) is not None)
    if result:
        # 一行8个，以20个字符为一个单元信息
        print("检测到你输入了:%d 个单词" % len(param))
        for index in range(0, len(param)):
            print(param[index].ljust(20, ' '), end='')
            if 0 != index and 0 == index % 8: print()
        print()
        print("是否导入！(y/n)")
        input_str = input("> ")
        if "yes" == input_str.lower() or 'y' == input_str.lower():
            #  导入单词
            import_data(param)
    return result


def import_resources():
    """导入资源文件"""
    data_query = DataQuery()
    data_query.import_resources(Configuration())


def open_config():
    # 打开配置文件
    open_file(Configuration().app_config_file)


def import_file(param, from_last=False):
    items = []
    if 0 == len(param):
        print("no file need import!")
    else:
        for path in param:
            if os.path.exists(path):
                try:
                    file = open(path, "r")
                    items.extend(list(map(lambda i: i.strip(), file.readlines())))
                    file.close()
                except Exception as e:
                    print("\t文件:%s读取异常！" % path)
                    print(e)
        # 如果不是从上一次记录经历，保存文件记录
        if not from_last:
            Configuration().write_last_file(param)  # 保存记录
        print("共%d个文件，共检测到:%d 个单词" % (len(param), len(items)))
        for index in range(0, len(items)):
            print(items[index].ljust(20, ' '), end='')
            if 0 != index and 0 == index % 8: print()
        print()
        print("是否导入！(y/n)")
        input_str = input("> ")
        if "yes" == input_str.lower().strip() or 'y' == input_str.lower().strip():
            #  导入单词
            import_data(items)
        else:
            print("import task abort!")


def import_last_file():
    config = Configuration()
    files = config.read_last_file()
    import_file(files, True)


def import_data(data):
    """导入数据"""
    data_query = DataQuery()
    data_query.process(Configuration(), data)
