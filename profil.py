"""GitHub profil kartları; Python stdlib, activity için yalnız kayıtlı Poppins yolları.

    python3 profil.py tools
    python3 profil.py activity [--veri dosya.json]
    python3 profil.py --kontrol

tools macOS/CoreText gerektirir. activity ve --kontrol Swift ya da ağda font istemez.
--veri, GraphQL yanıtını veya doğrudan contributionCalendar nesnesini kabul eder.
Takvim kaynak verisi SVG metadata'sında saklanır; --kontrol ağsız karşılaştırır.
"""
import argparse
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from identity import stars, wrap

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
NS = '{http://www.w3.org/2000/svg}'
MAX_BYTES = 150_000
MONTHS = ('Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz',
          'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara')
CAPTION = 'katkı · son 6 ay'
SHOWN_WEEKS = 26  # veri 53 hafta gelir; kart son 26 haftayı çizer
REQUIRED_CHARS = set('0123456789. ' + CAPTION + ''.join(MONTHS))
ICON_VERSION = '16.35.0'
ICON_SOURCE = f'https://github.com/simple-icons/simple-icons/tree/{ICON_VERSION}/icons'
TOOLS = (
    ('python', ('Python',)), ('n8n', ('n8n',)), ('git', ('Git',)),
    ('githubactions', ('GitHub', 'Actions')), ('markdown', ('Markdown',)),
    ('apple', ('macOS',)), ('claude', ('Claude',)),
    ('googlegemini', ('Gemini',)), ('modelcontextprotocol', ('MCP',)),
)
OMITTED = ('OpenAI', 'Open WebUI')
# Simple Icons 16.35.0, CC0-1.0; paths copied without alteration from icons/*.svg.
ICON_PATHS = {
    "python": "M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z",
    "n8n": "M21.4737 5.6842c-1.1772 0-2.1663.8051-2.4468 1.8947h-2.8955c-1.235 0-2.289.893-2.492 2.111l-.1038.623a1.263 1.263 0 0 1-1.246 1.0555H11.289c-.2805-1.0896-1.2696-1.8947-2.4468-1.8947s-2.1663.8051-2.4467 1.8947H4.973c-.2805-1.0896-1.2696-1.8947-2.4468-1.8947C1.1311 9.4737 0 10.6047 0 12s1.131 2.5263 2.5263 2.5263c1.1772 0 2.1663-.8051 2.4468-1.8947h1.4223c.2804 1.0896 1.2696 1.8947 2.4467 1.8947 1.1772 0 2.1663-.8051 2.4468-1.8947h1.0008a1.263 1.263 0 0 1 1.2459 1.0555l.1038.623c.203 1.218 1.257 2.111 2.492 2.111h.3692c.2804 1.0895 1.2696 1.8947 2.4468 1.8947 1.3952 0 2.5263-1.131 2.5263-2.5263s-1.131-2.5263-2.5263-2.5263c-1.1772 0-2.1664.805-2.4468 1.8947h-.3692a1.263 1.263 0 0 1-1.246-1.0555l-.1037-.623A2.52 2.52 0 0 0 13.9607 12a2.52 2.52 0 0 0 .821-1.4794l.1038-.623a1.263 1.263 0 0 1 1.2459-1.0555h2.8955c.2805 1.0896 1.2696 1.8947 2.4468 1.8947 1.3952 0 2.5263-1.131 2.5263-2.5263s-1.131-2.5263-2.5263-2.5263m0 1.2632a1.263 1.263 0 0 1 1.2631 1.2631 1.263 1.263 0 0 1-1.2631 1.2632 1.263 1.263 0 0 1-1.2632-1.2632 1.263 1.263 0 0 1 1.2632-1.2631M2.5263 10.7368A1.263 1.263 0 0 1 3.7895 12a1.263 1.263 0 0 1-1.2632 1.2632A1.263 1.263 0 0 1 1.2632 12a1.263 1.263 0 0 1 1.2631-1.2632m6.3158 0A1.263 1.263 0 0 1 10.1053 12a1.263 1.263 0 0 1-1.2632 1.2632A1.263 1.263 0 0 1 7.579 12a1.263 1.263 0 0 1 1.2632-1.2632m10.1053 3.7895a1.263 1.263 0 0 1 1.2631 1.2632 1.263 1.263 0 0 1-1.2631 1.2631 1.263 1.263 0 0 1-1.2632-1.2631 1.263 1.263 0 0 1 1.2632-1.2632",
    "git": "M13.09 23.549a1.54 1.54 0 0 1-2.18 0L.451 13.089a1.54 1.54 0 0 1 0-2.179l7.191-7.19 2.733 2.733a1.85 1.85 0 0 0 .964 2.326v6.66a1.849 1.849 0 1 0 1.54 0V8.957l2.508 2.508a1.85 1.85 0 1 0 1.09-1.09l-2.634-2.634a1.85 1.85 0 0 0-2.378-2.377L8.73 2.63 10.91.451a1.54 1.54 0 0 1 2.179 0l10.459 10.46a1.54 1.54 0 0 1 0 2.179z",
    "githubactions": "M10.984 13.836a.5.5 0 0 1-.353-.146l-.745-.743a.5.5 0 1 1 .706-.708l.392.391 1.181-1.18a.5.5 0 0 1 .708.707l-1.535 1.533a.504.504 0 0 1-.354.146zm9.353-.147l1.534-1.532a.5.5 0 0 0-.707-.707l-1.181 1.18-.392-.391a.5.5 0 1 0-.706.708l.746.743a.497.497 0 0 0 .706-.001zM4.527 7.452l2.557-1.585A1 1 0 0 0 7.09 4.17L4.533 2.56A1 1 0 0 0 3 3.406v3.196a1.001 1.001 0 0 0 1.527.85zm2.03-2.436L4 6.602V3.406l2.557 1.61zM24 12.5c0 1.93-1.57 3.5-3.5 3.5a3.503 3.503 0 0 1-3.46-3h-2.08a3.503 3.503 0 0 1-3.46 3 3.502 3.502 0 0 1-3.46-3h-.558c-.972 0-1.85-.399-2.482-1.042V17c0 1.654 1.346 3 3 3h.04c.244-1.693 1.7-3 3.46-3 1.93 0 3.5 1.57 3.5 3.5S13.43 24 11.5 24a3.502 3.502 0 0 1-3.46-3H8c-2.206 0-4-1.794-4-4V9.899A5.008 5.008 0 0 1 0 5c0-2.757 2.243-5 5-5s5 2.243 5 5a5.005 5.005 0 0 1-4.952 4.998A2.482 2.482 0 0 0 7.482 12h.558c.244-1.693 1.7-3 3.46-3a3.502 3.502 0 0 1 3.46 3h2.08a3.503 3.503 0 0 1 3.46-3c1.93 0 3.5 1.57 3.5 3.5zm-15 8c0 1.378 1.122 2.5 2.5 2.5s2.5-1.122 2.5-2.5-1.122-2.5-2.5-2.5S9 19.122 9 20.5zM5 9c2.206 0 4-1.794 4-4S7.206 1 5 1 1 2.794 1 5s1.794 4 4 4zm9 3.5c0-1.378-1.122-2.5-2.5-2.5S9 11.122 9 12.5s1.122 2.5 2.5 2.5 2.5-1.122 2.5-2.5zm9 0c0-1.378-1.122-2.5-2.5-2.5S18 11.122 18 12.5s1.122 2.5 2.5 2.5 2.5-1.122 2.5-2.5zm-13 8a.5.5 0 1 0 1 0 .5.5 0 0 0-1 0zm2 0a.5.5 0 1 0 1 0 .5.5 0 0 0-1 0zm12 0c0 1.93-1.57 3.5-3.5 3.5a3.503 3.503 0 0 1-3.46-3.002c-.007.001-.013.005-.021.005l-.506.017h-.017a.5.5 0 0 1-.016-.999l.506-.017c.018-.002.035.006.052.007A3.503 3.503 0 0 1 20.5 17c1.93 0 3.5 1.57 3.5 3.5zm-1 0c0-1.378-1.122-2.5-2.5-2.5S18 19.122 18 20.5s1.122 2.5 2.5 2.5 2.5-1.122 2.5-2.5z",
    "markdown": "M22.27 19.385H1.73A1.73 1.73 0 010 17.655V6.345a1.73 1.73 0 011.73-1.73h20.54A1.73 1.73 0 0124 6.345v11.308a1.73 1.73 0 01-1.73 1.731zM5.769 15.923v-4.5l2.308 2.885 2.307-2.885v4.5h2.308V8.078h-2.308l-2.307 2.885-2.308-2.885H3.46v7.847zM21.232 12h-2.309V8.077h-2.307V12h-2.308l3.461 4.039z",
    "apple": "M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701",
    "claude": "m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z",
    "googlegemini": "M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81",
    "modelcontextprotocol": "M13.85 0a4.16 4.16 0 0 0-2.95 1.217L1.456 10.66a.835.835 0 0 0 0 1.18.835.835 0 0 0 1.18 0l9.442-9.442a2.49 2.49 0 0 1 3.541 0 2.49 2.49 0 0 1 0 3.541L8.59 12.97l-.1.1a.835.835 0 0 0 0 1.18.835.835 0 0 0 1.18 0l.1-.098 7.03-7.034a2.49 2.49 0 0 1 3.542 0l.049.05a2.49 2.49 0 0 1 0 3.54l-8.54 8.54a1.96 1.96 0 0 0 0 2.755l1.753 1.753a.835.835 0 0 0 1.18 0 .835.835 0 0 0 0-1.18l-1.753-1.753a.266.266 0 0 1 0-.394l8.54-8.54a4.185 4.185 0 0 0 0-5.9l-.05-.05a4.16 4.16 0 0 0-2.95-1.218c-.2 0-.401.02-.6.048a4.17 4.17 0 0 0-1.17-3.552A4.16 4.16 0 0 0 13.85 0m0 3.333a.84.84 0 0 0-.59.245L6.275 10.56a4.186 4.186 0 0 0 0 5.902 4.186 4.186 0 0 0 5.902 0L19.16 9.48a.835.835 0 0 0 0-1.18.835.835 0 0 0-1.18 0l-6.985 6.984a2.49 2.49 0 0 1-3.54 0 2.49 2.49 0 0 1 0-3.54l6.983-6.985a.835.835 0 0 0 0-1.18.84.84 0 0 0-.59-.245"
}
QUERY = '''query {
  user(login: "hasancanyasar") {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}'''

