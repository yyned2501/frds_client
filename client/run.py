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


def work_time():
    t = time.time()
    hour = (t // 3600 + 8) % 24
    if 1 <= hour < 9:
        return False
    return True


def random_sleep(sleep_sec):
    time.sleep(random.randint(int(sleep_sec / 2), sleep_sec))


def start_my_game():
    global res_data
    global data
    while 1:
        if work_time():
            if not res_data.get(str(USERID), {"state": 1}).get("state", None):  # 未开局
                logger.info(f"服务器状态{res_data}")
                point = random.randint(max(int(BONUS_MIN), 1), max(
                    int(BONUS_MIN), int(BONUS_MAX), 1))
                logger.info(f"开局{point * 1000}")
                data["point"] = do_game(point * 1000)
                data["state"] = 1
                res_data = post_state(SERVER, data)
            random_sleep(1)
        else:
            time.sleep(60)


def post_frds_states():
    global res_data
    global data
    url = SERVER[:-1] if SERVER[-1] == "/" else SERVER
    url += "/api/states"
    while 1:
        if work_time():
            state = game_state(USERID)
            p_data = {"data": state}
            logger.info(f"在线游戏{state}")
            if state:
                if str(USERID) in state:
                    data["state"] = 1
                else:
                    data["state"] = None
                    data["point"] = None
                post_state(url, p_data)
                res_data = post_state(SERVER, data)
                logger.info(f"更新服务器状态{res_data}")
            random_sleep(NORMAL_SLEEP_TIME)
        else:
            time.sleep(60)


def help_friends():
    global res_data
    global data
    while 1:
        if work_time():
            res_data = get_state(SERVER)
            data = res_data.get(str(USERID), data)
            for key_id in res_data:
                if key_id != str(USERID):
                    friend_data = res_data.get(key_id, None)
                    if friend_data:
                        if friend_data.get("state", None):
                            if int(friend_data.get("point", 0)) > 21:
                                logger.info(f"服务器状态{res_data}")
                                logger.info(f"好友{key_id}点数超过21，开始平局")
                                if boom_game(key_id, USERID):
                                    logger.info(f"上传平局结果")
                                else:
                                    logger.warning(f"未找到对局，等待服务器更新数据")
                                friend_data["point"] = None
                                friend_data["state"] = None
                                res_data = post_state(SERVER, friend_data)
                                break
            random_sleep(FAST_SLEEP_TIME)
        else:
            time.sleep(60*10)


def hand_friend():
    global res_data
    global data
    while 1:
        res_data = get_state(SERVER)
        data = res_data.get(str(USERID), data)
        if friend_id := data.get("handid", None):
            friend_data = res_data.get(str(friend_id), None)
            if not friend_data:
                logger.info(f"好友{friend_id}已离线，解除绑定")
                data["handid"] = None
            else:
                friend_bind_id = friend_data.get("bindid", None)
                if friend_bind_id and friend_bind_id != USERID:
                    logger.info(f"好友{friend_id}已接收其他好友的帮助，解除绑定")
                    data["handid"] = None
                elif friend_data.get("state", None) and friend_data.get("point", 21) <= 21:
                    logger.info(f"好友{friend_id}已开始钓鱼，解除绑定")
                    data["handid"] = None
            if not data.get("handid", None):
                res_data = post_state(SERVER, data)
        else:
            for key_id in res_data:
                if key_id != str(USERID):
                    friend_data = res_data.get(key_id, None)
                    if friend_data:
                        if not friend_data.get("state", None) and not friend_data.get("bindid", None):
                            logger.info(f"检测到好友{key_id}需要帮助，开始绑定")
                            data["handid"] = key_id
                            res_data = post_state(SERVER, data)
                            break
        random_sleep(FAST_SLEEP_TIME)


def bind_friend():
    global res_data
    global data
    while 1:
        if friend_id := data.get("bindid", None):
            friend_data = res_data.get(str(friend_id), None)
            if not friend_data:
                logger.info(f"好友{friend_id}已离线，解除绑定")
                data["bindid"] = None
            elif friend_data.get("handid", None) != USERID:
                logger.info(f"好友{friend_id}不帮助我了，解除绑定")
                data["bindid"] = None
            else:
                if data.get("state", None):
                    point = data.get("point", 21) or 21
                    if point <= 21:
                        logger.info(f"开始钓鱼，解除绑定")
                        data["bindid"] = None
            if not data.get("bindid", None):
                res_data = post_state(SERVER, data)
        else:
            if not data.get("state", None):
                handids = []
                for key_id in res_data:
                    if key_id != str(USERID):
                        friend_data = res_data.get(key_id, None)
                        if friend_data:
                            if friend_data.get("handid", None) == USERID:  # 队友要帮助我
                                handids.append(key_id)
                                logger.info(f"绑定bindid:{key_id}")
                if len(handids) > 0:
                    data["bindid"] = random.choice(handids)  # 随机选一个好友帮助我
                    res_data = post_state(SERVER, data)
        time.sleep(1)


def safe_help():
    global res_data
    global data
    while 1:
        if friend_id := data.get("handid", None):
            if friend_data := res_data.get(str(friend_id), None):
                if bind_id := friend_data.get("bindid", None):
                    if bind_id == USERID:
                        if friend_data.get("point", None):
                            logger.info(f"服务器状态{res_data}")
                            logger.info(f"好友{friend_id}点数超过21，开始平局")
                            if boom_game(friend_id, USERID):
                                logger.info(f"上传平局结果")
                            else:
                                logger.warning(f"未找到对局，等待服务器更新数据")
                            friend_data["point"] = None
                            friend_data["state"] = None
                            res_data = post_state(SERVER, friend_data)
        time.sleep(1)


def safe_start():
    global res_data
    global data
    while 1:
        if not data.get("state", None):
            if friend_id := data.get("bindid", None):
                if res_data.get(str(friend_id), None):
                    bonus = random.randint(int(BONUS_MIN), int(BONUS_MAX))*1000
                    logger.info(data)
                    logger.info(f"已绑定好友{friend_id},开局{bonus}")
                    data["point"] = do_game(bonus)
                    data["state"] = 1
                    res_data = post_state(SERVER, data)
                else:
                    logger.info("帮助我的好友离线了，查找其他好友")
                    del data["bindid"]
        time.sleep(1)


def run():
    jobs = [
        gevent.spawn(post_frds_states),
        gevent.spawn(start_my_game),
        gevent.spawn(help_friends),
    ]
    gevent.joinall(jobs)


if __name__ == "__main__":
    run()
