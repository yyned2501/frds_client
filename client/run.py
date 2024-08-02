from libs import my_game_state, do_game, boom_game
import time, random, datetime
import requests
from config import USERID, SERVER
from logs import logger

data = {"userid": USERID}


def get_boomid(res_data):
    if res_data:
        for k in res_data:
            if int(k) != USERID:
                d: dict = res_data[k]
                if d.get("state", None):
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
                d: dict = res_data[k]
                if next_time := int(d.get("next_time", 0)):
                    if time.time() - next_time < 60:
                        return True


def run():
    while 1:
        state = my_game_state()  # 获取kf状态
        res_data = get_state()
        sleep_sec = random.randint(60, 120)
        if state == "请等待上局结束":  # 已开局
            if int(data.get("point", 21)) <= 21:  # 不需要帮助
                pass
            else:  # 需要帮助
                sleep_sec = random.randint(5, 10)
        else:  # 未开局
            if friend_online(res_data):
                logger.info("有好友在线")
                if friend_boom(res_data):
                    logger.info("有好友应答")
                    point = random.randint(8, 15)
                    logger.info(f"开局{point * 1000}")
                    data["point"] = do_game(point * 1000)
                sleep_sec = random.randint(5, 10)
            else:
                logger.info("没有好友在线")

        if boomid := data.get("boomid", None):  # 帮助好友
            logger.info(f"开始帮助好友{boomid}")
            sleep_sec = random.randint(5, 10)
            boomid = str(boomid)
            if res_data[boomid]["state"] == "请等待上局结束":
                if int(res_data[boomid]["point"]) > 21:
                    logger.info(f"好友点数超过21，开始平局")
                    boom_game(int(data["boomid"]), USERID)
                else:
                    logger.info(f"好友点数未超过21，帮助结束")
                    data["boomid"] = None
                    sleep_sec = random.randint(60, 120)
        else:
            logger.info(f"寻找需要帮助的好友")
            data["boomid"] = get_boomid(res_data)
            sleep_sec = random.randint(5, 10)

        data["next_time"] = int(time.time() + sleep_sec)
        data["next_date"] = datetime.datetime.fromtimestamp(
            int(time.time() + sleep_sec)
        )
        logger.info(post_state(data))
        time.sleep(sleep_sec)


def post_state(data) -> dict:
    with requests.post(SERVER, data=data) as r:
        if r.status_code == 200:
            return r.json()


def get_state():
    with requests.get(SERVER) as r:
        if r.status_code == 200:
            return r.json()


if __name__ == "__main__":
    run()