SWEEP_DEFS = '''<linearGradient id="sweep" x2="1">
<stop stop-color="#d2dfed" stop-opacity="0"/>
<stop offset=".5" stop-color="#d2dfed" stop-opacity=".09"/>
<stop offset="1" stop-color="#d2dfed" stop-opacity="0"/>
</linearGradient>'''
SWEEP_CSS = '''
.sweep{opacity:0;animation:sweep 10s linear infinite}
@keyframes sweep{
  0%,15%{transform:translateX(-240px);opacity:0}
  20%,80%{opacity:1}
  85%,100%{transform:translateX(1440px);opacity:0}
}
'''


def compact_path(path):
    return re.sub(r'-?\d+\.\d+', lambda match: format(float(match[0]), '.2f').rstrip('0').rstrip('.'), path)


def make_card(height, title, description, body, css='', defs='', metadata=None):
    svg = wrap(1200, height, escape(title), escape(description), body, css)
    svg = svg.replace('</defs>', SWEEP_DEFS + defs + '\n</defs>', 1)
    if metadata:
        extra = escape(json.dumps(metadata, ensure_ascii=False, separators=(',', ':')))
        svg = svg.replace('</metadata>', f'</metadata>\n<metadata id="source-data">{extra}</metadata>', 1)
    return svg + '\n'


