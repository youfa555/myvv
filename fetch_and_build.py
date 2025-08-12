# fetch_and_build.py
import base64, re, requests, time, html
from bs4 import BeautifulSoup
from collections import OrderedDict

SRC = "https://github.com/Alvin9999/new-pac/wiki/v2ray%E5%85%8D%E8%B4%B9%E8%B4%A6%E5%8F%B7"
UA  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"

# 需要识别的协议（含 hysteria2 / hy2）
SCHEMES = ("vmess","vless","trojan","ssr","ss","hysteria2","hy2","hysteria")

# 仅用于“可视文本”里的匹配；排除常见中英文括号/引号/标点，避免把结尾符号也抓进去
URI_RE = re.compile(
    r'(?:(?:' + "|".join(SCHEMES) + r')://)[^\s<>"\'`()\[\]{}“”‘’、，。；：！【】《》…]+',
    re.IGNORECASE
)

# 结尾需要剔除的字符（含中英文标点与空白/零宽）
TRAILING = ' \t\r\n.,;:!?)>]}，。；：、）】》”’…\u3000\u200b\ufeff'

def normalize(u: str) -> str:
    # HTML 反转义（把 &amp; 变回 &）
    u = html.unescape(u.strip())
    # 去掉结尾标点/零宽字符
    u = u.rstrip(TRAILING)
    # 协议名统一小写
    if "://" in u:
        scheme, rest = u.split("://", 1)
        u = scheme.lower() + "://" + rest
    return u

def extract_nodes_from_html(html_text: str):
    soup = BeautifulSoup(html_text, "html.parser")
    out = []

    # 1) 先取可点击链接的 href（最干净）
    for a in soup.select('a[href]'):
        href = a.get("href", "")
        if re.match(r'^(?:' + "|".join(SCHEMES) + r')://', href, re.IGNORECASE):
            out.append(href)

    # 2) 再从可视文本中用正则抓一遍（覆盖未加链接的纯文本）
    text = soup.get_text("\n")
    for m in URI_RE.finditer(text):
        out.append(m.group(0))

    # 3) 规范化 + 去重（顺序去重）
    normed = [normalize(x) for x in out if x]
    uniq = list(OrderedDict.fromkeys(normed))

    # 可选：只保留 vless 和 hysteria2（如果你只想这两种，把下一行解除注释）
    # uniq = [u for u in uniq if u.startswith(("vless://","hysteria2://","hy2://"))]

    return uniq

def main():
    r = requests.get(SRC, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    html_text = r.text

    nodes = extract_nodes_from_html(html_text)

    # 输出目录
    import os
    os.makedirs("public", exist_ok=True)

    # 纯文本订阅
    with open("public/nodes.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(nodes) + "\n")

    # v2rayN 常见 base64 订阅
    b64 = base64.b64encode(("\n".join(nodes) + "\n").encode("utf-8")).decode("utf-8")
    with open("public/v2rayn.txt", "w", encoding="utf-8") as f:
        f.write(b64)

    # 便于自查的状态文件
    with open("public/status.json", "w", encoding="utf-8") as f:
        f.write('{"count": %d, "updated_at": %d}\n' % (len(nodes), int(time.time())))

if __name__ == "__main__":
    main()
