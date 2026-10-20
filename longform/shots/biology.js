/* Procedural biological plates: volumetric tissue, deterministic geometry.
 * The main renderer owns the background, chapter typography and subtitles.
 * Each plate is built once at high resolution, then animated in local space.
 */
(() => {
  'use strict';
  const PI = Math.PI, TAU = PI * 2;
  const P = { gold: '#daa27d', warm: '#ac7859', pale: '#efc8aa', blue: '#496d85', ice: '#8cabb8', ink: '#06060e' };
  const cache = new Map();
  const clamp = (v, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
  const lerp = (a, b, p) => a + (b - a) * p;
  const smooth = v => { v = clamp(v); return v * v * (3 - 2 * v); };
  const ramp = (t, a, b) => smooth((t - a) / (b - a));
  const rand = n => { const v = Math.sin(n * 127.1 + 311.7) * 43758.5453123; return v - Math.floor(v); };
  const rgba = (rgb, a) => `rgba(${rgb},${a})`;
  function stroke(c, fn, color = P.gold, width = 2, alpha = 1) {
    c.save(); c.globalAlpha *= alpha; c.lineWidth = width; c.lineCap = 'round'; c.lineJoin = 'round'; c.strokeStyle = color;
    c.beginPath(); fn(c); c.stroke(); c.restore();
  }
  function fill(c, fn, color, alpha = 1) {
    c.save(); c.globalAlpha *= alpha; c.fillStyle = color; c.beginPath(); fn(c); c.fill(); c.restore();
  }
  function disc(c, x, y, r, color, alpha = 1) { fill(c, q => q.arc(x, y, r, 0, TAU), color, alpha); }
  function glow(c, x, y, r, rgb = '218,162,125', a = .12) {
    const g = c.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, rgba(rgb, a)); g.addColorStop(.38, rgba(rgb, a * .35)); g.addColorStop(1, rgba(rgb, 0));
    c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2);
  }
  function plate(name, w, h, draw, scale = 1.8) {
    if (!cache.has(name)) {
      const canvas = typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(Math.ceil(w * scale), Math.ceil(h * scale)) : document.createElement('canvas');
      canvas.width = Math.ceil(w * scale); canvas.height = Math.ceil(h * scale);
      const c = canvas.getContext('2d'); c.scale(scale, scale); c.translate(w / 2, h / 2); draw(c);
      cache.set(name, { canvas, w, h });
    }
    return cache.get(name);
  }
  function image(c, p, alpha = 1) { c.save(); c.globalAlpha *= alpha; c.drawImage(p.canvas, -p.w / 2, -p.h / 2, p.w, p.h); c.restore(); }
  function beatState(t, duration, env, count) {
    const fallback = t / Math.max(1, duration) * count;
    return { index: Number.isFinite(env?.beat) ? env.beat : Math.min(count - 1, Math.floor(fallback)),
      progress: Number.isFinite(env?.beatProgress) ? clamp(env.beatProgress) : fallback % 1,
      time: Number.isFinite(env?.beatT) ? env.beatT : t % (duration / count) };
  }
  function curvePoint(a, b, c, d, u) {
    const v = 1 - u; return { x: v*v*v*a.x+3*v*v*u*b.x+3*v*u*u*c.x+u*u*u*d.x, y: v*v*v*a.y+3*v*v*u*b.y+3*v*u*u*c.y+u*u*u*d.y };
  }
  function along(points, u) {
    const q = clamp(u, 0, .999999) * (points.length - 1), i = Math.floor(q), f = q - i;
    return { x: lerp(points[i].x, points[i + 1].x, f), y: lerp(points[i].y, points[i + 1].y, f) };
  }
  function luminous(c, x, y, r, rgb = '218,162,125', alpha = 1) {
    disc(c, x, y, r * 3.5, rgba(rgb, .035 * alpha));
    disc(c, x, y, r * 1.8, rgba(rgb, .12 * alpha));
    disc(c, x, y, r, rgba(rgb, .86 * alpha));
  }

  // A cached height-field cortex. Domain-warped sulci are shaded by their
  // actual local normals, giving gyri real relief instead of outlined icons.
  function cortexPlate() {
    return plate('cortex', 780, 620, c => {
      const w = 1050, h = 820, sc = 1.5;
      const pix = new OffscreenCanvas(w, h), pc = pix.getContext('2d'), im = pc.createImageData(w, h);
      function field(x, y) {
        const wx = x + 14 * Math.sin(y * .031) + 8 * Math.sin(x * .016 + y * .067);
        const wy = y + 13 * Math.sin(x * .024) - 9 * Math.cos(y * .039);
        const f = .75 * Math.sin(wx * .113 + 1.55 * Math.sin(wy * .055)) + .72 * Math.sin(wy * .107 + 1.7 * Math.cos(wx * .061)) + .32 * Math.sin((wx + wy) * .087);
        return Math.exp(-f * f * 6.2);
      }
      for (let py = 0; py < h; py++) for (let px = 0; px < w; px++) {
        const x = (px - w / 2) / sc, y = (py - h / 2) / sc;
        const side = x < 0 ? -1 : 1, cx = side * 128;
        const xx = x - cx, yy = y + 12 + side * 5;
        const theta = Math.atan2(yy / 231, xx / 184);
        const edge = 1 + .025 * Math.sin(theta * 7) + .013 * Math.cos(theta * 11 + side);
        const q = xx * xx / (184 * 184) + yy * yy / (231 * 231);
        if (q >= edge * edge) continue;
        const depth = Math.sqrt(Math.max(.003, 1 - q / (edge * edge)));
        const valley = field(x, y), gx = (field(x + .7, y) - field(x - .7, y)) / 1.4, gy = (field(x, y + .7) - field(x, y - .7)) / 1.4;
        let nx = xx / (184 * 184) * 178 / depth + gx * 11, ny = yy / (231 * 231) * 178 / depth + gy * 11, nz = 1;
        const norm = Math.sqrt(nx*nx+ny*ny+nz*nz); nx /= norm; ny /= norm; nz /= norm;
        const diffuse = Math.max(0, nx * -.46 + ny * -.51 + nz * .72);
        const rim = Math.pow(1 - depth, 1.9) * .44;
        const fissure = 1 - .62 * Math.exp(-x*x / 58);
        const shade = (.29 + diffuse * .66) * (1 - valley * .46) * fissure;
        const grain = .97 + .06 * rand(px * 19 + py * 179);
        const cool = clamp((x + 70) / 420) * .3;
        const index = (py * w + px) * 4;
        im.data[index] = Math.min(255, (79 - cool * 13) * shade * grain + rim * 153);
        im.data[index+1] = Math.min(255, (85 + cool * 8) * shade * grain + rim * 98);
        im.data[index+2] = Math.min(255, (96 + cool * 15) * shade * grain + rim * 66);
        im.data[index+3] = Math.round(255 * clamp((edge*edge - q) * 65));
      }
      pc.putImageData(im, 0, 0);
      glow(c, -30, -15, 365, '172,120,89', .11);
      c.drawImage(pix, -w / sc / 2, -h / sc / 2, w / sc, h / sc);
      // Fine axonal-looking strands follow the local folds, at mixed scales.
      // These are a visual network metaphor, not a tractography reconstruction.
      for(let i=0;i<260;i++){
        let x=(rand(i*7+83)-.5)*585,y=(rand(i*7+84)-.5)*425;
        let vx=Math.cos(rand(i*7+85)*TAU),vy=Math.sin(rand(i*7+85)*TAU);
        const pts=[];
        for(let j=0;j<26+Math.floor(rand(i+781)*42);j++){
          const side=x<0?-1:1,q=(x-side*128)**2/(184*184)+(y+12+side*5)**2/(231*231);
          if(q>.93)break;
          pts.push({x,y});
          const dx=field(x+.7,y)-field(x-.7,y),dy=field(x,y+.7)-field(x,y-.7),len=Math.hypot(dx,dy)||1;
          let tx=-dy/len,ty=dx/len;if(tx*vx+ty*vy<0){tx=-tx;ty=-ty;}
          vx=vx*.58+tx*.42;vy=vy*.58+ty*.42;const vl=Math.hypot(vx,vy)||1;vx/=vl;vy/=vl;
          x+=vx*1.7;y+=vy*1.7;
        }
        if(pts.length>3)stroke(c,p=>{pts.forEach((v,j)=>j?p.lineTo(v.x,v.y):p.moveTo(v.x,v.y));},i%6===0?P.gold:P.ice,i%7===0?.9:.55,i%6===0?.21:.12);
      }
      // Central sulcus and basal connection remain understated.
      stroke(c, p => { p.moveTo(0, -215); p.bezierCurveTo(-11,-125,12,-42,-3,61); p.bezierCurveTo(-5,116,11,162,3,195); }, '#15131b', 5, .65);
      stroke(c, p => { p.moveTo(6,-208);p.bezierCurveTo(0,-122,15,-66,5,-14); }, P.pale, 1.2, .16);
      const stem = c.createLinearGradient(-25,190,32,284); stem.addColorStop(0,'rgba(139,102,79,.75)');stem.addColorStop(1,'rgba(58,58,69,0)');
      fill(c,p=>{p.moveTo(-32,176);p.bezierCurveTo(-28,214,-17,239,-7,275);p.lineTo(24,278);p.bezierCurveTo(13,230,40,202,31,179);p.closePath();},stem);
    }, 1.5);
  }

  function hook(c, t, duration, env) {
    const b = beatState(t, duration, env, 2), settle = b.index > 0 ? ramp(b.progress, 0, .7) : 0;
    c.save(); c.translate(0, -5);
    const breath = 1 + Math.sin(t * 1.12) * .006; c.scale(breath, breath);
    image(c, cortexPlate());
    // Nine cortical routes, not a field of decorative sparkles.
    for (let i = 0; i < 9; i++) {
      const s = i / 8, side = i % 2 ? 1 : -1;
      const a = {x: side * (228 - s * 28),y:-147+s*290};
      const d = {x:-side*(120+s*87),y:118-s*227};
      const bb = {x: lerp(-side*210, side*67, settle),y:lerp(-215+s*403,a.y-23,settle)};
      const cc = {x:lerp(side*277,-side*45,settle),y:lerp(224-s*397,d.y+23,settle)};
      stroke(c,p=>{p.moveTo(a.x,a.y);p.bezierCurveTo(bb.x,bb.y,cc.x,cc.y,d.x,d.y);},i%3===0?P.blue:P.warm,1.2,.19+settle*.12);
      const u = (t * lerp(.27,.09,settle) + i * .117) % 1, pt = curvePoint(a,bb,cc,d,u);
      luminous(c,pt.x,pt.y,2.3,i%3===0?'129,170,192':'239,184,143',.55);
    }
    // A fragmented perimeter becomes an unbroken, quiet halo.
    c.save(); c.scale(1,.87);
    for (let j = 0; j < 3; j++) {
      const a = -.8 + j * 2.08;
      stroke(c,p=>p.arc(0,0,353+j*6,a,a+lerp(.64,2.08,settle)),j===1?P.blue:P.gold,1.2,.16+settle*.15);
    }
    c.restore();
    c.restore();
  }

  function lungShape(c, side) {
    c.moveTo(side*31,-227);
    c.bezierCurveTo(side*82,-267,side*156,-254,side*211,-181);
    c.bezierCurveTo(side*259,-119,side*300,-7,side*306,126);
    c.bezierCurveTo(side*315,200,side*272,239,side*206,227);
    c.bezierCurveTo(side*137,216,side*73,199,side*32,182);
    if(side < 0) c.bezierCurveTo(-72,135,-73,77,-36,34);
    else c.bezierCurveTo(20,106,29,20,28,-55);
    c.bezierCurveTo(side*28,-122,side*31,-177,side*31,-227);c.closePath();
  }
  let bronchialCache;
  function bronchi() {
    if (bronchialCache) return bronchialCache;
    const edges = [], routes = [];
    function grow(x,y,angle,length,depth,seed,chain) {
      const ex=x+Math.sin(angle)*length, ey=y+Math.cos(angle)*length;
      const mid={x:lerp(x,ex,.46)+Math.cos(angle)*(rand(seed+81)-.5)*12,y:lerp(y,ey,.46)};
      const next=chain.concat([{x:mid.x,y:mid.y},{x:ex,y:ey}]);
      edges.push({x,y,ex,ey,mx:mid.x,my:mid.y,width:Math.max(.65,depth*1.65),depth,seed});
      if(depth<=1){routes.push(next);return;}
      grow(ex,ey,angle-.43-rand(seed+3)*.16,length*.73,depth-1,seed*2+11,next);
      grow(ex,ey,angle+.37+rand(seed+7)*.18,length*.73,depth-1,seed*2+19,next);
    }
    for(const side of [-1,1]) {
      const root=[{x:0,y:-320},{x:0,y:-239},{x:side*47,y:-169}];
      grow(side*47,-169,side*.37,97,6,side===1?17:41,root);
      grow(side*83,-136,side*1.03,64,4,side===1?133:199,root.concat([{x:side*83,y:-136}]));
    }
    bronchialCache={edges,routes}; return bronchialCache;
  }
  function lungPlate() {
    return plate('lungs', 760, 730, c=>{
      glow(c,0,5,345,'116,127,139',.07);
      for(const side of [-1,1]) {
        c.save(); c.beginPath();lungShape(c,side);c.clip();
        const g=c.createRadialGradient(side*108,-75,25,side*165,6,324);
        g.addColorStop(0,'rgba(138,113,97,.7)');g.addColorStop(.48,'rgba(98,91,90,.61)');g.addColorStop(.83,'rgba(52,66,79,.56)');g.addColorStop(1,'rgba(16,26,41,.23)');
        c.fillStyle=g;c.fillRect(-330,-290,660,570);
        // Pleural microstructure: irregular cells and grain, clipped to the volume.
        for(let iy=0;iy<24;iy++)for(let ix=0;ix<16;ix++){
          const seed=iy*31+ix+3, x=side*(24+ix*19+(iy%2)*8), y=-258+iy*23;
          stroke(c,p=>{
            for(let k=0;k<=6;k++){const a=k/6*TAU,r=10+rand(seed*11+k)*4,xx=x+Math.cos(a)*r,yy=y+Math.sin(a)*r;if(!k)p.moveTo(xx,yy);else p.lineTo(xx,yy);}
          },ix%3===0?P.pale:P.ice,.65,.045+rand(seed)*.05);
        }
        const {edges}=bronchi();
        for(const e of edges){
          if(Math.sign(e.x)!==side)continue;
          stroke(c,p=>{p.moveTo(e.x,e.y);p.quadraticCurveTo(e.mx,e.my,e.ex,e.ey);},'#101927',e.width+5,.45);
          stroke(c,p=>{p.moveTo(e.x,e.y);p.quadraticCurveTo(e.mx,e.my,e.ex,e.ey);},e.depth>3?'#c99c7b':'#b9977c',e.width,.35+e.depth*.055);
          stroke(c,p=>{p.moveTo(e.x-1,e.y);p.quadraticCurveTo(e.mx-1,e.my,e.ex-1,e.ey);},P.pale,Math.max(.4,e.width*.17),.28);
          if(e.depth===1)for(let k=0;k<5;k++){const a=k/5*TAU;disc(c,e.ex+Math.cos(a)*3.5,e.ey+Math.sin(a)*3.5,1.5,P.ice,.28);}
        }
        const rim=c.createLinearGradient(side*35,-240,side*305,180);rim.addColorStop(0,'rgba(238,202,173,.28)');rim.addColorStop(.5,'rgba(218,162,125,.02)');rim.addColorStop(1,'rgba(122,162,182,.2)');
        stroke(c,p=>lungShape(p,side),rim,9,.75);
        c.restore();
        stroke(c,p=>lungShape(p,side),side<0?P.gold:P.ice,1.6,.46);
        // Interlobar fissures are thin shadows following each organ's curved surface.
        stroke(c,p=>{p.moveTo(side*87,-60);p.bezierCurveTo(side*166,23,side*234,93,side*293,116);},'#0b1523',3,.48);
        stroke(c,p=>{p.moveTo(side*89,-63);p.bezierCurveTo(side*167,20,side*234,91,side*293,114);},P.ice,.7,.2);
      }
      // Tracheal cartilage and primary bronchi sit in front of translucent tissue.
      stroke(c,p=>{p.moveTo(0,-321);p.lineTo(0,-235);p.quadraticCurveTo(-4,-202,-47,-169);},'#403c40',26,.95);
      stroke(c,p=>{p.moveTo(0,-238);p.quadraticCurveTo(6,-201,47,-169);},'#655349',23,.95);
      stroke(c,p=>{p.moveTo(-5,-321);p.lineTo(-5,-237);p.quadraticCurveTo(-9,-203,-49,-170);},P.gold,3,.6);
      stroke(c,p=>{p.moveTo(2,-239);p.quadraticCurveTo(9,-204,47,-171);},P.pale,2,.4);
      for(let i=0;i<9;i++)stroke(c,p=>{p.moveTo(-12,-313+i*9);p.quadraticCurveTo(0,-307+i*9,12,-313+i*9);},P.pale,1.5,.38);
    });
  }
  const alveoli = Array.from({length:37},(_,i)=>{
    const a=i*2.39996323, z=1-2*(i+.5)/37, r=Math.sqrt(1-z*z);
    return {x:Math.cos(a)*r*155,y:Math.sin(a)*r*134,z:z*90,r:37+rand(i+500)*17,seed:i};
  }).sort((a,b)=>a.z-b.z);
  function drawAlveoli(c,t,open=1){
    glow(c,0,0,268,'142,119,98',.11);
    // Small bronchioles feed the cluster from the left.
    for(let j=0;j<4;j++){
      stroke(c,p=>{p.moveTo(-285,-34);p.bezierCurveTo(-208,-34,-208,-125+j*74,-100,-116+j*69);},'#352d2c',20-j*2,.95);
      stroke(c,p=>{p.moveTo(-285,-37);p.bezierCurveTo(-208,-37,-208,-128+j*74,-100,-119+j*69);},P.warm,7-j*.9,.62);
      stroke(c,p=>{p.moveTo(-285,-40);p.bezierCurveTo(-208,-40,-208,-131+j*74,-100,-122+j*69);},P.pale,1.5,.45);
    }
    for(const a of alveoli){
      const selected=a.seed%11===0;
      const expansion=selected?lerp(.55,1,open):1;
      const rad=a.r*expansion*(1+Math.sin(t*.72+a.seed*.18)*.014), xx=a.x, yy=a.y;
      const g=c.createRadialGradient(xx-rad*.36,yy-rad*.42,rad*.03,xx,yy,rad);
      g.addColorStop(0,'rgba(237,197,158,.48)');g.addColorStop(.3,'rgba(150,117,94,.48)');g.addColorStop(.74,'rgba(67,76,84,.64)');g.addColorStop(.94,'rgba(114,126,132,.51)');g.addColorStop(1,'rgba(208,170,135,.16)');
      disc(c,xx,yy,rad+3,'#10121c',.65);disc(c,xx,yy,rad,g);
      stroke(c,p=>p.arc(xx,yy,rad,-2.75,-.6),P.pale,1.8,.61);
      stroke(c,p=>p.arc(xx,yy,rad*.91,.3,2.15),P.blue,1.4,.7);
      // Capillary mesh follows the spherical wall; no quantification implied.
      c.save();c.beginPath();c.arc(xx,yy,rad*.94,0,TAU);c.clip();
      for(let k=0;k<4;k++){
        const angle=k*.81+a.seed*.3,off=(k-1.5)*rad*.28;
        stroke(c,p=>{
          p.moveTo(xx-rad,yy+off);
          p.bezierCurveTo(xx-rad*.4,yy+off+Math.sin(angle)*rad*.6,xx+rad*.4,yy+off-Math.cos(angle)*rad*.6,xx+rad,yy+off*.6);
        },k%2?P.warm:P.blue,.85,.34);
      }
      for(let k=0;k<5;k++){
        const off=(k-2)*rad*.28;
        stroke(c,p=>{p.moveTo(xx+off,yy-rad);p.bezierCurveTo(xx+off-rad*.31,yy-rad*.33,xx+off+rad*.28,yy+rad*.32,xx+off*.7,yy+rad);},k%2?P.blue:P.warm,.7,.42);
      }
      for(let k=0;k<13;k++){const an=rand(a.seed*97+k)*TAU,rr=Math.sqrt(rand(a.seed*71+k+900))*rad*.9;disc(c,xx+Math.cos(an)*rr,yy+Math.sin(an)*rr,.6,P.pale,.1);}
      c.restore();
    }
    for(let i=0;i<12;i++){
      const j=i%4,u=(t*.14+i*.079)%1;
      const q=curvePoint({x:-285,y:-37},{x:-208,y:-37},{x:-208,y:-128+j*74},{x:-100,y:-119+j*69},u);
      luminous(c,q.x,q.y,1.7,'232,187,147',.72);
    }
    // Balanced exchange, represented by opposing local motions rather than purging.
    for(let i=0;i<14;i++){
      const u=(t*.12+i/14)%1, side=i%2?1:-1;
      const x=lerp(-235,201,side>0?u:1-u), y=Math.sin(u*PI*2+i*.7)*30+(i-7)*18;
      luminous(c,x,y,1.5,i%2?'141,181,201':'226,177,137',.55);
    }
  }
  function airflow(c,t,mode,amplitude=1){
    const {routes}=bronchi();
    c.save();c.beginPath();lungShape(c,-1);lungShape(c,1);c.rect(-18,-332,36,120);c.clip();
    for(let i=0;i<40;i++){
      const route=routes[(i*7)%routes.length];let u=(t*(mode==='out'?.11:.15)+i*.071)%1;if(mode==='out')u=1-u;
      const q=along(route,u),q2=along(route,clamp(u+(mode==='out'?.017:-.017)));
      stroke(c,p=>{p.moveTo(q2.x,q2.y);p.lineTo(q.x,q.y);},mode==='out'?P.ice:P.pale,1.7,.32*amplitude);
      luminous(c,q.x,q.y,1.8,mode==='out'?'143,184,205':'238,193,152',.72*amplitude);
    }
    c.restore();
  }
  function breathingTrace(c,t,alpha=1){
    c.save();c.globalAlpha*=alpha;
    stroke(c,p=>{
      for(let i=0;i<=260;i++){
        const x=-280+i*2.15, a=i/260*TAU*2.2-t*.23;
        // Asymmetric rounded cycles show timing only; there are no axes or values.
        const y=Math.sin(a)*31+Math.sin(a*2+.7)*8;
        if(!i)p.moveTo(x,y);else p.lineTo(x,y);
      }
    },P.ice,2.3,.66);
    c.restore();
  }
  function breath(c,t,duration,env){
    const b=beatState(t,duration,env,6);
    let inflation=.2, mode='in';
    if(b.index===0){const p=b.progress;inflation=p<.4?.12:p<.86?lerp(.12,.77,smooth((p-.4)/.46)):lerp(.77,1,smooth((p-.86)/.14));}
    else if(b.index===1){inflation=lerp(1,.15,smooth(b.progress));mode='out';}
    else {inflation=.18+(.5+.5*Math.sin(t*.8))*.19;mode=Math.cos(t*.8)>0?'in':'out';}
    const detail=b.index===3?ramp(b.progress,0,.24):b.index===4?1:b.index===5?1-ramp(b.progress,0,.28):0;
    const proof=b.index>=5?ramp(b.progress,0,.22):0;
    c.save();c.translate(lerp(0,-366,detail)*(1-proof*.35),lerp(14,38,detail));
    const scale=lerp(.96,.57,detail)*(1-proof*.14);c.scale(scale*(1+inflation*.047),scale*(1+inflation*.02));
    image(c,lungPlate(),1-detail*.42);
    airflow(c,t,mode,1-detail*.6);
    c.restore();
    if(detail>0){c.save();c.globalAlpha*=detail;c.translate(258,-2);c.scale(.99,.99);drawAlveoli(c,t,b.index===3?ramp(b.progress,.3,.82):1);c.restore();}
    if(b.index===2){c.save();c.translate(0,305);breathingTrace(c,t,.23);c.restore();}
    if(proof>0){c.save();c.globalAlpha*=proof;c.translate(0,298);breathingTrace(c,t,.85);c.restore();}
    if(b.index===4){c.save();c.globalAlpha*=.4;c.translate(-347,264);c.scale(.54,.54);breathingTrace(c,t);c.restore();}
  }


  function headPath(c) {
    c.moveTo(-135,278);
    c.bezierCurveTo(-122,221,-138,172,-173,111);
    c.bezierCurveTo(-214,42,-230,-70,-200,-161);
    c.bezierCurveTo(-174,-251,-100,-298,-17,-292);
    c.bezierCurveTo(92,-286,151,-219,153,-146);
    c.bezierCurveTo(153,-102,167,-72,194,-44);
    c.quadraticCurveTo(228,-16,188,-9);c.lineTo(170,-9);
    c.quadraticCurveTo(166,11,176,28);c.quadraticCurveTo(187,42,168,49);
    c.bezierCurveTo(171,86,133,114,81,116);
    c.bezierCurveTo(55,153,60,215,79,278);c.closePath();
  }
  function headPlate(){
    return plate('head',530,640,c=>{
      c.save();c.beginPath();headPath(c);c.clip();
      // Continuous relief shading gives the forehead, cheekbone and neck
      // different surface normals, rather than one flat silhouette gradient.
      const sc=1.7,sw=902,sh=1088,surface=new OffscreenCanvas(sw,sh),gc=surface.getContext('2d'),pixels=gc.createImageData(sw,sh);
      function height(x,y){
        const q=((x+41)/226)**2+((y+74)/257)**2;
        const cranium=151*Math.sqrt(Math.max(0,1-q));
        const cheek=34*Math.exp(-(((x-70)/103)**2+((y-15)/91)**2));
        const brow=22*Math.exp(-(((x-108)/62)**2+((y+125)/86)**2));
        const nose=29*Math.exp(-(((x-175)/42)**2+((y+26)/52)**2));
        const neck=71*Math.sqrt(Math.max(0,1-((x+27)/114)**2));
        const skull=cranium+cheek+brow+nose,lower=neck*ramp(y,35,174);
        return (skull+lower+Math.sqrt((skull-lower)**2+18*18))/2;
      }
      for(let py=0;py<sh;py++)for(let px=0;px<sw;px++){
        const x=(px-sw/2)/sc,y=(py-sh/2)/sc,z=height(x,y);
        let nx=-(height(x+.6,y)-height(x-.6,y))/1.2,ny=-(height(x,y+.6)-height(x,y-.6))/1.2,nz=1;
        const norm=Math.hypot(nx,ny,nz);nx/=norm;ny/=norm;nz/=norm;
        const diffuse=Math.max(0,nx*-.5+ny*-.49+nz*.72),spec=Math.pow(Math.max(0,nx*-.26+ny*-.25+nz*.93),18)*.1;
        const light=.24+diffuse*.7,blue=clamp((x+90)/330)*.18+clamp((y-70)/220)*.2,grain=.985+rand(px*7+py*97)*.03;
        const j=(py*sw+px)*4;
        pixels.data[j]=(169-blue*84)*light*grain+spec*170;
        pixels.data[j+1]=(128-blue*23)*light*grain+spec*128;
        pixels.data[j+2]=(99+blue*24)*light*grain+spec*99;pixels.data[j+3]=255;
      }
      gc.putImageData(pixels,0,0);c.drawImage(surface,-sw/sc/2,-sh/sc/2,sw/sc,sh/sc);
      glow(c,130,-65,150,'235,182,139',.055);
      glow(c,-163,-127,172,'104,137,158',.08);
      // Fine, fixed skin grain sits below features and remains visible at 1440p.
      for(let i=0;i<6800;i++){
        const x=-240+rand(i*3+1)*480,y=-310+rand(i*3+2)*610;
        disc(c,x,y,.25+rand(i*3+3)*.38,i%3?'#e4bd9c':'#1b2331',.035+rand(i+921)*.025);
      }
      // Soft cheekbone and jaw modelling, not an opaque medical cutaway.
      stroke(c,p=>{p.moveTo(-68,-10);p.bezierCurveTo(-6,18,62,19,124,3);},'#e3ae87',22,.035);
      stroke(c,p=>{p.moveTo(-89,111);p.bezierCurveTo(-29,144,27,133,79,112);},'#0d1626',8,.045);
      stroke(c,p=>{p.moveTo(-97,128);p.bezierCurveTo(-57,181,-40,230,-35,278);},'#b08669',3,.035);
      c.restore();
      stroke(c,p=>headPath(p),P.gold,1.65,.44);
      stroke(c,p=>{p.moveTo(113,-121);p.quadraticCurveTo(130,-127,143,-114);},'#3b302e',5,.65);
      stroke(c,p=>{p.moveTo(114,-99);p.quadraticCurveTo(130,-91,142,-99);},'#211f26',3.3,.8);
      stroke(c,p=>{p.moveTo(112,-103);p.quadraticCurveTo(127,-97,140,-103);},P.pale,1,.3);
      stroke(c,p=>{p.moveTo(180,-17);p.quadraticCurveTo(188,-20,194,-18);},'#1c202b',2.2,.6);
      stroke(c,p=>{p.moveTo(162,33);p.quadraticCurveTo(172,35,177,32);},'#291e23',2.5,.6);
      stroke(c,p=>{p.moveTo(163,51);p.quadraticCurveTo(173,54,178,47);},'#c49b80',1.2,.33);
      // The same sculpted auricle is seen here at its anatomical scale.
      c.save();c.translate(-85,-31);c.scale(.25,.25);c.rotate(-.08);image(c,earPlate(),.72);c.restore();
    });
  }
  function clothPlate(){
    return plate('cloth',190,160,c=>{
      const outline=p=>{p.moveTo(-61,-49);p.quadraticCurveTo(2,-65,65,-39);p.bezierCurveTo(73,-12,74,28,61,52);p.quadraticCurveTo(0,67,-58,42);p.bezierCurveTo(-68,17,-68,-20,-61,-49);p.closePath();};
      c.save();c.beginPath();outline(c);c.clip();
      const g=c.createLinearGradient(-60,-53,66,58);g.addColorStop(0,'#a8bdc0');g.addColorStop(.28,'#829da8');g.addColorStop(.65,'#526f84');g.addColorStop(1,'#253f59');c.fillStyle=g;c.fillRect(-90,-80,180,160);
      for(let i=-30;i<32;i++){
        const x=i*3;
        stroke(c,p=>{p.moveTo(x,-79);p.bezierCurveTo(x-4,-20,x+5,27,x+2,80);},i%2?'#d0d8cf':'#233f56',.7,.13);
        stroke(c,p=>{p.moveTo(-94,x);p.bezierCurveTo(-35,x+2,29,x-4,94,x+1);},i%2?'#b9c6c4':'#253b4b',.7,.13);
      }
      stroke(c,p=>{p.moveTo(-60,-38);p.quadraticCurveTo(5,-51,68,-27);},'#d1d7cb',3,.38);
      stroke(c,p=>{p.moveTo(-60,33);p.quadraticCurveTo(2,58,67,42);},'#bfd1d3',2.6,.34);
      for(let k=0;k<5;k++)stroke(c,p=>{p.moveTo(-42+k*22,-29);p.bezierCurveTo(-46+k*22,-6,-39+k*22,16,-42+k*22,34);},'#1b344b',3,.12);
      c.restore();stroke(c,outline,P.ice,1.2,.68);
    },2);
  }
  function heartPath(p){
    p.moveTo(-30,-149);p.bezierCurveTo(-80,-190,-156,-149,-166,-77);
    p.bezierCurveTo(-186,20,-127,125,-28,201);p.quadraticCurveTo(1,224,28,196);
    p.bezierCurveTo(110,128,165,52,151,-37);p.bezierCurveTo(145,-116,98,-163,48,-148);
    p.quadraticCurveTo(10,-137,-30,-149);p.closePath();
  }
  function heartPlate(){
    return plate('heart',450,560,c=>{
      // Great vessels, with a deeper cool vessel behind the aortic arch.
      stroke(c,p=>{p.moveTo(-53,-107);p.bezierCurveTo(-72,-147,-81,-187,-73,-236);},'#273e50',43,.9);
      stroke(c,p=>{p.moveTo(-62,-119);p.bezierCurveTo(-80,-162,-86,-195,-78,-234);},'#668798',5,.6);
      stroke(c,p=>{p.moveTo(10,-117);p.bezierCurveTo(-9,-167,-15,-214,37,-233);p.bezierCurveTo(85,-251,113,-218,110,-177);},'#755441',43,1);
      stroke(c,p=>{p.moveTo(1,-123);p.bezierCurveTo(-18,-172,-14,-218,36,-240);p.bezierCurveTo(82,-258,116,-225,116,-181);},'#d8a17a',4,.72);
      for(let i=0;i<3;i++)stroke(c,p=>{p.moveTo(20+i*25,-233);p.lineTo(15+i*29,-271-i*4);},'#997056',12,.85);
      c.save();c.beginPath();heartPath(c);c.clip();
      const g=c.createRadialGradient(-65,-49,8,-19,17,238);g.addColorStop(0,'#b27b5b');g.addColorStop(.4,'#80533e');g.addColorStop(.72,'#4e3940');g.addColorStop(1,'#142438');c.fillStyle=g;c.fillRect(-230,-220,460,460);
      glow(c,-110,-66,124,'246,180,128',.17);
      for(let i=0;i<56;i++){
        const yy=-158+i*6.5,slant=Math.sin(i*.21)*9;
        stroke(c,p=>{p.moveTo(-195,yy);p.bezierCurveTo(-98,yy+slant,8,yy+58,108,yy+103);},i%3?'#e7ae7d':'#1a2431',.75,.055);
      }
      for(let i=0;i<3400;i++){const x=-190+rand(i*2+2)*380,y=-180+rand(i*2+3)*400;disc(c,x,y,.35,'#edbe95',.025);}
      // The anterior groove and branching surface vessels track the organ form.
      stroke(c,p=>{p.moveTo(6,-139);p.bezierCurveTo(-21,-54,13,46,3,179);},'#1e2430',12,.75);
      stroke(c,p=>{p.moveTo(12,-139);p.bezierCurveTo(-13,-54,20,46,9,179);},'#c59369',4,.75);
      for(let j=0;j<9;j++){
        const yy=-89+j*28, side=j%2?1:-1;
        stroke(c,p=>{p.moveTo(4,yy);p.bezierCurveTo(side*28,yy-19,side*(70-j*3),yy-14,side*(129-j*8),yy+17);},j%2?'#688392':'#d19a6c',2.2,.58);
        stroke(c,p=>{p.moveTo(side*44,yy-9);p.quadraticCurveTo(side*73,yy-23,side*83,yy-44);},j%2?'#4d718b':'#a27458',1,.48);
      }
      c.restore();stroke(c,heartPath,P.gold,1.4,.4);
      stroke(c,p=>{p.moveTo(-22,-120);p.bezierCurveTo(26,-184,91,-181,153,-154);},'#3c6076',29,.94);
      stroke(c,p=>{p.moveTo(-25,-130);p.bezierCurveTo(25,-193,91,-190,154,-163);},'#9ab4bf',3,.55);
    });
  }
  function brainstemPlate(){
    return plate('brainstem',255,385,c=>{
      const shape=p=>{p.moveTo(-35,-121);p.bezierCurveTo(-99,-111,-99,-35,-44,-11);p.bezierCurveTo(-40,47,-17,89,-17,160);p.lineTo(21,162);p.bezierCurveTo(16,86,49,44,47,-17);p.bezierCurveTo(101,-47,90,-110,36,-126);p.closePath();};
      const g=c.createLinearGradient(-80,0,80,0);g.addColorStop(0,'#2c3b4d');g.addColorStop(.25,'#86715c');g.addColorStop(.53,'#b08a68');g.addColorStop(.8,'#514c49');g.addColorStop(1,'#233b50');
      fill(c,shape,g,.9);stroke(c,shape,P.pale,1.5,.3);
      c.save();c.beginPath();shape(c);c.clip();
      for(let i=0;i<21;i++){
        const x=(i-10)*5;
        stroke(c,p=>{p.moveTo(x,-169);p.bezierCurveTo(x*1.6,-90,x*.39,24,x*.22,169);},i%3?P.pale:P.ice,.8,.19);
      }
      for(let i=0;i<14;i++)stroke(c,p=>{p.moveTo(-92,-112+i*6);p.quadraticCurveTo(0,-64+i*3,92,-112+i*6);},'#0f1d2c',1,.22);
      c.restore();
      for(let j=0;j<3;j++)stroke(c,p=>{p.moveTo(-66,-74+j*17);p.quadraticCurveTo(-100,-83+j*22,-123,-64+j*24);},j===1?P.blue:P.warm,3-j*.4,.75);
    },2);
  }
  function signalCurve(c,a,b,cc,d,t,alpha,color,phase=0){
    stroke(c,p=>{p.moveTo(a.x,a.y);p.bezierCurveTo(b.x,b.y,cc.x,cc.y,d.x,d.y);},'#182331',8,.45*alpha);
    stroke(c,p=>{p.moveTo(a.x,a.y);p.bezierCurveTo(b.x,b.y,cc.x,cc.y,d.x,d.y);},color,1.8,.52*alpha);
    for(let i=0;i<3;i++){const q=curvePoint(a,b,cc,d,(t*.12+i/3+phase)%1);luminous(c,q.x,q.y,2,color===P.blue?'143,180,196':'230,180,139',alpha*.7);}
  }
  function cold(c,t,duration,env){
    const b=beatState(t,duration,env,5);
    const mechanism=b.index===1?ramp(b.progress,0,.24):b.index===2?1:b.index===3?1-ramp(b.progress,0,.3):0;
    const hx=lerp(0,-430,mechanism),hs=lerp(1,.78,mechanism);
    c.save();c.translate(hx,0);c.scale(hs,hs);image(c,headPlate(),1-mechanism*.17);
    const clothAlpha=1-mechanism*.3;
    c.save();c.translate(65,44);c.rotate(.045);image(c,clothPlate(),clothAlpha);c.restore();
    glow(c,65,44,103,'96,151,185',.07+Math.sin(t*.7)**2*.025);
    // Gentle contact pulses remain on the skin; the nose and mouth stay clear.
    for(let k=0;k<2;k++){
      const p=(t*.12+k*.5)%1;
      stroke(c,q=>{q.ellipse(65,44,75+p*35,61+p*25,0,.7,3.7);},P.blue,1,(1-p)*.14);
    }
    c.restore();
    if(mechanism>.001){
      c.save();c.globalAlpha*=mechanism;
      c.save();c.translate(-44,2);image(c,brainstemPlate(),.94);c.restore();
      signalCurve(c,{x:-345,y:24},{x:-294,y:-71},{x:-218,y:-62},{x:-160,y:-44},t,1,P.blue);
      signalCurve(c,{x:-27,y:146},{x:93,y:204},{x:200,y:42},{x:310,y:-69},t,1,P.gold,.3);
      const pulse=Math.exp(-Math.pow(((t*.93)%1-.18)/.095,2))*.022;
      c.save();c.translate(399,20);c.scale(.91+pulse,.91+pulse);image(c,heartPlate());c.restore();
      // A quiet peripheral branch shows that this is not whole-body relaxation.
      if(b.index>=2){stroke(c,p=>{p.moveTo(-10,130);p.bezierCurveTo(69,147,132,255,245,278);},'#717b82',1.2,.34);stroke(c,p=>{p.moveTo(165,243);p.quadraticCurveTo(213,229,254,239);},'#717b82',1.2,.24);}
      c.restore();
    }
  }

  function earOutline(p){
    p.moveTo(-35,245);p.bezierCurveTo(-99,259,-139,204,-154,133);
    p.bezierCurveTo(-170,60,-233,-29,-217,-137);
    p.bezierCurveTo(-205,-249,-111,-295,-24,-283);
    p.bezierCurveTo(91,-272,154,-193,142,-90);
    p.bezierCurveTo(133,-7,106,46,74,95);
    p.bezierCurveTo(48,142,63,210,13,241);p.quadraticCurveTo(-9,253,-35,245);p.closePath();
  }
  function earPlate(){
    return plate('auricle',550,650,c=>{
      const sc=1.8,w=990,h=1170,hm=new OffscreenCanvas(w,h),hc=hm.getContext('2d');
      hc.scale(sc,sc);hc.translate(275,325);hc.save();hc.beginPath();earOutline(hc);hc.clip();
      const base=hc.createRadialGradient(-83,-71,10,-53,-15,307);
      base.addColorStop(0,'#828282');base.addColorStop(.5,'#686868');base.addColorStop(1,'#282828');
      hc.fillStyle=base;hc.fillRect(-280,-330,560,660);
      const helix=p=>{p.moveTo(-77,181);p.bezierCurveTo(-94,118,-178,7,-181,-112);p.bezierCurveTo(-184,-202,-104,-254,-33,-250);p.bezierCurveTo(62,-247,119,-181,104,-96);p.bezierCurveTo(94,-35,62,27,35,84);};
      const anti=p=>{p.moveTo(-30,132);p.bezierCurveTo(-48,76,-17,32,-45,-22);p.bezierCurveTo(-72,-91,-48,-158,-72,-206);};
      const fork=p=>{p.moveTo(-45,-22);p.bezierCurveTo(1,-71,37,-123,12,-168);};
      function relief(fn,width){
        hc.save();hc.filter='blur(10px)';stroke(hc,fn,'#2d2d2d',width+24,.58);hc.restore();
        hc.save();hc.filter='blur(7px)';stroke(hc,fn,'#b8b8b8',width,1);stroke(hc,fn,'#dedede',width*.38,.7);hc.restore();
      }
      relief(helix,31);relief(anti,20);relief(fork,19);
      const bowl=hc.createRadialGradient(-13,13,5,-32,1,94);bowl.addColorStop(0,'#0c0c0c');bowl.addColorStop(.37,'#202020');bowl.addColorStop(.75,'#656565');bowl.addColorStop(1,'rgba(100,100,100,0)');
      hc.fillStyle=bowl;hc.fillRect(-155,-144,280,305);
      relief(p=>{p.moveTo(9,-44);p.bezierCurveTo(-49,-70,-79,-9,-63,44);p.bezierCurveTo(-49,77,-12,86,21,50);},12);

      hc.save();hc.filter='blur(5px)';fill(hc,p=>{p.ellipse(28,17,15,30,.1,0,TAU);},'#bcbcbc');fill(hc,p=>{p.ellipse(2,87,23,12,-.25,0,TAU);},'#b2b2b2');hc.restore();
      hc.restore();
      const source=hc.getImageData(0,0,w,h),out=hc.createImageData(w,h),data=source.data;
      // Smooth in floating point before taking normals: no 8-bit contour banding.
      const tmp=new Float32Array(w*h),heightField=new Float32Array(w*h);
      for(let y=2;y<h-2;y++)for(let x=2;x<w-2;x++){
        const q=y*w+x;tmp[q]=(data[(q-2)*4]+4*data[(q-1)*4]+6*data[q*4]+4*data[(q+1)*4]+data[(q+2)*4])/16;
      }
      for(let y=2;y<h-2;y++)for(let x=2;x<w-2;x++){
        const q=y*w+x;heightField[q]=(tmp[q-2*w]+4*tmp[q-w]+6*tmp[q]+4*tmp[q+w]+tmp[q+2*w])/16;
      }
      for(let y=1;y<h-1;y++)for(let x=1;x<w-1;x++){
        const i=(y*w+x)*4;if(data[i+3]<1)continue;
        const q=y*w+x,height=heightField[q]/255,dx=(heightField[q+1]-heightField[q-1])*.15,dy=(heightField[q+w]-heightField[q-w])*.15;
        let nx=-dx,ny=-dy,nz=1;const n=Math.hypot(nx,ny,nz);nx/=n;ny/=n;nz/=n;
        const diffuse=Math.max(0,nx*-.55+ny*-.48+nz*.68);
        const spec=Math.pow(Math.max(0,nx*-.29+ny*-.27+nz*.92),18)*.18;
        const ao=.58+height*.42,light=(.25+diffuse*.77)*ao;
        const cool=clamp((y/h-.52)*1.7),grain=.97+rand(x*13+y*431)*.06;
        out.data[i]=(161-cool*39)*light*grain+spec*182;
        out.data[i+1]=(125-cool*8)*light*grain+spec*133;
        out.data[i+2]=(94+cool*22)*light*grain+spec*95;
        out.data[i+3]=data[i+3];
      }
      hc.resetTransform();hc.putImageData(out,0,0);c.drawImage(hm,-275,-325,550,650);
      stroke(c,earOutline,P.gold,1.1,.31);
      // Fine pores are fixed in surface space; no animated noise or shimmer.
      c.save();c.beginPath();earOutline(c);c.clip();
      for(let i=0;i<4800;i++){const x=-245+rand(i*3+40)*450,y=-305+rand(i*3+41)*580;disc(c,x,y,.22+rand(i*3+42)*.3,i%4?P.pale:'#111b29',.035);}
      c.restore();
    },1.8);
  }
  function fingerPlate(){
    return plate('fingers',485,250,c=>{
      const finger=p=>{p.moveTo(237,80);p.bezierCurveTo(147,62,63,21,-78,-22);p.bezierCurveTo(-126,-38,-157,-32,-166,-5);p.bezierCurveTo(-176,27,-153,44,-119,51);p.bezierCurveTo(9,80,103,118,231,120);p.closePath();};
      const g=c.createLinearGradient(0,-33,0,114);g.addColorStop(0,'#a78062');g.addColorStop(.2,'#c69d79');g.addColorStop(.47,'#b08a6c');g.addColorStop(.75,'#6a5549');g.addColorStop(1,'#26303e');fill(c,finger,g);
      c.save();c.beginPath();finger(c);c.clip();
      for(let i=0;i<16;i++)stroke(c,p=>{p.ellipse(-132,9,12+i*2.6,17+i*2.6,-.5,.2,5.3);},'#4c4843',.7,.13);
      for(let i=0;i<1800;i++){const x=-180+rand(i*2+65)*420,y=-51+rand(i*2+66)*180;disc(c,x,y,.3,'#f0c5a0',.055);}
      stroke(c,p=>{p.moveTo(72,10);p.quadraticCurveTo(58,37,74,76);p.moveTo(83,17);p.quadraticCurveTo(74,39,87,72);},'#55453d',1.2,.3);
      c.restore();stroke(c,finger,P.gold,1,.4);
      stroke(c,p=>{p.moveTo(-157,-14);p.quadraticCurveTo(-143,-33,-118,-26);},P.pale,1.5,.35);
    },2);
  }
  function sensorySources(c,t,alpha){
    c.save();c.globalAlpha*=alpha;
    const paths=[
      {a:{x:-335,y:-171},b:{x:-242,y:-185},cc:{x:-158,y:-213},d:{x:-101,y:-179},col:'#b59b83'},
      {a:{x:-330,y:198},b:{x:-221,y:205},cc:{x:-150,y:121},d:{x:-82,y:152},col:'#899393'},
      {a:{x:284,y:-104},b:{x:173,y:-91},cc:{x:71,y:-43},d:{x:-12,y:7},col:P.blue}
    ];
    for(const [i,v] of paths.entries()){
      stroke(c,p=>{p.moveTo(v.a.x,v.a.y);p.bezierCurveTo(v.b.x,v.b.y,v.cc.x,v.cc.y,v.d.x,v.d.y);},v.col,2,.52);
      for(let k=0;k<4;k++){
        const q=curvePoint(v.a,v.b,v.cc,v.d,.5+k*.14),side=i===2?-1:1;
        stroke(c,p=>{p.moveTo(q.x,q.y);p.quadraticCurveTo(q.x+side*21,q.y-20,q.x+side*(28+k*3),q.y-31-k*7);},v.col,1.2,.4);
      }
    }
    // Local, overlapping sensory territories, deliberately not an exact atlas.
    glow(c,-110,-177,62,'181,155,131',.12);
    glow(c,-68,155,68,'137,147,147',.1);
    glow(c,-21,6,47,'73,109,133',.21);
    c.restore();
  }
  function ear(c,t,duration,env){
    const b=beatState(t,duration,env,3);
    const mapped=b.index===1?ramp(b.progress,0,.18):b.index===2?1-ramp(b.progress,0,.22):0;
    c.save();c.translate(-26-mapped*28,-5);image(c,earPlate());
    if(mapped>0)sensorySources(c,t,mapped);
    const touch=1-mapped;
    if(touch>.001){
      const gentle=Math.sin(t*.82)*3;
      c.save();c.globalAlpha*=touch;c.translate(200+gentle,142+Math.sin(t*.6)*8);c.rotate(-.12);image(c,fingerPlate());c.restore();
      glow(c,31+gentle,147,35,'235,189,150',.09*touch);
    }
    c.restore();
  }

  window.LongScenes=window.LongScenes||{};
  Object.assign(window.LongScenes,{hook,breath,cold,ear});
})();