def coretext(binary, text, size=40, weight='Regular'):
    output = subprocess.check_output([
        str(binary), str(ASSETS / f'fonts/Poppins-{weight}.ttf'), str(size), text,
    ], text=True, timeout=30)
    result = json.loads(output)
    result['path'] = compact_path(result['path'])
    return result


def tools_card(binary):
    height = 380
    body = [stars(18, 1200, height, 56)]
    for index, (slug, lines) in enumerate(TOOLS):
        row = 0 if index < 5 else 1
        column = index if row == 0 else index - 5
        x = 160 + column * 220 + (110 if row else 0)
        y = 86 if row == 0 else 260
        # Peak follows the same left-to-right ten-second sweep on both rows.
        glint_delay = 1.5 + (x + 240) / 1680 * 7 - 1
        body.append(f'<g class="tool-reveal" style="animation-delay:{index * .12:.2f}s">')
        body.append(f'<g transform="translate({x - 36} {y - 36}) scale(3)">')
        body.append(f'<path d="{ICON_PATHS[slug]}" fill="url(#silver)" opacity=".84"/>')
        body.append(f'<path class="tool-glint" d="{ICON_PATHS[slug]}" fill="url(#silver)" style="animation-delay:{glint_delay:.2f}s"/>')
        body.append('</g>')
        for line, text in enumerate(lines):
            glyph = coretext(binary, text, 38)
            left = x - glyph['width'] / 2
            body.append(f'<path class="lettering" d="{glyph["path"]}" transform="translate({left:.2f} {y + 77 + line * 34}) scale(1 -1)" fill="url(#silver)" opacity=".84"/>')
        body.append('</g>')
    body.append(f'<rect class="sweep" x="0" y="0" width="180" height="{height}" fill="url(#sweep)"/>')
    css = SWEEP_CSS + '''
.tool-reveal{opacity:1;animation:reveal .85s ease-out backwards}
@keyframes reveal{from{opacity:0}to{opacity:1}}
.tool-glint{opacity:0;animation:glint 10s ease-in-out infinite}
@keyframes glint{0%,3%,17%,100%{opacity:0}10%{opacity:.7}}
'''
    metadata = {
        'icons': {'project': 'Simple Icons', 'version': ICON_VERSION, 'license': 'CC0-1.0',
                  'source': ICON_SOURCE, 'slugs': [slug for slug, _ in TOOLS],
                  'omitted': list(OMITTED)},
    }
    return make_card(height, 'Kullandığım araçlar',
                     'Python, n8n, Git, GitHub Actions, Markdown, macOS, Claude, '
                     'Google Gemini ve Model Context Protocol. Gümüş simgeler iki sırada '
                     'beliriyor; yavaş bir ışık soldan sağa süzülüyor.',
                     '\n'.join(body), css, metadata=metadata)


