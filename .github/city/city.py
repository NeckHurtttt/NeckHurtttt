#!/usr/bin/env python3
"""Neon City: cada edificio es una semana de contribuciones. Uso: GITHUB_TOKEN=... python city.py usuario salida.svg"""
import json, math, os, pathlib, random, sys, urllib.request
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = pathlib.Path(__file__).parent
CREAM, DIM, BG = '#e8f6ff', '#8a86b0', '#06040e'
ORANGE, YELLOW, PINK, CYAN, PURPLE = '#ff8a1e', '#fcee0a', '#ff2a6d', '#05d9e8', '#9d4edd'
MES = 'ENE FEB MAR ABR MAY JUN JUL AGO SEP OCT NOV DIC'.split()

class F:
    def __init__(s, p):
        s.t = TTFont(p); s.gs = s.t.getGlyphSet(); s.cm = s.t.getBestCmap(); s.upm = s.t['head'].unitsPerEm
    def g(s, c): return s.gs[s.cm.get(ord(c), s.cm[32])]
    def width(s, txt, size, tr=0): return sum(s.g(c).width * size / s.upm + tr for c in txt)
    def path(s, txt, x, y, size, tr=0):
        k = size / s.upm; pen = SVGPathPen(s.gs, ntos=lambda v: f'{v:.1f}'.rstrip('0').rstrip('.'))
        for c in txt:
            g = s.g(c); g.draw(TransformPen(pen, (k, 0, 0, -k, x, y))); x += g.width * k + tr
        return pen.getCommands()
MONO, MONOB = F(HERE/'mono.ttf'), F(HERE/'monob.ttf')

def T(txt, x, y, size, f=MONO, fill=CREAM, anchor='s', tr=0):
    if anchor == 'e': x -= f.width(txt, size, tr)
    return f'<path fill="{fill}" d="{f.path(txt, x, y, size, tr)}"/>'

def frame(w, h, l, r, ac):
    c = 14
    return (f'<path d="M{c} .5H{w-.5}V{h-c}L{w-c} {h-.5}H.5V{c}Z" fill="none" stroke="{ac}" stroke-width="1.5"/>'
            f'<path d="M.5 {c+18}V{c}L{c} .5H{c+40}" fill="none" stroke="{ac}" stroke-width="4"/><rect x="{w-60}" y="{h-5}" width="40" height="3" fill="{ac}"/>'
            + T(l, 20, 24, 10.5, MONOB, ac, tr=1.4) + T(r, w - 20, 24, 10, anchor='e', tr=1.2, fill=DIM)
            + f'<rect x="20" y="32" width="{w-40}" height="1" fill="{DIM}" opacity=".35"/>')

def fetch(user):
    q = '{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}' % user
    req = urllib.request.Request('https://api.github.com/graphql', json.dumps({'query': q}).encode(),
                                 {'Authorization': 'bearer ' + os.environ['GITHUB_TOKEN'], 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req))['data']['user']['contributionsCollection']['contributionCalendar']

def build(cal):
    random.seed(7)
    weeks = [[d['contributionCount'] for d in w['contributionDays']] for w in cal['weeks']]
    sums = [sum(w) for w in weeks]; top = max(max(sums), 1); tot = cal['totalContributions']
    lvlc = lambda c: DIM if not c else (PURPLE if c < 3 else CYAN if c < 8 else PINK if c < 20 else YELLOW)
    W, H = 1000, 270; bw = 920 / len(weeks); base = 230
    o = (f'<defs><linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d0722"/><stop offset="1" stop-color="#3a0d4a"/></linearGradient></defs>'
         f'<rect width="{W}" height="{H}" fill="url(#sk)"/>' + frame(W, H, 'NEON CITY // CADA EDIFICIO ES UNA SEMANA', f'{tot} COMMITS · 1 AÑO', CYAN))
    for i, (wk, s) in enumerate(zip(weeks, sums)):
        h = 14 + 150 * math.sqrt(s / top); x = 40 + i * bw
        o += f'<rect x="{x:.1f}" y="{base-h:.1f}" width="{bw-3:.1f}" height="{h:.1f}" fill="#1a1036" stroke="{lvlc(max(wk))}" stroke-opacity=".5"/>'
        nwin = int((h - 10) / 7); lit = min(nwin * 2, s)
        for r in range(nwin):
            for cc in range(2):
                on = r * 2 + cc < lit
                o += f'<rect x="{x+2.5+cc*6:.1f}" y="{base-h+5+r*7:.1f}" width="3.5" height="4" fill="{random.choice((CYAN, PINK, YELLOW)) if on else "#2b1b5e"}" opacity="{.9 if on else .5}"/>'
        if s == top and s:
            o += f'<rect class="bl" x="{x+bw/2-2:.1f}" y="{base-h-14:.1f}" width="2" height="14" fill="{PINK}"/>' + T(f'RÉCORD {s}', x - 30, base - h - 20, 9, MONOB, PINK)
    o += f'<rect x="20" y="{base}" width="{W-40}" height="2" fill="{PINK}"/>'
    prev = None
    for i, w in enumerate(cal['weeks']):
        m = int(w['contributionDays'][0]['date'][5:7])
        if m != prev: o += T(MES[m-1], 40 + i * bw, base + 18, 9, fill=DIM, tr=1); prev = m
    o += (f'<g class="car"><rect x="-60" y="70" width="34" height="8" rx="3" fill="{PINK}"/><rect x="-54" y="66" width="18" height="5" fill="{CYAN}"/>'
          f'<rect x="-26" y="72" width="40" height="2" fill="{PINK}" opacity=".4"/></g>')
    rain = ''.join(f'<rect x="{random.randint(0, W)}" y="{random.randint(-H, H)}" width="1" height="{random.randint(6, 14)}" fill="{CYAN}" opacity=".3"/>' for _ in range(70))
    o += f'<g class="rain">{rain}</g>'
    css = ('.bl{animation:bl 1.1s steps(2) infinite}@keyframes bl{50%{opacity:.1}}.rain{animation:rn .9s linear infinite}@keyframes rn{to{transform:translate(0,260px)}}'
           '.car{animation:ca 7s linear infinite}@keyframes ca{to{transform:translateX(1080px)}}@media (prefers-reduced-motion: reduce){*{animation:none!important}}')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Neon City: {tot} contribuciones, cada edificio es una semana">'
            f'<style>{css}</style><rect width="{W}" height="{H}" fill="{BG}"/>{o}</svg>')

if __name__ == '__main__':
    out = pathlib.Path(sys.argv[2]); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(fetch(sys.argv[1])))
