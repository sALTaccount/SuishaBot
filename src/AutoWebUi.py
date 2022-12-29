import base64
import io
from urllib.parse import urljoin
import requests
from PIL import Image


class QueueObj:
    def __init__(self, event_loop, ctx, args):
        self.event_loop = event_loop
        self.ctx = ctx
        self.args = args


class WebUi:
    class WebuiException(Exception):
        pass

    def __init__(self, ip):
        self._base_url = ip

    def txt_to_img(self, queue_obj):
        endpoint = urljoin(self._base_url, '/sdapi/v1/txt2img')
        payload = queue_obj.args
        response = requests.post(url=endpoint, json=payload)
        r = response.json()
        return r, response.status_code

    def heartbeat(self):
        endpoint = urljoin(self._base_url, '/user/')
        try:
            r = requests.get(endpoint, timeout=10)
            return r.status_code == 200
        except:
            return False