def build_tools():
    # Compile the existing Swift helper once; never called by activity or --kontrol.
    with tempfile.TemporaryDirectory(prefix='profil-coretext-') as directory:
        binary = Path(directory) / 'type'
        subprocess.run([
            'swiftc', '-sdk', '/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk',
            str(ROOT / 'type.swift'), '-o', str(binary),
        ], check=True, timeout=60)
        glyphs = {
            'version': 1, 'font': 'Poppins-Regular', 'size': 40,
            'source': 'type.swift · macOS CoreText',
            'license': 'SIL Open Font License 1.1; assets/fonts/OFL.txt',
            'characters': {char: coretext(binary, char) for char in sorted(REQUIRED_CHARS)},
        }
        svg = tools_card(binary)
    validate_svg('tools.svg', svg)
    atomic_write(ASSETS / 'glyphs.json', json.dumps(glyphs, ensure_ascii=False, indent=2) + '\n')
    atomic_write(ASSETS / 'tools.svg', svg)
    print(f'tools.svg: {len(TOOLS)} simge, {len(svg.encode())} bayt. Atlanan: {", ".join(OMITTED)}.')


def load_glyphs():
    glyphs = json.loads((ASSETS / 'glyphs.json').read_text(encoding='utf-8'))
    characters = glyphs['characters']
    missing = REQUIRED_CHARS - characters.keys()
    if missing:
        raise ValueError('glyphs.json eksik karakterler: ' + repr(''.join(sorted(missing))))
    if glyphs.get('font') != 'Poppins-Regular' or glyphs.get('size') != 40:
        raise ValueError('glyphs.json Poppins-Regular / 40 ölçeğinde olmalı.')
    for char in REQUIRED_CHARS:
        glyph = characters[char]
        if not isinstance(glyph['path'], str) or (char != ' ' and not glyph['path']):
            raise ValueError(f'Geçersiz harf yolu: {char!r}')
        if isinstance(glyph['width'], bool) or not isinstance(glyph['width'], (int, float)):
            raise ValueError(f'Geçersiz harf genişliği: {char!r}')
        if not math.isfinite(glyph['width']) or glyph['width'] <= 0:
            raise ValueError(f'Geçersiz harf genişliği: {char!r}')
        if glyph['path'] and not re.fullmatch(r'[MLQCZmlqcz0-9. ,\-]+', glyph['path']):
            raise ValueError(f'Geçersiz harf yolu: {char!r}')
    return glyphs


