import drawSvg as draw
import subprocess

symbols = [
    '☿',
    '♀',
    '♂',
    '♃',
    'I',
    '♒',
    '♑',
    '♐',
    '⛎',
    '♈',
    '♉',
    '♎',
    '♏',
    '♓',
    '♊',
    '♋',
    '♌',
    '♍',
]


for sym in symbols:
    d = draw.Drawing(64, 64, origin='center')
    d.append(draw.Text(sym, 64, -32, -32, fill='black'))
    d.saveSvg(f'{sym}.svg')
    subprocess.run(
        ['inkscape', '--without-gui', f'--file={sym}.svg', '--export-text-to-path', f'--export-plain-svg={sym}.svg'])
