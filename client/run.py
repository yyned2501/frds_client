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


def random_sleep(sleep_sec):
    time.sleep(random.randint(int(sleep_sec / 2), sleep_sec))


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
        random_sleep(1)


def post_frds_states():
    global res_data
    global data
    url = SERVER[:-1] if SERVER[-1] == "/" else SERVER
    url += "/api/states"
    while 1:
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


def hand_friend():
    global res_data
    global data
    while 1:
        if friend_id := data.get("handid", None):
            if friend_data := res_data.get(str(friend_id), None):
                if friend_data.get("bindid", None) != USERID:
                    logger.info(f"好友{friend_id}已接收其他好友的帮助，解除绑定")
                    del data["handid"]
                if friend_data.get("point", 22) < 21:
                    logger.info(f"好友{friend_id}已开始钓鱼，解除绑定")
                    del data["handid"]
            else:
                logger.info(f"好友{friend_id}已离线，解除绑定")
                del data["handid"]
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
        time.sleep(1)


def bind_friend():
    global res_data
    global data
    while 1:
        for key_id in res_data:
            if key_id != str(USERID):
                friend_data = res_data.get(key_id, None)
                if friend_data:
                    if friend_data.get("handid", None) == USERID:  # 队友要帮助我
                        data["bindid"] = key_id  # 我绑定要帮助我的队友
                        res_data = post_state(SERVER, data)
                        break
        time.sleep(1)


def safe_help():
    global res_data
    global data
    while 1:
        if friend_id := data.get("handid", None):
            logger.info(f"准备帮助好友{friend_id}")
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

                else:
                    logger.info(f"等待好友{friend_id}应答帮助")
        time.sleep(1)


def safe_start():
    global res_data
    global data
    while 1:
        if friend_id := data.get("bandid", None):
            if res_data.get(str(friend_id), None):
                bonus = random.randint(BONUS_MIN, BONUS_MAX)*1000
                logger.info(f"已绑定好友{friend_id},开局{bonus}")
                point = do_game(bonus)
                if point <= 21:
                    logger.info("点数未超过21，不需要帮助")
                    del data["bandid"]
                data["point"] = do_game(bonus)
                data["state"] = 1
                res_data = post_state(SERVER, data)
            else:
                logger.info("帮助我的好友离线了，查找其他好友")
                del data["bandid"]
        time.sleep(1)


def help_friends():
    global res_data
    global data
    while 1:
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

        time.sleep(FAST_SLEEP_TIME)


def run():
    jobs = [
        gevent.spawn(safe_help),
        gevent.spawn(safe_start),
        gevent.spawn(bind_friend),
        gevent.spawn(hand_friend),
        gevent.spawn(post_frds_states),
        # gevent.spawn(start_my_game),
    ]
    gevent.joinall(jobs)


if __name__ == "__main__":
    run()
