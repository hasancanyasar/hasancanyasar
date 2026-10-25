"""GitHub profil kartları; Python stdlib.

    python3 profil.py tools
    python3 profil.py --kontrol

tools macOS/CoreText gerektirir; --kontrol ağ ve Swift istemez.
"""
import argparse
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from identity import stars, wrap

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
NS = '{http://www.w3.org/2000/svg}'
MAX_BYTES = 150_000
ICON_VERSION = '16.35.0'
ICON_SOURCE = f'https://github.com/simple-icons/simple-icons/tree/{ICON_VERSION}/icons'
TOOLS = (
    ('python', ('Python',)), ('go', ('Go',)), ('javascript', ('JavaScript',)),
    ('n8n', ('n8n',)), ('git', ('Git',)),
    ('archlinux', ('Arch', 'Linux')), ('apple', ('macOS',)), ('claude', ('Claude',)), ('openai', ('Codex',)),
    ('googlegemini', ('Gemini',)), ('modelcontextprotocol', ('MCP',)),
)
ROWS = (4, 3, 4)  # diller / araçlar ve platformlar / yapay zekâ
OMITTED = ('Open WebUI',)
# OpenAI simgesi 16.35.0'da yok; son bulunduğu sabit sürümden alındı.
ICON_OVERRIDES = {'openai': '15.0.0'}
# Simple Icons 16.35.0, CC0-1.0; paths copied without alteration from icons/*.svg.
ICON_PATHS = {
    "go": "M1.811 10.231c-.047 0-.058-.023-.035-.059l.246-.315c.023-.035.081-.058.128-.058h4.172c.046 0 .058.035.035.07l-.199.303c-.023.036-.082.07-.117.07zM.047 11.306c-.047 0-.059-.023-.035-.058l.245-.316c.023-.035.082-.058.129-.058h5.328c.047 0 .07.035.058.07l-.093.28c-.012.047-.058.07-.105.07zm2.828 1.075c-.047 0-.059-.035-.035-.07l.163-.292c.023-.035.07-.07.117-.07h2.337c.047 0 .07.035.07.082l-.023.28c0 .047-.047.082-.082.082zm12.129-2.36c-.736.187-1.239.327-1.963.514-.176.046-.187.058-.34-.117-.174-.199-.303-.327-.548-.444-.737-.362-1.45-.257-2.115.175-.795.514-1.204 1.274-1.192 2.22.011.935.654 1.706 1.577 1.835.795.105 1.46-.175 1.987-.77.105-.13.198-.27.315-.434H10.47c-.245 0-.304-.152-.222-.35.152-.362.432-.97.596-1.274a.315.315 0 01.292-.187h4.253c-.023.316-.023.631-.07.947a4.983 4.983 0 01-.958 2.29c-.841 1.11-1.94 1.8-3.33 1.986-1.145.152-2.209-.07-3.143-.77-.865-.655-1.356-1.52-1.484-2.595-.152-1.274.222-2.419.993-3.424.83-1.086 1.928-1.776 3.272-2.02 1.098-.2 2.15-.07 3.096.571.62.41 1.063.97 1.356 1.648.07.105.023.164-.117.2m3.868 6.461c-1.064-.024-2.034-.328-2.852-1.029a3.665 3.665 0 01-1.262-2.255c-.21-1.32.152-2.489.947-3.529.853-1.122 1.881-1.706 3.272-1.95 1.192-.21 2.314-.095 3.33.595.923.63 1.496 1.484 1.648 2.605.198 1.578-.257 2.863-1.344 3.962-.771.783-1.718 1.273-2.805 1.495-.315.06-.63.07-.934.106zm2.78-4.72c-.011-.153-.011-.27-.034-.387-.21-1.157-1.274-1.81-2.384-1.554-1.087.245-1.788.935-2.045 2.033-.21.912.234 1.835 1.075 2.21.643.28 1.285.244 1.905-.07.923-.48 1.425-1.228 1.484-2.233z",
    "javascript": "M0 0h24v24H0V0zm22.034 18.276c-.175-1.095-.888-2.015-3.003-2.873-.736-.345-1.554-.585-1.797-1.14-.091-.33-.105-.51-.046-.705.15-.646.915-.84 1.515-.66.39.12.75.42.976.9 1.034-.676 1.034-.676 1.755-1.125-.27-.42-.404-.601-.586-.78-.63-.705-1.469-1.065-2.834-1.034l-.705.089c-.676.165-1.32.525-1.71 1.005-1.14 1.291-.811 3.541.569 4.471 1.365 1.02 3.361 1.244 3.616 2.205.24 1.17-.87 1.545-1.966 1.41-.811-.18-1.26-.586-1.755-1.336l-1.83 1.051c.21.48.45.689.81 1.109 1.74 1.756 6.09 1.666 6.871-1.004.029-.09.24-.705.074-1.65l.046.067zm-8.983-7.245h-2.248c0 1.938-.009 3.864-.009 5.805 0 1.232.063 2.363-.138 2.711-.33.689-1.18.601-1.566.48-.396-.196-.597-.466-.83-.855-.063-.105-.11-.196-.127-.196l-1.825 1.125c.305.63.75 1.172 1.324 1.517.855.51 2.004.675 3.207.405.783-.226 1.458-.691 1.811-1.411.51-.93.402-2.07.397-3.346.012-2.054 0-4.109 0-6.179l.004-.056z",
    "archlinux": "M11.39.605C10.376 3.092 9.764 4.72 8.635 7.132c.693.734 1.543 1.589 2.923 2.554-1.484-.61-2.496-1.224-3.252-1.86C6.86 10.842 4.596 15.138 0 23.395c3.612-2.085 6.412-3.37 9.021-3.862a6.61 6.61 0 01-.171-1.547l.003-.115c.058-2.315 1.261-4.095 2.687-3.973 1.426.12 2.534 2.096 2.478 4.409a6.52 6.52 0 01-.146 1.243c2.58.505 5.352 1.787 8.914 3.844-.702-1.293-1.33-2.459-1.929-3.57-.943-.73-1.926-1.682-3.933-2.713 1.38.359 2.367.772 3.137 1.234-6.09-11.334-6.582-12.84-8.67-17.74zM22.898 21.36v-.623h-.234v-.084h.562v.084h-.234v.623h.331v-.707h.142l.167.5.034.107a2.26 2.26 0 01.038-.114l.17-.493H24v.707h-.091v-.593l-.206.593h-.084l-.205-.602v.602h-.091",
    "openai": "M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z",
    "python": "M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z",
    "n8n": "M21.4737 5.6842c-1.1772 0-2.1663.8051-2.4468 1.8947h-2.8955c-1.235 0-2.289.893-2.492 2.111l-.1038.623a1.263 1.263 0 0 1-1.246 1.0555H11.289c-.2805-1.0896-1.2696-1.8947-2.4468-1.8947s-2.1663.8051-2.4467 1.8947H4.973c-.2805-1.0896-1.2696-1.8947-2.4468-1.8947C1.1311 9.4737 0 10.6047 0 12s1.131 2.5263 2.5263 2.5263c1.1772 0 2.1663-.8051 2.4468-1.8947h1.4223c.2804 1.0896 1.2696 1.8947 2.4467 1.8947 1.1772 0 2.1663-.8051 2.4468-1.8947h1.0008a1.263 1.263 0 0 1 1.2459 1.0555l.1038.623c.203 1.218 1.257 2.111 2.492 2.111h.3692c.2804 1.0895 1.2696 1.8947 2.4468 1.8947 1.3952 0 2.5263-1.131 2.5263-2.5263s-1.131-2.5263-2.5263-2.5263c-1.1772 0-2.1664.805-2.4468 1.8947h-.3692a1.263 1.263 0 0 1-1.246-1.0555l-.1037-.623A2.52 2.52 0 0 0 13.9607 12a2.52 2.52 0 0 0 .821-1.4794l.1038-.623a1.263 1.263 0 0 1 1.2459-1.0555h2.8955c.2805 1.0896 1.2696 1.8947 2.4468 1.8947 1.3952 0 2.5263-1.131 2.5263-2.5263s-1.131-2.5263-2.5263-2.5263m0 1.2632a1.263 1.263 0 0 1 1.2631 1.2631 1.263 1.263 0 0 1-1.2631 1.2632 1.263 1.263 0 0 1-1.2632-1.2632 1.263 1.263 0 0 1 1.2632-1.2631M2.5263 10.7368A1.263 1.263 0 0 1 3.7895 12a1.263 1.263 0 0 1-1.2632 1.2632A1.263 1.263 0 0 1 1.2632 12a1.263 1.263 0 0 1 1.2631-1.2632m6.3158 0A1.263 1.263 0 0 1 10.1053 12a1.263 1.263 0 0 1-1.2632 1.2632A1.263 1.263 0 0 1 7.579 12a1.263 1.263 0 0 1 1.2632-1.2632m10.1053 3.7895a1.263 1.263 0 0 1 1.2631 1.2632 1.263 1.263 0 0 1-1.2631 1.2631 1.263 1.263 0 0 1-1.2632-1.2631 1.263 1.263 0 0 1 1.2632-1.2632",
    "git": "M13.09 23.549a1.54 1.54 0 0 1-2.18 0L.451 13.089a1.54 1.54 0 0 1 0-2.179l7.191-7.19 2.733 2.733a1.85 1.85 0 0 0 .964 2.326v6.66a1.849 1.849 0 1 0 1.54 0V8.957l2.508 2.508a1.85 1.85 0 1 0 1.09-1.09l-2.634-2.634a1.85 1.85 0 0 0-2.378-2.377L8.73 2.63 10.91.451a1.54 1.54 0 0 1 2.179 0l10.459 10.46a1.54 1.54 0 0 1 0 2.179z",
    "apple": "M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701",
    "claude": "m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z",
    "googlegemini": "M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81",
    "modelcontextprotocol": "M13.85 0a4.16 4.16 0 0 0-2.95 1.217L1.456 10.66a.835.835 0 0 0 0 1.18.835.835 0 0 0 1.18 0l9.442-9.442a2.49 2.49 0 0 1 3.541 0 2.49 2.49 0 0 1 0 3.541L8.59 12.97l-.1.1a.835.835 0 0 0 0 1.18.835.835 0 0 0 1.18 0l.1-.098 7.03-7.034a2.49 2.49 0 0 1 3.542 0l.049.05a2.49 2.49 0 0 1 0 3.54l-8.54 8.54a1.96 1.96 0 0 0 0 2.755l1.753 1.753a.835.835 0 0 0 1.18 0 .835.835 0 0 0 0-1.18l-1.753-1.753a.266.266 0 0 1 0-.394l8.54-8.54a4.185 4.185 0 0 0 0-5.9l-.05-.05a4.16 4.16 0 0 0-2.95-1.218c-.2 0-.401.02-.6.048a4.17 4.17 0 0 0-1.17-3.552A4.16 4.16 0 0 0 13.85 0m0 3.333a.84.84 0 0 0-.59.245L6.275 10.56a4.186 4.186 0 0 0 0 5.902 4.186 4.186 0 0 0 5.902 0L19.16 9.48a.835.835 0 0 0 0-1.18.835.835 0 0 0-1.18 0l-6.985 6.984a2.49 2.49 0 0 1-3.54 0 2.49 2.49 0 0 1 0-3.54l6.983-6.985a.835.835 0 0 0 0-1.18.84.84 0 0 0-.59-.245"
}
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