def glyph_id(char):
    return f'glyph-{ord(char):x}'


def text_path(text, size, x, y, glyphs, opacity=1):
    parts = [f'<g class="lettering" transform="translate({x:.2f} {y}) scale({size / glyphs["size"]:g} {-size / glyphs["size"]:g})" fill="url(#silver)" opacity="{opacity}">']
    cursor = 0
    for char in text:
        if char != ' ':
            parts.append(f'<use href="#{glyph_id(char)}" transform="translate({cursor:.2f} 0)"/>')
        cursor += glyphs['characters'][char]['width']
    parts.append('</g>')
    return ''.join(parts)


def calendar_data(payload):
    if not isinstance(payload, dict):
        raise ValueError('Takvim JSON nesnesi olmalı.')
    if payload.get('errors'):
        raise ValueError('GitHub GraphQL hata döndürdü; mevcut takvim korunuyor.')
    if 'data' in payload:
        try:
            payload = payload['data']['user']['contributionsCollection']['contributionCalendar']
        except (TypeError, KeyError):
            raise ValueError('GitHub yanıtında kullanıcı veya katkı takvimi yok.') from None
    if not isinstance(payload, dict):
        raise ValueError('GitHub yanıtında katkı takvimi nesnesi yok.')
    total, weeks = payload.get('totalContributions'), payload.get('weeks')
    if type(total) is not int or total < 0 or not isinstance(weeks, list) or len(weeks) != 53:
        raise ValueError('Takvim, katkı toplamı ve 53 hafta içermeli.')
    previous = None
    normalized = []
    for index, week in enumerate(weeks):
        days = week.get('contributionDays') if isinstance(week, dict) else None
        if not isinstance(days, list) or not 1 <= len(days) <= 7:
            raise ValueError('Her hafta 1–7 gün içermeli.')
        if 0 < index < 52 and len(days) != 7:
            raise ValueError('Ara haftalar 7 gün içermeli.')
        clean = []
        for day_index, day in enumerate(days):
            if not isinstance(day, dict) or not isinstance(day.get('date'), str):
                raise ValueError('Geçersiz katkı günü.')
            stamp, count = date.fromisoformat(day['date']), day.get('contributionCount')
            if stamp.isoformat() != day['date'] or type(count) is not int or count < 0:
                raise ValueError('Gün tarihi veya katkı sayısı geçersiz.')
            if previous is not None and stamp != previous + timedelta(days=1):
                raise ValueError('Katkı günleri kesintisiz ve tarih sırasıyla olmalı.')
            if (stamp.weekday() + 1) % 7 + len(days) - day_index > 7:
                raise ValueError('Hafta sınırları pazar–cumartesi düzenine uymuyor.')
            clean.append({'date': day['date'], 'contributionCount': count})
            previous = stamp
        normalized.append({'contributionDays': clean})
    count_sum = sum(day['contributionCount'] for week in normalized for day in week['contributionDays'])
    if count_sum != total:
        raise ValueError('Katkı toplamı günlerin toplamına eşit değil.')
    return {'totalContributions': total, 'weeks': normalized}


