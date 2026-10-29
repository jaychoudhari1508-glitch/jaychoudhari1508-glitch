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
    # leg angles from the heading (radians): two pairs forward, two pairs backward
    LEG_ANGLES = [0.55, 1.2, 1.95, 2.6]

    def __init__(self, scale, follow, offset):
        self.s = scale
        self.follow = follow
        self.offset = offset
        self.x = random.random() * W
        self.y = random.random() * H
        self.vx = self.vy = 0.0
        self.heading = -math.pi / 2          # head points up at the start
        self.legs = []
        for side in (-1, 1):
            for ang in self.LEG_ANGLES:
                self.legs.append({
                    "ang": ang, "side": side,
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
            # turn smoothly towards the direction of travel
            target = math.atan2(self.vy, self.vx)
            diff = (target - self.heading + math.pi) % (2 * math.pi) - math.pi
            self.heading += diff * 0.12

        reach = 85 * self.s
        for i, L in enumerate(self.legs):
            ra = self.heading + L["side"] * L["ang"]
            rx = self.x + math.cos(ra) * reach + self.vx * 6
            ry = self.y + math.sin(ra) * reach + self.vy * 6
            if L["t"] >= 1:
                if math.hypot(L["foot"][0] - rx, L["foot"][1] - ry) > reach * 0.45:
                    L["from"] = list(L["foot"])
                    L["to"] = [rx, ry]
                    L["t"] = 0.0
            else:
                L["t"] = min(1.0, L["t"] + 0.16 + sp * 0.01)
                e = L["t"] * L["t"] * (3 - 2 * L["t"])
                L["foot"][0] = L["from"][0] + (L["to"][0] - L["from"][0]) * e
                L["foot"][1] = L["from"][1] + (L["to"][1] - L["from"][1]) * e
                if L["t"] >= 1:
                    spark(L["foot"][0], L["foot"][1], 2)

    def draw_leg(self, L):
        s = self.s
        hx, hy = self.x, self.y
        dx, dy = L["foot"][0] - hx, L["foot"][1] - hy
        d = math.hypot(dx, dy) or 0.001
        seg = 52 * s
        max_d = seg * 2 - 2
        if d > max_d:
            dx *= max_d / d
            dy *= max_d / d
            d = max_d
        h = math.sqrt(max(0.0, seg * seg - (d / 2) ** 2))
        h = min(h, 0.4 * d)
        nx, ny = -dy / d, dx / d
        # knee bends away from the body axis
        px, py = -math.sin(self.heading), math.cos(self.heading)
        if (nx * px + ny * py) * L["side"] < 0:
            nx, ny = -nx, -ny
        kx, ky = hx + dx / 2 + nx * h, hy + dy / 2 + ny * h
        fx, fy = hx + dx, hy + dy
        # curve through hip -> knee -> foot (quadratic bezier)
        cx, cy = 2 * kx - (hx + fx) / 2, 2 * ky - (hy + fy) / 2
        pts = []
        steps = 12
        for i in range(steps + 1):
            t = i / steps
            x = (1 - t) ** 2 * hx + 2 * (1 - t) * t * cx + t * t * fx
            y = (1 - t) ** 2 * hy + 2 * (1 - t) * t * cy + t * t * fy
            pts.append((x, y, t))
        left, right = [], []
        for i, (x, y, t) in enumerate(pts):
            x2, y2, _ = pts[min(i + 1, steps)]
            x1, y1, _ = pts[max(i - 1, 0)]
            tx, ty = x2 - x1, y2 - y1
            tl = math.hypot(tx, ty) or 1
            ox, oy = -ty / tl, tx / tl
            w = (5.5 * (1 - t) + 0.6) * s          # thick at the body, sharp at the tip
            left.append((x + ox * w, y + oy * w))
            right.append((x - ox * w, y - oy * w))
        poly = left + right[::-1]
        flat = [c for p in poly for c in p]
        canvas.create_polygon(*flat, fill="white", outline="")

    def draw(self):
        s = self.s
        for L in self.legs:
            self.draw_leg(L)
        ux, uy = math.cos(self.heading), math.sin(self.heading)
        px, py = -uy, ux
        # abdomen (big, behind), head (small, in front)
        ax, ay = self.x - ux * 11 * s, self.y - uy * 11 * s
        r = 12 * s
        canvas.create_oval(ax - r, ay - r, ax + r, ay + r, fill="white", outline="")
        hx, hy = self.x + ux * 9 * s, self.y + uy * 9 * s
        r2 = 8 * s
        canvas.create_oval(hx - r2, hy - r2, hx + r2, hy + r2, fill="white", outline="")
        # two small curved pincers on the head
        for side in (-1, 1):
            bx, by = hx + ux * 5 * s + px * side * 4 * s, hy + uy * 5 * s + py * side * 4 * s
            mx, my = bx + ux * 7 * s + px * side * 5 * s, by + uy * 7 * s + py * side * 5 * s
            ex, ey = bx + ux * 12 * s + px * side * 1 * s, by + uy * 12 * s + py * side * 1 * s
            canvas.create_line(bx, by, mx, my, ex, ey, fill="white",
                               width=max(1, 2 * s), smooth=True, capstyle="round")


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