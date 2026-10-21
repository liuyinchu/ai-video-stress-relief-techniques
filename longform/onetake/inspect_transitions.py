"""Extract adjacent frames from the encoded preview for handoff inspection."""
import json,subprocess
from pathlib import Path
import imageio_ffmpeg
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'longform/onetake';OUT=BASE/'output'
video=OUT/'film-1080p30.mp4'
report=json.loads((OUT/'preview/report.json').read_text())
assert report['complete'] and video.exists()
timeline=json.loads((ROOT/'longform/content/timeline.json').read_text())
directory=OUT/'transition-sheets';directory.mkdir(exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
items=[]
for chapter in timeline['chapters'][1:]:
 start=round((chapter['start']-3)*30)/30
 cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-v','error','-ss',str(start),'-i',str(video),'-an','-vf','select=not(mod(n\\,12)),scale=480:270','-frames:v','12','-fps_mode','vfr','-f','rawvideo','-pix_fmt','rgb24','-']
 raw=subprocess.check_output(cmd);size=480*270*3
 assert len(raw)==12*size,(chapter['id'],len(raw))
 sheet=Image.new('RGB',(1920,894),'#10141c');draw=ImageDraw.Draw(sheet)
 for i in range(12):
  x=(i%4)*480;y=(i//4)*298
  im=Image.frombytes('RGB',(480,270),raw[i*size:(i+1)*size]);sheet.paste(im,(x,y))
  draw.text((x+12,y+274),f"{chapter['id']} | {start+i*.4:.2f} s",fill='#ded9cf',font=font)
 path=directory/(chapter['id']+'.jpg');sheet.save(path,quality=93)
 items.append({'chapter':chapter['id'],'source_sha256':report['sha256'],'first_time':start,'step':.4,'frames':12,'sheet':str(path.relative_to(ROOT))})
(directory/'index.json').write_text(json.dumps(items,indent=2)+'\n')
print(json.dumps({'sheets':len(items),'frames_sampled':len(items)*12,'source_sha256':report['sha256']}))
