/* One continuous wall, two independent camera framings. No accumulated state. */
(() => {
  const stage = document.getElementById("stage");
  const portrait = stage.dataset.format === "portrait";
  const cover = stage.dataset.cover === "true";
  const edition = window.FILM_EDITION || {};
  const W = portrait ? 1080 : 1920, H = portrait ? 1920 : 1080;
  const canvas = document.getElementById("scene");
  const ctx = canvas.getContext("2d", {alpha:false});
  const DPR = window.devicePixelRatio || 1;
  canvas.width=W*DPR; canvas.height=H*DPR;
  canvas.style.width=W+"px"; canvas.style.height=H+"px";
  const C = {bg:"#06060e",warm:"#daa27d",white:"#f3eee8",muted:"#a39b96",blue:"#7096b0",line:"#6d5c51"};
  const labels = [
    ["01 / THE BODY FIRST", "先松一口气", "给身体一点缓冲"],
    ["01 / BREATHE", "双吸 · 长呼", "轻轻吸  /  再补一点  /  慢慢呼"],
    ["02 / COOL TOUCH", "一条凉毛巾", "轻敷脸颊 · 自然呼吸"],
    ["03 / SOFT TOUCH", "轻揉耳廓", "轻一点 · 以舒服为准"],
    ["04 / UNCLENCH", "松开肩膀", "轻动手脚 · 不甩头"],
    ["05 / LET IT GO", "写下，再放下", "写在纸上 · 揉成团 · 丢掉"],
    ["06 / LOOK OUTSIDE", "让目光休息", "看看树叶 · 看看云朵"],
    ["07 / A SMALL ORDER", "只收拾一小块", "一角桌面，也很好"],
    ["A MOMENT FOR YOURSELF", "挑一个，就好", "先松一口气，再处理眼前的事"]
  ];
  const lines = [
    ["压力上来，先别急着说服自己", "给身体一点缓冲"],
    ["鼻子吸气，再轻轻补一小口", "嘴巴慢慢呼出", "不要用力，头晕就停"],
    ["用凉毛巾轻敷脸颊", "保持自然呼吸"],
    ["轻揉耳廓，以舒服为准"],
    ["轻轻抖动手脚，放松肩膀", "别甩头"],
    ["把烦心事写下来", "揉成纸团，再丢掉"],
    ["看一会儿树叶、云朵", "让目光慢下来"],
    ["只整理桌面一小块", "让眼前恢复一点秩序"],
    ["不必全做，挑一个就好", "先松一口气", "再处理眼前的事"]
  ];
  let data;
  let captionCues;
  const textCuts=edition.cuts || [0.4, 3.5, 4.9, 5.4, 8.0, 8.7, 11.2, 15, 16.6, 17.4, 20.4, 22.7, 23.4, 27.7, 28.4, 32.4, 33.7, 34.4, 37.0, 41.7, 42.4, 45.6, 48.7, 49.4, 52.0, 54.7, 55.2, 55.5, 58.3, 59.5, 61.5];
  const clamp = (v,a=0,b=1) => Math.max(a,Math.min(b,v));
  const smooth = u => {u=clamp(u);return u*u*u*(u*(u*6-15)+10);};
  const mix = (a,b,k)=>a+(b-a)*k;
  const font = (size,weight=500)=>`${weight} ${size}px "PingFang SC", "Heiti SC", sans-serif`;
  function text(s,x,y,size=40,color=C.white,weight=500,align="center") {
    ctx.font=font(size,weight);ctx.fillStyle=color;ctx.textAlign=align;ctx.textBaseline="middle";ctx.fillText(s,x,y);
  }
  function tracking(s,x,y,size=18,color=C.warm,space=4) {
    ctx.font=`500 ${size}px Arial`;ctx.fillStyle=color;ctx.textBaseline="middle";ctx.textAlign="left";
    let total=0;for(const ch of s)total+=ctx.measureText(ch).width+space;
    let xx=x-total/2;for(const ch of s){ctx.fillText(ch,xx,y);xx+=ctx.measureText(ch).width+space;}
  }
  function line(x1,y1,x2,y2,color=C.line,width=1) {
    ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();
  }
  function camera(t) {
    let i=0; for(let n=1;n<data.stations.length;n++)if(t>=data.stations[n].start-.48)i=n;
    const b=data.stations[i],a=data.stations[Math.max(0,i-1)];
    const p=i?smooth((t-(b.start-.48))/.96):1;
    // A shallow pull-back gives travel room; the camera stops exactly on the station.
    const travel=1-.09*Math.sin(Math.PI*p);
    return {x:mix(a.x,b.x,p),y:mix(a.y,b.y,p),z:(portrait?1:.96)*travel,i,p};
  }
  function atmosphericBackground(t,cam) {
    ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);
    const glow=ctx.createRadialGradient(W*.5,H*.49,0,W*.5,H*.49,W*.64);
    glow.addColorStop(0,"#11101c");glow.addColorStop(.42,"#0b0b16");glow.addColorStop(1,C.bg);
    ctx.fillStyle=glow;ctx.fillRect(0,0,W,H);
    // Sparse fixed dust: positions belong to the wall and move with the camera.
    for(let i=0;i<115;i++){
      const x=((Math.sin(i*127.1+45)*43758.5453)%1+1)%1*W;
      const y=((Math.sin(i*269.5+83)*32545.1231)%1+1)%1*H;
      const a=.09+(((i*17)%9)/9)*.14;
      ctx.fillStyle=`rgba(212,183,154,${a})`;
      const xx=(x-cam.x*.018+W*100)%W,yy=(y-cam.y*.018+H*100)%H;
      ctx.fillRect(xx,yy,i%13===0?2:1,i%13===0?2:1);
    }
  }
  function wallLinks() {
    ctx.save();ctx.strokeStyle="rgba(163,120,85,.20)";ctx.lineWidth=1.2;
    for(let i=1;i<data.stations.length;i++){
      const a=data.stations[i-1],b=data.stations[i];
      const dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy),ux=dx/d,uy=dy/d;
      ctx.beginPath();ctx.moveTo(a.x+ux*600,a.y+uy*600);ctx.lineTo(b.x-ux*600,b.y-uy*600);ctx.stroke();
      const mx=(a.x+b.x)/2,my=(a.y+b.y)/2;
      ctx.beginPath();ctx.arc(mx,my,5,0,Math.PI*2);ctx.stroke();
      line(mx-uy*18,my+ux*18,mx+uy*18,my-ux*18,"rgba(163,120,85,.26)",1);
    }
    ctx.restore();
  }
  function retime(id,t) {
    const keys=edition.retime && edition.retime[id];
    if(!keys)return t;
    for(let k=1;k<keys.length;k++){
      if(t<=keys[k][0])return mix(keys[k-1][1],keys[k][1],clamp((t-keys[k-1][0])/(keys[k][0]-keys[k-1][0])));
    }
    return keys[keys.length-1][1];
  }
  function station(s,i,t) {
    const local=clamp(t-s.start,0,s.end-s.start);
    const artTime=retime(s.id,local);
    ctx.save();ctx.translate(s.x,s.y);
    const titleY=portrait?-475:-352, artY=portrait?35:20;
    // These faint edge fragments belong to a continuous mural, never individual cards.
    ctx.strokeStyle="rgba(218,162,125,.09)";ctx.lineWidth=1;
    ctx.beginPath();ctx.arc(0,artY,portrait?430:415,-.22,.46);ctx.stroke();
    ctx.beginPath();ctx.arc(0,artY,portrait?430:415,Math.PI-.46,Math.PI+.22);ctx.stroke();
    if(i===0){
      if(portrait){
        tracking("A SMALL RESET",0,-600,20,C.warm,6);
        text("先松",0,-426,152,C.white,600);text("一口气",0,-252,152,C.white,600);
        ctx.save();ctx.translate(0,150);window.drawIllustration(ctx,"intro",artTime);ctx.restore();
        text("7 个让身体缓下来的小动作",0,510,39,C.warm,500);
      }else{
        tracking("A SMALL RESET",-430,-261,19,C.warm,5);
        text("先松",-430,-103,140,C.white,600);text("一口气",-430,60,140,C.white,600);
        text("7 个让身体缓下来的小动作",-430,240,33,C.warm,500);
        ctx.save();ctx.translate(340,0);window.drawIllustration(ctx,"intro",artTime);ctx.restore();
      }
    }else if(i===8){
      tracking(labels[i][0],0,titleY-75,18,C.warm,4);
      text(labels[i][1],0,titleY+30,portrait?92:94,C.white,600);
      ctx.save();ctx.translate(0,artY+25);window.drawIllustration(ctx,"outro",artTime);ctx.restore();
      text("先松一口气",0,portrait?440:338,42,C.warm,500);
      text("不必全做，也不必立刻变好",0,portrait?510:397,30,C.muted,400);
    }else{
      tracking(labels[i][0],0,titleY-65,18,C.warm,4);
      text(labels[i][1],0,titleY+26,portrait?84:87,C.white,600);
      ctx.save();ctx.translate(0,artY);window.drawIllustration(ctx,s.id,artTime);ctx.restore();
      if(i===1){
        const cue=artTime<3-1e-7?"吸气":artTime<3.7-1e-7?"再补一小口":artTime<10-1e-7?"慢慢呼出":"自然呼吸";
        text(cue,0,artY+4,42,C.white,500);
        const sequence=["吸","补","呼"];
        sequence.forEach((label,j)=>{
          let active=(j===0&&artTime<3-1e-7)||(j===1&&artTime>=3-1e-7&&artTime<3.7-1e-7)||(j===2&&artTime>=3.7-1e-7&&artTime<10-1e-7);
          text(label,(j-1)*170,portrait?435:338,31,active?C.warm:"#6c6667",500);
          if(j<2)line((j-1)*170+38,portrait?435:338,(j)*170-38,portrait?435:338,"#3d3431",1);
        });
      }else text(labels[i][2],0,portrait?440:350,32,C.warm,400);
    }
    ctx.restore();
  }
  function subtitle(t) {
    if(cover)return;
    let n=data.segments.findIndex(s=>t>=s.start&&t<=s.end);
    if(n<0)return;
    const s=data.segments[n];const arr=lines[n];
    const cue=captionCues.find(c=>t+1e-7>=c.start&&t+1e-7<c.end);
    if(!cue)return;
    const selected=cue.text;
    const fade=Math.min(clamp((t-s.start)/.15),clamp((s.end-t)/.15));
    ctx.save();ctx.globalAlpha=fade;
    const yy=portrait?1662:980;
    const shade=ctx.createLinearGradient(0,yy-75,0,H);shade.addColorStop(0,"rgba(6,6,14,0)");shade.addColorStop(.5,"rgba(6,6,14,.9)");shade.addColorStop(1,"rgba(6,6,14,1)");
    ctx.fillStyle=shade;ctx.fillRect(0,yy-75,W,H-yy+75);
    ctx.shadowColor="rgba(255,245,233,.17)";ctx.shadowBlur=9;
    text(selected,W/2,yy,portrait?44:42,C.white,600);
    ctx.restore();
  }
  function frame(t) {
    t=cover?2.6:clamp(t,0,62);
    ctx.setTransform(DPR,0,0,DPR,0,0);
    const cam=camera(t);atmosphericBackground(t,cam);
    ctx.save();ctx.translate(W/2,H/2-(portrait?24:16));ctx.scale(cam.z,cam.z);ctx.translate(-cam.x,-cam.y);
    wallLinks();
    data.stations.forEach((s,i)=>{if(Math.abs(s.x-cam.x)<W/cam.z/2+1000&&Math.abs(s.y-cam.y)<H/cam.z/2+1000)station(s,i,t);});
    ctx.restore();
    ctx.save();
    const edge=portrait?82:72;
    tracking("身 体 的 缓 冲 时 间",W/2,edge,portrait?18:16,"#8c8078",3);
    if(!cover){
      const yy=portrait?1788:1042;
      const x0=W/2-120;
      if(t<55.2)data.stations.slice(1,8).forEach((s,i)=>{
        const active=t>=s.start;ctx.fillStyle=active?C.warm:"#423632";
        ctx.beginPath();ctx.arc(x0+i*40,yy,active?3:2.3,0,Math.PI*2);ctx.fill();
      });
    }else{
      tracking("01   /   EVERYDAY PRACTICE",W/2,portrait?1758:1002,18,C.muted,4);
    }
    ctx.restore();subtitle(t);
    if(!cover&&t>=55.2){
      text("效果因人而异 · 持续困扰可寻求专业支持",W/2,portrait?1846:1041,portrait?22:18,"#a59b95",400);
    }
  }
  Shot.define({
    duration:cover?1:62,fps:30,cuts:cover?[]:textCuts,
    fonts:[["600 152px PingFang SC","先松一口气双吸长呼轻揉耳廓肩膀写下放下让目光休息只收拾一小块挑一个就好"],["500 20px Arial","A SMALL RESET"]],
    setup:async()=>{data=await (await fetch(edition.timeline || "../content/timeline.json")).json();captionCues=await (await fetch(edition.captions || "../content/captions.json")).json();},
    post:{motionBlur:12,maxMotionBlur:12,shutter:.32,grain:0},
    blurAt(t){if(cover||textCuts.some(c=>Math.abs(t-c)<.034))return 1;return data.stations.slice(1).some(s=>t>s.start-.55&&t<s.start+.55)?12:2;},
    meta:{title:"先松一口气",format:portrait?"9:16":"16:9",concept:"One continuous luminous mural, nine camera stations",version:edition.version || "v1"},
    render:frame
  });
})();
