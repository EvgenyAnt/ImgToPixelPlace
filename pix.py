import requests
import math
from PIL import Image
import time
import queue
import threading
import json
import sys


try:
    image = str(sys.argv[1])
    place_id = str(sys.argv[2])
    x_offset = int(sys.argv[3])
    y_offset = int(sys.argv[4])
    phpsessid = str(sys.argv[5])
except:
    print('python pix.py <image> <place_id> <x_offset> <y_offset> <php_session>')
    exit()


divs = """
<div class="palette-color" style="background-color:#FFFFFF" data-index="0"></div><div class="palette-color" style="background-color:#C4C4C4" data-index="1"></div><div class="palette-color" style="background-color:#888888" data-index="2"></div><div class="palette-color" style="background-color:#222222" data-index="3"></div><div class="palette-color" style="background-color:#FFA7D1" data-index="4"></div><div class="palette-color" style="background-color:#E50000" data-index="5"></div><div class="palette-color" style="background-color:#E59500" data-index="6"></div><div class="palette-color" style="background-color:#A06A42" data-index="7"></div><div class="palette-color" style="background-color:#E5D900" data-index="8"></div><div class="palette-color" style="background-color:#94E044" data-index="9"></div><div class="palette-color" style="background-color:#02BE01" data-index="10"></div><div class="palette-color color-selected" style="background-color:#00D3DD" data-index="11"></div><div class="palette-color" style="background-color:#0083C7" data-index="12"></div><div class="palette-color" style="background-color:#0000EA" data-index="13"></div><div class="palette-color" style="background-color:#CF6EE4" data-index="14"></div><div class="palette-color" style="background-color:#820080" data-index="15"></div><div class="palette-color" style="background-color:#ffdfcc" data-index="16">
"""
flag1 = 'style="background-color:'
flag2 = '" data-index='
time_left = 0
color_keys = {}

data = divs.split("</div>")
for item in data:
    color = item[item.find(flag1)+len(flag1):item.find(flag2)]
    color = color.lstrip('#')
    color = tuple(int(color[i:i+2], 16) for i in (0, 2 ,4))
    index = item[item.find(flag2)+len(flag2)+1:item.find(">")-1]
    color_keys[color] = index


que = queue.Queue()
que2 = queue.Queue()
s = requests.session()

s.cookies['PHPSESSID'] = phpsessid

def distance(c1, c2):
    (r1,g1,b1) = c1
    (r2,g2,b2) = c2
    return math.sqrt((r1 - r2)**2 + (g1 - g2) ** 2 + (b1 - b2) **2)

im = Image.open(image)
rgb_im = im.convert('RGB')
x_val, y_val = im.size
for x in range(0, x_val):
    for y in range(0, y_val):
        r, g, b = rgb_im.getpixel((x, y))
        this_color = (r, g, b)
        colors = list(color_keys.keys())
        c_colors = sorted(colors, key=lambda color: distance(color, this_color))
        c_color = c_colors[0]
        index_col = color_keys[c_color]
        que.put([x+x_offset, y+y_offset, index_col])

def pix():
    while que.qsize() > 0:
        try:
            item = que.get()
            r = s.post('https://pixelplace.io/back/placepixelV3.php', data={'attemptPlaceV3': 'true', 'x': item[0], 'y': item[1], 'c': item[2], 'b': place_id}, timeout=3)
            try:
                r = json.loads(r.content.decode())
            except:
                r = []
            if 'success' in r and r['success'] == False:
                que.put(item)
                time.sleep(int(r['data']['secondsLeft']))
        except Exception as ex:
            que2.put(ex)
            que.put(item)
            time.sleep(3)

for i in range(0, 100):
    th = threading.Thread(target=pix)
    th.daemon = True
    th.start()


while que.qsize() > 0:
    print('In queue:'+str(que.qsize()))
    while que2.qsize() > 0:
        print(que2.get())
    time.sleep(10)

