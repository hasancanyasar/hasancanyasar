"""Gece yarısı GitHub kimliği: python3 identity.py (stdlib + macOS CoreText)."""
from functools import lru_cache
import json
from pathlib import Path
import random
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).parent
GLYPHS = {
    'h': ['X....', 'X....', 'X.XX.', 'XX..X', 'X...X', 'X...X', 'X...X'],
    '4': ['...X.', '..XX.', '.X.X.', 'X..X.', 'XXXXX', '...X.', '...X.'],
    's': ['.....', '.XXXX', 'X....', '.XXX.', '....X', 'X...X', '.XXX.'],
    '0': ['.XXX.', 'X...X', 'X..XX', 'X.X.X', 'XX..X', 'X...X', '.XXX.'],
}


@lru_cache
def outline(text, size, weight='SemiBold'):
    output = subprocess.check_output([
        'swift', '-sdk', '/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk', str(ROOT / 'type.swift'),
        str(ROOT / f'assets/fonts/Poppins-{weight}.ttf'), str(size), text,
    ], text=True)
    return json.loads(output)


def label(text, size, x, y, fill, weight='SemiBold', center=False):
    glyphs = outline(text, size, weight)
    if center:
        x -= glyphs['width'] / 2
    return f'<path class="lettering" d="{glyphs["path"]}" transform="translate({x:.2f} {y}) scale(1 -1)" fill="{fill}"/>'


def stars(seed, width, height, count):
    rng = random.Random(seed)
    return '\n'.join(
        f'<circle class="star" cx="{rng.uniform(12, width - 12):.1f}" cy="{rng.uniform(12, height - 12):.1f}" '
        f'r="{rng.uniform(.4, 1.3):.1f}" style="--a:{rng.uniform(.16, .48):.2f};animation-delay:-{rng.uniform(0, 8):.1f}s"/>'
        for _ in range(count)
    )


def wrap(width, height, title, description, body, css=''):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{title}</title><desc id="desc">{description}</desc>
<metadata>Poppins, Copyright 2020 The Poppins Project Authors. SIL Open Font License 1.1; assets/fonts/OFL.txt. Lettering outlined with CoreText.</metadata>
<defs>
  <linearGradient id="bg" x2="1" y2="1"><stop stop-color="#0b1018"/><stop offset="1" stop-color="#171e28"/></linearGradient>
  <radialGradient id="nebula" cx="72%" cy="46%" r="64%"><stop stop-color="#394b60" stop-opacity=".44"/><stop offset="1" stop-color="#18212c" stop-opacity="0"/></radialGradient>
  <linearGradient id="silver" x2=".3" y2="1"><stop stop-color="#f4f7fb"/><stop offset="1" stop-color="#aebdce"/></linearGradient>
  <radialGradient id="sphere" cx="36%" cy="25%" r="74%"><stop stop-color="#354355"/><stop offset=".6" stop-color="#1c2634"/><stop offset="1" stop-color="#0b111b"/></radialGradient>
  <linearGradient id="orbit" x2="1" y2=".3"><stop stop-color="#637a96" stop-opacity="0"/><stop offset=".47" stop-color="#7f9ab8"/><stop offset=".72" stop-color="#d2dfed"/><stop offset="1" stop-color="#637a96" stop-opacity="0"/></linearGradient>
  <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9"/></filter>
  <clipPath id="clip"><rect width="{width}" height="{height}" rx="20"/></clipPath>
