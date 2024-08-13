import monkey
import requests
from bs4 import BeautifulSoup
from config import COOKIE, REMAIN_POINT, REMAIN_POINT_LOW, REMAIN_POINT_LOW_P, SAVE_ERR_PAGE, PROXY
from log import logger
import os
import random
import time

import gevent
url = "https://pt.keepfrds.com/blackjack.php"
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh",
    "Cookie": COOKIE,
    "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}


def get_state(url) -> dict[str, dict]:
    proxies = {"http": PROXY, "https": PROXY} if PROXY else None
    error = 0
    while error < 3:
        try:
            with requests.get(url, proxies=proxies) as r:
                if r.status_code == 200:
                    return r.json()
                else:
                    error += 1
                    logger.error(f"请求错误{error}次,错误代码{r.status_code}")
        except Exception as e:
            error += 1
            logger.error(f"请求错误{error}次,{e}")


def post_state(url, data) -> dict:
    proxies = {"http": PROXY, "https": PROXY} if PROXY else None
    error = 0
    while error < 3:
        try:
            with requests.post(url, data=data, proxies=proxies) as r:
                if r.status_code == 200:
                    return r.json()
                else:
                    logger.error(r.status_code)
            error += 1
            logger.error(f"请求错误{error}次,错误代码{r.status_code}")
        except Exception as e:
            error += 1
            logger.error(f"请求错误{error}次,{e}")


def parse_form_from_html(soup):
    form_elements = {}
    for input_tag in soup.find_all("input"):
        if "name" in input_tag.attrs:
            form_elements[input_tag["name"]] = input_tag["value"]
    logger.info(f"找到平局信息：{form_elements},开始平局")
    return form_elements


def find_game(userid):
    error = 0
    while error < 3:
        try:
            with requests.get(url, headers=headers) as response:
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    forms = soup.select(
                        "#game_available tr td:nth-of-type(4) form")
                    for form in forms:
                        if form.find("input", value=str(userid)):
                            return parse_form_from_html(form)
                    return None
                else:
                    raise (response.status_code)
        except:
            error += 1
            logger.error(f"请求错误{error}次")
            # traceback.print_exc()


def my_game_state():
    error = 0
    while error < 3:
        try:
            with requests.get(url, headers=headers) as response:
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    forms = soup.select("#details tr")
                    if forms and forms[-1].text.strip() == "请等待上局结束":
                        return 1
                    return None
                else:
                    raise (response.status_code)
        except:
            error += 1
            logger.error(f"请求错误{error}次")
            # traceback.print_exc()


def game(data):
    error = 0
    while error < 3:
        try:
            with requests.post(url, headers=headers, data=data) as response:
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    element = soup.select_one("#details b")
                    if element:
                        text = element.get_text(strip=True)
                        try:
                            point = int(text.split("=")[-1])
                        except:
                            logger.error("未能获取到页面点数，返回0")
                            point = 0
                        return point, None
                    else:
                        element = soup.select_one(
                            "#outer table table td") or soup.select_one("form strong")
                        if element:
                            logger.warning(element.text)
                            return None, element.text
                        else:
                            if SAVE_ERR_PAGE:
                                if not os.path.exists("error_pages"):
                                    os.makedirs("error_pages")
                                with open(f"error_pages/error_page_{int(time.time())}.html", "w") as f:
                                    f.write(soup.prettify())
                                logger.error("未知错误,已将页面保存至error_pages文件夹")
                        logger.error("未能获取到页面点数，返回None")
                        return None, None
                else:
                    raise (response.status_code)
        except:
            error += 1
            logger.error(f"请求错误{error}次")
    return None, None


def boom_game(boom_data, my_userid):
    start_data = boom_data
    continue_data = {"game": "hit", "continue": "yes", "userid": my_userid}
    hit_data = {"game": "hit", "userid": my_userid}
    stop_data = {"game": "stop", "userid": my_userid}

    s, e = game(start_data)
    if not s:
        if e == "该对局已结束":
            logger.warning(f"平局：对局被人抢了")
            return None
        elif e == "您必须先完成当前的游戏。":
            logger.warning(f"平局：上局未结束，无法获知对局对象，直接结束")
            game(stop_data)
            return None
        else:
            logger.warning("平局：月月链接错误，稍后重试")
            return None
    while s < 21:
        logger.info(f"平局：当前点数{s}，继续抓牌")
        s_, e = game(hit_data)
        if s_:
            s = s_
        else:
            if e == "Starship":
                logger.warn("平局：对局已结束")
                return None
            logger.error("平局：获取对局数据失败，直接结束")
            game(stop_data)
            return None
    if s == 21:
        logger.info(f"平局：当前点数{s}，平局失败")
        return s
    else:
        logger.info(f"平局：当前点数{s}，平局成功")
        return s


def do_game(amount=100):
    start_data = {"game": "hit", "start": "yes",
                  "amount": amount, "downloads": 0}
    continue_data = {"game": "hit", "continue": "yes"}
    hit_data = {"game": "hit", "userid": 0}
    stop_data = {"game": "stop", "userid": 0}
    remain_point = REMAIN_POINT if random.random(
    ) > REMAIN_POINT_LOW_P else REMAIN_POINT_LOW
    s, e = game(start_data)
    if not s:
        if e == "您必须先完成当前的游戏。":
            s, e = game(continue_data)
        else:
            return
    while s < remain_point:
        logger.info(f"当前点数{s}，继续抓牌")
        s_, e = game(hit_data)
        if s_:
            s = s_
        else:
            if e == "Starship":
                logger.warn("当前点数{s}，对局已结束")
                return s
            else:
                logger.error("当前点数{s}，访问错误，等待重试")
                return None
    if s == 21:
        logger.info(f"当前点数{s}，完美")
    elif s < 21:
        logger.info(f"当前点数{s}，停止抓牌")
        s, e = game(stop_data)
    else:
        logger.info(f"当前点数{s}，爆了")
    return s


def game_state(userid):
    error = 0
    state = []
    while error < 3:
        try:
            with requests.get(url, headers=headers) as response:
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    inputs = soup.select(
                        "#game_available tr td:nth-of-type(4) form input[name='userid']"
                    )
                    state = [input["value"] for input in inputs]
                    forms = soup.select("#details tr")
                    if forms and forms[-1].text.strip() == "请等待上局结束":
                        state.append(str(userid))
                    return state
                else:
                    logger.error(response.status_code)
                    raise (response.status_code)
        except Exception as e:
            logger.error(e)
            error += 1
            logger.error(f"请求错误{error}次")
            gevent.sleep(3)


if __name__ == "__main__":
    s = {'game': 'hit', 'start': 'yes', 'userid': 31341,
         'amount': 1000, 'downloads': '0'}
    start_data = {"game": "hit", "start": "yes",
                  "amount": 1000, "downloads": 0}
    hit_data = {"game": "hit", "userid": 0}
    # game(hit_data)
    print(boom_game(s, 40074))
