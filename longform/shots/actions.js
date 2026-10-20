/* Longform tactile action studies. Deterministic Canvas2D geometry, no external assets.
 * Input: centered 1920 × 1080 logical canvas; subject extent x ±760, y ±350.
 * Public scenes: shake, paper, order. All motion is sampled directly at t.
 */
(function () {
  'use strict';
  const NS = window.LongScenes = window.LongScenes || {};
  const TAU = Math.PI * 2;
  const clamp = (v, lo=0, hi=1) => Math.max(lo, Math.min(hi,v));
  const mix = (a,b,v) => a+(b-a)*v;
  const smooth = v => { v=clamp(v); return v*v*(3-2*v); };
  const ease = v => { v=clamp(v); return v*v*v*(v*(v*6-15)+10); };
  const phase = (v,a,b) => smooth((v-a)/(b-a));
  const hash = n => { const v=Math.sin(n*127.1+311.7)*43758.5453; return v-Math.floor(v); };
  const rgba = (r,g,b,a=1) => `rgba(${Math.round(r)},${Math.round(g)},${Math.round(b)},${clamp(a)})`;
  const gold = a=>rgba(218,162,125,a), blue=a=>rgba(73,109,133,a);
  function poly(c,ps,fill,stroke,width=1){c.beginPath();ps.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));c.closePath();if(fill){c.fillStyle=fill;c.fill();}if(stroke){c.lineWidth=width;c.strokeStyle=stroke;c.stroke();}}
  function line(c,ps,stroke,width=1){c.beginPath();ps.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));c.strokeStyle=stroke;c.lineWidth=width;c.lineJoin='round';c.lineCap='round';c.stroke();}
  function ellipse(c,x,y,rx,ry,fill,stroke,width=1){c.beginPath();c.ellipse(x,y,Math.max(.01,rx),Math.max(.01,ry),0,0,TAU);if(fill){c.fillStyle=fill;c.fill();}if(stroke){c.strokeStyle=stroke;c.lineWidth=width;c.stroke();}}
  function glow(c,x,y,r,col,alpha=.15){const g=c.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,col(alpha));g.addColorStop(1,col(0));c.fillStyle=g;c.fillRect(x-r,y-r,r*2,r*2);}
  function radialShadow(c,x,y,rx,ry,a=.4){c.save();c.translate(x,y);c.scale(rx,ry);const g=c.createRadialGradient(0,0,.1,0,0,1);g.addColorStop(0,rgba(0,0,0,a));g.addColorStop(.55,rgba(0,0,0,a*.48));g.addColorStop(1,'rgba(0,0,0,0)');c.fillStyle=g;c.fillRect(-1,-1,2,2);c.restore();}
  function bezier(c,p,stroke,width){c.beginPath();c.moveTo(...p[0]);c.bezierCurveTo(...p[1],...p[2],...p[3]);c.strokeStyle=stroke;c.lineWidth=width;c.lineCap='round';c.stroke();}
  function tube(c,a,b,r1,r2,alpha=1){
    const dx=b[0]-a[0],dy=b[1]-a[1],l=Math.hypot(dx,dy),nx=-dy/l,ny=dx/l;
    const grad=c.createLinearGradient(a[0]-nx*r1,a[1]-ny*r1,a[0]+nx*r1,a[1]+ny*r1);
    grad.addColorStop(0,rgba(39,34,36,alpha));grad.addColorStop(.22,rgba(120,88,70,alpha));grad.addColorStop(.43,rgba(201,151,114,alpha));grad.addColorStop(.62,rgba(130,100,84,alpha));grad.addColorStop(1,rgba(29,31,40,alpha));
    c.beginPath();c.moveTo(a[0]+nx*r1,a[1]+ny*r1);c.bezierCurveTo(a[0]+dx*.35+nx*r1,a[1]+dy*.35+ny*r1,b[0]-dx*.2+nx*r2,b[1]-dy*.2+ny*r2,b[0]+nx*r2,b[1]+ny*r2);c.quadraticCurveTo(b[0]+dx*.1,b[1]+dy*.1,b[0]-nx*r2,b[1]-ny*r2);c.bezierCurveTo(b[0]-dx*.2-nx*r2,b[1]-dy*.2-ny*r2,a[0]+dx*.35-nx*r1,a[1]+dy*.35-ny*r1,a[0]-nx*r1,a[1]-ny*r1);c.closePath();c.fillStyle=grad;c.fill();c.strokeStyle=gold(.21*alpha);c.lineWidth=1;c.stroke();
    for(let j=0;j<10;j++){const q=(j/9-.5)*1.5;bezier(c,[[a[0]+nx*r1*q,a[1]+ny*r1*q],[a[0]+dx*.35+nx*r1*q,a[1]+dy*.35+ny*r1*q],[b[0]-dx*.25+nx*r2*q,b[1]-dy*.25+ny*r2*q],[b[0]+nx*r2*q,b[1]+ny*r2*q]],gold((j%3===0?.12:.05)*alpha),.7);}
  }
  function torsoPath(c,shoulderY,breath=0){
    c.beginPath();c.moveTo(-39,-174);c.bezierCurveTo(-45,-133,-78,shoulderY-20,-137,shoulderY);c.bezierCurveTo(-167,shoulderY+23,-170,35,-128,95);c.bezierCurveTo(-108,139,-113,192,-120,241);c.bezierCurveTo(-66,268,66,268,120,241);c.bezierCurveTo(113,192,108,139,128,95);c.bezierCurveTo(170,35,167,shoulderY+23,137,shoulderY);c.bezierCurveTo(78,shoulderY-20,45,-133,39,-174);c.closePath();
  }
  function hand(c,x,y,side,angle,alpha=1){c.save();c.translate(x,y);c.rotate(angle);const g=c.createLinearGradient(-20,0,20,0);g.addColorStop(0,rgba(63,53,49,alpha));g.addColorStop(.45,rgba(175,127,93,alpha));g.addColorStop(1,rgba(71,63,61,alpha));c.fillStyle=g;c.beginPath();c.moveTo(-12,-15);c.bezierCurveTo(-20,2,-18,37,-9,50);c.bezierCurveTo(-4,58,13,57,17,45);c.lineTo(20,18);c.bezierCurveTo(31,4,27,-2,21,2);c.lineTo(13,14);c.lineTo(11,-15);c.closePath();c.fill();c.strokeStyle=gold(.2);c.lineWidth=.7;c.stroke();for(let j=0;j<3;j++)bezier(c,[[-8+j*7,18],[-8+j*7,27],[-8+j*7,39],[-4+j*6,49]],gold(.16),.65);c.restore();}

  NS.shake = function(c,t,duration,env={}){
    const beat=Number.isFinite(env.beat)?env.beat:null, bp=clamp(env.beatProgress||0);
    const p=beat===null?clamp(t/duration):beat===0?mix(0,.64,bp):beat===1?mix(.64,.86,bp):mix(.86,1,bp);
    const begin=phase(p,.13,.26), settle=phase(p,.64,.82);
    const active=begin*(1-settle), tension=beat===2?Math.sin(bp*Math.PI)*.58:1-phase(p,.06,.30), breath=Math.sin(t*.72)*1.6;
    const wave=Math.sin(t*8.4)*active, wave2=Math.sin(t*8.4+1.9)*active;
    const shoulderY=-86-tension*31+breath, shoulderDX=wave*4;
    c.save();c.translate(0,19);glow(c,0,30,390,blue,.09);glow(c,-75,-80,270,gold,.06);
    // Dim, stable field: concentric contours become less compressed as the body settles.
    for(let j=0;j<5;j++){const r=244+j*29,alpha=.025+(1-settle)*.012;c.beginPath();c.ellipse(0,42,r*.77,r,0,-Math.PI*.91,Math.PI*.91);c.strokeStyle=gold(alpha);c.lineWidth=.8;c.stroke();}
    radialShadow(c,0,286,268,28,.52);
    // Three delayed silhouettes give elastic motion a finite return, without moving the head.
    for(let k=3;k>0;k--){const q=Math.sin(t*8.4-k*.6)*active;c.save();c.translate(q*(7+k*2),0);torsoPath(c,shoulderY);c.strokeStyle=blue(.025*active*(4-k));c.lineWidth=2;c.stroke();c.restore();}
    // Lateral arms are articulated at the shoulder and elbow. The neck remains stable.
    for(const side of [-1,1]){
      const shoulder=[side*(137+shoulderDX),shoulderY+16];
      const elbow=[side*(177+wave*6),83+wave2*5];
      const wrist=[side*(189+wave2*13),204+wave*5];
      tube(c,shoulder,elbow,31,21,.82);tube(c,elbow,wrist,20,12,.86);
      ellipse(c,elbow[0],elbow[1],18,17,rgba(82,66,58,.44),gold(.14),.6);
      hand(c,wrist[0],wrist[1]+11,side,side*(.07+wave*.065));
      // The ribbons remain attached: strain is a deformation, never released "substance".
      for(let j=0;j<5;j++){
        const x=side*(225+j*13),a=active*(1-j*.14),pts=[];
        for(let k=0;k<=32;k++){const yy=-69+k*9,off=Math.sin(k*.28-t*8.4+j*.4)*10*a;pts.push([x+off,yy]);}
        line(c,pts,gold(.07*a),1.1);
      }
    }
    // Translucent torso volume.
    const body=c.createLinearGradient(-165,-10,165,25);body.addColorStop(0,'#191b25');body.addColorStop(.17,'#514237');body.addColorStop(.42,'#7c5d48');body.addColorStop(.54,'#483d38');body.addColorStop(.76,'#635144');body.addColorStop(1,'#161b28');
    torsoPath(c,shoulderY);c.fillStyle=body;c.fill();c.strokeStyle=gold(.3);c.lineWidth=1;c.stroke();
    c.save();torsoPath(c,shoulderY);c.clip();
    const chestGlow=c.createRadialGradient(-42,-10,5,-42,-10,195);chestGlow.addColorStop(0,gold(.16));chestGlow.addColorStop(.7,gold(.015));chestGlow.addColorStop(1,blue(.06));c.fillStyle=chestGlow;c.fillRect(-200,-200,400,500);
    // Two pectoral fans, layered fiber direction and intercostal contours.
    for(const side of [-1,1]){
      for(let k=0;k<32;k++){
        const q=k/31,sx=side*(13+q*8),sy=-79+q*91;
        const ex=side*(135-q*19),ey=shoulderY+17+q*86;
        bezier(c,[[sx,sy],[side*49,-97+q*93],[side*(94+wave*1.5),ey-29],[ex,ey]],gold(.055+Math.sin(q*Math.PI)*.12),.65+(k%4===0?.6:0));
      }
      for(let k=0;k<12;k++){
        const y=43+k*13;
        bezier(c,[[side*8,y],[side*46,y+16],[side*92,y+17],[side*(121-k*1.7),y-3]],k%3===0?gold(.16):gold(.065),k%3===0?1.1:.7);
      }
      for(let k=0;k<15;k++){const xx=side*(38+k*5);bezier(c,[[side*(103+k),58],[xx,112],[xx*1.06,186],[side*(51+k*4.1),244]],blue(.08),.6);}
      // Collar bone and trapezius: lowering is visibly separate from shaking.
      bezier(c,[[side*4,-102],[side*35,-85],[side*66,shoulderY-3],[side*128,shoulderY+9]],gold(.52),2.2);
      bezier(c,[[side*22,-161],[side*31,-136],[side*70,shoulderY-4],[side*123,shoulderY+4]],gold(.15),7);
      for(let j=0;j<9;j++)bezier(c,[[side*(27+j),-156],[side*(38+j*2),-134],[side*(70+j*5),shoulderY],[side*(87+j*5),shoulderY+15]],gold(.15),.7);
    }
    // Sternum and central lower seam.
    bezier(c,[[0,-99],[5,-43],[-3,10],[0,56]],gold(.35),2);
    bezier(c,[[0,64],[-3,113],[2,193],[0,247]],gold(.10),1);
    for(let j=0;j<600;j++){const x=(hash(j*3)-.5)*300,y=hash(j*3+1)*440-180;ellipse(c,x,y,.32+hash(j*3+2)*.4,.35,gold(.035));}
    c.restore();
    // Neck, ears, and a sculpted anonymous head. No fast head rotation.
    tube(c,[0,-167],[0,-224],29,27,1);
    for(const side of [-1,1]){ellipse(c,side*49,-237,9,20,rgba(112,82,64,.9),gold(.18),.8);bezier(c,[[side*47,-249],[side*56,-249],[side*53,-229],[side*47,-232]],gold(.2),.9);}
    const hg=c.createLinearGradient(-57,-269,58,-212);hg.addColorStop(0,'#42362e');hg.addColorStop(.25,'#a27a5c');hg.addColorStop(.53,'#795c47');hg.addColorStop(.8,'#373237');hg.addColorStop(1,'#1a202d');
    c.beginPath();c.moveTo(0,-311);c.bezierCurveTo(-48,-314,-57,-279,-48,-233);c.bezierCurveTo(-45,-204,-21,-186,0,-184);c.bezierCurveTo(21,-186,45,-204,48,-233);c.bezierCurveTo(57,-279,48,-314,0,-311);c.closePath();c.fillStyle=hg;c.fill();c.strokeStyle=gold(.22);c.lineWidth=1;c.stroke();
    // Quiet facial planes catch light, but are deliberately not a portrait.
    bezier(c,[[-32,-262],[-20,-266],[-11,-263],[-6,-259]],gold(.21),1.3);bezier(c,[[6,-259],[15,-264],[26,-265],[34,-260]],gold(.12),1.2);
    bezier(c,[[1,-261],[-2,-247],[-7,-235],[3,-232]],gold(.17),1);bezier(c,[[-15,-218],[-5,-214],[7,-215],[17,-219]],gold(.13),1);
    bezier(c,[[-36,-244],[-41,-233],[-32,-217],[-23,-210]],gold(.13),1);
    // A pair of mechanically inspired strain traces become level and readable.
    for(const side of [-1,1]){
      const pts=[];for(let j=0;j<86;j++){const x=side*(329+j*2.1),y=64+Math.sin(j*.20-t*3.5)*Math.sin(j/85*Math.PI)*(32*tension+16*active);pts.push([x,y]);}
      line(c,pts,side<0?gold(.4):blue(.6),1.4);
      line(c,[[side*321,105],[side*519,105]],gold(.08),.8);
      for(let j=0;j<11;j++)line(c,[[side*(328+j*18),101],[side*(328+j*18),109]],gold(.13),.7);
      ellipse(c,side*324,64,3.2,3.2,gold(.7));
    }
    if(settle>0){glow(c,0,0,300,gold,.04*settle);const a=phase(p,.78,.9);line(c,[[-52,302],[52,302]],gold(.25*a),1);ellipse(c,0,302,2.3,2.3,gold(.65*a));}
    c.restore();
  };

  // Physically shaded paper mesh. Paper is a continuous sheet, including its ink.
  const PAPER_N=18;
  const paperRest=[];
  for(let j=0;j<=PAPER_N;j++)for(let i=0;i<=PAPER_N;i++){
    const u=i/PAPER_N*2-1,v=j/PAPER_N*2-1;
    const theta=(u+1)*Math.PI*1.08 + .14*Math.sin(v*7),phi=(v+1)*Math.PI*.48+.065;
    const radius=1+.19*Math.sin(i*2.31+j*1.91)+.055*Math.cos(i*7.1-j*3.2);
    paperRest.push({u,v,seed:hash(i*117+j*43),ball:[Math.sin(phi)*Math.cos(theta)*radius,Math.cos(phi)*radius,Math.sin(phi)*Math.sin(theta)*radius]});
  }
  const tris=[];
  for(let j=0;j<PAPER_N;j++)for(let i=0;i<PAPER_N;i++){
    const a=j*(PAPER_N+1)+i,b=a+1,d=a+PAPER_N+1,e=d+1;
    if((i+j)%2)tris.push([a,b,d],[b,e,d]);else tris.push([a,b,e],[a,e,d]);
  }
  function rot3(v,ax,ay,az){let[x,y,z]=v;let cy=Math.cos(ax),sy=Math.sin(ax),q=y*cy-z*sy;z=y*sy+z*cy;y=q;cy=Math.cos(ay);sy=Math.sin(ay);q=x*cy+z*sy;z=-x*sy+z*cy;x=q;cy=Math.cos(az);sy=Math.sin(az);q=x*cy-y*sy;y=x*sy+y*cy;x=q;return[x,y,z];}
  function cross(a,b){return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];}
  function norm(a){const l=Math.hypot(...a)||1;return a.map(v=>v/l);}
  function shadePaper(n,seed){const d=Math.abs(n[0]*-.36+n[1]*-.57+n[2]*.74),l=.44+d*.53,grain=(seed-.5)*10;return rgba(225*l+grain,208*l+grain,181*l+grain,1);}
  function paperBall(c,x,y,r=48,angle=.5,alpha=1){
    c.save();c.globalAlpha=alpha;
    const vs=paperRest.map(v=>rot3(v.ball,.3,angle,.1).map(q=>q*r));
    const faces=tris.map((ids,i)=>{const a=vs[ids[0]],b=vs[ids[1]],d=vs[ids[2]],n=norm(cross(b.map((v,k)=>v-a[k]),d.map((v,k)=>v-a[k])));return {ids,i,n,z:(a[2]+b[2]+d[2])/3};}).sort((a,b)=>b.z-a.z);
    for(const f of faces){const ps=f.ids.map(i=>[x+vs[i][0],y+vs[i][1]]),fill=shadePaper(f.n,paperRest[f.ids[0]].seed);poly(c,ps,fill,fill,.5);if(f.i%7===1)line(c,[ps[0].map((v,k)=>mix(v,ps[1][k],.22)),ps[0].map((v,k)=>mix(v,ps[2][k],.72))],rgba(52,47,44,.27),.65);if(f.i%5===0)line(c,[ps[0],ps[2]],rgba(255,235,197,.14),.5);}
    c.restore();
  }
  function basket(c,x,y,r=75){
    c.save();c.translate(x,y);radialShadow(c,0,99,r*1.4,28,.65);
    // Open wire wastebasket: rear half first; front ribs drawn after the paper.
    const g=c.createLinearGradient(-r,0,r,0);g.addColorStop(0,'#16191e');g.addColorStop(.42,'#3e3830');g.addColorStop(1,'#15171d');
    c.beginPath();c.moveTo(-r,-22);c.lineTo(-r*.73,99);c.quadraticCurveTo(0,126,r*.73,99);c.lineTo(r,-22);c.quadraticCurveTo(0,-1,-r,-22);c.fillStyle=g;c.fill();
    ellipse(c,0,-22,r,25,'#06080d',gold(.31),2);
    for(let k=0;k<13;k++){const a=Math.PI+(k/12)*Math.PI;const xx=Math.cos(a)*r,yy=-22+Math.sin(a)*25;line(c,[[xx,yy],[xx*.73,99+Math.sin(a)*18]],gold(.13),1);}
    for(let k=1;k<=4;k++){const yy=-22+k*25,rr=r*(1-k*.054);c.beginPath();c.ellipse(0,yy,rr,25-k*1.5,0,Math.PI,TAU);c.strokeStyle=gold(.12);c.lineWidth=.9;c.stroke();}
    c.restore();
  }
  function basketFront(c,x,y,r=75,opacity=1){c.save();c.globalAlpha=opacity;c.translate(x,y);for(let k=0;k<13;k++){const a=(k/12)*Math.PI;const xx=Math.cos(a)*r,yy=-22+Math.sin(a)*25;line(c,[[xx,yy],[xx*.73,99+Math.sin(a)*18]],gold(.31),1.15);}for(let k=1;k<=4;k++){const yy=-22+k*25,rr=r*(1-k*.054);c.beginPath();c.ellipse(0,yy,rr,25-k*1.5,0,0,Math.PI);c.strokeStyle=gold(.24);c.lineWidth=1;c.stroke();}c.beginPath();c.ellipse(0,-22,r,25,0,0,Math.PI);c.strokeStyle=gold(.5);c.lineWidth=2;c.stroke();c.restore();}

  function tearStudy(c,t,u){
    const tear=phase(u,.08,.70),open=phase(u,.13,.82),cutY=-157+tear*314;
    c.save();c.translate(-38,-18);glow(c,0,0,330,gold,.06);
    radialShadow(c,0,222,287,30,.4);
    // A sheet parts from top to bottom; the unbroken lower portion stays joined.
    for(const side of [-1,1]){
      c.save();
      const tp=(x,y)=>{const f=mix(1-smooth((y-cutY+18)/36),1,phase(tear,.95,1));return [x+side*open*68*f,y+(x/214)*open*7*f];};
      const ps=[tp(side*214,-157),tp(0,-157)];
      for(let j=0;j<=63;j++){const yy=-157+j*314/63,jag=2.6*Math.sin(j*3.2)+1.4*Math.sin(j*1.1),f=1-smooth((yy-cutY+12)/25);ps.push(tp(jag*f+side*(.65+hash(j+10)*2)*f,yy));}
      for(let j=0;j<=32;j++)ps.push(tp(side*214,157-j*314/32));
      const g=c.createLinearGradient(side*214,-150,-side*15,165);g.addColorStop(0,'#d1bea0');g.addColorStop(.35,'#c7b79b');g.addColorStop(.8,'#bca98d');g.addColorStop(1,'#9f8b74');poly(c,ps,g,rgba(239,214,177,.32),.8);
      c.save();c.beginPath();ps.forEach((q,i)=>i?c.lineTo(...q):c.moveTo(...q));c.closePath();c.clip();
      for(let j=0;j<420;j++){const xx=side*(hash(j*3)*213),yy=hash(j*3+1)*314-157;line(c,[tp(xx,yy),tp(xx+2+hash(j*3+2)*6,yy+.5)],rgba(70,57,45,.045),.45);}
      for(let j=0;j<10;j++){const yy=-107+j*24;const aa=side<0?-164:14,bb=side<0?-13:164;const pts=[];for(let k=0;k<20;k++)pts.push(tp(mix(aa,bb,k/19),yy+Math.sin(k*3.7+j)*1.4));line(c,pts,rgba(66,52,42,.30),1.05);}
      // The curved hinge is drawn across both halves just ahead of the tear.
      if(tear>.01&&tear<.99){const crease=[];for(let j=0;j<=30;j++){const x=side*j/30*214;crease.push(tp(x,cutY+12+Math.pow(j/30,.8)*17));}line(c,crease,rgba(245,219,176,.16),3);line(c,crease,rgba(58,43,32,.15),.8);}
      c.restore();
      // Cellulose filaments remain attached to the ragged cut edge.
      for(let j=0;j<95;j++){const yy=-157+j*3.3;if(yy>cutY)break;const jag=2.6*Math.sin(j*3.2*63/95)+1.4*Math.sin(j*1.1*63/95),len=2+hash(j*7+side)*5;bezier(c,[tp(jag,yy),tp(jag-side*len*.4,yy-1.5),tp(jag-side*len*.8,yy+1),tp(jag-side*len,yy-1)],rgba(241,226,198,.5),.55);}
      const edge=[];for(let j=0;j<=63;j++){const yy=-157+j*314/63;if(yy>cutY)break;edge.push(tp(2.6*Math.sin(j*3.2)+1.4*Math.sin(j*1.1),yy));}if(edge.length>1)line(c,edge,rgba(252,231,193,.55*open),1.15);
      c.restore();
    }
    // At the advancing tear, a few connecting fibers stretch before parting.
    if(tear>.02&&tear<.98){for(let j=0;j<9;j++){const yy=cutY-4+j*1.4;bezier(c,[[-open*21,yy],[0,yy-3],[open*8,yy+3],[open*21,yy]],rgba(226,210,179,.18*(1-tear)),.6);}}
    for(const side of [-1,1]){c.save();c.translate(side*(245+open*54),-77);c.rotate(side*-.10);for(let j=0;j<3;j++){c.beginPath();c.ellipse(0,j*18,13,23,0,side<0?-.8:Math.PI-.8,side<0?.8:Math.PI+.8);c.strokeStyle=gold(.13*(1-phase(u,.72,.92)));c.lineWidth=1.15;c.stroke();}c.restore();}
    line(c,[[-110,257],[110,257]],gold(.15),.8);ellipse(c,mix(-110,110,tear),257,2.5,2.5,gold(.6));
    c.restore();
  }
  function smallNote(c,x,y,a,alpha=1){
    c.save();c.globalAlpha=alpha;c.translate(x,y);c.rotate(a);radialShadow(c,13,124,130,18,.33);
    const g=c.createLinearGradient(-117,-130,117,130);g.addColorStop(0,'#d0bfa3');g.addColorStop(.58,'#bca88c');g.addColorStop(1,'#a58f72');poly(c,[[-117,-139],[117,-134],[112,141],[-113,139]],g,rgba(238,216,176,.28),.8);
    for(let j=0;j<150;j++){const xx=hash(j*3)*220-110,yy=hash(j*3+1)*268-134;line(c,[[xx,yy],[xx+hash(j*3+2)*5,yy+.4]],rgba(77,61,44,.07),.5);}
    line(c,[[-79,-101],[-20,-101]],rgba(91,59,40,.5),2.4);
    for(let j=0;j<10;j++){const pts=[];for(let k=0;k<18;k++)pts.push([-79+k*(8.2-hash(j+2)*1.2),-74+j*18+Math.sin(k*3.8+j)*1.3]);line(c,pts,rgba(57,48,41,.4),.9);}
    c.restore();
  }
  function paperEvidence(c,t,u){
    c.save();glow(c,0,30,480,gold,.035);
    // Reuse the physical objects as experimental conditions, avoiding a chart of invented amounts.
    smallNote(c,-259,-4,-.055,1);
    basket(c,290,66,86);paperBall(c,290,87,43,.6);basketFront(c,290,66,86);
    const link=phase(u,.12,.30);c.save();c.globalAlpha=link;
    // Branches identify actions only. There is intentionally no outcome magnitude or biomarker scale.
    line(c,[[0,-221],[0,-186],[-250,-186],[-250,-162]],gold(.23),1);line(c,[[0,-186],[290,-186],[290,-151]],blue(.35),1);
    ellipse(c,0,-221,4,4,gold(.8));ellipse(c,-250,-162,2.5,2.5,gold(.5));ellipse(c,290,-151,2.5,2.5,blue(.8));
    c.fillStyle=gold(.63);c.font='500 18px Arial, sans-serif';c.textAlign='center';c.fillText('2024',0,-246);
    c.font='500 20px "PingFang SC", sans-serif';c.fillStyle=rgba(195,179,158,.7);c.fillText('保留纸张',-259,201);c.fillText('写下后丢弃',290,201);
    c.font='15px "PingFang SC", sans-serif';c.fillStyle=rgba(151,145,140,.54);c.fillText('实验比较的是愤怒感，不是破坏力度',0,269);
    c.restore();c.restore();
  }

  NS.paper = function(c,t,duration,env={}){
    const beat=Number.isFinite(env.beat)?env.beat:null,bp=clamp(env.beatProgress||0);
    if(beat===1){tearStudy(c,t,bp);return;}
    if(beat===2){paperEvidence(c,t,bp);return;}
    const p=beat===null?clamp(t/duration):beat===0?mix(0,.95,bp):mix(.95,1,bp),fold=phase(p,.27,.58),ball=phase(p,.44,.62),toss=phase(p,.72,.88),land=phase(p,.88,.94);
    const lift=Math.sin(Math.min(1,phase(p,.13,.64))*Math.PI)*51;
    const x=mix(-63,409,toss),y=mix(-27,158,toss)-Math.sin(toss*Math.PI)*221+land*48;
    const scale=mix(1,.88,toss),az=mix(-.075,1.9,toss)+fold*.16,ay=.08+fold*.44+toss*2.2,ax=.48*(1-fold)+fold*.22+toss*.7;
    c.save();glow(c,-74,25,425,gold,.055);glow(c,425,154,190,blue,.05);
    // A desk edge and faint tactile work plane anchor the manipulation.
    const desk=c.createLinearGradient(0,153,0,270);desk.addColorStop(0,rgba(78,59,46,.12));desk.addColorStop(1,rgba(26,26,33,0));
    poly(c,[[-680,154],[309,154],[359,241],[-724,241]],desk);line(c,[[-680,154],[309,154],[359,241]],gold(.1),1);
    for(let j=0;j<14;j++)line(c,[[-664,166+j*4],[310+j*1.7,166+j*4]],gold(.015),.6);
    basket(c,410,154,75);
    radialShadow(c,mix(-65,409,toss),174,180*(1-fold)+80,24, .25+.27*fold);
    // Short motion arcs disclose the path, then disappear into stillness.
    if(toss>.01 && toss<.98){for(let k=0;k<3;k++){const pts=[];for(let j=0;j<=22;j++){const v=clamp(toss-j*.007-k*.015);pts.push([mix(-63,409,v),mix(-27,158,v)-Math.sin(v*Math.PI)*221+16+k*4]);}line(c,pts,gold(.05*(1-toss)),1.2-k*.2);}}
    const verts=paperRest.map((r,i)=>{
      const spread=1-fold*.74;
      let xx=r.u*214*spread,yy=r.v*153*spread;
      const bend=Math.pow(Math.abs(r.u),2)*(16+fold*42)+Math.pow(Math.abs(r.v),2)*fold*48;
      let zz=Math.sin(r.u*7.5+r.v*4.5)*fold*35+Math.sin(r.v*13-r.u*2)*fold*22+bend;
      xx+=Math.sin(r.v*10)*fold*19;yy+=Math.sin(r.u*11)*fold*15;
      const k=phase(fold,.36,1);xx=mix(xx,r.ball[0]*70,k);yy=mix(yy,r.ball[1]*70,k);zz=mix(zz,r.ball[2]*70,k);
      const vv=rot3([xx,yy,zz],ax,ay,az),z=vv[2],f=1100/(1100+z);
      return {v:vv,p:[x+vv[0]*scale*f,y-lift*(1-toss)+vv[1]*scale*f],seed:r.seed};
    });
    const mesh=tris.map((ids,i)=>{const a=verts[ids[0]],b=verts[ids[1]],d=verts[ids[2]],n=norm(cross(b.v.map((v,j)=>v-a.v[j]),d.v.map((v,j)=>v-a.v[j])));return {ids,n,z:(a.v[2]+b.v[2]+d.v[2])/3,i};}).sort((a,b)=>b.z-a.z);
    // Continuous, double-sided triangular sheet. Facet changes are geometry-based lighting.
    c.save();if(land>0){c.beginPath();c.rect(-800,-400,1600,400+154-22+land*28);c.clip();}
    for(const tr of mesh){const ps=tr.ids.map(i=>verts[i].p),sd=mix(.5,paperRest[tr.ids[0]].seed,fold),fill=shadePaper(tr.n,sd);poly(c,ps,fill,fill,.65);
      const edgeAlpha=(.16*fold)*(tr.i%7===0?1:.35);
      line(c,[ps[0],ps[1],ps[2]],rgba(67,48,34,edgeAlpha),.55);
      // A warm and a cool micro-edge describe actual crease ridges.
      if(tr.i%5===0 && fold>.1)line(c,[ps[0],ps[2]],rgba(255,235,197,.24*fold),.65);
      if(fold>.5&&tr.i%7===1){const aa=ps[0].map((v,k)=>mix(v,ps[1][k],.22)),bb=ps[0].map((v,k)=>mix(v,ps[2][k],.72));line(c,[aa,bb],rgba(52,47,44,.25*fold),.85);} 
    }
    // Ink is sampled in the original page coordinate grid and deforms with it.
    function sample(u,v){const ii=clamp((u+1)/2)*PAPER_N,jj=clamp((v+1)/2)*PAPER_N,i=Math.min(PAPER_N-1,Math.floor(ii)),j=Math.min(PAPER_N-1,Math.floor(jj)),a=ii-i,b=jj-j,vs=[verts[j*(PAPER_N+1)+i],verts[j*(PAPER_N+1)+i+1],verts[(j+1)*(PAPER_N+1)+i],verts[(j+1)*(PAPER_N+1)+i+1]];return [0,1].map(k=>mix(mix(vs[0].p[k],vs[1].p[k],a),mix(vs[2].p[k],vs[3].p[k],a),b));}
    if(fold<.7){c.globalAlpha=(1-phase(fold,.3,.7));for(let row=0;row<10;row++){const v=-.67+row*.135;const end=.56-hash(row+15)*.26,pts=[],write=clamp(phase(p,.015,.24)*10-row);for(let k=0;k<29;k++)pts.push(sample(mix(-.68,end,k/28*write),v+.007*Math.sin(k*2.8+row)));if(write>0)line(c,pts,rgba(68,59,53,.5),row===0?2:1.1);}const mark=[sample(-.71,-.82),sample(-.41,-.82)];line(c,mark,'rgba(94,62,42,.55)',3);c.globalAlpha=1;}
    c.restore();
    // Fine finger-like pressure arcs communicate a hand action without a literal cartoon hand.
    const grip=phase(p,.18,.28)*(1-phase(p,.55,.64));
    if(grip>0){for(const side of [-1,1])for(let j=0;j<3;j++){const xx=side*(225-fold*134)-63,yy=-45+j*29;c.beginPath();c.ellipse(xx,yy,22,28,side*.2,side<0?-.8:Math.PI-.8,side<0?.8:Math.PI+.8);c.strokeStyle=gold(.17*grip);c.lineWidth=1.4;c.stroke();}}
    basketFront(c,410,154,75);
    // Tiny discarded sheet glints remain inside the basket after landing.
    if(land>.7){paperBall(c,410,184,34,.7,phase(land,.7,1));basketFront(c,410,154,75,.75);}
    // A very low-contrast starting boundary; completion extinguishes the active field.
    if(p<.7){line(c,[[-318,231],[-318,243],[-306,243]],gold(.18*(1-ball)),1);line(c,[[184,231],[184,243],[172,243]],gold(.18*(1-ball)),1);}
    c.restore();
  };

  // Desk coordinates: x left/right, z front/back, y height above the desk.
  function deskProject(x,y,z){const f=1120/(1120-z*.25);return[x*f,78+z*.51-y*f];}
  function transform(v,obj){const a=obj.a||0,ca=Math.cos(a),sa=Math.sin(a);return[obj.x+v[0]*ca-v[2]*sa,(obj.y||0)+v[1],obj.z+v[0]*sa+v[2]*ca];}
  function dp(v,obj){return deskProject(...transform(v,obj));}
  function slab(c,obj,w,d,h,colors){const v=[[-w/2,0,-d/2],[w/2,0,-d/2],[w/2,0,d/2],[-w/2,0,d/2],[-w/2,h,-d/2],[w/2,h,-d/2],[w/2,h,d/2],[-w/2,h,d/2]].map(q=>dp(q,obj));poly(c,[v[0],v[3],v[7],v[4]],colors[1]);poly(c,[v[3],v[2],v[6],v[7]],colors[2]);poly(c,[v[2],v[1],v[5],v[6]],colors[1]);poly(c,[v[4],v[5],v[6],v[7]],colors[0],colors[3]||gold(.08),.7);return v;}
  function itemShadow(c,obj,w,d,alpha=.45){const p=deskProject(obj.x,0,obj.z);radialShadow(c,p[0]+9,p[1]+8,w*.63+(obj.y||0)*.22,d*.31+(obj.y||0)*.12,alpha/(1+(obj.y||0)*.018));}
  function paperPile(c,obj){itemShadow(c,obj,181,127,.38);for(let k=0;k<4;k++){const q={...obj,x:obj.x+(3-k)*2.5,z:obj.z+(3-k)*1.1,y:(obj.y||0)+k*1.7,a:obj.a+(3-k)*.017};slab(c,q,177,121,1.2,['#bdb09a','#695d4e','#968974',gold(.13)]);if(k===3){for(let j=0;j<7;j++){const z=-36+j*11;line(c,[dp([-65,1.5,z],q),dp([58-hash(j+7)*34,1.5,z],q)],rgba(65,62,58,.34),1);}line(c,[dp([-65,1.5,-48],q),dp([-14,1.5,-48],q)],rgba(97,67,46,.56),2.3);}}
  }
  function book(c,obj,kind=0){const w=kind?151:185,d=kind?199:211,h=kind?13:26;itemShadow(c,obj,w,d,.5);slab(c,obj,w+4,d+3,3,kind?['#3c4b51','#263037','#1d242b']:['#875c41','#4d3527','#5c3f2d']);const pages={...obj,y:(obj.y||0)+3};slab(c,pages,w-3,d-5,h-5,['#bcb09b','#8b816e','#9e927d']);for(let j=0;j<7;j++){const yy=4+j*(h-5)/7;line(c,[dp([-w/2,yy,d/2-3],obj),dp([w/2,yy,d/2-3],obj)],rgba(36,32,31,.25),.55);}const cover={...obj,y:(obj.y||0)+h-2};slab(c,cover,w+5,d+4,3,kind?['#3d5360','#243640','#2b3b44']:['#a27452','#65462f','#6f4c33']);const top= {...obj,y:(obj.y||0)+h+1};
    for(let k=0;k<70;k++){const x=(hash(k*3+5)-.5)*(w-10),z=(hash(k*3+6)-.5)*(d-10);const p=dp([x,.1,z],top);ellipse(c,p[0],p[1],.5,.25,rgba(255,218,164,.09));}
    line(c,[dp([-w/2+13,1,-d/2+2],top),dp([-w/2+13,1,d/2-2],top)],rgba(26,28,31,.3),1.4);
    // Blind-debossed publishing marks and delicate cover rule.
    line(c,[dp([-w*.25,1,-43],top),dp([w*.27,1,-43],top)],gold(kind?.35:.45),2);
    line(c,[dp([-w*.15,1,-31],top),dp([w*.17,1,-31],top)],gold(kind?.25:.35),1);
    const circle=[];for(let k=0;k<=40;k++){const a=k/40*TAU;circle.push(dp([Math.cos(a)*22,1,Math.sin(a)*22+23],top));}line(c,circle,gold(.26),1);
    line(c,[dp([0,1,0],top),dp([0,1,47],top)],gold(.2),.8);
    // Ribbon has a soft fold, rather than being flush with the page block.
    poly(c,[dp([32,h+1,d/2-6],obj),dp([45,h+1,d/2-6],obj),dp([45,2,d/2+19],obj),dp([38,2,d/2+15],obj),dp([32,2,d/2+20],obj)],kind?'#917052':'#495c67');
  }
  function cup(c,obj){itemShadow(c,obj,87,86,.5);const center=dp([0,0,0],obj),top=dp([0,100,0],obj),rx=40,ry=20;const g=c.createLinearGradient(center[0]-rx,0,center[0]+rx,0);g.addColorStop(0,'#33434e');g.addColorStop(.2,'#6e7e82');g.addColorStop(.43,'#8b9693');g.addColorStop(.76,'#465963');g.addColorStop(1,'#263540');
    // Porcelain handle behind the vessel, with its own rim reflection.
    c.beginPath();c.ellipse(center[0]+46,top[1]+43,26,35,-.08,-1.7,1.7);c.strokeStyle='#576970';c.lineWidth=9;c.stroke();c.strokeStyle=rgba(186,184,166,.2);c.lineWidth=2;c.stroke();
    c.beginPath();c.moveTo(top[0]-rx,top[1]);c.bezierCurveTo(top[0]-rx+2,top[1]+49,center[0]-rx+6,center[1],center[0]-rx+9,center[1]);c.ellipse(center[0],center[1],rx-9,14,0,Math.PI,0,true);c.bezierCurveTo(center[0]+rx-6,center[1]-1,top[0]+rx-2,top[1]+49,top[0]+rx,top[1]);c.closePath();c.fillStyle=g;c.fill();ellipse(c,top[0],top[1],rx,ry,'#9eaaa4',rgba(201,197,176,.55),1);ellipse(c,top[0],top[1]+1,rx-5,ry-4,'#242724');ellipse(c,top[0],top[1]+5,rx-8,ry-8,'#47362b');c.beginPath();c.ellipse(top[0],top[1]+5,rx-9,ry-9,0,3.45,5.85);c.strokeStyle=gold(.26);c.lineWidth=1;c.stroke();
    bezier(c,[[center[0]-23,top[1]+19],[center[0]-25,top[1]+42],[center[0]-23,center[1]-12],[center[0]-18,center[1]-5]],rgba(221,215,190,.2),2.3);
    ellipse(c,center[0],center[1]+1,rx-8,12,null,rgba(190,193,178,.17),1);
  }
  function pen(c,obj,kind=0){const len=kind?145:166;itemShadow(c,obj,len,10,.4);const a=dp([-len/2,5,0],obj),b=dp([len/2-16,5,0],obj),tip=dp([len/2,5,0],obj);line(c,[a,b],kind?'#a87c52':'#344f60',7);line(c,[[a[0],a[1]-1.2],[b[0],b[1]-1.2]],kind?'#d6b082':'#78929d',1.5);line(c,[b,tip],'#aeaa99',4);line(c,[[tip[0]-2,tip[1]],tip],'#181f28',1.7);const cap=dp([-len/2+28,6,0],obj);line(c,[a,cap],kind?'#684e38':'#203b4b',8);line(c,[dp([-len/2+5,8,-2],obj),dp([-len/2+26,8,-2],obj)],gold(.5),1.4);}
  function cable(c,obj,tidy){itemShadow(c,obj,180,83,.18);const pts=[];for(let k=0;k<=160;k++){const a=k/160*TAU*2.5;const xx=mix(Math.sin(a*.65)*95+Math.sin(a*2.1)*21,Math.cos(a)*57,tidy),zz=mix(Math.cos(a)*33+Math.sin(a*1.4)*31,Math.sin(a)*28,tidy);pts.push(dp([xx,3,zz],obj));}line(c,pts,'#111925',5.4);line(c,pts,'#4e5d63',2.8);line(c,pts,rgba(190,189,167,.22),.7);for(const end of [pts[0],pts[pts.length-1]]){c.save();c.translate(...end);c.rotate(obj.a);c.fillStyle='#909894';c.fillRect(-9,-3,18,6);c.fillStyle='#2b3843';c.fillRect(-13,-5,12,10);c.restore();}if(tidy>.7){const a=dp([0,5,-30],obj),b=dp([0,5,30],obj);line(c,[a,b],'#99734f',8);line(c,[a,b],gold(.5),1.4);}}
  function tray(c,obj){itemShadow(c,obj,187,100,.25);slab(c,obj,187,103,6,['#252d33','#121923','#1b232c']);for(const q of [{x:-92,z:0,w:4,d:103},{x:92,z:0,w:4,d:103},{x:0,z:-49,w:187,d:4},{x:0,z:49,w:187,d:4}]){const cc=transform([q.x,0,q.z],obj);slab(c,{x:cc[0],z:cc[2],y:cc[1],a:obj.a},q.w,q.d,18,['#596066','#2c363f','#3b454d',gold(.09)]);}}
  function moveObj(start,end,p,index){const a=.19+index*.077,b=a+.116,v=ease((p-a)/(b-a));return {x:mix(start.x,end.x,v),z:mix(start.z,end.z,v),a:mix(start.a,end.a,v),y:Math.sin(v*Math.PI)*(index===4?34:19),v};}
  NS.order = function(c,t,duration,env={}){
    const beat=Number.isFinite(env.beat)?env.beat:null,bp=clamp(env.beatProgress||0);
    const p=beat===null?clamp(t/duration):beat===0?mix(0,.60,bp):beat===1?mix(.60,.96,bp):mix(.96,1,bp),warm=phase(p,.68,.94);
    c.save();c.translate(0,-19);glow(c,0,45,610,gold,.035+warm*.025);
    // The rest of the room is deliberately below the contrast of the selected square.
    line(c,[[-755,-231],[-544,-138],[546,-138],[755,-231]],rgba(79,85,100,.08),1);
    line(c,[[-624,220],[-689,350]],rgba(78,79,87,.10),13);line(c,[[592,218],[650,350]],rgba(78,79,87,.09),13);
    radialShadow(c,0,308,660,48,.5);
    const corners=[deskProject(-608,0,-295),deskProject(608,0,-295),deskProject(608,0,295),deskProject(-608,0,295)];
    const board=c.createLinearGradient(-400,-80,400,250);board.addColorStop(0,'#241e1e');board.addColorStop(.32,'#453327');board.addColorStop(.65,'#372a24');board.addColorStop(1,'#1f1d22');
    const front=[corners[3],corners[2],[corners[2][0],corners[2][1]+18],[corners[3][0],corners[3][1]+18]];
    poly(c,front,'#1d1b20',gold(.08),.7);poly(c,corners,board,gold(.19),1);
    c.save();c.beginPath();corners.forEach((q,i)=>i?c.lineTo(...q):c.moveTo(...q));c.closePath();c.clip();
    // Open grain from many tapered fibers, no repeating image texture.
    for(let k=0;k<210;k++){const z=-295+k*2.85,pts=[];for(let j=0;j<=24;j++){const x=-615+j*52;pts.push(deskProject(x,0,z+Math.sin(j*.18+k*.13)*2.2+Math.sin(j*.6+k*.22)*.7));}line(c,pts,rgba(157,113,77,.018+hash(k+1)*.03),.45+hash(k+100)*.65);}
    for(let k=0;k<11;k++){const pts=[];for(let j=0;j<72;j++){const a=j/71*TAU;pts.push(deskProject(-450+Math.cos(a)*(44+k*8),.1,70+Math.sin(a)*(7+k*2)));}line(c,pts,gold(.025),.6);}
    // Warm boundary is a reflected pool of task-light, not a UI selection box.
    const light=c.createRadialGradient(-90,25,50,-90,25,610);light.addColorStop(0,gold(.04+warm*.05));light.addColorStop(.7,gold(.018));light.addColorStop(1,gold(0));c.fillStyle=light;c.fillRect(-740,-100,1480,400);
    const ring=[];for(let j=0;j<=120;j++){const a=j/120*TAU;ring.push(deskProject(Math.cos(a)*518,0,Math.sin(a)*246));}c.save();c.shadowColor=gold(.2);c.shadowBlur=17;line(c,ring,gold(.12+warm*.17),1.2);c.restore();
    c.restore();
    const specs=[
      {kind:'book',s:{x:-244,z:54,a:-.35},e:{x:-325,z:-101,a:.025}},
      {kind:'paper',s:{x:104,z:-118,a:.37},e:{x:-325,z:100,a:.025}},
      {kind:'notebook',s:{x:-26,z:149,a:-.42},e:{x:-325,z:-101,a:.025}},
      {kind:'cable',s:{x:-386,z:153,a:.31},e:{x:331,z:-147,a:0}},
      {kind:'cup',s:{x:159,z:62,a:0},e:{x:378,z:85,a:0}},
      {kind:'pen',s:{x:-34,z:-93,a:-.74},e:{x:102,z:-168,a:.02}},
      {kind:'pencil',s:{x:317,z:174,a:1.94},e:{x:102,z:-143,a:.02}}
    ];
    // The stationery tray is stationary; only chosen objects are moved into it.
    tray(c,{x:100,z:-158,a:.02,y:0});
    const items=specs.map((s,i)=>{const o=moveObj(s.s,s.e,p,i);if(s.kind==='notebook')o.y+=26*o.v;return{...s,o};}).sort((a,b)=>a.o.z-b.o.z || (a.o.y-b.o.y));
    for(const it of items){const o=it.o;if(it.kind==='book')book(c,o,0);else if(it.kind==='notebook')book(c,o,1);else if(it.kind==='paper')paperPile(c,o);else if(it.kind==='cup')cup(c,o);else if(it.kind==='cable')cable(c,o,o.v);else pen(c,o,it.kind==='pencil'?1:0);}
    // The clear center is a positive outcome: a usable working surface, not an empty grid.
    const done=phase(p,.83,.96);if(done>0){const pp=deskProject(42,0,47);glow(c,pp[0],pp[1],150,gold,.035*done);const a=deskProject(-58,.5,47),b=deskProject(100,.5,47);line(c,[a,b],gold(.15*done),.8);ellipse(c,(a[0]+b[0])/2,(a[1]+b[1])/2,2,1,gold(.4*done));}
    c.restore();
  };
})();
