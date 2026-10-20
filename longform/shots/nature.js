/* Nature / title / closing — deterministic, self-contained botanical & optical studies.
 * Coordinates: renderer translates to the subject centre in a 1920×1080 scene.
 * No global clock, random source, fonts, image files, or shared helper dependencies.
 */
(function () {
  'use strict';
  const S = window.LongScenes = window.LongScenes || {};
  const TAU = Math.PI * 2;
  const C = { dark: '#06060e', warm: '#daa27d', copper: '#ac7859', cool: '#496d85' };
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const mix = (a, b, p) => a + (b - a) * p;
  const smooth = x => { x = clamp(x); return x * x * (3 - 2 * x); };
  const ramp = (a, b, t) => smooth((t - a) / (b - a));
  const windowed = (a, b, c, d, t) => ramp(a, b, t) * (1 - ramp(c, d, t));
  const hash = x => { const v = Math.sin(x * 127.13 + 17.71) * 43758.5453; return v - Math.floor(v); };
  const rgba = (c, a) => {
    const n = parseInt(c.slice(1), 16);
    return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${clamp(a)})`;
  };
  const stroke = (ctx, pts, color, width = 1, alpha = 1, amount = 1) => {
    if (pts.length < 2 || amount <= 0 || alpha <= 0) return;
    const n = Math.max(1, amount * (pts.length - 1)), end = Math.min(pts.length - 1, Math.floor(n));
    ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
    for (let k = 1; k <= end; k++) ctx.lineTo(pts[k][0], pts[k][1]);
    if (end < pts.length - 1) {
      const f = n - end;
      ctx.lineTo(mix(pts[end][0], pts[end + 1][0], f), mix(pts[end][1], pts[end + 1][1], f));
    }
    ctx.strokeStyle = rgba(color, alpha); ctx.lineWidth = width; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
  };
  function halo(ctx, x, y, rx, ry, color, alpha) {
    ctx.save(); ctx.translate(x, y); ctx.scale(1, ry / rx);
    const g = ctx.createRadialGradient(0, 0, 0, 0, 0, rx);
    g.addColorStop(0, rgba(color, alpha)); g.addColorStop(.4, rgba(color, alpha * .35)); g.addColorStop(1, rgba(color, 0));
    ctx.fillStyle = g; ctx.fillRect(-rx, -rx, rx * 2, rx * 2); ctx.restore();
  }
  function project(x, y, z, ax = .95, ay = -.25, az = -.22) {
    let yy = y * Math.cos(ax) - z * Math.sin(ax), zz = y * Math.sin(ax) + z * Math.cos(ax);
    let xx = x * Math.cos(ay) + zz * Math.sin(ay); zz = -x * Math.sin(ay) + zz * Math.cos(ay);
    return [xx * Math.cos(az) - yy * Math.sin(az), xx * Math.sin(az) + yy * Math.cos(az), zz];
  }
  function silkTorus(ctx, t, radius, tube, alpha = 1, unfold = 1) {
    // The surface is woven, rather than populated with unattached glow particles.
    const faces = [];
    for (let a = 0; a < 56; a++) for (let b = 0; b < 18; b++) {
      const points = []; let z = 0;
      for (const [du,dv] of [[0,0],[1,0],[1,1],[0,1]]) {
        const u = (a+du)/56*TAU, v = (b+dv)/18*TAU;
        const rr = radius + tube*Math.cos(v);
        const q = project(rr*Math.cos(u),rr*Math.sin(u),tube*Math.sin(v),.9,-.32,-.28);
        points.push(q); z+=q[2];
      }
      const u=(a+.5)/56*TAU,v=(b+.5)/18*TAU;
      const normal=project(Math.cos(v)*Math.cos(u),Math.cos(v)*Math.sin(u),Math.sin(v),.9,-.32,-.28);
      const light=Math.pow(Math.max(0,-normal[0]*.38-normal[1]*.6+normal[2]*.7),2);
      faces.push({points,depth:z/4,light});
    }
    faces.sort((a,b)=>a.depth-b.depth);
    for (const f of faces) {
      ctx.beginPath();ctx.moveTo(f.points[0][0],f.points[0][1]);
      for(let i=1;i<4;i++)ctx.lineTo(f.points[i][0],f.points[i][1]);ctx.closePath();
      ctx.fillStyle=rgba(f.light>.45?C.warm:C.copper,alpha*(.035+.29*f.light));ctx.fill();
    }
    const layers = [];
    for (let j = 0; j < 42; j++) {
      const v = j / 42 * TAU, points = []; let depth = 0;
      for (let i = 0; i <= 144; i++) {
        const u = i / 144 * TAU;
        const corrugation = Math.sin(u * 3 + v * 2) * 2.2 + Math.sin(u * 7 - v) * .8;
        const r = radius + tube * Math.cos(v) + corrugation;
        const k = (1 - unfold) * Math.sin(u * 3 + v) * 34;
        const q = project(r * Math.cos(u), r * Math.sin(u), tube * Math.sin(v) + k, .9, -.32, -.28);
        points.push(q); depth += q[2];
      }
      layers.push({ points, depth: depth / points.length, j });
    }
    layers.sort((a, b) => a.depth - b.depth);
    layers.forEach(layer => {
      const lit = clamp((layer.depth + radius + tube) / (2 * radius + 2 * tube));
      stroke(ctx, layer.points, layer.j % 9 === 0 ? C.cool : C.warm, .38 + lit * .65, alpha * (.12 + lit * .57));
    });
    for (let k = 0; k < 38; k++) {
      const u = k / 38 * TAU, points = [];
      for (let j = 0; j <= 52; j++) {
        const v = j / 52 * TAU;
        const rr = radius + tube * Math.cos(v);
        points.push(project(rr * Math.cos(u), rr * Math.sin(u), tube * Math.sin(v), .9, -.32, -.28));
      }
      stroke(ctx, points, C.copper, .42, alpha * (.09 + .18 * Math.max(0, Math.cos(u - 2))));
    }
    // A restrained moving reflection on one coherent edge.
    const glint = [], at = .54 + .04 * Math.sin(t * .12);
    for (let i = 0; i <= 38; i++) {
      const u = (at + i / 38 * .14) * TAU;
      glint.push(project((radius + tube) * Math.cos(u), (radius + tube) * Math.sin(u), 0, .9, -.32, -.28));
    }
    ctx.save(); ctx.shadowColor = rgba(C.warm, .5); ctx.shadowBlur = 9;
    stroke(ctx, glint, C.warm, 1.1, alpha * .65); ctx.restore();
  }

  S.title = function (ctx, t, duration, env) {
    const unfold = ramp(.2, Math.min(4, duration * .62), t);
    const appear = ramp(0, 1.2, t);
    ctx.save();
    halo(ctx, 0, 20, 540, 270, C.cool, .075 * appear);
    halo(ctx, -50, -10, 345, 260, C.warm, .065 * appear);
    ctx.translate(0, 18); ctx.scale(1.42,1.42);
    // Quiet glass lamellae behind the toroidal object.
    for (let k = 0; k < 18; k++) {
      const pts = [], shift = (k - 8.5) * 3.7;
      for (let i = 0; i <= 90; i++) {
        const u = i / 90, x = mix(-430, 430, u);
        pts.push([x, 76 * Math.sin(u * Math.PI * 1.5 + .4) + shift + 22 * Math.sin(u * Math.PI)]);
      }
      stroke(ctx, pts, k % 5 === 0 ? C.cool : C.warm, .5, appear * (.035 + .055 * Math.sin(k / 18 * Math.PI)), unfold);
    }
    silkTorus(ctx, t, mix(174, 236, unfold), mix(84, 51, unfold), appear, unfold);
    // Interior membrane: finely separated warped contours with an open centre.
    for (let k = 0; k < 22; k++) {
      const q = (k - 10.5) / 10.5, pts = [];
      for (let i = 0; i <= 82; i++) {
        const u = i / 82 * TAU;
        const rr = 108 + 12 * Math.cos(3 * u + q) + q * 17;
        pts.push(project(rr * Math.cos(u), rr * Math.sin(u), q * 38 + Math.sin(u * 2) * 14, .85, -.32, -.28));
      }
      stroke(ctx, pts, C.copper, .5, appear * .12 * (1 - .3 * unfold));
    }
    ctx.restore();
  };

  // Botanical coordinate field: the blade has curl, asymmetry and restrained irregularity.
  function leafPoint(u, v) {
    u = clamp(u); v = clamp(v, -1, 1);
    const w = 137 * Math.pow(Math.sin(Math.PI * u), .88) * (1 + .08 * Math.sin(u * 13.7 + v));
    const y = 132 - u * 280 + 31 * Math.sin(Math.PI * u);
    const curl = 17 * v * v * Math.sin(u * Math.PI * 1.8);
    return [-336 + 672 * u + v * w * .39 + curl * .3,
      y + v * w * .91 - curl + .8 * Math.sin(u * 54 + v * 10) * Math.abs(v)];
  }
  function leafOutline(ctx) {
    ctx.beginPath();
    for (let side = 0; side < 2; side++) {
      for (let i = 0; i <= 130; i++) {
        const u = side ? 1 - i / 130 : i / 130, v = side ? -1 : 1;
        const p = leafPoint(u, v);
        if (!side && !i) ctx.moveTo(...p); else ctx.lineTo(...p);
      }
    }
    ctx.closePath();
  }
  const leafVeins = [];
  function addVein(points, level, birth, width, opacity) { leafVeins.push({ points, level, birth, width, opacity }); }
  const midrib = Array.from({ length: 130 }, (_, i) => leafPoint(i / 129, 0));
  addVein(midrib, 0, 0, 2.4, .8);
  for (const side of [-1, 1]) {
    for (let k = 0; k < 13; k++) {
      const root = .04 + k * .064, bend = .21 * (1 - root) + .045;
      const secondary = [];
      for (let j = 0; j <= 42; j++) {
        const v = j / 42, u = root + bend * v + .006 * Math.sin(v * 5 + k) * v;
        secondary.push(leafPoint(u, side * v * .98));
      }
      addVein(secondary, 1, root * .53 + .1, 1.05 - root * .43, .45 + .13 * hash(k + side));
      for (let m = 1; m <= 7; m++) {
        const base = m / 9, rootU = root + bend * base, sign = m % 2 ? 1 : -1;
        const tertiary = [];
        for (let j = 0; j <= 18; j++) {
          const q = j / 18, v = base + q * .18, u = rootU + q * (.04 + .02 * (1 - base)) * sign + bend * q * .13;
          tertiary.push(leafPoint(u, side * Math.min(.985, v)));
        }
        addVein(tertiary, 2, root * .53 + .25 + base * .14, .38 + .12 * hash(k * 17 + m), .38);
        for (let n = 1; n <= 3; n++) {
          const source = tertiary[Math.floor(n / 4 * 18)], end = tertiary[Math.min(18, Math.floor(n / 4 * 18) + 5)];
          const dx = end[0] - source[0], dy = end[1] - source[1], bran = [];
          for (let z = 0; z <= 6; z++) {
            const q = z / 6, b = 5 + 5 * hash(k * 23 + m * 9 + n);
            bran.push([source[0] + dx * q + b * q, source[1] + dy * q - side * b * q * (1 - .25 * q)]);
          }
          addVein(bran, 3, root * .53 + .42 + base * .12, .27, .23);
        }
      }
    }
  }
  let bladeCache = null;
  function getBlade() {
    if (bladeCache) return bladeCache;
    const canvas = typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(1600, 1000) : document.createElement('canvas');
    canvas.width = 1600; canvas.height = 1000;
    const ctx = canvas.getContext('2d'); ctx.scale(2, 2); ctx.translate(400, 250);
    ctx.save(); leafOutline(ctx); ctx.clip();
    const base = ctx.createLinearGradient(-240, -180, 240, 200);
    base.addColorStop(0, rgba(C.copper, .28)); base.addColorStop(.42, rgba(C.warm, .21)); base.addColorStop(1, rgba(C.cool, .23));
    ctx.fillStyle = base; ctx.fillRect(-400, -250, 800, 500);
    // Lamina cells are irregular quadrilaterals; they make a surface, not noise specks.
    for (let a = 0; a < 120; a++) for (let b = 0; b < 36; b++) {
      const u = (a + .5) / 120, v = (b + .5) / 18 - 1, h = hash(a * 73 + b * 19);
      const du = .0051 + h * .0026, dv = .020 + .006 * hash(a + b * 31);
      const ps = [leafPoint(u - du, v - dv), leafPoint(u + du, v - dv * .8), leafPoint(u + du * .8, v + dv), leafPoint(u - du, v + dv * .7)];
      ctx.beginPath(); ctx.moveTo(...ps[0]); for (let k = 1; k < ps.length; k++) ctx.lineTo(...ps[k]); ctx.closePath();
      const light = .006 + .035 * Math.pow(Math.max(0, .6 - v * .3 + .25 * Math.sin(u * 9)), 2) * h;
      ctx.fillStyle = rgba(h > .3 ? C.warm : C.cool, light); ctx.fill();
      if ((a + b) % 3 === 0) { ctx.strokeStyle = rgba(C.copper, .035); ctx.lineWidth = .22; ctx.stroke(); }
    }
    // Soft relief on the central rib and a thin shadow underneath it.
    for (let k = 10; k >= 1; k--) stroke(ctx, midrib.map(p => [p[0], p[1] + 1.5]), C.dark, k * 1.1, .026);
    for (let k = 11; k >= 1; k--) stroke(ctx, midrib, C.warm, k * .65, .008);
    ctx.restore();
    leafOutline(ctx); ctx.strokeStyle = rgba(C.warm, .3); ctx.lineWidth = .75; ctx.stroke();
    const rim = Array.from({ length: 90 }, (_, i) => leafPoint(.32 + i / 89 * .51, -1));
    stroke(ctx, rim, C.warm, .8, .38);
    bladeCache = canvas; return canvas;
  }
  function drawLeaf(ctx, t, growth = 1, surface = 1, illumination = 1) {
    ctx.save(); ctx.globalAlpha *= surface;
    ctx.drawImage(getBlade(), -400, -250, 800, 500); ctx.restore();
    ctx.save(); leafOutline(ctx); ctx.clip();
    leafVeins.forEach(v => {
      const amount = clamp((growth - v.birth) / (.28 - v.level * .04));
      stroke(ctx, v.points, v.level > 2 ? C.copper : C.warm, v.width, v.opacity * illumination, smooth(amount));
    });
    // One warm impulse travels along the anatomical spine; no random sparkle field.
    const loc = clamp(.08 + (t % 19) / 19 * .84), width = .045;
    if (growth > .85) {
      const pts = Array.from({ length: 18 }, (_, i) => leafPoint(clamp(loc - width + i / 17 * width * 2), 0));
      ctx.save(); ctx.shadowColor = rgba(C.warm, .65); ctx.shadowBlur = 8;
      stroke(ctx, pts, C.warm, 2.0, .45 * illumination); ctx.restore();
    }
    ctx.restore();
  }

  // Compound fern with leaflets, secondary pinnae and visibly tapered rachises.
  const fernParts = [];
  function smallBlade(x, y, angle, length, width, seed, birth) {
    fernParts.push({ type: 'blade', x, y, angle, length, width, seed, birth });
  }
  const fernSpine = Array.from({ length: 90 }, (_, i) => leafPoint(i / 89, 0));
  for (let k = 0; k < 15; k++) for (const side of [-1, 1]) {
    const u = .045 + k * .060, base = leafPoint(u, 0);
    const len = 180 * Math.pow(Math.sin(Math.PI * u), .8) * (1 + .045 * Math.sin(k * 2.1 + side));
    const angle = (side > 0 ? .61 : -1.39) + .18 * u;
    const direction = [Math.cos(angle), Math.sin(angle)];
    const rachis = [];
    for (let j = 0; j <= 30; j++) {
      const q = j / 30;
      rachis.push([base[0] + direction[0] * len * q, base[1] + direction[1] * len * q + side * 10 * q * q]);
    }
    fernParts.push({ type: 'rachis', points: rachis, birth: u * .45, width: 1.25 - u * .6 });
    for (let j = 1; j <= 8; j++) for (const wing of [-1, 1]) {
      const q = j / 9, p = rachis[Math.floor(q * 30)];
      const l = len * .26 * Math.pow(1 - q, .45) * (.94 + .1 * hash(k * 100 + j));
      smallBlade(p[0], p[1], angle + wing * .79, l, l * .29, k * 19 + j * 3 + side + wing, u * .45 + q * .2);
    }
  }
  function drawFern(ctx, growth, alpha) {
    if (alpha < .001) return;
    ctx.save(); ctx.globalAlpha *= alpha;
    stroke(ctx, fernSpine, C.warm, 2.4, .58, growth);
    fernParts.forEach(part => {
      const g = ramp(part.birth, part.birth + .28, growth);
      if (g <= 0) return;
      if (part.type === 'rachis') { stroke(ctx, part.points, C.warm, part.width, .42, g); return; }
      const l = part.length * (.25 + g * .75), w = part.width * g;
      ctx.save(); ctx.translate(part.x, part.y); ctx.rotate(part.angle);
      const path = new Path2D(); path.moveTo(0, 0);
      path.bezierCurveTo(l * .25, -w, l * .71, -w * .54, l, 0);
      path.bezierCurveTo(l * .74, w * .35, l * .18, w * .74, 0, 0);
      const grd = ctx.createLinearGradient(0, -w, 0, w);
      grd.addColorStop(0, rgba(C.warm, .13 + .06 * hash(part.seed)));
      grd.addColorStop(.46, rgba(C.copper, .12)); grd.addColorStop(1, rgba(C.cool, .035));
      ctx.fillStyle = grd; ctx.fill(path); ctx.strokeStyle = rgba(C.warm, .35 * g); ctx.lineWidth = .45; ctx.stroke(path);
      stroke(ctx, [[0,0],[l*.35,-.3],[l*.75,-.4],[l,0]], C.warm, .47, .37);
      for (let j = 1; j <= 5; j++) {
        const q = j / 7, h = Math.sin(q * Math.PI) * w;
        stroke(ctx, [[l*q,0],[l*(q+.08),-h*.55],[l*(q+.14),-h*.71]], C.copper, .25, .28);
        stroke(ctx, [[l*q,0],[l*(q+.07),h*.38],[l*(q+.12),h*.51]], C.warm, .24, .2);
      }
      ctx.restore();
    });
    ctx.restore();
  }
  function atmosphere(ctx, t, alpha) {
    // Long, spatially coherent cloud/water contours. Motion is subpixel over a second.
    ctx.save();
    for (let k = 0; k < 22; k++) {
      const pts = [], offset = (k - 11) * 7;
      for (let j = 0; j <= 100; j++) {
        const x = -710 + j / 100 * 1420;
        const wave = Math.sin(x * .0041 + k * .027 + t * .012) * 20 + Math.sin(x * .009 - k * .043) * 6;
        pts.push([x, 205 + offset + wave]);
      }
      stroke(ctx, pts, k % 4 ? C.cool : C.warm, .45, alpha * .035 * Math.sin(k / 22 * Math.PI));
    }
    ctx.restore();
  }
  S.fractal = function (ctx, t, duration, env) {
    const p = clamp(t / Math.max(1, duration));
    const grow = ramp(0, Math.min(8, duration * .15), t);
    const lens = windowed(.19, .27, .51, .58, p);
    const fern = windowed(.47, .57, .75, .86, p);
    const settle = ramp(.81, .96, p);
    ctx.save();
    atmosphere(ctx, t, .6 + .4 * settle);
    halo(ctx, -60, 5, 460, 260, C.warm, .038);
    halo(ctx, 160, 40, 500, 290, C.cool, .035);
    ctx.translate(-140 * lens, 5);
    const leafScale = 1.3 + .025 * settle;
    ctx.scale(leafScale, leafScale);
    drawLeaf(ctx, t, grow, (1 - fern * .85) * (.3 + .7 * grow), 1 - fern * .76);
    drawFern(ctx, ramp(.48, .62, p), fern);
    ctx.restore();
    if (lens > .001) {
      const x = 452, y = -32, radius = 166;
      ctx.save(); ctx.globalAlpha *= lens;
      // The lens is a part of the same leaf, with one correspondingly magnified structure.
      const sample = leafPoint(.64, -.22);
      const sampleX = sample[0] * 1.3 - 140 * lens, sampleY = sample[1] * 1.3 + 5;
      ctx.setLineDash([2, 7]);
      stroke(ctx, [[sampleX + 22, sampleY - 18],[258, -107],[x - radius + 4,y-40]], C.cool, .65, .4);
      ctx.setLineDash([]);
      ctx.beginPath(); ctx.arc(sampleX, sampleY, 20, 0, TAU); ctx.strokeStyle = rgba(C.warm,.45); ctx.lineWidth=.7; ctx.stroke();
      halo(ctx,x,y,radius+24,radius+24,C.warm,.035);
      ctx.beginPath();ctx.arc(x,y,radius,0,TAU);ctx.fillStyle=rgba(C.dark,.96);ctx.fill();
      ctx.save();ctx.clip();ctx.translate(x,y);ctx.scale(3.15,3.15);ctx.translate(-sample[0],-sample[1]);
      drawLeaf(ctx,t,grow,1,.85);ctx.restore();
      ctx.beginPath();ctx.arc(x,y,radius,0,TAU);ctx.strokeStyle=rgba(C.warm,.48);ctx.lineWidth=.65;ctx.stroke();
      ctx.beginPath();ctx.arc(x,y,radius+3,.95*Math.PI,1.8*Math.PI);ctx.strokeStyle=rgba(C.cool,.3);ctx.lineWidth=.55;ctx.stroke();
      // Glass edge reflection occupies one arc, leaving the internal anatomy legible.
      ctx.beginPath();ctx.arc(x,y,radius-2,1.1*Math.PI,1.39*Math.PI);ctx.strokeStyle=rgba(C.warm,.62);ctx.lineWidth=1.1;ctx.stroke();
      ctx.restore();
    }
  };

  function renderSculpture(ctx, kind, radius, time, alpha, opening = 1) {
    const lines = [], ax = .88 + kind * .11, ay = -.4 + kind * .13;
    // Continuous pleated shell. The seven related objects have distinct internal symmetries.
    for (let j = 1; j < 24; j++) {
      const lat = j / 24 * Math.PI, pts = []; let zsum = 0;
      for (let i = 0; i <= 78; i++) {
        const u = i / 78 * TAU;
        const fold = Math.sin((3 + kind % 4) * u + lat * (kind % 2 ? 2 : 1)) * Math.pow(Math.sin(lat), 1.4);
        const r = radius * (1 + .11 * fold + .035 * Math.cos(7 * lat));
        let x = r * Math.sin(lat) * Math.cos(u), y = r * Math.cos(lat), z = r * Math.sin(lat) * Math.sin(u);
        x *= 1 + .09 * Math.sin(kind); y *= 1 + .16 * Math.cos(kind * 1.4);
        z *= .78 + .2 * opening;
        const q = project(x,y,z,ax,ay,-.18);pts.push(q);zsum += q[2];
      }
      lines.push({pts,depth:zsum/pts.length,j});
    }
    const faces=[];
    for(let j=0;j<lines.length-1;j++)for(let i=0;i<78;i++){
      const pts=[lines[j].pts[i],lines[j].pts[i+1],lines[j+1].pts[i+1],lines[j+1].pts[i]];
      const z=pts.reduce((a,p)=>a+p[2],0)/4;
      const light=clamp(.35+z/radius*.3-(pts[0][0]+pts[0][1])/radius*.25);
      faces.push({pts,z,light});
    }
    faces.sort((a,b)=>a.z-b.z);
    for(const f of faces){ctx.beginPath();ctx.moveTo(f.pts[0][0],f.pts[0][1]);for(let j=1;j<4;j++)ctx.lineTo(f.pts[j][0],f.pts[j][1]);ctx.closePath();ctx.fillStyle=rgba(C.copper,alpha*(.025+.15*f.light*f.light));ctx.fill();}
    lines.sort((a,b)=>a.depth-b.depth);
    for (const line of lines) {
      const lit = clamp((line.depth/radius+1)/2);
      stroke(ctx,line.pts,line.j%7===0?C.cool:C.warm,.42+lit*.3,alpha*(.15+.57*lit));
    }
    for (let j=0;j<12;j++) {
      const u=j/12*TAU,pts=[];
      for(let i=1;i<48;i++) {
        const lat=i/48*Math.PI;
        const fold=Math.sin((3+kind%4)*u+lat*(kind%2?2:1))*Math.pow(Math.sin(lat),1.4);
        const r=radius*(1+.11*fold+.035*Math.cos(7*lat));
        pts.push(project(r*Math.sin(lat)*Math.cos(u)*(1+.09*Math.sin(kind)),r*Math.cos(lat)*(1+.16*Math.cos(kind*1.4)),r*Math.sin(lat)*Math.sin(u)*(.78+.2*opening),ax,ay,-.18));
      }
      stroke(ctx,pts,C.copper,.4,alpha*.18);
    }
  }
  const sculptureCaches = new Map();
  function sculpture(ctx, kind, radius, time, alpha, opening = 1) {
    const key = kind + ':' + radius;
    if (!sculptureCaches.has(key)) {
      const c = typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(320,320) : document.createElement('canvas');
      c.width=320;c.height=320;const cc=c.getContext('2d');cc.scale(2,2);cc.translate(80,80);
      renderSculpture(cc,kind,radius,0,1,1);sculptureCaches.set(key,c);
    }
    ctx.save();ctx.globalAlpha*=alpha;ctx.scale(1,.94+.06*opening);
    ctx.drawImage(sculptureCaches.get(key),-80,-80,160,160);ctx.restore();
  }
  function tendril(ctx, target, kind, amount, alpha) {
    const side=kind%2?1:-1;
    for(let k=0;k<4;k++) {
      const pts=[];
      for(let j=0;j<=80;j++) {
        const q=j/80, e=smooth(q);
        const bend=Math.sin(Math.PI*q)*(28*side+(k-1.5)*3);
        pts.push([mix(0,target[0],e)+bend*.5,mix(0,target[1],e)+bend]);
      }
      stroke(ctx,pts,k===0?C.cool:C.warm,.48,alpha*(k===0?.34:.14),amount);
    }
  }
  S.closing = function(ctx,t,duration,env) {
    const p=clamp(t/Math.max(1,duration)), release=ramp(0,Math.min(8,duration*.3),t);
    const targets=Array.from({length:7},(_,i)=>{
      const a=-Math.PI/2+i/7*TAU;
      return [Math.cos(a)*500,Math.sin(a)*247];
    });
    ctx.save();
    halo(ctx,0,12,630,330,C.cool,.03);
    for(let i=0;i<7;i++) {
      const on=ramp(i*.045,.18+i*.045,p), target=targets[i];
      tendril(ctx,target,i,on,.75);
      ctx.save();ctx.translate(...target);
      halo(ctx,0,0,100,100,i===1||i===5?C.cool:C.warm,.035*on);
      sculpture(ctx,i,55+4*Math.sin(i*.9),t,.8*on,release);
      ctx.restore();
    }
    // The initially tight central weave becomes a supple, stable suspended form.
    halo(ctx,0,0,220,150,C.warm,.055);
    ctx.save();ctx.scale(1.4,1.12);
    silkTorus(ctx,t, mix(67,103,release),mix(52,29,release),.76,release);
    for(let k=0;k<16;k++) {
      const pts=[];
      for(let i=0;i<=105;i++) {
        const u=i/105*TAU, rr=53+12*Math.sin(u*3+k*.08)*(1-release*.8)+(k-7.5)*1.2;
        pts.push(project(rr*Math.cos(u),rr*Math.sin(u),Math.sin(u*2+k*.1)*20*(1-release*.8),.95,-.25,-.28));
      }
      stroke(ctx,pts,C.warm,.45,.10);
    }
    ctx.restore();
    // A final still topology: highlight just two choices, never imply all seven are required.
    const chosen=ramp(.56,.72,p);
    for(const i of [0,5]) {
      const pt=targets[i];
      ctx.save();ctx.translate(...pt);ctx.beginPath();ctx.ellipse(0,0,75,75,0,0,TAU);
      ctx.strokeStyle=rgba(C.warm,.16*chosen);ctx.lineWidth=.6;ctx.stroke();ctx.restore();
    }
    ctx.restore();
  };
})();
