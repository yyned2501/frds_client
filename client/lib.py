import monkey
import requests
from bs4 import BeautifulSoup
from config import COOKIE, REMAIN_POINT
from log import logger
import traceback

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
            traceback.print_exc()


def post_state(url, data) -> dict:
    error = 0
    while error < 3:
        try:
            with requests.post(url, data=data) as r:
                if r.status_code == 200:
                    rd = r.json()
                    # logger.info(rd)
                    return rd
                else:
                    logger.error(r.status_code)
            error += 1
            logger.error(f"请求错误{error}次,错误代码{r.status_code}")
        except:
            error += 1
            logger.error(f"请求错误{error}次")
            traceback.print_exc()


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
                    forms = soup.select("#game_available tr td:nth-of-type(4) form")
                    for form in forms:
                        if form.find("input", value=str(userid)):
                            return parse_form_from_html(form)
                    return None
                else:
                    raise (response.status_code)
        except:
            error += 1
            logger.error(f"请求错误{error}次")
            traceback.print_exc()


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
            traceback.print_exc()


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
                            point = 0
                        return point
                    else:
                        logger.error(soup.prettify())
                        return None
                else:
                    raise (response.status_code)
        except:
            error += 1
            logger.error(f"请求错误{error}次")
            traceback.print_exc()
    return 22


def boom_game(userid, my_userid):
    start_data = find_game(userid)
    continue_data = {"game": "hit", "continue": "yes", "userid": my_userid}
    hit_data = {"game": "hit", "userid": my_userid}
    stop_data = {"game": "stop", "userid": my_userid}
    if not start_data:
        logger.warn(f"平局：对局已结束")
        return None
    s = game(start_data) or game(continue_data)
    if not s:
        logger.warn(f"平局：对局被人抢了")
        return None
    while s < 21:
        logger.info(f"平局：当前点数{s}，继续抓牌")
        s = game(hit_data)
    if s == 21:
        logger.info(f"平局：当前点数{s}，平局失败")
        return s
    else:
        logger.info(f"平局：当前点数{s}，平局成功")
        return s


def do_game(amount=100):
    start_data = {"game": "hit", "start": "yes", "amount": amount, "downloads": 0}
    continue_data = {"game": "hit", "continue": "yes"}
    hit_data = {"game": "hit", "userid": 0}
    stop_data = {"game": "stop", "userid": 0}
    s = game(start_data)
    if not s:
        s = game(continue_data)
    if not s:
        logger.info("上一场未结束")
        return
    while s < REMAIN_POINT:
        logger.info(f"当前点数{s}，继续抓牌")
        s = game(hit_data) or 22
    if s == 21:
        logger.info(f"当前点数{s}，完美")
    elif s < 21:
        logger.info(f"当前点数{s}，停止抓牌")
        game(stop_data)
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


if __name__ == "__main__":
    print(game_state(0))
