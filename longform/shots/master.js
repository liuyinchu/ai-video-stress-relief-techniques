/* Longform master: fixed camera, sampled geometry, synchronous metadata and text.
 * Pixel stage 2560×1440; all art and typography use a 1920×1080 logical canvas.
 */
(() => {
  'use strict';
  const data=window.LONG_RENDER_DATA;
  if(!data)throw new Error('Run longform/scripts/build_render_data.py before loading the master.');
  const canvas=document.getElementById('scene'),ctx=canvas.getContext('2d',{alpha:false});
  const artCanvas=document.createElement('canvas');artCanvas.width=2560;artCanvas.height=1440;
  const art=artCanvas.getContext('2d');
  const C={bg:'#06060e',warm:'#daa27d',copper:'#ac7859',cool:'#496d85',white:'#f3eee8',muted:'#a39b96'};
  const EPS=1e-7,FPS=data.fps,SCALE=4/3;
  const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
  const smooth=v=>{v=clamp(v);return v*v*(3-2*v);};
  const phase=(t,a,b)=>smooth((t-a)/(b-a));
  const chapterById=new Map(data.chapters.map(c=>[c.id,c]));
  const captions=data.captions,captionBoundaries=data.caption_boundaries;
  const font=(n,w=500)=>`${w} ${n}px "PingFang SC", "Heiti SC", sans-serif`;
  const english={hook:'THE BODY FIRST',title:'SEVEN SMALL PRACTICES',breath:'01 / BREATHE',cold:'02 / COOL TOUCH',ear:'03 / SOFT TOUCH',shake:'04 / UNCLENCH',paper:'05 / LET IT GO',fractal:'06 / LOOK AT NATURE',order:'07 / A SMALL ORDER',closing:'ROOM TO CHOOSE'};
  const keywords=['战或逃','双吸长呼','生理性叹气','自然呼吸','头晕','不必勉强','三叉神经','迷走神经','凉毛巾','舒服','轻轻','分形','一平米','相关','愤怒','写下','丢弃','节奏','专业人士','重新选择'];
  function text(s,x,y,size,color=C.white,weight=500,align='center'){
    ctx.font=font(size,weight);ctx.textAlign=align;ctx.textBaseline='middle';ctx.fillStyle=color;ctx.fillText(s,x,y);
  }
  function captionAt(t){
    const tt=t+EPS;let lo=0,hi=captions.length-1,found=-1;
    while(lo<=hi){const mid=(lo+hi)>>1;if(captions[mid].start<=tt){found=mid;lo=mid+1;}else hi=mid-1;}
    return found>=0&&tt<captions[found].end?captions[found]:null;
  }
  function chapterAt(t){
    let picked=data.chapters[0];
    for(const c of data.chapters){if(t+EPS>=c.start)picked=c;else break;}
    return picked;
  }
  function segmentEnv(c,t,cue){
    let beat=0;
    for(let i=0;i<c.segments.length;i++){if(t+EPS>=c.segments[i].start)beat=i;else break;}
    const s=c.segments[beat],beatT=clamp(t-s.start,0,s.end-s.start);
    const rawBeatProgress=clamp(beatT/Math.max(.001,s.end-s.start));
    let beatProgress=rawBeatProgress;
    const points=data.motion_remap?.[s.id];
    if(points){
      beatProgress=points[points.length-1][1];
      for(let i=1;i<points.length;i++)if(t<=points[i][0]+EPS){
        const a=points[i-1],b=points[i];
        beatProgress=a[1]+(b[1]-a[1])*clamp((t-a[0])/Math.max(EPS,b[0]-a[0]));break;
      }
    }
    return {beat,beatT,beatProgress,rawBeatProgress,segments:c.segments,
      chapterStart:c.start,globalTime:t,cue,palette:C};
  }
  function background(){
    ctx.setTransform(SCALE,0,0,SCALE,0,0);ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
    ctx.fillStyle=C.bg;ctx.fillRect(0,0,1920,1080);
    const g=ctx.createRadialGradient(960,490,30,960,490,880);
    g.addColorStop(0,'#0b0b15');g.addColorStop(.55,'#080810');g.addColorStop(1,C.bg);
    ctx.fillStyle=g;ctx.fillRect(0,0,1920,1080);
    // The entire film lives in the same dark volume, with two very faint wall contours.
    ctx.strokeStyle='rgba(73,109,133,.028)';ctx.lineWidth=.65;
    ctx.beginPath();ctx.ellipse(960,510,790,365,0,.05,Math.PI-.05);ctx.stroke();
    ctx.beginPath();ctx.ellipse(960,510,798,369,0,Math.PI+.1,Math.PI*2-.1);ctx.stroke();
  }
  function lightBridge(tr,t){
    const p=clamp((t-tr.start)/(tr.end-tr.start)),a=Math.sin(Math.PI*p)*.26;
    if(a<=0)return;
    const x=960+(p-.5)*700;
    const g=ctx.createRadialGradient(x,500,0,x,500,230);g.addColorStop(0,`rgba(218,162,125,${a*.12})`);g.addColorStop(1,'rgba(218,162,125,0)');
    ctx.fillStyle=g;ctx.fillRect(x-230,270,460,460);
    for(let k=0;k<5;k++){
      ctx.beginPath();
      for(let j=0;j<=90;j++){
        const q=j/90,xx=540+q*840,yy=500+Math.sin(q*Math.PI)*((k-2)*9+Math.sin(p*Math.PI)*17);
        if(j)ctx.lineTo(xx,yy);else ctx.moveTo(xx,yy);
      }
      ctx.strokeStyle=`rgba(218,162,125,${a*(k===2?.6:.16)})`;ctx.lineWidth=k===2?1:.55;ctx.stroke();
    }
  }
  function titleTreatment(alpha){
    ctx.save();ctx.globalAlpha=alpha;ctx.shadowColor='rgba(6,6,14,.95)';ctx.shadowBlur=19;
    text('压力上来',960,407,53,C.white,500);
    text('先让身体缓一缓',960,520,84,C.white,600);
    ctx.shadowBlur=0;text('七种生理与心理小技巧',960,657,28,C.warm,400);
    ctx.restore();
  }
  function heading(c,alpha){
    if(c.id==='title')return;
    ctx.save();ctx.globalAlpha=alpha;
    const label=c.id==='hook'?'压力 · 身体 · 注意力':c.id==='closing'?'缓下来，留一点选择的空间':c.title;
    text(label,960,75,30,C.warm,500);
    ctx.font='500 12px Arial, sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='rgba(172,120,89,.55)';ctx.fillText(english[c.id]||'',960,110);
    ctx.restore();
  }
  function drawChapter(c,t,alpha,cue){
    if(alpha<=.0001)return;
    const local=clamp(t-c.start,0,c.duration),env=segmentEnv(c,t,cue);
    // Composite the chapter as one layer, so local alpha assignments inside art
    // cannot bypass the master fade during a transition.
    art.setTransform(1,0,0,1,0,0);art.clearRect(0,0,2560,1440);art.globalAlpha=1;
    art.setTransform(SCALE,0,0,SCALE,0,0);art.save();art.translate(960,500);
    window.LongScenes[c.id](art,local,c.duration,env);art.restore();
    ctx.save();ctx.globalAlpha=alpha*(c.id==='title'?.43:1);
    if(c.id==='fractal'||c.id==='closing')ctx.filter='brightness(1.25)';
    ctx.drawImage(artCanvas,0,0,1920,1080);ctx.restore();
    heading(c,alpha);
    if(c.id==='cold'&&[1,2,3].includes(env.beat)){
      ctx.save();ctx.globalAlpha=alpha;
      text(env.beat===3?'凉毛巾不等于实验条件':'冷刺激 + 屏息：实验机制示意',960,158,25,C.muted,400);
      ctx.restore();
    }
    if(c.id==='closing'){
      const names=['呼吸','凉意','触觉','活动','写下','自然','整理'],p=local/Math.max(1,c.duration);
      ctx.save();
      names.forEach((name,i)=>{const a=-Math.PI/2+i/7*Math.PI*2;ctx.globalAlpha=alpha*phase(p,i*.045,.18+i*.045);text(name,960+Math.cos(a)*500,500+Math.sin(a)*247+82,29,C.warm,400);});
      ctx.restore();
    }
    if(c.id==='title')titleTreatment(alpha);
  }
  function subtitle(cue){
    if(!cue)return;
    const s=cue.text;ctx.save();
    const g=ctx.createLinearGradient(0,900,0,1080);g.addColorStop(0,'rgba(6,6,14,0)');g.addColorStop(.3,'rgba(6,6,14,.88)');g.addColorStop(1,C.bg);
    ctx.fillStyle=g;ctx.fillRect(0,900,1920,180);
    ctx.font=font(46,500);ctx.textAlign='left';ctx.textBaseline='middle';
    const width=ctx.measureText(s).width,x=960-width/2;
    // Keep exact subtitle wording; a single phrase receives a restrained warm accent.
    const keyword=keywords.find(k=>s.includes(k)),at=keyword?s.indexOf(keyword):-1;
    ctx.shadowColor='rgba(0,0,0,.9)';ctx.shadowBlur=7;
    if(at<0){ctx.fillStyle=C.white;ctx.fillText(s,x,980);}
    else{
      const a=s.slice(0,at),b=s.slice(at,at+keyword.length),z=s.slice(at+keyword.length);
      ctx.fillStyle=C.white;ctx.fillText(a,x,980);let xx=x+ctx.measureText(a).width;
      ctx.fillStyle=C.warm;ctx.fillText(b,xx,980);xx+=ctx.measureText(b).width;
      ctx.fillStyle=C.white;ctx.fillText(z,xx,980);
    }
    ctx.restore();
  }
  function transitionAt(t){return data.transitions.find(tr=>t+EPS>=tr.start&&t+EPS<tr.end);}
  function frame(time){
    const t=clamp(time,0,data.duration-EPS),cue=captionAt(t);background();
    const tr=transitionAt(t);
    if(tr){
      if(t+EPS<tr.mid){const c=chapterById.get(tr.from);drawChapter(c,t,1-phase(t,tr.start,tr.mid),cue);}
      else{const c=chapterById.get(tr.to);drawChapter(c,t,phase(t,tr.mid,tr.end),cue);}
      lightBridge(tr,t);
    }else{
      const c=chapterAt(t);let alpha=1;
      if(c.index===0)alpha=phase(t,0,.55);
      if(c.id==='closing')alpha*=1-phase(t,data.duration-.85,data.duration);
      drawChapter(c,t,alpha,cue);
    }
    subtitle(cue);
  }
  function blurAt(t){
    // Epsilon and a full frame guard keep text immune to floating-point cut ghosts.
    if(captionBoundaries.some(c=>Math.abs(t-c)<=1/FPS+EPS))return 1;
    if(data.cuts.some(c=>Math.abs(t-c)<=EPS))return 1;
    if(transitionAt(t))return 3;
    const c=chapterAt(t),env=segmentEnv(c,t,captionAt(t));
    if(c.id==='shake'&&env.beat===0&&env.beatProgress>.2)return 3;
    if(c.id==='paper'&&env.beat===0&&env.beatProgress>.72&&env.beatProgress<.95)return 3;
    return 1;
  }
  // Small inspection surface for QA only; no playback state is retained here.
  window.LONG_MASTER={render:frame,blurAt,captionAt,chapterAt,segmentEnv,data};
  Shot.define({duration:data.duration,fps:FPS,cuts:data.cuts,
    fonts:[[font(46,500),captions.map(c=>c.text).join('')],[font(84,600),'压力上来先让身体缓一缓'],['500 12px Arial','THE BODY FIRST']],
    async setup(){
      await document.fonts.ready;
      for(const c of data.chapters)if(typeof window.LongScenes?.[c.id]!=='function')throw new Error('Missing chapter renderer: '+c.id);
      // Build immutable art caches before capture. Every live frame still depends only on t.
      const warm=document.createElement('canvas');warm.width=2560;warm.height=1440;const wc=warm.getContext('2d');
      for(const c of data.chapters){wc.setTransform(SCALE,0,0,SCALE,0,0);wc.clearRect(0,0,1920,1080);wc.save();wc.translate(960,500);const t=c.start+c.duration*.5;window.LongScenes[c.id](wc,t-c.start,c.duration,segmentEnv(c,t,null));wc.restore();}
    },
    post:{motionBlur:3,maxMotionBlur:3,shutter:.28,grain:0},blurAt,
    meta:{title:data.title,format:'16:9',width:2560,height:1440,timing_status:data.timing_status,estimated:data.estimated,version:'longform-master-v1',render_core:'Multiplane 0.3.13'},render:frame
  });
})();
