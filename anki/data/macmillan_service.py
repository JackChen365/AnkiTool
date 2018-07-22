import collections
import os
import re
import shutil
from concurrent import futures

from anki.data.dict_service import DictService
from mdict_query import IndexBuilder


class WordItem(object):
    """单词信息"""

    def __init__(self, word):
        self.word = word
        self.uk_sound = ""
        self.us_sound = ""
        self.uk_phonetic = None
        self.us_phonetic = None
        self.star = "☆☆☆&nbsp;&nbsp;&nbsp;"
        self.description = ""  # 主要解释
        self.description_html = ""  # 所有解释的html信息
        self.html_doc = ""  # html文档

    def __str__(self):
        return "%s %s %s\n%s\n%s\n%s" % (
            self.vocabulary, self.uk_phonetic, self.us_phonetic, self.uk_sound, self.us_sound, self.description)


result_dict = {}


class MacmillanService(DictService):
    """Macmillan词典数据服务对象"""

    def __init__(self):
        super(MacmillanService, self).__init__()
        self.name = "Macmillan"

    def is_alive(self, config):
        return os.path.exists(config.macmillan)

    def process_data(self, config, data):
        """Macmillan数据处理"""
        print("Macmillan词典服务开始处理数据！")
        # 获得所有数据
        # Macmillan词典信息
        file_name = self.name
        dict_builder = IndexBuilder(config.macmillan)
        # 1：查询到所有单词的字典html信息
        (doc_items, invalid_items) = self._query_word_items(file_name, dict_builder, data)
        # 2：记录扫描无效信息
        print("\t检索字典：%s检索完毕！\n\t开始写入无效数据" % file_name)
        self.write_invalid_items(config, file_name + "_invalid", invalid_items)
        # 3：分析文本信息
        print("\t开始分析整体数据")
        self.result = self._analysis_items(doc_items)
        # 4：扫描文本内资源信息
        print("是否写入字典内所有资源！(y/n)")
        input_str = input("> ")
        if "yes" == input_str.lower() or 'y' == input_str.lower():
            print("\t开始写入资源数据")
            self.save_resource(config, dict_builder, doc_items, file_name)
        # 5：重置资源引用信息
        self.reset_html_res(doc_items)
        # 6：记录扫描结果
        print("\t开始写入正常数据")
        self.write_items(config, file_name, doc_items)
        # 7:更改html_doc信息，流程设计问题，因为需要将html内的多层资源引用，改为一级，但是检索的正则，与其他信息，以发现这问题之前就写完了
        for name, item in self.result.items():
            item.html_doc = doc_items[name]
        # 8:检测代码---检测资源路径信息
        invalid_res = []
        for _, item in doc_items.items():
            all_items = self.pattern.findall(item)
            for _, path in all_items:
                if -1 != path.find("/"):
                    invalid_res.append(path)
        if 0 < len(invalid_res):
            print("\t查找到包含路径资源:%d" % len(invalid_res))

    def _analysis_items(self, items):
        """分析文本内容"""
        vocabulary = {}
        for (key, item) in items.items():
            word_item = self._analysis(key, item)
            vocabulary[word_item.word] = word_item
        print("\t分析单词个数：%d" % len(vocabulary))
        return vocabulary

    def _analysis(self, word, out):
        """分析单词信息"""
        word_item = WordItem(word)
        pattern = re.compile(
            r"(?=<b>(<font>)?(?P<name>[^<]+)(</font>)?</b>|"
            r"<b><font color=\"#b904af\">▪ <font>I+.</font></font>\s?(<font>)?(?P<name1>[^<]+)(</font>)?</b>)")
        matcher = pattern.search(out)
        if matcher is not None:
            result_dict.setdefault("name", 0)
            result_dict["name"] += 1
        else:
            result_dict.setdefault("un_name", 0)
            result_dict["un_name"] += 1
        # 测试提取uk音标
        uk_phonetic_pattern = re.compile(
            r"<font color=\"#ff5400\">UK</font>\s<a href=\"sound://(?P<uk_sound>[^\"]+)\">"
            r"<img[^>]+></a>\s?<font color=\"#21887d\">\[(?P<uk_phonetic>[^\]]+)\]</font>")
        matcher = uk_phonetic_pattern.search(out)
        if matcher is not None:
            word_item.uk_sound = matcher.group("uk_sound")
            word_item.uk_phonetic = matcher.group("uk_phonetic")
            result_dict.setdefault("uk_phonetic", 0)
            result_dict["uk_phonetic"] += 1
        else:
            result_dict.setdefault("un_uk_phonetic", 0)
            result_dict["un_uk_phonetic"] += 1
        # # 测试提取us音标
        us_phonetic_pattern = re.compile(
            r"<font color=\"#ff5400\">US</font>\s<a href=\"sound://(?P<us_sound>[^\"]+)\">")
        matcher = us_phonetic_pattern.search(out)
        if matcher is not None:
            word_item.us_sound = matcher.group("us_sound")
            us_phonetic_pattern = re.compile(r"<font color=\"#ff5400\">US</font>\s<a href=\"([^\"]+)\">"
                                             r"<img[^>]+></a>\s?<font color=\"#21887d\">\[(?P<us_phonetic>[^\]]+)\]</font>").search(
                out)
            # 美式单独检测，因为可能与英式一致
            if us_phonetic_pattern is not None:
                word_item.us_phonetic = us_phonetic_pattern.group("us_phonetic")
            result_dict.setdefault("us_phonetic", 0)
            result_dict["us_phonetic"] += 1
        else:
            result_dict.setdefault("un_us_phonetic", 0)
            result_dict["un_us_phonetic"] += 1
        # 测试提取星级 <font color="#ff5400">★★</font>
        star_pattern = re.compile(r"<font color=\"#ff5400\">(?P<star>★+)</font>")
        matcher = star_pattern.search(out)
        if matcher is not None:
            result_dict.setdefault("star", 0)
            result_dict["star"] += 1
            word_item.star = matcher.group("star").ljust(3, "☆") + "&nbsp;&nbsp;&nbsp;"
        else:
            result_dict.setdefault("un_star", 0)
            result_dict["un_star"] += 1
        # #取解释
        # 检测是否存在大分层
        level_items = re.compile(r"<b><font color=\"#b904af\">▪ <font>[VI]+\.</font></font>").findall(out)
        item_level = len(level_items)
        result_dict.setdefault(item_level, 0)
        result_dict[item_level] += 1
        # 记录解释信息
        desc_items = collections.OrderedDict()
        if 0 == item_level:
            # 记录子解释个数
            query_desc_items = self._query_desc_items(word, out)
            if 0 < len(query_desc_items):
                desc_items.setdefault(0, [])
                desc_items[0] = query_desc_items
        elif 1 <= item_level:
            # 多级的
            level_items = re.compile(r"<b><font color=\"#b904af\">▪ <font>[VI]+\.</font></font>").split(out)
            # 过滤空信息
            level_items = list(filter(lambda x: 0 != len(x.strip()), level_items))
            level = 0
            for item in level_items:
                # 记录子解释个数
                query_desc_items = self._query_desc_items(word, item)
                desc_items.setdefault(level, [])
                desc_items[level] = query_desc_items
                level += 1
        # 拼装描述信息html
        # word_item.desc_items = desc_items
        levels = ["I", "II", "III", "IV", "V", "VI", "VII", "V"]
        for key, items in desc_items.items():
            word_item.description_html += (
                    "<b><font color=\"#b904af\">▪ <font>%s.</font></font></b>" % levels[key] + "<br>")
            index = 1
            for in_item in items:
                word_item.description_html += (
                        "&nbsp;&nbsp;&nbsp;&nbsp;<font color=\"#b904af\"><b>%d.</b></font> " % index + in_item.strip() + "<br>")
                index += 1
        # 记录主要解释信息，取第一条
        for level, items in desc_items.items():
            if 0 != len(items):
                word_item.description = items[0]
                break

        # 如果美式音标为空，则美式与英文一致
        if word_item.us_phonetic is None:
            word_item.us_phonetic = word_item.uk_phonetic
        word_item.html_doc = out
        return word_item

    def _query_word_items(self, file_name, dict_builder, data):
        """查询Macmillan词典内单词信息"""
        items = {}
        invalid_items = []
        # 提取网页内单词名称正则，用以校验多个翻译文本时，哪个为解释文本，哪个为外链介绍
        pattern = re.compile(
            r"(?=<b><font>(?P<name>[\w\-\s]+)</font></b>|"
            r"<b><font color=\"#b904af\">▪ <font>I+.</font></font>\s?(<font>)?(?P<name1>[\w\-\s]+)(</font>)?</b>)")
        future_items = []
        for name in data:
            future_items.append(self.executor.submit(self._query_dict_item, dict_builder, name))
        # 轮询所有任务
        for future in futures.as_completed(future_items):
            (name, rs) = future.result()
            if 0 == len(rs):
                invalid_items.append(name)
            elif 1 == len(rs):
                # 只有一个词条
                items[name] = rs[0].replace(",", "&#44;").strip()
            elif 1 < len(rs):
                for r in rs:
                    if pattern.search(r) is not None:
                        items[name] = r.replace(",", "&#44;").strip()
                        break
                if items[name] is None:
                    print("\t%s 匹配失败！" % name)
        print("\t%s 字典内共查询%d 条结果，无效：%d" % (file_name, len(items), len(invalid_items)))
        return items, invalid_items

    @staticmethod
    def _query_desc_items(word, out):
        """查找单词解释信息"""
        team_items = re.compile(r"<b>\d+.</b></font>(.+?)<br>").findall(out)
        if 0 == len(team_items):
            # 如果没有分组信息
            items = []
            summary_matcher = re.compile("<font color=\"#019444\"><i><font>Summary</font></i></font>").search(out)
            if summary_matcher is not None:
                # 总结性片断，忽略
                print("\t%s Summery chapter!" % word)
            else:
                matcher = re.compile(r"<br>(.+?)<br>").search(out)
                if matcher is not None:
                    # 记录结果
                    items.append(matcher.group(1))
            return items
        else:
            # 如果存在分组
            return team_items

    def get_write_data(self, name):
        """返回当前列数据,按data顺序添加"""
        item = self.result.get(name)
        if item is None:
            items = [name]
            items.extend(list(map(lambda i: "", range(0, 8))))
            return items
        else:
            # 添加单词，音标,音频
            items = [item.word,
                     "" if item.uk_phonetic is None else item.uk_phonetic,
                     "" if item.us_phonetic is None else item.us_phonetic,
                     "" if item.uk_sound is None else "[sound:%s]" % item.uk_sound,
                     "" if item.us_sound is None else "[sound:%s]" % item.us_sound]
            # 添加星级，英文简介，所有简介
            items.extend([item.star, item.description, item.description_html, item.html_doc])
            return items

    def import_resources(self, config):
        """"导入所有资源文件到anki目录"""
        path = os.path.join(config.app_dir, self.name) + "/resources"
        if not os.path.exists(path):
            print("\t资源目录:%s不存在！" % path)
        else:
            for file_name in os.listdir(path):
                abs_path = os.path.join(path, file_name)
                # 拷贝文件
                shutil.copyfile(abs_path, os.path.join(config.anki_user_dir, file_name))
                # 移除原资源文件
                os.remove(abs_path)