def coretext(binary, text, size=40, weight='Regular', font=None):
    output = subprocess.check_output([
        str(binary), str(ASSETS / 'fonts' / (font or f'Poppins-{weight}.ttf')), str(size), text,
    ], text=True, timeout=30)
    result = json.loads(output)
    result['path'] = compact_path(result['path'])
    return result


def tools_card(binary):
    height = 554
    body = [stars(18, 1200, height, 56)]
    for index, (slug, lines) in enumerate(TOOLS):
        row = next(r for r in range(len(ROWS)) if index < sum(ROWS[:r + 1]))
        column = index - sum(ROWS[:row])
        x = 600 + (column - (ROWS[row] - 1) / 2) * 220
        y = 86 + row * 174
        # Peak follows the same left-to-right ten-second sweep on both rows.
        glint_delay = 1.5 + (x + 240) / 1680 * 7 - 1
        body.append(f'<g class="tool-reveal" style="animation-delay:{index * .12:.2f}s">')
        body.append(f'<g class="float" style="animation-delay:-{index * .7:.1f}s">')
        body.append(f'<g transform="translate({x - 36} {y - 36}) scale(3)">')
        body.append(f'<path d="{ICON_PATHS[slug]}" fill="url(#silver)" opacity=".84"/>')
        body.append(f'<path class="tool-glint" d="{ICON_PATHS[slug]}" fill="url(#silver)" style="animation-delay:{glint_delay:.2f}s"/>')
        body.append('</g>')
        for line, text in enumerate(lines):
            glyph = coretext(binary, text, 38)
            left = x - glyph['width'] / 2
            body.append(f'<path class="lettering" d="{glyph["path"]}" transform="translate({left:.2f} {y + 77 + line * 34}) scale(1 -1)" fill="url(#silver)" opacity=".84"/>')
        body.append('</g></g>')
    body.append(f'<rect class="sweep" x="0" y="0" width="180" height="{height}" fill="url(#sweep)"/>')
    css = SWEEP_CSS + '''
.tool-reveal{opacity:1;animation:reveal 1s cubic-bezier(.2,.8,.2,1) backwards}
@keyframes reveal{from{opacity:0;transform:translateY(18px)}to{opacity:1}}
.float{animation:float 6s ease-in-out infinite}
@keyframes float{50%{transform:translateY(-7px)}}
.tool-glint{opacity:0;animation:glint 10s ease-in-out infinite}
@keyframes glint{0%,3%,17%,100%{opacity:0}10%{opacity:.7}}
'''
    metadata = {
        'icons': {'project': 'Simple Icons', 'version': ICON_VERSION, 'license': 'CC0-1.0',
                  'source': ICON_SOURCE, 'slugs': [slug for slug, _ in TOOLS],
                  'overrides': ICON_OVERRIDES, 'omitted': list(OMITTED)},
    }
    return make_card(height, 'Kullandığım araçlar',
                     'Python, Go, JavaScript, n8n, Git, Arch Linux, macOS, Claude, '
                     'Codex, Google Gemini ve Model Context Protocol. Gümüş simgeler üç sırada '
                     'beliriyor, hafifçe süzülüyor; yavaş bir ışık soldan sağa geçiyor.',
                     '\n'.join(body), css, metadata=metadata)


