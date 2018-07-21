import os
import requests


class DownloadItem(object):
    def __init__(self, url):
        self.url = url
        self.result = None


class WebService(object):
    """web service class"""

    def __init__(self):
        super(WebService, self).__init__()

    def download(self, url, file_path, failure_retry=False):
        file_name = os.path.basename(url)
        item = DownloadItem(url)
        try:
            with open(file_path + file_name, "wb") as f:
                f.write(requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                                  '(KHTML, like Gecko) Chrome/31.0.1623.0 Safari/537.36'
                }).content)
                item.result = f
            return item
        except Exception:
            # 失败重试
            if failure_retry:
                print("\tfile:%s download failure，retry!" % file_name)
                return self.download(self, url, file_path, False)
            else:
                print("\tfile:%s download failure!" % file_name)
                return item
