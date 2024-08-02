import requests
from bs4 import BeautifulSoup
from config import COOKIE


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


def parse_form_from_html(soup):
    form_elements = {}
    for input_tag in soup.find_all("input"):
        if "name" in input_tag.attrs:
            form_elements[input_tag["name"]] = input_tag["value"]
    return form_elements


def find_game(userid):
    with requests.get(url, headers=headers) as response:
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            forms = soup.select("#game_available tr td:nth-of-type(4) form")
            for form in forms:
                if form.find("input", value=str(userid)):
                    return parse_form_from_html(form)
        else:
            raise (response.status_code)


def my_game_state():
    with requests.get(url, headers=headers) as response:
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            forms = soup.select("#details tr")
            if forms and forms[-1].text.strip() == "请等待上局结束":
                return forms[-1].text.strip()
            return None
        else:
            raise (response.status_code)


def game(data):
    with requests.post(url, headers=headers, data=data) as response:
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            with open("a.html", "w") as f:
                f.write(response.text)
            element = soup.select_one("#details b")
            if element:
                text = element.get_text(strip=True)
                return int(text.split("=")[-1])
        else:
            raise (response.status_code)


def boom_game(userid, my_userid=40074):
    start_data = find_game(userid)
    continue_data = {"game": "hit", "continue": "yes", "userid": my_userid}
    hit_data = {"game": "hit", "userid": my_userid}
    stop_data = {"game": "stop", "userid": my_userid}
    s = game(start_data)
    if not s:
        s = game(continue_data)
    while s < 21:
        print(f"当前点数{s}，继续抓牌")
        s = game(hit_data)
    if s == 21:
        print(f"当前点数{s}，平局失败")
        return s
    else:
        print(f"当前点数{s}，平局成功")
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
        print("上一场未结束")
        return
    while s < 20:
        print(f"当前点数{s}，继续抓牌")
        s = game(hit_data)
    if s == 21:
        print(f"当前点数{s}，完美")
    elif s == 20:
        print(f"当前点数{s}，停止抓牌")
        return game(stop_data)
    else:
        print(f"当前点数{s}，爆了")
    return s
