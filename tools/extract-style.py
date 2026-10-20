from pathlib import Path
import json
import fitz
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
out = root / 'reference/style'
out.mkdir(parents=True, exist_ok=True)
source = out / 'style-guide.pdf'
original = root / 'style-guide.pdf'
if not source.exists():
    original.rename(source)
doc = fitz.open(source)
texts, thumbs = [], []
for i, page in enumerate(doc):
    n = i + 1
    texts.append(f'\n===== PAGE {n} =====\n' + page.get_text('text'))
    scale = min(1.75, 1800 / max(page.rect.width, page.rect.height))
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    name = out / f'page-{n:02}.png'
    pix.save(name)
    im = Image.open(name).convert('RGB')
    im.thumbnail((460, 350))
    thumbs.append(im.copy())
(out / 'extracted-text.txt').write_text('\n'.join(texts))
cols = min(3, len(thumbs))
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new('RGB', (cols * 480, rows * 390), '#deded8')
draw = ImageDraw.Draw(sheet)
for i, im in enumerate(thumbs):
    x = i % cols * 480
    y = i // cols * 390
    sheet.paste(im, (x + (480-im.width)//2, y + 25))
    draw.text((x+15, y+8), f'PAGE {i+1}', fill='#111111')
sheet.save(out / 'contact-sheet.jpg', quality=92)
(out / 'pages.json').write_text(json.dumps({'pages':len(doc),'source':str(source),'images':[str(out/f'page-{i+1:02}.png') for i in range(len(doc))]},ensure_ascii=False,indent=2))
print('\n'.join(texts))
print(f'PAGES={len(doc)} CONTACT_SHEET={out / "contact-sheet.jpg"}')