def fetch_calendar():
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token:
        try:
            token = subprocess.check_output(['gh', 'auth', 'token'], text=True, stderr=subprocess.DEVNULL, timeout=15).strip()
        except (OSError, subprocess.SubprocessError):
            raise ValueError('GH_TOKEN veya GITHUB_TOKEN gerekli; yerelde gh auth token kullanılabilir.') from None
    if not token:
        raise ValueError('GitHub token boş.')
    request = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': QUERY}).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                 'User-Agent': 'hasancanyasar-profile'},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        raise ValueError(f'GitHub API HTTP {error.code}; mevcut takvim korunuyor.') from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError('GitHub API bağlantısı başarısız; mevcut takvim korunuyor.') from None
    return calendar_data(payload)


def contribution_level(count):
    # Five fixed steps, including zero; no ranking or changing thresholds.
    return sum(count >= threshold for threshold in (1, 5, 15, 30))


def activity_card(calendar, glyphs):
    weeks = calendar['weeks'][-SHOWN_WEEKS:]
    total = sum(day['contributionCount'] for week in weeks for day in week['contributionDays'])
    height, left, step, top, row_step = 340, 86, 1028 / (SHOWN_WEEKS - 1), 128, 23
    title = f'{total:,}'.replace(',', '.') + ' ' + CAPTION
    body = [stars(24, 1200, height, 42), text_path(title, 38, left, 73, glyphs)]
    radii = (1.3, 2.6, 3.8, 5, 6.2)
    opacities = (.16, .5, .68, .86, 1)
    # Reuse five outlined star shapes; even a fully active year stays below 150 KB.
    shapes = []
    for level, radius in enumerate(radii):
        shape = [f'<g id="point-{level}">']
        if level:
            shape.append(f'<circle r="{radius * 2.1:.2f}" fill="#b9cde5" opacity="{.035 + level * .017:.3f}"/>')
        if level >= 3:
            span = radius * 1.6
            shape.append(f'<path d="M{-span:.2f} 0H{span:.2f}M0 {-span:.2f}V{span:.2f}" stroke="#c9d8e9" stroke-width=".7" opacity=".32"/>')
        shape.append(f'<circle class="core" r="{radius}" fill="url(#silver)" opacity="{opacities[level]}"/></g>')
        shapes.append(''.join(shape))
    month = None
    for column, week in enumerate(weeks):
        x = left + column * step
        for day in week['contributionDays']:
            stamp = date.fromisoformat(day['date'])
            count = day['contributionCount']
            row, level = (stamp.weekday() + 1) % 7, contribution_level(count)
            y = top + row * row_step
            delay = -(column * .19 + row * .67) % 7 - 7
            animation = f' style="animation-delay:{delay:.2f}s"' if level >= 3 else ''
            body.append(f'<g class="day level-{level}" data-date="{stamp}" data-count="{count}" data-week="{column}" data-row="{row}"{animation}><use class="point" href="#point-{level}" transform="translate({x:.2f} {y})"/></g>')
            current_month = (stamp.year, stamp.month)
            if current_month != month:
                body.append(text_path(MONTHS[stamp.month - 1], 25, x - 2, 310, glyphs, .3))
                month = current_month
    body.append(f'<rect class="sweep" x="0" y="0" width="180" height="{height}" fill="url(#sweep)"/>')
    defs = '\n'.join(shapes) + '\n' + '\n'.join(f'<path id="{glyph_id(char)}" d="{glyphs["characters"][char]["path"]}"/>' for char in sorted(REQUIRED_CHARS) if char != ' ')
    css = SWEEP_CSS + '''
.day.level-3,.day.level-4{opacity:1;animation:starlight 7s ease-in-out infinite}
@keyframes starlight{50%{opacity:.79}}
'''
    metadata = {'source': 'https://api.github.com/graphql', 'login': 'hasancanyasar',
                'query': QUERY, 'levels': [0, 1, 5, 15, 30], 'calendar': calendar}
    days = [day for week in weeks for day in week['contributionDays']]
    description = (f'{days[0]["date"]} – {days[-1]["date"]}: {total} katkı, '
                   f'{len(days)} gün, {SHOWN_WEEKS} hafta ve 7 günlük takımyıldız ızgarası. '
                   'Katkı sayısı arttıkça yıldız beş basamakta büyüyüp parlar. '
                   'Yavaş ışık bandı ve parlak günlerde hafif titreşim.')
    return make_card(height, title, description, '\n'.join(body), css, defs, metadata)


