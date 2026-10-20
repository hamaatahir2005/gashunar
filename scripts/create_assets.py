"""Generate original GAS HUNAR artwork. Requires Pillow and bundled DejaVu Sans."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]

def main():
    assets=ROOT/'assets';assets.mkdir(exist_ok=True)
    im=Image.new('RGBA',(512,512),(16,24,39,255));d=ImageDraw.Draw(im)
    d.rounded_rectangle((14,14,498,498),radius=100,fill='#101827',outline='#d7b66f',width=10)
    d.arc((120,120,392,365),180,360,fill='#d7b66f',width=15)
    d.line((103,249,409,249),fill='#d7b66f',width=15)
    d.ellipse((242,103,270,130),fill='#d7b66f')
    for x in (200,256,312):d.arc((x-10,45,x+10,98),70,260,fill='#d7b66f',width=5)
    font=ImageFont.truetype(str(assets/'DejaVuSans.ttf'),38)
    d.text((256,314),'GAS HUNAR',font=font,fill='#f5f4ef',anchor='mm')
    # Pillow RAQM, when available, shapes the Kurdish wordmark correctly.
    small=ImageFont.truetype(str(assets/'DejaVuSans.ttf'),38)
    try:d.text((256,378),'گەس هونەر',font=small,fill='#d7b66f',anchor='mm',direction='rtl')
    except (KeyError,ValueError):pass
    im.save(assets/'gas-hunar.png');im.save(assets/'gas-hunar.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    (assets/'logo.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="240" viewBox="0 0 640 240"><rect width="640" height="240" rx="28" fill="#101827"/><g stroke="#d7b66f" stroke-width="7" fill="none"><path d="M47 126 A66 66 0 0 1 179 126 M35 128 H191"/><circle cx="113" cy="53" r="6"/></g><text x="225" y="100" font-family="DejaVu Sans,sans-serif" font-size="44" fill="#fff">GAS HUNAR</text><text x="585" y="163" text-anchor="end" font-family="DejaVu Sans,sans-serif" font-size="42" fill="#d7b66f">گەس هونەر</text></svg>''',encoding='utf-8')

if __name__=='__main__':main()
