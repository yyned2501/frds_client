from gevent import monkey

import gevent
import requests
import time
from logs import logger
from config import USERID, SERVER
from lib import my_game_state, do_game, boom_game

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
        logger.info(f"服务器状态{res_data}")
        for key_id in res_data:
            friend_data = res_data[key_id]
            if friend_data:
                if friend_data.get("state", None):
                    if int(friend_data.get("point", 0)) > 21:
                        logger.info(f"好友点数超过21，开始平局")
                        if not boom_game(key_id, USERID):
                            logger.info(f"未找到对局，等待服务器更新数据")
                        else:
                            logger.info(f"上传平局结果")
                            friend_data["state"] = None
                            post_state(friend_data)
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


def get_state() -> dict[str, dict]:
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
    jobs = [gevent.spawn(help_friends)]
    gevent.joinall(jobs)


if __name__ == "__main__":
    run()
