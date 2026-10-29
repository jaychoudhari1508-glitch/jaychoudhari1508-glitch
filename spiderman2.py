import tkinter as tk
import math
import random

W, H = 1000, 650

root = tk.Tk()
root.title("Spider Cursor Animation")
canvas = tk.Canvas(root, width=W, height=H, bg="black", highlightthickness=0, cursor="none")  # system cursor hidden, we draw our own
canvas.pack(fill="both", expand=True)

mouse = {"x": W / 2, "y": H / 2}


def on_move(e):
    mouse["x"], mouse["y"] = e.x, e.y


canvas.bind("<Motion>", on_move)

particles = []

# background stars (twinkling)
stars = [{"x": random.randint(0, W), "y": random.randint(0, H),
          "r": random.choice([0.6, 0.8, 1.0, 1.4]), "ph": random.random() * 6.28,
          "sp": random.uniform(0.02, 0.07)} for _ in range(160)]
tick = 0


def draw_stars():
    for st in stars:
        b = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(tick * st["sp"] + st["ph"]))
        g = int(200 * b)
        c = f"#{g:02x}{g:02x}{g:02x}"
        r = st["r"]
        canvas.create_oval(st["x"] - r, st["y"] - r, st["x"] + r, st["y"] + r, fill=c, outline="")


def draw_cursor():
    x, y = mouse["x"], mouse["y"]
    canvas.create_polygon(x, y, x, y + 17, x + 4, y + 13, x + 8, y + 21, x + 11, y + 19,
                          x + 7, y + 12, x + 12, y + 12,
                          fill="white", outline="black")


def spark(x, y, n):
    for _ in range(n):
        a = random.random() * math.pi * 2
        s = random.random() * 1.5
        particles.append({"x": x, "y": y, "vx": math.cos(a) * s, "vy": math.sin(a) * s,
                          "life": 1.0, "size": random.random() * 1.6 + 0.6})


class Spider:
    def __init__(self, scale, follow, offset):
        self.s = scale
        self.follow = follow
        self.offset = offset
        self.x = random.random() * W
        self.y = random.random() * H
        self.vx = self.vy = 0.0
        self.heading = 0.0
        self.legs = []
        n = 8
        for i in range(n):
            side = -1 if i < n // 2 else 1
            k = i % (n // 2)
            self.legs.append({
                "base": side * (0.45 + k * 0.5), "side": side,
                "foot": [self.x, self.y], "from": [self.x, self.y],
                "to": [self.x, self.y], "t": 1.0,
            })

    def update(self):
        tx, ty = mouse["x"] + self.offset[0], mouse["y"] + self.offset[1]
        self.vx += (tx - self.x) * self.follow
        self.vy += (ty - self.y) * self.follow
        self.vx *= 0.86
        self.vy *= 0.86
        self.x += self.vx
        self.y += self.vy
        sp = math.hypot(self.vx, self.vy)
        if sp > 0.3:
            self.heading = math.atan2(self.vy, self.vx)

        reach = 85 * self.s
        for L in self.legs:
            ra = self.heading + L["base"] * L["side"] + (-0.2 if L["side"] < 0 else 0.2)
            rx = self.x + math.cos(ra) * reach + self.vx * 6
            ry = self.y + math.sin(ra) * reach + self.vy * 6
            if L["t"] >= 1:
                if math.hypot(L["foot"][0] - rx, L["foot"][1] - ry) > reach * 0.55:
                    L["from"] = list(L["foot"])
                    L["to"] = [rx, ry]
                    L["t"] = 0.0
            else:
                L["t"] = min(1.0, L["t"] + 0.14 + sp * 0.01)
                e = L["t"] * L["t"] * (3 - 2 * L["t"])
                L["foot"][0] = L["from"][0] + (L["to"][0] - L["from"][0]) * e
                L["foot"][1] = L["from"][1] + (L["to"][1] - L["from"][1]) * e
                if L["t"] >= 1:
                    spark(L["foot"][0], L["foot"][1], 3)

    def draw(self):
        seg = 58 * self.s
        for L in self.legs:
            hx, hy = self.x, self.y
            dx, dy = L["foot"][0] - hx, L["foot"][1] - hy
            d = math.hypot(dx, dy) or 0.001
            max_d = seg * 2 - 1
            if d > max_d:
                dx *= max_d / d
                dy *= max_d / d
                d = max_d
            h = math.sqrt(max(0.0, seg * seg - (d / 2) ** 2))
            mx, my = hx + dx / 2, hy + dy / 2
            nx, ny = -dy / d, dx / d
            kx, ky = mx + nx * h * L["side"], my + ny * h * L["side"]
            canvas.create_line(hx, hy, kx, ky, hx + dx, hy + dy,
                               fill="white", width=max(1, 1.4 * self.s), capstyle="round",
                               joinstyle="round")
        r = 4 * self.s
        canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill="white", outline="")
        bx = self.x - math.cos(self.heading) * 9 * self.s
        by = self.y - math.sin(self.heading) * 9 * self.s
        r2 = 5 * self.s
        canvas.create_oval(bx - r2, by - r2, bx + r2, by + r2, fill="white", outline="")


spiders = [
    Spider(1.0, 0.010, (-30, 20)),
    Spider(0.85, 0.007, (40, 35)),
]


def loop():
    global tick
    tick += 1
    canvas.delete("all")
    draw_stars()
    for sp in spiders:
        sp.update()
        sp.draw()
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 0.02
        if p["life"] <= 0:
            particles.remove(p)
            continue
        g = int(255 * p["life"])
        c = f"#{g:02x}{g:02x}{g:02x}"
        r = p["size"]
        canvas.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r, fill=c, outline="")
    draw_cursor()
    root.after(16, loop)


loop()
root.mainloop()