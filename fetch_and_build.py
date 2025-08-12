# fetch_and_build.py
import base64, re, requests, time
from bs4 import BeautifulSoup
from collections import OrderedDict

# 需要抓取的页面（就是你给的 Wiki 链接）
SRC = "https://github.com/Alvin9999/new-pac/wiki/v2ray%E5%85%8D%E8%B4%B9%E8%B4%A6%E5%8F%B7"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"

def extract_nodes(s: str):
    pattern = re.compile(r'(?:vmess|vless|trojan|ssr|ss)://[^\s<>"\'`]+', re.IGNORECASE)
    found = pattern.findall(s)
    return list(OrderedDict.fromkeys(found))  # 去重保序

def main():
    r = requests.get(SRC, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    html = r.text

    soup = BeautifulSoup(html, "html.parser")
    txt = soup.get_text("\n")

    nodes = extract_nodes(html) + extract_nodes(txt)
    nodes = list(OrderedDict.fromkeys(nodes))

    # 输出目录
    import os
    os.makedirs("public", exist_ok=True)

    # 纯文本（每行一个 URI）
    with open("public/nodes.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(nodes) + "\n")

    # v2rayN 常用的 base64 订阅
    b64 = base64.b64encode(("\n".join(nodes) + "\n").encode("utf-8")).decode("utf-8")
    with open("public/v2rayn.txt", "w", encoding="utf-8") as f:
        f.write(b64)

    # 简单状态文件
    with open("public/status.json", "w", encoding="utf-8") as f:
        f.write('{"count": %d, "updated_at": %d}\n' % (len(nodes), int(time.time())))

if __name__ == "__main__":
    main()
