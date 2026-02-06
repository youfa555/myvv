# fetch_and_build.py
import os, argparse, base64, re, requests, time, html
from bs4 import BeautifulSoup
from collections import OrderedDict

SRC = "https://github.com/Alvin9999/new-pac/wiki/v2ray%E5%85%8D%E8%B4%B9%E8%B4%A6%E5%8F%B7"
UA  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"

# 支持的协议
SCHEMES = ("vmess","vless","trojan","ssr","ss","hysteria2","hy2","hysteria")

# URL 内允许的字符集合（RFC3986 常见安全字符 + 一些常见扩展）
URL_SAFE_CHARS = r"A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%"

# 从可视文本中“跨行”提取，匹配时允许出现换行和空白，提取后再把空白移除
URI_TXT_RE = re.compile(
    r'((?:' + "|".join(SCHEMES) + r')://(?:[' + URL_SAFE_CHARS + r']|\s)+)',
    re.IGNORECASE
)

# href 中的链接通常更干净（但 GitHub 可能会截断），按传统“非空白非尖括号”提取
URI_HREF_RE = re.compile(
    r'^(?:' + "|".join(SCHEMES) + r')://[' + URL_SAFE_CHARS + r']+$',
    re.IGNORECASE
)

# 需要剔除的尾随字符（中英文标点、空白、零宽）
TRAILING = ' \t\r\n.,;:!?)>]}，。；：、）】》”’…\u3000\u200b\ufeff'

def normalize(u: str) -> str:
    # HTML 反转义，把 &amp; 还原为 &
    u = html.unescape(u.strip())
    # 移除零宽字符
    u = u.replace("\u200b", "").replace("\ufeff", "")
    # 去掉结尾标点/空白
    u = u.rstrip(TRAILING)
    # 协议小写
    if "://" in u:
        scheme, rest = u.split("://", 1)
        u = scheme.lower() + "://" + rest
    return u

def dedup_prefer_longer(urls):
    # 以“去掉 #fragment 后”的主体作为 key，保留更长的那一条
    best = {}
    order = []
    for u in urls:
        key = u.split("#", 1)[0]
        if key not in best or len(u) > len(best[key]):
            best[key] = u
            if key not in order:
                order.append(key)
    return [best[k] for k in order]

def extract_nodes_from_html(html_text: str):
    soup = BeautifulSoup(html_text, "html.parser")
    out = []

    # 1) href 提取（相对干净）
    for a in soup.select('a[href]'):
        href = a.get("href", "").strip()
        href = html.unescape(href)
        if URI_HREF_RE.match(href):
            out.append(href)

    # 2) 可视文本“跨行”提取（把 URL 内的空白全部去掉）
    text = soup.get_text("\n")
    # 先简单去掉零宽
    text = text.replace("\u200b", "").replace("\ufeff", "")
    for m in URI_TXT_RE.finditer(text):
        raw = m.group(0)
        compact = re.sub(r'\s+', '', raw)  # 去掉 URL 内所有空白（包含换行）
        out.append(compact)

    # 3) 规范化
    normed = [normalize(x) for x in out if x]
    # 4) 偏向更长的去重（先去“主体重复”），再做一次顺序去重
    normed = dedup_prefer_longer(normed)
    uniq = list(OrderedDict.fromkeys(normed))

    # 可选过滤：只保留 vless + hysteria2（如果你只想要这两种，取消下一行注释）
    # uniq = [u for u in uniq if u.startswith(("vless://","hysteria2://","hy2://"))]

    return uniq

def get_source():
    """返回抓取源：优先使用命令行 `--src`，其次使用环境变量 `SRC_OVERRIDE`，最后使用默认 `SRC`。"""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--src', help='override source URL')
    args, _ = parser.parse_known_args()
    return args.src or os.getenv('SRC_OVERRIDE') or SRC

def main():
    src = get_source()
    r = requests.get(src, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    html_text = r.text

    nodes = extract_nodes_from_html(html_text)

    # 输出
    import os
    os.makedirs("public", exist_ok=True)

    with open("public/nodes.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(nodes) + "\n")

    b64 = base64.b64encode(("\n".join(nodes) + "\n").encode("utf-8")).decode("utf-8")
    with open("public/v2rayn.txt", "w", encoding="utf-8") as f:
        f.write(b64)

    with open("public/status.json", "w", encoding="utf-8") as f:
        f.write('{"count": %d, "updated_at": %d}\n' % (len(nodes), int(time.time())))

if __name__ == "__main__":
    main()
