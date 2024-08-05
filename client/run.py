from libs import my_game_state, do_game, boom_game
import time
import random
import datetime
import requests
from config import USERID, SERVER
from logs import logger

data = {"userid": USERID}
FAST_SLEEP_TIME = 3
NORMAL_SLEEP_TIME = 120
BONUS_MIN = 5
BONUS_MAX = 9


def get_boomid(res_data):
    if res_data:
        friend_boom_list = [
            str(res_data[k].get("boomid", 0)) for k in res_data if int(k) != USERID
        ]
        for k in res_data:
            if int(k) != USERID and int(k) not in friend_boom_list:
                d: dict = res_data[k]
                if not d.get("state", None):
                    return int(k)
                if d.get("point", 0) > 21:
                    return int(k)
    return None


def friend_boom(res_data):
    """
    获取帮助我的朋友的id
    """
    if res_data:
        for k in res_data:
            if int(k) != USERID:
                d: dict = res_data[k]
                if frient_boomid := d.get("boomid", None):
                    if frient_boomid == USERID:
                        return True


def friend_online(res_data):
    if res_data:
        for k in res_data:
            if int(k) != USERID:
                return True


def get_friend_next_time(data: dict, res_data: dict[str, dict]):
    if not (data and res_data):
        return 0

    boom_friend_nexttime_list = [
        str(res_data[k].get("next_time", int(time.time() + FAST_SLEEP_TIME)))
        for k in res_data
        if res_data[k].get("boomid", 0) == USERID
    ]
    if len(boom_friend_nexttime_list) > 0:
        next_time = min(boom_friend_nexttime_list)
        logger.info(f"帮助我的好友下次刷新时间：{next_time}")
        return next_time

    if boom_id := data.get("boomid", None):
        if d := res_data.get(str(boom_id), None):
            next_time = d.get("next_time", int(time.time() + FAST_SLEEP_TIME))
            logger.info(f"我帮助的好友下次刷新时间：{next_time}")
            return next_time

    if not data.get("state", None) or data.get("point", 0) > 21:
        free_friend_nexttime_list = [
            str(res_data[k].get("next_time", int(time.time() + FAST_SLEEP_TIME)))
            for k in res_data
            if int(k) != USERID and not res_data[k].get("boomid", None)
        ]
        if len(free_friend_nexttime_list) > 0:
            next_time = min(free_friend_nexttime_list)
            logger.info(f"可以帮助我的好友下次刷新时间：{next_time}")
            return next_time


def run():
    while 1:
        res_data = get_state()
        logger.info(f"服务器状态{res_data}")
        if boomid := data.get("boomid", None):  # 帮助好友
            logger.info(f"开始帮助好友{boomid}")
            friend_data = res_data.get(str(boomid), None)
            if friend_data:
                if friend_data.get("state", None):
                    if int(friend_data["point"]) > 21:
                        logger.info(f"好友点数超过21，开始平局")
                        if not boom_game(boomid, USERID):
                            logger.info(f"未找到对局，等待服务器更新数据")
                        else:
                            logger.info(f"上传平局结果")
                            friend_data["state"] = None
                            friend_data["next_time"] = int(time.time() + 1)
                            post_state(friend_data)
                    else:
                        logger.info(f"好友点数未超过21，帮助结束")
                        data["boomid"] = None
            else:
                logger.info(f"好友 {boomid} 离线")
                data["boomid"] = None
        else:
            data["boomid"] = get_boomid(res_data)
            if data["boomid"]:
                logger.info(f'帮助{data["boomid"]}')
            else:
                logger.info(f"没有需要帮助的朋友")

        state = my_game_state()  # 获取kf状态
        data["state"] = state
        if not state:  # 未开局
            if friend_online(res_data):
                logger.info("有好友在线")
                if friend_boom(res_data):
                    logger.info("有好友应答")
                    point = random.randint(5, 9)
                    logger.info(f"开局{point * 1000}")
                    data["point"] = do_game(point * 1000)
                    data["state"] = 1
            else:
                logger.info("没有好友在线")

        sleep_sec = NORMAL_SLEEP_TIME
        friend_next_time = get_friend_next_time(data, res_data)
        if not friend_next_time:
            sleep_sec = random.randint(int(sleep_sec / 2), sleep_sec)
        else:
            friend_next_time = int(friend_next_time)
            sleep_sec = max(
                random.randint(0, FAST_SLEEP_TIME), int(friend_next_time - time.time())
            )
        data["sleep"] = sleep_sec
        logger.info(f"延迟{sleep_sec}秒，汇报状态{data}")
        post_state(data)
        time.sleep(sleep_sec)


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


if __name__ == "__main__":
    run()
