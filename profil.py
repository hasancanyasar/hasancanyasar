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
    ('githubactions', ('GitHub', 'Actions')), ('linux', ('Linux',)),
    ('archlinux', ('Arch', 'Linux')),
    ('apple', ('macOS',)), ('claude', ('Claude',)), ('openai', ('Codex',)),
    ('googlegemini', ('Gemini',)), ('modelcontextprotocol', ('MCP',)),
)
FIRST_ROW = 6
OMITTED = ('Open WebUI',)
# OpenAI simgesi 16.35.0'da yok; son bulunduğu sabit sürümden alındı.
ICON_OVERRIDES = {'openai': '15.0.0'}
# Simple Icons 16.35.0, CC0-1.0; paths copied without alteration from icons/*.svg.
ICON_PATHS = {
    "linux": "M12.504 0c-.155 0-.315.008-.48.021-4.226.333-3.105 4.807-3.17 6.298-.076 1.092-.3 1.953-1.05 3.02-.885 1.051-2.127 2.75-2.716 4.521-.278.832-.41 1.684-.287 2.489a.424.424 0 00-.11.135c-.26.268-.45.6-.663.839-.199.199-.485.267-.797.4-.313.136-.658.269-.864.68-.09.189-.136.394-.132.602 0 .199.027.4.055.536.058.399.116.728.04.97-.249.68-.28 1.145-.106 1.484.174.334.535.47.94.601.81.2 1.91.135 2.774.6.926.466 1.866.67 2.616.47.526-.116.97-.464 1.208-.946.587-.003 1.23-.269 2.26-.334.699-.058 1.574.267 2.577.2.025.134.063.198.114.333l.003.003c.391.778 1.113 1.132 1.884 1.071.771-.06 1.592-.536 2.257-1.306.631-.765 1.683-1.084 2.378-1.503.348-.199.629-.469.649-.853.023-.4-.2-.811-.714-1.376v-.097l-.003-.003c-.17-.2-.25-.535-.338-.926-.085-.401-.182-.786-.492-1.046h-.003c-.059-.054-.123-.067-.188-.135a.357.357 0 00-.19-.064c.431-1.278.264-2.55-.173-3.694-.533-1.41-1.465-2.638-2.175-3.483-.796-1.005-1.576-1.957-1.56-3.368.026-2.152.236-6.133-3.544-6.139zm.529 3.405h.013c.213 0 .396.062.584.198.19.135.33.332.438.533.105.259.158.459.166.724 0-.02.006-.04.006-.06v.105a.086.086 0 01-.004-.021l-.004-.024a1.807 1.807 0 01-.15.706.953.953 0 01-.213.335.71.71 0 00-.088-.042c-.104-.045-.198-.064-.284-.133a1.312 1.312 0 00-.22-.066c.05-.06.146-.133.183-.198.053-.128.082-.264.088-.402v-.02a1.21 1.21 0 00-.061-.4c-.045-.134-.101-.2-.183-.333-.084-.066-.167-.132-.267-.132h-.016c-.093 0-.176.03-.262.132a.8.8 0 00-.205.334 1.18 1.18 0 00-.09.4v.019c.002.089.008.179.02.267-.193-.067-.438-.135-.607-.202a1.635 1.635 0 01-.018-.2v-.02a1.772 1.772 0 01.15-.768c.082-.22.232-.406.43-.533a.985.985 0 01.594-.2zm-2.962.059h.036c.142 0 .27.048.399.135.146.129.264.288.344.465.09.199.14.4.153.667v.004c.007.134.006.2-.002.266v.08c-.03.007-.056.018-.083.024-.152.055-.274.135-.393.2.012-.09.013-.18.003-.267v-.015c-.012-.133-.04-.2-.082-.333a.613.613 0 00-.166-.267.248.248 0 00-.183-.064h-.021c-.071.006-.13.04-.186.132a.552.552 0 00-.12.27.944.944 0 00-.023.33v.015c.012.135.037.2.08.334.046.134.098.2.166.268.01.009.02.018.034.024-.07.057-.117.07-.176.136a.304.304 0 01-.131.068 2.62 2.62 0 01-.275-.402 1.772 1.772 0 01-.155-.667 1.759 1.759 0 01.08-.668 1.43 1.43 0 01.283-.535c.128-.133.26-.2.418-.2zm1.37 1.706c.332 0 .733.065 1.216.399.293.2.523.269 1.052.468h.003c.255.136.405.266.478.399v-.131a.571.571 0 01.016.47c-.123.31-.516.643-1.063.842v.002c-.268.135-.501.333-.775.465-.276.135-.588.292-1.012.267a1.139 1.139 0 01-.448-.067 3.566 3.566 0 01-.322-.198c-.195-.135-.363-.332-.612-.465v-.005h-.005c-.4-.246-.616-.512-.686-.71-.07-.268-.005-.47.193-.6.224-.135.38-.271.483-.336.104-.074.143-.102.176-.131h.002v-.003c.169-.202.436-.47.839-.601.139-.036.294-.065.466-.065zm2.8 2.142c.358 1.417 1.196 3.475 1.735 4.473.286.534.855 1.659 1.102 3.024.156-.005.33.018.513.064.646-1.671-.546-3.467-1.089-3.966-.22-.2-.232-.335-.123-.335.59.534 1.365 1.572 1.646 2.757.13.535.16 1.104.021 1.67.067.028.135.06.205.067 1.032.534 1.413.938 1.23 1.537v-.043c-.06-.003-.12 0-.18 0h-.016c.151-.467-.182-.825-1.065-1.224-.915-.4-1.646-.336-1.77.465-.008.043-.013.066-.018.135-.068.023-.139.053-.209.064-.43.268-.662.669-.793 1.187-.13.533-.17 1.156-.205 1.869v.003c-.02.334-.17.838-.319 1.35-1.5 1.072-3.58 1.538-5.348.334a2.645 2.645 0 00-.402-.533 1.45 1.45 0 00-.275-.333c.182 0 .338-.03.465-.067a.615.615 0 00.314-.334c.108-.267 0-.697-.345-1.163-.345-.467-.931-.995-1.788-1.521-.63-.4-.986-.87-1.15-1.396-.165-.534-.143-1.085-.015-1.645.245-1.07.873-2.11 1.274-2.763.107-.065.037.135-.408.974-.396.751-1.14 2.497-.122 3.854a8.123 8.123 0 01.647-2.876c.564-1.278 1.743-3.504 1.836-5.268.048.036.217.135.289.202.218.133.38.333.59.465.21.201.477.335.876.335.039.003.075.006.11.006.412 0 .73-.134.997-.268.29-.134.52-.334.74-.4h.005c.467-.135.835-.402 1.044-.7zm2.185 8.958c.037.6.343 1.245.882 1.377.588.134 1.434-.333 1.791-.765l.211-.01c.315-.007.577.01.847.268l.003.003c.208.199.305.53.391.876.085.4.154.78.409 1.066.486.527.645.906.636 1.14l.003-.007v.018l-.003-.012c-.015.262-.185.396-.498.595-.63.401-1.746.712-2.457 1.57-.618.737-1.37 1.14-2.036 1.191-.664.053-1.237-.2-1.574-.898l-.005-.003c-.21-.4-.12-1.025.056-1.69.176-.668.428-1.344.463-1.897.037-.714.076-1.335.195-1.814.12-.465.308-.797.641-.984l.045-.022zm-10.814.049h.01c.053 0 .105.005.157.014.376.055.706.333 1.023.752l.91 1.664.003.003c.243.533.754 1.064 1.189 1.637.434.598.77 1.131.729 1.57v.006c-.057.744-.48 1.148-1.125 1.294-.645.135-1.52.002-2.395-.464-.968-.536-2.118-.469-2.857-.602-.369-.066-.61-.2-.723-.4-.11-.2-.113-.602.123-1.23v-.004l.002-.003c.117-.334.03-.752-.027-1.118-.055-.401-.083-.71.043-.94.16-.334.396-.4.69-.533.294-.135.64-.202.915-.47h.002v-.002c.256-.268.445-.601.668-.838.19-.201.38-.336.663-.336zm7.159-9.074c-.435.201-.945.535-1.488.535-.542 0-.97-.267-1.28-.466-.154-.134-.28-.268-.373-.335-.164-.134-.144-.333-.074-.333.109.016.129.134.199.2.096.066.215.2.36.333.292.2.68.467 1.167.467.485 0 1.053-.267 1.398-.466.195-.135.445-.334.648-.467.156-.136.149-.267.279-.267.128.016.034.134-.147.332a8.097 8.097 0 01-.69.468zm-1.082-1.583V5.64c-.006-.02.013-.042.029-.05.074-.043.18-.027.26.004.063 0 .16.067.15.135-.006.049-.085.066-.135.066-.055 0-.092-.043-.141-.068-.052-.018-.146-.008-.163-.065zm-.551 0c-.02.058-.113.049-.166.066-.047.025-.086.068-.14.068-.05 0-.13-.02-.136-.068-.01-.066.088-.133.15-.133.08-.031.184-.047.259-.005.019.009.036.03.03.05v.02h.003z",
    "archlinux": "M11.39.605C10.376 3.092 9.764 4.72 8.635 7.132c.693.734 1.543 1.589 2.923 2.554-1.484-.61-2.496-1.224-3.252-1.86C6.86 10.842 4.596 15.138 0 23.395c3.612-2.085 6.412-3.37 9.021-3.862a6.61 6.61 0 01-.171-1.547l.003-.115c.058-2.315 1.261-4.095 2.687-3.973 1.426.12 2.534 2.096 2.478 4.409a6.52 6.52 0 01-.146 1.243c2.58.505 5.352 1.787 8.914 3.844-.702-1.293-1.33-2.459-1.929-3.57-.943-.73-1.926-1.682-3.933-2.713 1.38.359 2.367.772 3.137 1.234-6.09-11.334-6.582-12.84-8.67-17.74zM22.898 21.36v-.623h-.234v-.084h.562v.084h-.234v.623h.331v-.707h.142l.167.5.034.107a2.26 2.26 0 01.038-.114l.17-.493H24v.707h-.091v-.593l-.206.593h-.084l-.205-.602v.602h-.091",
    "openai": "M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z",
    "python": "M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z",
    "n8n": "M21.4737 5.6842c-1.1772 0-2.1663.8051-2.4468 1.8947h-2.8955c-1.235 0-2.289.893-2.492 2.111l-.1038.623a1.263 1.263 0 0 1-1.246 1.0555H11.289c-.2805-1.0896-1.2696-1.8947-2.4468-1.8947s-2.1663.8051-2.4467 1.8947H4.973c-.2805-1.0896-1.2696-1.8947-2.4468-1.8947C1.1311 9.4737 0 10.6047 0 12s1.131 2.5263 2.5263 2.5263c1.1772 0 2.1663-.8051 2.4468-1.8947h1.4223c.2804 1.0896 1.2696 1.8947 2.4467 1.8947 1.1772 0 2.1663-.8051 2.4468-1.8947h1.0008a1.263 1.263 0 0 1 1.2459 1.0555l.1038.623c.203 1.218 1.257 2.111 2.492 2.111h.3692c.2804 1.0895 1.2696 1.8947 2.4468 1.8947 1.3952 0 2.5263-1.131 2.5263-2.5263s-1.131-2.5263-2.5263-2.5263c-1.1772 0-2.1664.805-2.4468 1.8947h-.3692a1.263 1.263 0 0 1-1.246-1.0555l-.1037-.623A2.52 2.52 0 0 0 13.9607 12a2.52 2.52 0 0 0 .821-1.4794l.1038-.623a1.263 1.263 0 0 1 1.2459-1.0555h2.8955c.2805 1.0896 1.2696 1.8947 2.4468 1.8947 1.3952 0 2.5263-1.131 2.5263-2.5263s-1.131-2.5263-2.5263-2.5263m0 1.2632a1.263 1.263 0 0 1 1.2631 1.2631 1.263 1.263 0 0 1-1.2631 1.2632 1.263 1.263 0 0 1-1.2632-1.2632 1.263 1.263 0 0 1 1.2632-1.2631M2.5263 10.7368A1.263 1.263 0 0 1 3.7895 12a1.263 1.263 0 0 1-1.2632 1.2632A1.263 1.263 0 0 1 1.2632 12a1.263 1.263 0 0 1 1.2631-1.2632m6.3158 0A1.263 1.263 0 0 1 10.1053 12a1.263 1.263 0 0 1-1.2632 1.2632A1.263 1.263 0 0 1 7.579 12a1.263 1.263 0 0 1 1.2632-1.2632m10.1053 3.7895a1.263 1.263 0 0 1 1.2631 1.2632 1.263 1.263 0 0 1-1.2631 1.2631 1.263 1.263 0 0 1-1.2632-1.2631 1.263 1.263 0 0 1 1.2632-1.2632",
    "git": "M13.09 23.549a1.54 1.54 0 0 1-2.18 0L.451 13.089a1.54 1.54 0 0 1 0-2.179l7.191-7.19 2.733 2.733a1.85 1.85 0 0 0 .964 2.326v6.66a1.849 1.849 0 1 0 1.54 0V8.957l2.508 2.508a1.85 1.85 0 1 0 1.09-1.09l-2.634-2.634a1.85 1.85 0 0 0-2.378-2.377L8.73 2.63 10.91.451a1.54 1.54 0 0 1 2.179 0l10.459 10.46a1.54 1.54 0 0 1 0 2.179z",
    "githubactions": "M10.984 13.836a.5.5 0 0 1-.353-.146l-.745-.743a.5.5 0 1 1 .706-.708l.392.391 1.181-1.18a.5.5 0 0 1 .708.707l-1.535 1.533a.504.504 0 0 1-.354.146zm9.353-.147l1.534-1.532a.5.5 0 0 0-.707-.707l-1.181 1.18-.392-.391a.5.5 0 1 0-.706.708l.746.743a.497.497 0 0 0 .706-.001zM4.527 7.452l2.557-1.585A1 1 0 0 0 7.09 4.17L4.533 2.56A1 1 0 0 0 3 3.406v3.196a1.001 1.001 0 0 0 1.527.85zm2.03-2.436L4 6.602V3.406l2.557 1.61zM24 12.5c0 1.93-1.57 3.5-3.5 3.5a3.503 3.503 0 0 1-3.46-3h-2.08a3.503 3.503 0 0 1-3.46 3 3.502 3.502 0 0 1-3.46-3h-.558c-.972 0-1.85-.399-2.482-1.042V17c0 1.654 1.346 3 3 3h.04c.244-1.693 1.7-3 3.46-3 1.93 0 3.5 1.57 3.5 3.5S13.43 24 11.5 24a3.502 3.502 0 0 1-3.46-3H8c-2.206 0-4-1.794-4-4V9.899A5.008 5.008 0 0 1 0 5c0-2.757 2.243-5 5-5s5 2.243 5 5a5.005 5.005 0 0 1-4.952 4.998A2.482 2.482 0 0 0 7.482 12h.558c.244-1.693 1.7-3 3.46-3a3.502 3.502 0 0 1 3.46 3h2.08a3.503 3.503 0 0 1 3.46-3c1.93 0 3.5 1.57 3.5 3.5zm-15 8c0 1.378 1.122 2.5 2.5 2.5s2.5-1.122 2.5-2.5-1.122-2.5-2.5-2.5S9 19.122 9 20.5zM5 9c2.206 0 4-1.794 4-4S7.206 1 5 1 1 2.794 1 5s1.794 4 4 4zm9 3.5c0-1.378-1.122-2.5-2.5-2.5S9 11.122 9 12.5s1.122 2.5 2.5 2.5 2.5-1.122 2.5-2.5zm9 0c0-1.378-1.122-2.5-2.5-2.5S18 11.122 18 12.5s1.122 2.5 2.5 2.5 2.5-1.122 2.5-2.5zm-13 8a.5.5 0 1 0 1 0 .5.5 0 0 0-1 0zm2 0a.5.5 0 1 0 1 0 .5.5 0 0 0-1 0zm12 0c0 1.93-1.57 3.5-3.5 3.5a3.503 3.503 0 0 1-3.46-3.002c-.007.001-.013.005-.021.005l-.506.017h-.017a.5.5 0 0 1-.016-.999l.506-.017c.018-.002.035.006.052.007A3.503 3.503 0 0 1 20.5 17c1.93 0 3.5 1.57 3.5 3.5zm-1 0c0-1.378-1.122-2.5-2.5-2.5S18 19.122 18 20.5s1.122 2.5 2.5 2.5 2.5-1.122 2.5-2.5z",
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
        row = 0 if index < FIRST_ROW else 1
        column = index if row == 0 else index - FIRST_ROW
        x = 110 + column * 196 + (98 if row else 0)
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
                  'overrides': ICON_OVERRIDES, 'omitted': list(OMITTED)},
    }
    return make_card(height, 'Kullandığım araçlar',
                     'Python, n8n, Git, GitHub Actions, Linux, Arch Linux, macOS, Claude, '
                     'Codex, Google Gemini ve Model Context Protocol. Gümüş simgeler iki sırada '
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
    if type(total) is not int or total < 0 or not isinstance(weeks, list) or not SHOWN_WEEKS <= len(weeks) <= 54:
        raise ValueError(f'Takvim, katkı toplamı ve {SHOWN_WEEKS}–54 hafta içermeli.')
    previous = None
    normalized = []
    for index, week in enumerate(weeks):
        days = week.get('contributionDays') if isinstance(week, dict) else None
        if not isinstance(days, list) or not 1 <= len(days) <= 7:
            raise ValueError('Her hafta 1–7 gün içermeli.')
        if 0 < index < len(weeks) - 1 and len(days) != 7:
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
                body.append(text_path(MONTHS[stamp.month - 1], 25, x - 2, 310, glyphs, .45))
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