</defs>
<style>
.star{{fill:#c6d1df;opacity:var(--a);animation:twinkle 8s ease-in-out infinite}}
@keyframes twinkle{{50%{{opacity:.75}}}}
{css}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<g clip-path="url(#clip)">
<rect width="{width}" height="{height}" fill="url(#bg)"/>
<rect width="{width}" height="{height}" fill="url(#nebula)"/>
{body}
</g>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="20" fill="none" stroke="#c5d2e2" stroke-opacity=".09"/>
</svg>'''


def hero():
    rng = random.Random(40)
    particles = []
    for gi, letter in enumerate('h4s0'):
        for row, cells in enumerate(GLYPHS[letter]):
            for col, on in enumerate(cells):
                if on != 'X':
                    continue
                x, y = 743 + gi * 68 + col * 11, 209 + row * 11
                dx, dy = rng.uniform(660, 1110) - x, rng.uniform(83, 395) - y
                particles.append(f'<circle class="particle" cx="{x}" cy="{y}" r="2.55" style="--dx:{dx:.1f}px;--dy:{dy:.1f}px;animation-delay:-{rng.uniform(0, .65):.2f}s"/>')
    css = '''
.particle{fill:#d4dfed;animation:gather 14s cubic-bezier(.4,0,.2,1) infinite}
@keyframes gather{0%,13%,87%,100%{transform:translate(var(--dx),var(--dy));opacity:.22}35%,65%{transform:translate(0,0);opacity:1}}
.satellite{animation:orbit 26s linear infinite;transform-origin:866px 243px}
@keyframes orbit{to{transform:rotate(360deg)}}
.halo{animation:breathe 10s ease-in-out infinite}
@keyframes breathe{50%{opacity:.4}}
'''
    body = f'''
{stars(8, 1200, 470, 92)}
<ellipse class="halo" cx="866" cy="243" rx="167" ry="167" fill="none" stroke="#7b96b6" stroke-width="2" opacity=".3" filter="url(#soft)"/>
<circle cx="866" cy="243" r="151" fill="url(#sphere)" stroke="#8497ae" stroke-opacity=".17"/>
<path d="M738 164A151 151 0 0 1 1010 199" fill="none" stroke="url(#orbit)" stroke-width="1.3"/>
<g transform="rotate(-24 866 243)" fill="none" stroke="url(#orbit)">
  <ellipse cx="866" cy="243" rx="231" ry="79" stroke-width="1.1" opacity=".46"/>
  <ellipse cx="866" cy="243" rx="242" ry="90" stroke-width=".5" opacity=".17"/>
</g>
<circle cx="866" cy="243" r="180" fill="none" stroke="#8b9db4" stroke-width=".6" opacity=".11"/>
<g class="satellite"><circle cx="866" cy="63" r="3" fill="#c9d6e5"/><circle cx="866" cy="63" r="6" fill="#9bb7d8" opacity=".4" filter="url(#soft)"/></g>
{''.join(particles)}
{label('h4s0', 24, 74, 82, '#92a5bd')}
{label('Hasan Can', 82, 69, 220, 'url(#silver)')}
{label('Yaşar', 82, 69, 318, 'url(#silver)')}
<path d="M74 394H1126" stroke="#99adc6" stroke-width=".7" opacity=".13"/>
{label('@hasancanyasar', 17, 74, 431, '#7f90a6', 'Regular')}
<g transform="translate(1109 424)" stroke="#b1c1d5" stroke-width="1" opacity=".7"><path d="M0 -6V6M-6 0H6"/><circle r="2.3" fill="#b1c1d5" stroke="none"/></g>
'''
    return wrap(1200, 470, 'Hasan Can Yaşar · h4s0', 'Gece yarısı gri ve mavi galaksi. Yıldızlar h4s0 yazısında toplanıp dağılıyor; bir ışık yavaşça yörüngede dönüyor.', body, css)


def horizon():
    body = f'''
{stars(12, 1200, 150, 48)}
<g class="wave"><path d="M120 170Q600 -1 1080 170" fill="none" stroke="#809ab9" stroke-width="4" opacity=".16" filter="url(#soft)"/><path d="M120 170Q600 -1 1080 170" fill="none" stroke="url(#orbit)" stroke-width="1.2"/></g>
<path d="M120 170Q600 -1 1080 170V200H120Z" fill="#0d131d"/>
<path d="M120 170Q600 -1 1080 170" fill="none" stroke="url(#orbit)" stroke-width=".8" opacity=".7"/>
<g class="comet"><path d="M610 35H727" stroke="url(#orbit)" stroke-width=".8"/><circle cx="727" cy="35" r="1.7" fill="#dce6f3"/></g>
'''
    css = '''.wave{animation:wave 12s ease-in-out infinite}@keyframes wave{50%{opacity:.4;transform:translateY(3px)}}
.comet{animation:comet 18s linear infinite}@keyframes comet{0%,20%{transform:translate(-500px,15px);opacity:0}24%,45%{opacity:.7}50%,100%{transform:translate(480px,-10px);opacity:0}}'''
    return wrap(1200, 150, 'Gece yarısı galaksi ufku', 'Gri mavi bir gezegenin ufkunda yavaşça süzülen bir ışık.', body, css)


def avatar():
    body = f'''
{stars(3, 800, 800, 55)}
<circle cx="400" cy="400" r="255" fill="url(#sphere)"/>
<circle cx="400" cy="400" r="255" fill="none" stroke="#a9bed7" stroke-opacity=".16"/>
<ellipse cx="400" cy="400" rx="318" ry="114" transform="rotate(-30 400 400)" fill="none" stroke="url(#orbit)" stroke-width="1.7" opacity=".7"/>
{label('h', 356, 400, 523, 'url(#silver)', center=True)}
<circle cx="514" cy="503" r="15" fill="#8aa8cc"/>
'''
    return wrap(800, 800, 'h4s0 profil simgesi', 'Gece yarısı gri galakside Poppins h harfi ve gümüş mavi bir yörünge.', body)


if __name__ == '__main__':
    files = {'identity.svg': hero(), 'horizon.svg': horizon(), 'avatar.svg': avatar()}
    for name, svg in files.items():
        tree = ET.fromstring(svg)
        assert not tree.findall('.//{http://www.w3.org/2000/svg}script')
        assert not tree.findall('.//{http://www.w3.org/2000/svg}foreignObject')
        assert 'prefers-reduced-motion:reduce' in svg
        assert 'font-family' not in svg, 'Fontun SVG yollarına dönüşmesi gerekir.'
        (ROOT / 'assets' / name).write_text(svg, encoding='utf-8')
    readme = (ROOT / 'README.md').read_text()
    assert re.findall(r'src="([^"]+)"', readme) == ['assets/identity.svg', 'assets/horizon.svg']
    assert not any(word in readme.casefold() for word in ('projeler', 'terminal', 'veri', 'modelleri'))
    assert len(ET.fromstring(files['identity.svg']).findall('.//{http://www.w3.org/2000/svg}circle[@class="particle"]')) > 50
    print('3 SVG üretildi; font, animasyon ve kişisel profil kontrolleri geçti.')
