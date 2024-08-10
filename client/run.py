import random
import time
import gevent
from lib import do_game, boom_game, game_state, get_state, post_state
from config import (
    USERID,
    SERVER,
    FAST_SLEEP_TIME,
    NORMAL_SLEEP_TIME,
    BONUS_MIN,
    BONUS_MAX,
)
from log import logger


res_data = {}
data = {"userid": USERID, "state": 1, "sleep": NORMAL_SLEEP_TIME}
SERVER = SERVER[:-1] if SERVER[-1] == "/" else SERVER
STATE_URL = SERVER + "/api/state"
STATES_URL = SERVER + "/api/states"


def work_time():
    t = time.time()
    hour = (t // 3600 + 8) % 24
    if 1 <= hour < 9:
        return False
    return True


def random_sleep(sleep_sec):
    half_sec = sleep_sec / 2
    gevent.sleep(random.random()*half_sec+half_sec)


def post_frds_states():
    global res_data
    global data
    while 1:
        if work_time():
            state = game_state(USERID)
            p_data = {"data": state, "userid": USERID,
                      "sleep": NORMAL_SLEEP_TIME}
            logger.info(f"在线游戏{state}")
            if state:
                if str(USERID) in state:
                    data["state"] = 1
                else:
                    data["state"] = None
                    data["point"] = None
                res_data = post_state(STATES_URL, p_data)
                logger.info(f"更新服务器状态{res_data}")
            random_sleep(NORMAL_SLEEP_TIME)
        else:
            time.sleep(60)


def start_my_game():
    global res_data
    global data
    while 1:
        if work_time():
            if not data.get("state", None):
                logger.info(f"服务器状态{res_data}")
                state = game_state(USERID)  # 本地校验状态
                if state:
                    if str(USERID) in state:
                        data["state"] = 1
                        res_data = post_state(STATE_URL, data)
                    else:
                        bonus = random.randint(
                            max(int(BONUS_MIN), 1), max(
                                int(BONUS_MIN), int(BONUS_MAX), 1)
                        )*1000
                        logger.info(f"开局{bonus}")
                        p = do_game(bonus)
                        if p:
                            data["point"] = p
                            data["bonus"] = bonus
                            data["state"] = 1
                            logger.info(f"上报点数{data}")
                            res_data = post_state(STATE_URL, data)
                            logger.info(f"更新服务器状态{res_data}")
                        else:
                            logger.warning("开局未知错误，20秒后重试")
                            random_sleep(20)
            random_sleep(1)
        else:
            gevent.sleep(60)


def help_friends():
    global res_data
    global data
    url = SERVER[:-1] if SERVER[-1] == "/" else SERVER
    url += "/api/state"
    while 1:
        if work_time():
            res_data = get_state(url)
            data = res_data.get(str(USERID), data)
            for key_id in res_data:
                if key_id != str(USERID):
                    friend_data = res_data.get(key_id, None)
                    if friend_data:
                        if friend_data.get("state", None):
                            if int(friend_data.get("point", 0)) > 21:
                                logger.info(f"服务器状态{res_data}")
                                logger.info(f"好友{key_id}点数超过21，开始平局")
                                bonus = friend_data.get("bonus", 100)
                                boom_data = {
                                    'game': 'hit', 'start': 'yes', 'userid': key_id, 'amount': bonus, 'downloads': '0'}
                                if boom_game(boom_data, USERID):
                                    logger.info(f"上传平局结果")
                                    friend_data["point"] = None
                                    friend_data["state"] = None
                                    res_data = post_state(url, friend_data)
                                    break
                                else:
                                    logger.warning(f"未找到对局，等待服务器更新数据")

            random_sleep(FAST_SLEEP_TIME)
        else:
            gevent.sleep(60 * 10)


def run():
    jobs = [
        gevent.spawn(post_frds_states),
        gevent.spawn(start_my_game),
        gevent.spawn(help_friends),
    ]
    gevent.joinall(jobs)


if __name__ == "__main__":
    run()
