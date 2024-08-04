from libs import my_game_state, do_game, boom_game
import time
import random
import datetime
import requests
from config import USERID, SERVER
from logs import logger

data = {"userid": USERID}
FAST_SLEEP_TIME = 2
NORMAL_SLEEP_TIME = 60
BONUS_MIN = 5
BONUS_MAX = 9


def get_boomid(res_data):
    if res_data:
        for k in res_data:
            if int(k) != USERID:
                d: dict = res_data[k]
                if not d.get("state", None):
                    return int(k)
                if d.get("point", 0) > 21:
                    return int(k)


def friend_boom(res_data):
    if res_data:
        for k in res_data:
            if int(k) != USERID:
                d: dict = res_data[k]
                if d.get("boomid", None):
                    return int(k)


def friend_online(res_data):
    if res_data:
        for k in res_data:
            if int(k) != USERID:
                return True


def run():
    while 1:
        res_data = get_state()
        logger.info(f"服务器状态{res_data}")
        boomid_next_time = None
        if boomid := data.get("boomid", None):  # 帮助好友
            logger.info(f"开始帮助好友{boomid}")
            friend_data = res_data.get(str(boomid), None)
            if friend_data:
                if friend_data.get("state", None) == "请等待上局结束":
                    if int(friend_data["point"]) > 21:
                        logger.info(f"好友点数超过21，开始平局")
                        if not boom_game(boomid, USERID):
                            logger.info(f"未找到对局，等待服务器更新数据")
                        else:
                            logger.info(f"上传平局结果")
                            friend_data["state"] = None
                            friend_data["state"] = None
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
            else:
                logger.info("没有好友在线")

        sleep_sec = NORMAL_SLEEP_TIME
        if (not state) or boomid:
            sleep_sec = FAST_SLEEP_TIME
        

        data["next_time"] = int(time.time() + sleep_sec)
        data["next_date"] = datetime.datetime.fromtimestamp(
            int(time.time() + sleep_sec)
        )
        logger.info(f"汇报状态{data}")
        logger.info(f"服务器返回{post_state(data)}")
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