def validate_svg(name, svg):
    if len(svg.encode('utf-8')) > MAX_BYTES:
        raise ValueError(f'{name}: SVG 150 KB sınırını aşıyor.')
    if re.search(r'<!DOCTYPE|<!ENTITY|<\?xml-stylesheet', svg, re.I):
        raise ValueError(f'{name}: dış kaynak veya XML entity yasak.')
    tree = ET.fromstring(svg)
    if tree.tag != NS + 'svg' or tree.get('role') != 'img':
        raise ValueError(f'{name}: SVG kökü veya role="img" eksik.')
    for tag in ('title', 'desc'):
        if not (tree.findtext(NS + tag) or '').strip():
            raise ValueError(f'{name}: {tag} eksik.')
    if not re.search(r'@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)', svg):
        raise ValueError(f'{name}: reduced-motion kuralı eksik.')
    for element in tree.iter():
        tag = element.tag.rsplit('}', 1)[-1]
        if tag in ('script', 'foreignObject', 'text', 'tspan', 'image'):
            raise ValueError(f'{name}: yasak SVG öğesi: {tag}.')
        for attr, value in element.attrib.items():
            local = attr.rsplit('}', 1)[-1]
            if local.lower().startswith('on') or (local in ('href', 'src') and not value.startswith('#')):
                raise ValueError(f'{name}: dış bağlantı veya çalıştırılabilir öznitelik.')
        if tag in ('animate', 'animateTransform', 'set') and element.get('attributeName') not in ('opacity', 'transform'):
            raise ValueError(f'{name}: animasyon yalnız transform/opacity olabilir.')
        if tag == 'clipPath' and any(child.tag.rsplit('}', 1)[-1].startswith('animate') for child in element.iter()):
            raise ValueError(f'{name}: clipPath animasyonu yasak.')
    for reference in re.findall(r'url\(\s*[\'"]?([^\s)\'"]+)', svg, re.I):
        if not reference.startswith('#'):
            raise ValueError(f'{name}: dış url() kaynağı.')
    if re.search(r'@import|@font-face|font-family|\bd\s*:\s*path\(', svg, re.I):
        raise ValueError(f'{name}: dış font veya CSS path animasyonu.')
    return tree