SIGNATURE = 'Hasan Can'
SIGNATURE_FONT = 'MrsSaintDelafield-Regular.ttf'


def signature_card(binary):
    # Her harf ayrı yol: önce ince kontur çizilir, sonra dolgu oturur; harfler soldan sağa sırayla yazılır.
    height, size, baseline = 300, 190, 196
    full = coretext(binary, SIGNATURE, size, font=SIGNATURE_FONT)
    left = 600 - full['width'] / 2
    body = [stars(31, 1200, height, 40)]
    previous, order = '', 0
    body.append(f'<g transform="translate({left:.2f} {baseline}) scale(1 -1)">')
    for end in range(1, len(SIGNATURE) + 1):
        path = coretext(binary, SIGNATURE[:end], size, font=SIGNATURE_FONT)['path']
        if not path.startswith(previous):
            raise ValueError('İmza harfleri ayrıştırılamadı.')
        glyph, previous = path[len(previous):], path
        if not glyph:
            continue
        body.append(f'<path class="pen" pathLength="1" d="{glyph}" fill="url(#silver)" stroke="#d2dfed" stroke-width="1.1" style="animation-delay:{order * .26:.2f}s"/>')
        order += 1
    body.append('</g>')
    # İmzanın altındaki tek çizgi; yazı bittikten sonra çekilir.
    start, finish = left + 40, left + full['width'] + 10
    span = finish - start
    body.append(f'<path class="flourish" pathLength="1" d="M{start:.1f} 246 C{start + span * .3:.1f} 226 {start + span * .62:.1f} 262 {finish:.1f} 232" fill="none" stroke="url(#silver)" stroke-width="2.2" stroke-linecap="round" opacity=".7" style="animation-delay:{order * .26 + 1.3:.2f}s"/>')
    css = '''
.pen{stroke-dasharray:1;stroke-dashoffset:0;fill-opacity:1;stroke-opacity:0;animation:pen 14s ease-in-out infinite backwards}
@keyframes pen{
  0%{stroke-dashoffset:1;fill-opacity:0;stroke-opacity:1}
  7%{stroke-dashoffset:0;fill-opacity:0;stroke-opacity:1}
  11%{stroke-dashoffset:0;fill-opacity:1;stroke-opacity:0}
  86%{stroke-dashoffset:0;fill-opacity:1;stroke-opacity:0}
  93%,100%{stroke-dashoffset:0;fill-opacity:0;stroke-opacity:0}
}
.flourish{stroke-dasharray:1;stroke-dashoffset:0;animation:flourish 14s ease-in-out infinite backwards}
@keyframes flourish{
  0%{stroke-dashoffset:1;opacity:.7}
  6%{stroke-dashoffset:0;opacity:.7}
  78%{stroke-dashoffset:0;opacity:.7}
  84%,100%{stroke-dashoffset:0;opacity:0}
}
'''
    metadata = {'font': {'name': 'Mrs Saint Delafield', 'author': 'Alejandro Paul (Sudtipos)',
                         'license': 'SIL Open Font License 1.1; assets/fonts/OFL-MrsSaintDelafield.txt'}}
    return make_card(height, 'Hasan Can', 'El yazısıyla Hasan Can imzası: harfler soldan sağa sırayla yazılır, altına tek bir çizgi çekilir.',
                     '\n'.join(body), css, metadata=metadata)


