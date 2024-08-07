import random
from lib import do_game, boom_game, game_state
from config import USERID, SERVER, FAST_SLEEP_TIME, NORMAL_SLEEP_TIME, BONUS_MIN, BONUS_MAX
from log import logger
import time
import requests
import gevent


res_data = {}
data = {"userid": USERID, "state": 1, "sleep": NORMAL_SLEEP_TIME}


def random_sleep(sleep_sec):
    time.sleep(random.randint(int(sleep_sec / 2), sleep_sec))


def get_state(url) -> dict[str, dict]:
    error = 0
    while error < 3:
        try:
            with requests.get(url) as r:
                if r.status_code == 200:
                    return r.json()
                else:
                    error += 1
                    logger.error(f"请求错误{error}次,错误代码{r.status_code}")
        except:
            error += 1
            logger.error(f"请求错误{error}次")


def post_state(url, data) -> dict:
    error = 0
    while error < 3:
        try:
            with requests.post(url, data=data) as r:
                if r.status_code == 200:
                    return r.json()
                else:
                    logger.error(r.status_code)
            error += 1
            logger.error(f"请求错误{error}次,错误代码{r.status_code}")
        except:
            error += 1
            logger.error(f"请求错误{error}次")


def start_my_game():
    global res_data
    global data
    while 1:
        if not res_data.get(str(USERID), {"state": 1}).get("state", None):  # 未开局
            logger.info(f"服务器状态{res_data}")
            point = random.randint(BONUS_MIN, BONUS_MAX)
            logger.info(f"开局{point * 1000}")
            data["point"] = do_game(point * 1000)
            data["state"] = 1
            res_data = post_state(SERVER, data)
        random_sleep(FAST_SLEEP_TIME)


def post_frds_states():
    global res_data
    global data
    url = SERVER[:-1] if SERVER[-1] == "/" else SERVER
    url += "/api/states"
    while 1:
        state = game_state(USERID)
        p_data = {"data": state}
        logger.info(f"在线游戏{state}")
        if str(USERID) in state:
            data["state"] = 1
        else:
            data["state"] = None
            data["point"] = None
        post_state(url, p_data)
        res_data = post_state(SERVER, data)
        logger.info(f"更新服务器状态{res_data}")
        random_sleep(NORMAL_SLEEP_TIME)


def help_friends():
    global res_data
    while 1:
        res_data = get_state(SERVER)
        for key_id in res_data:
            if key_id != str(USERID):
                friend_data = res_data.get(key_id, None)
                if friend_data:
                    if friend_data.get("state", None):
                        if int(friend_data.get("point", 0)) > 21:
                            logger.info(f"服务器状态{res_data}")
                            logger.info(f"好友{key_id}点数超过21，开始平局")
                            friend_data["state"] = None
                            res_data = post_state(SERVER, friend_data)
                            logger.info(f"汇报好友，防止他人误点{res_data}")
                            friend_data = res_data.get(key_id, {})
                            if int(friend_data.get("point", 0)) > 21:
                                if boom_game(key_id, USERID):
                                    logger.info(f"上传平局结果")
                                else:
                                    logger.warning(f"未找到对局，等待服务器更新数据")
                            else:
                                logger.info(f"重复校验，已平局，放弃平局")

        time.sleep(FAST_SLEEP_TIME)


def run():
    jobs = [
        gevent.spawn(help_friends),
        gevent.spawn(post_frds_states),
        gevent.spawn(start_my_game)
    ]
    gevent.joinall(jobs)


if __name__ == "__main__":
    run()
