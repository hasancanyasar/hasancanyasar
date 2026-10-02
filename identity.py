"""Kişisel GitHub sahnesi: python3 identity.py. Yalnız stdlib."""
from pathlib import Path
import random
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).parent


def scene():
    rng = random.Random(40)
    stars = "\n".join(
        f'<circle cx="{rng.uniform(20, 1180):.1f}" cy="{rng.uniform(20, 430):.1f}" '
        f'r="{rng.uniform(.4, 1.3):.1f}" opacity="{rng.uniform(.15, .65):.2f}"/>'
        for _ in range(130)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760" role="img" aria-labelledby="title desc">
<title id="title">Hasan Can Yaşar · h4s0</title>
<desc id="desc">Yıldızlı mürdüm gökyüzü, altın tutulma halkası ve dağların arasında ışığa açılan bir geçit.</desc>
<defs>
  <linearGradient id="sky" x2="0" y2="1"><stop stop-color="#100e1c"/><stop offset=".6" stop-color="#302136"/><stop offset="1" stop-color="#71605a"/></linearGradient>
  <radialGradient id="halo"><stop offset=".45" stop-color="#efc894" stop-opacity="0"/><stop offset=".54" stop-color="#efc894" stop-opacity=".24"/><stop offset="1" stop-color="#efc894" stop-opacity="0"/></radialGradient>
  <linearGradient id="gold" x2="1" y2="1"><stop stop-color="#fff1d4"/><stop offset=".5" stop-color="#c29369"/><stop offset="1" stop-color="#f5d9ac"/></linearGradient>
  <linearGradient id="ink" x2="0" y2="1"><stop stop-color="#fff6e8"/><stop offset="1" stop-color="#d9c2b1"/></linearGradient>
  <linearGradient id="haze" x2="0" y2="1"><stop stop-color="#eac5a2" stop-opacity=".16"/><stop offset="1" stop-color="#eac5a2" stop-opacity="0"/></linearGradient>
  <linearGradient id="path" x2="0" y2="1"><stop stop-color="#f6debc" stop-opacity=".7"/><stop offset="1" stop-color="#aa8c7a" stop-opacity="0"/></linearGradient>
  <filter id="blur"><feGaussianBlur stdDeviation="7"/></filter>
  <clipPath id="frame"><rect width="1200" height="760" rx="12"/></clipPath>
</defs>
<style>
  .breath{{animation:breath 9s ease-in-out infinite}}
  .drift{{animation:drift 18s ease-in-out infinite;transform-origin:600px 286px}}
  @keyframes breath{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
  @keyframes drift{{0%,100%{{transform:rotate(-8deg)}}50%{{transform:rotate(8deg)}}}}
  @media(prefers-reduced-motion:reduce){{.breath,.drift{{animation:none}}}}
</style>
<g clip-path="url(#frame)">
  <rect width="1200" height="760" fill="url(#sky)"/>
  <g fill="#f5e7d7">{stars}</g>
  <circle cx="600" cy="286" r="286" fill="url(#halo)" class="breath"/>
  <circle cx="600" cy="286" r="153" fill="#17131f"/>
  <circle cx="600" cy="286" r="155" fill="none" stroke="url(#gold)" stroke-width="5" filter="url(#blur)" class="breath"/>
  <circle cx="600" cy="286" r="155" fill="none" stroke="url(#gold)" stroke-width="1.6"/>
  <g fill="none" stroke="#d4b594" stroke-width=".7">
    <ellipse cx="600" cy="286" rx="290" ry="88" transform="rotate(-28 600 286)" opacity=".24"/>
    <ellipse cx="600" cy="286" rx="233" ry="202" transform="rotate(35 600 286)" opacity=".12"/>
    <circle cx="600" cy="286" r="176" stroke-dasharray="1 17" opacity=".4"/>
  </g>
  <g class="drift"><path d="M600 98v18M591 107h18" stroke="#f5d9ac" stroke-width="1"/><circle cx="600" cy="107" r="3" fill="#fff1d4"/></g>
  <path d="M0 476L86 446 130 462 230 365 300 449 357 421 452 502 566 456 642 480 731 412 801 454 932 359 1048 462 1130 431 1200 467V760H0Z" fill="#3c3244"/>
  <path d="M0 525L112 478 209 534 326 453 414 522 535 494 620 539 729 471 805 505 913 456 1058 528 1200 480V760H0Z" fill="#292331"/>
  <ellipse cx="600" cy="536" rx="560" ry="80" fill="url(#haze)"/>
  <path d="M0 584L144 547 257 575 361 549 490 581 597 558 705 582 834 534 963 567 1082 543 1200 579V760H0Z" fill="#191821"/>
  <path d="M590 576Q563 649 407 760H795Q636 647 610 576Z" fill="url(#path)" opacity=".19"/>
  <path d="M578 590V550a22 22 0 0 1 44 0v40" fill="#13121b" stroke="#d0ad86" stroke-width="1.4"/>
  <path d="M589 587v-35a11 11 0 0 1 22 0v35" fill="#e9c8a2" class="breath"/>
  <path d="M591 587v-33a9 9 0 0 1 18 0v33" fill="#f5ddbc" filter="url(#blur)" class="breath"/>
  <text x="600" y="71" text-anchor="middle" fill="#d4b594" font-family="Georgia,'Times New Roman',serif" font-size="20" letter-spacing="9">h4s0</text>
  <text x="600" y="296" text-anchor="middle" fill="url(#ink)" font-family="Georgia,'Times New Roman',serif" font-size="78" letter-spacing="-3">Hasan Can</text>
  <text x="600" y="372" text-anchor="middle" fill="url(#ink)" font-family="Georgia,'Times New Roman',serif" font-size="78" letter-spacing="-3">Yaşar</text>
  <path d="M559 687h26m30 0h26M600 680l7 7-7 7-7-7Z" fill="none" stroke="#d0ad86" stroke-width=".8" opacity=".65"/>
</g>
</svg>
'''


if __name__ == "__main__":
    svg = scene()
    ET.fromstring(svg)
    readme = (ROOT / "README.md").read_text()
    assert re.findall(r'src="([^"]+)"', readme) == ["assets/identity.svg"]
    assert not any(word in readme.casefold() for word in ("projeler", "terminal", "veri", "modelleri"))
    (ROOT / "assets/identity.svg").write_text(svg, encoding="utf-8")
    print("identity.svg üretildi; SVG ve sade profil kontrolü geçti.")