def build_tools():
    # Mevcut Swift yardımcısını bir kez derle; --kontrol bunu çağırmaz.
    with tempfile.TemporaryDirectory(prefix='profil-coretext-') as directory:
        binary = Path(directory) / 'type'
        subprocess.run([
            'swiftc', '-sdk', '/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk',
            str(ROOT / 'type.swift'), '-o', str(binary),
        ], check=True, timeout=60)
        svg = tools_card(binary)
        signature = signature_card(binary)
    validate_svg('araclar.svg', svg)
    validate_svg('imza.svg', signature)
    atomic_write(ASSETS / 'araclar.svg', svg)
    atomic_write(ASSETS / 'imza.svg', signature)
    print(f'imza.svg: {len(signature.encode())} bayt. araclar.svg: {len(TOOLS)} simge, {len(svg.encode())} bayt. Atlanan: {", ".join(OMITTED)}.')


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
    expected = ['assets/identity.svg', 'assets/araclar.svg', 'assets/imza.svg', 'assets/horizon.svg']
    if [item.get('src') for item in parser.images] != expected:
        raise ValueError('README görselleri identity, araclar, imza, horizon sırasında olmalı.')
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
    for path in sorted(ASSETS.rglob('*.svg')):
        svg = path.read_text(encoding='utf-8')
        validate_svg(path.name, svg)
        print(f'{path.relative_to(ROOT)}: {len(svg.encode()):,} bayt · geçerli')
    print('README yolları, XML, bağımsız SVG, boyut ve reduced-motion doğrulandı.')


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
    parser.add_argument('command', nargs='?', choices=('tools',))
    parser.add_argument('--kontrol', action='store_true', help='Ağsız README / SVG kontrolü')
    args = parser.parse_args()
    if args.kontrol:
        if args.command:
            parser.error('--kontrol başka seçenekle birleştirilemez.')
        check_profile()
    elif args.command == 'tools':
        build_tools()
    else:
        parser.error('tools veya --kontrol gerekli.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError, subprocess.SubprocessError) as error:
        print(f'Hata: {error}', file=sys.stderr)
        sys.exit(1)
