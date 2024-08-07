from gevent import monkey

import gevent
import requests
import time
from logs import logger
from config import USERID, SERVER

monkey.patch_all()

res_data = {}
FAST_SLEEP_TIME = 3


def friend_online(res_data):
    if res_data:
        for k in res_data:
            if int(k) != USERID:
                return True


def ppp():
    global res_data
    while 1:
        print(res_data)
        time.sleep(FAST_SLEEP_TIME)


def help_friends():
    global res_data
    while 1:
        res_data = get_state()
        if boomid := friend_online(res_data):
            pass
        time.sleep(FAST_SLEEP_TIME)


def post_state(data) -> dict:
    error = 0
    while error < 3:
        try:
            with requests.post(SERVER, data=data) as r:
                if r.status_code == 200:
                    return r.json()
                else:
                    error += 1
                    logger.error(f"请求错误{error}次,错误代码{r.status_code}")
        except:
            error += 1
            logger.error(f"请求错误{error}次")


def get_state():
    error = 0
    while error < 3:
        try:
            with requests.get(SERVER, proxies={}) as r:
                if r.status_code == 200:
                    return r.json()
                else:
                    error += 1
                    logger.error(f"请求错误{error}次,错误代码{r.status_code}")
        except:
            error += 1
            logger.error(f"请求错误{error}次")


def run():
    jobs = [gevent.spawn(help_friends), gevent.spawn(ppp)]
    gevent.joinall(jobs)


if __name__ == "__main__":
    run()
