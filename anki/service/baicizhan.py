# 利用百词斩的查询接口，获取图片以及提示信息，还有辅助视频
# http://mall.baicizhan.com/ws/search?w=apple
import os
import urllib
from urllib import parse

from anki.service.base import WebService


class ResponseItem(object):
    def __init__(self, word):
        self.word = word
        self.result = None


class Baicizhan(WebService):
    def __init__(self):
        super(Baicizhan, self).__init__()

    def request(self, query_word, cache_path, retry):
        url = u"http://mall.baicizhan.com/ws/search?w={word}".format(word=parse.quote(query_word))
        response_item = ResponseItem(query_word)
        try:
            # 加_为避免关键字冲突
            cache_file = os.path.join(cache_path, "_" + query_word+".json")
            if not os.path.exists(cache_file):
                # 网络请求获取数据
                html = urllib.request.urlopen(url, timeout=5).read().decode('utf-8')
                # 缓存文件
                file = open(cache_file, "w", encoding="utf-8")
                file.write(html)
                file.close()
                response_item.result = html
            else:
                # 本地缓存文件获取
                file = open(cache_file, encoding="utf-8")
                out = ""
                for line in file.readlines():
                    out += line.strip()
                file.close()
                response_item.result = out
        except IOError:
            print("\t单词查询失败:%s" % query_word)
            if retry:
                return self.request(query_word, cache_path, False)
            else:
                return response_item
        else:
            return response_item