def validate_activity(tree):
    metadata = tree.find(NS + 'metadata[@id="source-data"]')
    if metadata is None:
        raise ValueError('activity.svg: kaynak verisi metadata içinde eksik.')
    source = json.loads(metadata.text)
    calendar = calendar_data(source['calendar'])
    expected = [(day['date'], str(day['contributionCount']), str(column),
                 str((date.fromisoformat(day['date']).weekday() + 1) % 7),
                 f'level-{contribution_level(day["contributionCount"])}')
                for column, week in enumerate(calendar['weeks'][-SHOWN_WEEKS:]) for day in week['contributionDays']]
    actual = []
    for node in tree.iter(NS + 'g'):
        classes = node.get('class', '').split()
        if 'day' in classes:
            levels = [item for item in classes if item.startswith('level-')]
            actual.append((node.get('data-date'), node.get('data-count'), node.get('data-week'),
                           node.get('data-row'), levels[0] if len(levels) == 1 else None))
            points = node.findall(NS + 'use[@class="point"]')
            level = levels[0].removeprefix('level-') if len(levels) == 1 else ''
            shape = tree.find(f'.//{NS}g[@id="point-{level}"]')
            if (len(points) != 1 or points[0].get('href') != f'#point-{level}'
                    or shape is None or len(shape.findall(NS + 'circle[@class="core"]')) != 1):
                raise ValueError('activity.svg: her güne tam bir yıldız çekirdeği gerekli.')
    if actual != expected:
        raise ValueError('activity.svg: yıldızların gün sayısı, tarih, seviye veya katkı verisi uyuşmuyor.')
    return len(actual)


class ReadmeImages(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images.append(dict(attrs))


def check_profile():
    parser = ReadmeImages()
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    parser.feed(readme)
    expected = ['assets/identity.svg', 'assets/tools.svg', 'assets/activity.svg', 'assets/horizon.svg']
    if [item.get('src') for item in parser.images] != expected:
        raise ValueError('README görselleri identity, tools, activity, horizon sırasında olmalı.')
    for image in parser.images:
        path = (ROOT / image['src']).resolve()
        if not path.is_file() or ROOT not in path.parents:
            raise ValueError('README görsel yolu yok veya depo dışında: ' + image['src'])
        if image.get('width') != '100%' or not image.get('alt', '').strip():
            raise ValueError('README görsellerinde width="100%" ve anlamlı alt gerekli.')
    expected_markup = '\n'.join(
        f'<p align="center"><img src="{image["src"]}" width="100%" alt="{escape(image["alt"], quote=True)}"></p>'
        for image in parser.images)
    if re.sub(r'\s+', '', readme) != re.sub(r'\s+', '', expected_markup):
        raise ValueError('README yalnız ortalanmış dört görsel içermeli.')
    load_glyphs()
    days = None
    for path in sorted(ASSETS.rglob('*.svg')):
        svg = path.read_text(encoding='utf-8')
        tree = validate_svg(path.name, svg)
        if path.name == 'activity.svg':
            days = validate_activity(tree)
        print(f'{path.relative_to(ROOT)}: {len(svg.encode()):,} bayt · geçerli')
    print(f'README yolları, XML, bağımsız SVG, boyut, reduced-motion, harfler ve {days} katkı günü doğrulandı.')


def atomic_write(path, content):
    # Full generation and validation precede replacement; API errors never truncate the old SVG.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.' + path.name + '-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        temporary.chmod(0o644)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', nargs='?', choices=('tools', 'activity'))
    parser.add_argument('--veri', type=Path, help='GraphQL yanıtı veya contributionCalendar JSON dosyası')
    parser.add_argument('--kontrol', action='store_true', help='Ağsız README / SVG / harf / takvim kontrolü')
    args = parser.parse_args()
    if args.kontrol:
        if args.command or args.veri:
            parser.error('--kontrol başka seçenekle birleştirilemez.')
        check_profile()
    elif args.command == 'tools':
        if args.veri:
            parser.error('--veri yalnız activity ile kullanılabilir.')
        build_tools()
    elif args.command == 'activity':
        calendar = calendar_data(json.loads(args.veri.read_text(encoding='utf-8'))) if args.veri else fetch_calendar()
        svg = activity_card(calendar, load_glyphs())
        tree = validate_svg('activity.svg', svg)
        count = validate_activity(tree)
        atomic_write(ASSETS / 'activity.svg', svg)
        print(f'activity.svg: {calendar["totalContributions"]} katkı, {count} gün, {len(svg.encode())} bayt.')
    else:
        parser.error('tools, activity veya --kontrol gerekli.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError, subprocess.SubprocessError) as error:
        print(f'Hata: {error}', file=sys.stderr)
        sys.exit(1)
