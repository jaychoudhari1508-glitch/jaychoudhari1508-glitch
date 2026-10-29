import math
import time

import cv2
import numpy as np
import turtle


IMAGE = "spiderman.png"   
MUSIC = "song.mp3"       
COLORS = 12              
SKETCH = True            
DRAW_SECONDS = 15        
FILL_SECONDS = 15         
OUTLINE_AT_END = False    
FPS = 60                 
BOX_W, BOX_H = 860, 640   
SS = 2                    
MIN_AREA = 40             
raw = cv2.imread(IMAGE, cv2.IMREAD_UNCHANGED)

if raw is None:
    print("Image not found!")
    raise SystemExit


if raw.ndim == 2:
    bgr = cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)
elif raw.shape[2] == 4:
    a = raw[:, :, 3:4].astype(np.float32) / 255.0
    bgr = (raw[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)
else:
    bgr = raw

ih, iw = bgr.shape[:2]
f = min(BOX_W / iw, BOX_H / ih)
bw, bh = iw * f, ih * f                      
ww, wh = max(2, round(bw * SS)), max(2, round(bh * SS))   

interp = cv2.INTER_AREA if f * SS < 1 else cv2.INTER_CUBIC
work = cv2.resize(bgr, (ww, wh), interpolation=interp)
work = cv2.bilateralFilter(work, 7, 35, 7)   


s = 300 / max(ww, wh)
small = cv2.resize(work, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else work
data = small.reshape(-1, 3).astype(np.float32)
K = int(max(2, min(COLORS, len(np.unique(data, axis=0)))))
crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
_, _, centers = cv2.kmeans(data, K, None, crit, 3, cv2.KMEANS_PP_CENTERS)


wf = work.astype(np.float32)
best = np.full((wh, ww), np.inf, np.float32)
lab = np.zeros((wh, ww), np.uint8)
for k in range(K):
    d = ((wf - centers[k]) ** 2).sum(axis=2)
    better = d < best
    best[better] = d[better]
    lab[better] = k
lab = cv2.medianBlur(lab, 5)                  

counts = np.bincount(lab.ravel(), minlength=K)
order = [int(k) for k in np.argsort(-counts) if counts[k] > 0]
base = order[0]                               


def rgb(k):
    b, g, r = centers[k]
    return int(r), int(g), int(b)


def to_screen(pt):
    x, y = pt
    return (x / SS - bw / 2, bh / 2 - y / SS)


def ring(c):
    c = cv2.approxPolyDP(c, 0.7, True).reshape(-1, 2)
    return [to_screen(p) for p in c]



layers = []   
for k in order[1:]:
    m = (lab == k).astype(np.uint8) * 255
    m = cv2.GaussianBlur(m, (5, 5), 1.2)
    m = (m > 127).astype(np.uint8) * 255
    cnts, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hier is None:
        continue
    hier = hier[0]
    regions = []
    for i, c in enumerate(cnts):
        if hier[i][3] != -1 or len(c) < 4 or cv2.contourArea(c) < MIN_AREA:
            continue
        holes = [ring(cnts[j]) for j in range(len(cnts))
                 if hier[j][3] == i and len(cnts[j]) >= 4 and cv2.contourArea(cnts[j]) >= MIN_AREA]
        regions.append((ring(c), holes))
    if regions:
        layers.append((rgb(k), regions))


screen = turtle.Screen()
screen.setup(width=BOX_W + 60, height=BOX_H + 80)
screen.title("Python Turtle Graphics")
screen.colormode(255)
screen.bgcolor(rgb(base))
screen.tracer(0)                 

t = turtle.Turtle()
t.hideturtle()
t.speed(0)
t.pensize(1)

try:
    import pygame
    pygame.mixer.init()
    pygame.mixer.music.load(MUSIC)
    pygame.mixer.music.play()
except Exception as e:
    print("Music not played:", e)
    print("(गाणे हवे असेल तर: pip install pygame आणि song.mp3 फोल्डरमध्ये ठेवा)")


def refresh():
    screen.update()
    time.sleep(1 / FPS)


def per_frame(total, seconds):
    return max(1, math.ceil(total / max(1, int(seconds * FPS))))


def trace(points, close=True):
    t.penup()
    t.goto(points[0])
    t.pendown()
    for p in points[1:]:
        t.goto(p)
    if close:
        t.goto(points[0])



if SKETCH:
    br = sum(rgb(base)) / 3
    t.pencolor((235, 235, 235) if br < 110 else (30, 30, 30))
    rings = [r for _, regs in layers for outer, holes in regs for r in [outer] + holes]
    total = sum(len(r) for r in rings)
    step = per_frame(total, DRAW_SECONDS)
    n = 0
    for r in rings:
        t.penup()
        t.goto(r[0])
        t.pendown()
        for p in r[1:] + [r[0]]:
            t.goto(p)
            n += 1
            if n % step == 0:
                refresh()
    t.penup()
    screen.update()
    time.sleep(0.8)
    t.clear()                    
 
total = sum(len(o) + sum(len(h) for h in hs) for _, regs in layers for o, hs in regs)
step = per_frame(total, FILL_SECONDS)
n = 0
for col, regs in layers:
    t.color(col, col)
    for outer, holes in regs:
        t.penup()
        t.goto(outer[0])
        t.begin_fill()
        t.pendown()
        for p in outer[1:] + [outer[0]]:
            t.goto(p)
        for hole in holes:                 
            t.goto(hole[0])
            t.pendown()
            for p in hole[1:] + [hole[0]]:
                t.goto(p)
            t.penup()
            t.goto(outer[0])              
        t.end_fill()
        t.penup()
        n += len(outer) + sum(len(h) for h in holes)
        if n >= step:
            refresh()
            n = 0


if OUTLINE_AT_END:
    t.pencolor((20, 20, 20))
    for _, regs in layers:
        for outer, holes in regs:
            trace(outer)
            for h in holes:
                trace(h)

screen.update()
turtle.done()