/*
 * Gentle relief — procedural illustrations for the continuous world wall.
 * Public API: window.drawIllustration(ctx, id, localSeconds)
 * Transparent artwork, centered at (0, 0), confined to ±390 × ±290.
 * All motion is a pure function of time; every invocation restores ctx state.
 */
(() => {
  'use strict';

  const TAU = Math.PI * 2;
  const C = {
    gold: '#daa27d', copper: '#ac7859', blue: '#496d85', indigo: '#363b68',
    pale: '#efc7a5', ice: '#8aafc2', ink: '#06060e'
  };
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const mix = (a, b, p) => a + (b - a) * p;
  const ease = x => { x = clamp(x); return x * x * (3 - 2 * x); };
  const phase = (t, a, b) => ease((t - a) / (b - a));
  const seeded = n => { const v = Math.sin(n * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };

  function path(ctx, draw, color = C.gold, width = 2.4, alpha = 1) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    draw(ctx);
    ctx.stroke();
    ctx.restore();
  }

  function ring(ctx, x, y, r, color = C.gold, width = 2, alpha = 1, a = 0, b = TAU) {
    path(ctx, p => p.arc(x, y, r, a, b), color, width, alpha);
  }

  function dot(ctx, x, y, r = 3, color = C.gold, alpha = 1) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    ctx.restore();
  }

  // Glows are a few bounded gradients per illustration, never per path.
  function glow(ctx, x, y, r, rgb = '218,162,125', strength = .14) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(${rgb},${strength})`);
    g.addColorStop(.35, `rgba(${rgb},${strength * .48})`);
    g.addColorStop(1, `rgba(${rgb},0)`);
    ctx.fillStyle = g;
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }

  function ellipse(ctx, x, y, rx, ry, angle, color, width = 2, alpha = 1) {
    path(ctx, p => p.ellipse(x, y, rx, ry, angle, 0, TAU), color, width, alpha);
  }

  function intro(ctx, t) {
    const release = phase(t, .3, 5.2);
    glow(ctx, 0, 0, 218, '172,120,89', .1 + release * .04);
    ring(ctx, 0, 0, 232, C.blue, 1.3, .24, -.8, 2.5);
    ring(ctx, 0, 0, 240, C.indigo, 1.3, .2, 2.65, 4.35);
    for (let k = 0; k < 9; k++) {
      const z = k / 8;
      const rx = mix(116 + k * 7, 154 + k * 8, release);
      const ry = mix(74 + k * 8, 100 + k * 9, release);
      const twist = (1 - release) * (1.3 + z * 1.6);
      path(ctx, p => {
        for (let j = 0; j <= 128; j++) {
          const a = j / 128 * TAU;
          const modulation = (1 - release) * (20 * Math.sin(a * 3 + k * .82));
          const xx = Math.cos(a + twist * Math.sin(a * 2)) * (rx + modulation);
          const yy = Math.sin(a) * ry + Math.sin(a * 4 + k) * (1 - release) * 20;
          const x = xx * Math.cos(z * .25) - yy * Math.sin(z * .25);
          const y = xx * Math.sin(z * .25) + yy * Math.cos(z * .25);
          if (!j) p.moveTo(x, y); else p.lineTo(x, y);
        }
      }, k % 3 ? C.copper : C.blue, k % 3 ? 2 : 1.5, .25 + z * .065);
    }
    const a = -.68 + release * .22;
    const x = Math.cos(a) * (178 + release * 31);
    const y = Math.sin(a) * (125 + release * 45);
    glow(ctx, x, y, 30, '218,162,125', .25);
    dot(ctx, x, y, 4, C.pale);
    dot(ctx, -179 - release * 28, 52 + release * 24, 3, C.blue, .8);
  }

  function breath(ctx, t) {
    const clock = clamp(t, 0, 10);
    let r;
    if (clock < 3) r = mix(90, 166, ease(clock / 3));
    else if (clock < 3.7) r = mix(166, 190, ease((clock - 3) / .7));
    else r = mix(190, 90, ease((clock - 3.7) / 6.3));
    glow(ctx, 0, 0, r + 58, '218,162,125', .17);
    ring(ctx, 0, 0, 238, C.blue, 1.3, .24, .12, TAU - .12);
    ring(ctx, 0, 0, r + 20, C.copper, 1.5, .25);
    ring(ctx, 0, 0, r, C.gold, 3.2, .9);
    ring(ctx, 0, 0, r - 17, C.blue, 1.5, .64);
    ring(ctx, 0, 0, r * .68, C.copper, 1.2, .22);
    dot(ctx, 0, 0, 4.2, C.pale, .85);
    for (let i = 0; i < 12; i++) {
      const a = i / 12 * TAU;
      const l = i % 3 === 0 ? 11 : 5;
      path(ctx, p => {
        p.moveTo(Math.cos(a) * 246, Math.sin(a) * 246);
        p.lineTo(Math.cos(a) * (246 + l), Math.sin(a) * (246 + l));
      }, C.blue, 1.4, .38);
    }
    const exhale = phase(clock, 3.7, 9.2);
    for (let i = 0; i < 2; i++) {
      const a = -.7 + i * .38;
      const pr = r + 30 + exhale * 43;
      dot(ctx, Math.cos(a) * pr, Math.sin(a) * pr, 3 - exhale * .5, C.pale, .8 - exhale * .5);
    }
    // One broad arc follows the slower outgoing breath without rotating the scene.
    ring(ctx, 0, 0, r + 9, C.pale, 2, .45, -.2, .8 + exhale * 1.35);
  }

  function cool(ctx, t) {
    // Keep the cooling cue below the nose, on the visible cheek.
    glow(ctx, 26, 53, 113, '73,109,133', .17);
    glow(ctx, 80, 78, 62, '218,162,125', .055);
    const profile = p => {
      p.moveTo(-97, 174);
      p.bezierCurveTo(-91, 126, -119, 92, -127, 19);
      p.bezierCurveTo(-143, -76, -100, -159, -25, -173);
      p.bezierCurveTo(52, -187, 98, -139, 100, -82);
      p.bezierCurveTo(99, -46, 113, -22, 137, 4);
      p.quadraticCurveTo(149, 20, 122, 24);
      p.lineTo(113, 25);
      p.quadraticCurveTo(113, 43, 104, 48);
      p.quadraticCurveTo(117, 61, 106, 69);
      p.bezierCurveTo(105, 95, 78, 113, 39, 108);
      p.quadraticCurveTo(25, 143, 46, 177);
    };
    // One faint, narrow under-stroke keeps the contour legible after compression.
    // The glow is limited to this silhouette; detail paths remain unblurred.
    ctx.save();
    ctx.shadowColor = 'rgba(218,162,125,.16)';
    ctx.shadowBlur = 7;
    path(ctx, profile, C.gold, 5, .12);
    ctx.restore();
    path(ctx, profile, C.gold, 3.15, .96);
    path(ctx, p => {
      p.moveTo(-42, 174); p.quadraticCurveTo(0, 155, 27, 167);
      // A quiet eyelid makes the unobscured face easy to read.
      p.moveTo(66, -40); p.quadraticCurveTo(80, -35, 91, -41);
    }, C.copper, 1.7, .52);
    // A small soft cloth rests on the cheek, clear of the nose and mouth.
    const cloth = p => {
      p.moveTo(-34, 17); p.quadraticCurveTo(20, 5, 76, 24);
      p.bezierCurveTo(83, 44, 85, 68, 75, 88);
      p.quadraticCurveTo(20, 103, -30, 82);
      p.bezierCurveTo(-37, 64, -39, 37, -34, 17);
      p.closePath();
    };
    ctx.save();
    ctx.fillStyle = 'rgba(73,109,133,.14)';
    ctx.beginPath(); cloth(ctx); ctx.fill();
    path(ctx, cloth, C.ice, 2.6, .91);
    path(ctx, p => {
      p.moveTo(-33, 29); p.quadraticCurveTo(21, 18, 78, 37);
      p.moveTo(-31, 71); p.quadraticCurveTo(20, 91, 78, 76);
    }, C.blue, 1.7, .9);
    for (let i = 0; i < 4; i++) {
      const x = -16 + i * 24;
      path(ctx, p => {
        p.moveTo(x, 38 + i * 1.1);
        p.quadraticCurveTo(x - 6, 51 + i * 1.1, x - 2, 65 + i * 1.1);
      }, C.blue, 1.3, .57);
    }
    ctx.restore();
    for (let i = 0; i < 3; i++) {
      const offset = Math.sin(t * 1.25 - i * .65) * 4;
      path(ctx, p => {
        p.moveTo(-170 - i * 23, 11 + offset);
        p.bezierCurveTo(-188 - i * 23, 34 + offset, -188 - i * 23, 69 + offset, -170 - i * 23, 91 + offset);
      }, C.blue, 2 - i * .3, .56 - i * .13);
    }
    dot(ctx, 75, 54, 3, C.ice, .82);
  }

  function ear(ctx, t) {
    glow(ctx, -14, 0, 211, '172,120,89', .1);
    path(ctx, p => {
      p.moveTo(45, 119);
      p.bezierCurveTo(110, 49, 133, -68, 75, -148);
      p.bezierCurveTo(26, -214, -88, -194, -113, -109);
      p.bezierCurveTo(-137, -36, -108, 14, -91, 55);
      p.bezierCurveTo(-76, 93, -81, 127, -52, 153);
      p.bezierCurveTo(-24, 180, 28, 162, 45, 119);
    }, C.gold, 3.2, .94);
    path(ctx, p => {
      p.moveTo(-77, -77);
      p.bezierCurveTo(-87, -154, 16, -173, 59, -119);
      p.bezierCurveTo(88, -81, 72, -21, 42, 23);
      p.bezierCurveTo(27, 44, 15, 65, 16, 92);
    }, C.copper, 2.8, .8);
    path(ctx, p => {
      p.moveTo(-39, -90);
      p.bezierCurveTo(8, -122, 34, -67, 14, -35);
      p.bezierCurveTo(2, -15, -39, -18, -39, 7);
      p.quadraticCurveTo(-39, 34, -12, 42);
      p.quadraticCurveTo(6, 55, -10, 76);
      p.quadraticCurveTo(-34, 100, -42, 77);
    }, C.blue, 2.5, .9);
    path(ctx, p => {
      p.moveTo(30, -129); p.quadraticCurveTo(10, -96, 14, -69);
    }, C.copper, 1.8, .65);
    const touch = .6 + .4 * Math.sin(t * 1.6) ** 2;
    glow(ctx, 12, 133, 46, '218,162,125', .12 * touch);
    ring(ctx, 12, 133, 13 + touch * 3, C.gold, 1.8, .62);
    dot(ctx, 12, 133, 3.5, C.pale, .9);
    // Two light fingertip contours imply gentle touch; no nerve mapping.
    path(ctx, p => {
      p.moveTo(193, 174);
      p.bezierCurveTo(155, 170, 111, 144, 49, 139);
      p.quadraticCurveTo(22, 134, 30, 120);
      p.quadraticCurveTo(37, 109, 63, 114);
      p.lineTo(141, 128);
      p.moveTo(191, 211);
      p.bezierCurveTo(142, 208, 95, 179, 54, 171);
      p.quadraticCurveTo(35, 165, 40, 154);
    }, C.blue, 2.5, .75);
  }

  function hand(ctx, x, y, side, t) {
    const shift = Math.sin(t * 9 + (side < 0 ? .5 : 2)) * 7;
    ctx.save(); ctx.translate(x + shift, y); ctx.scale(side, 1);
    path(ctx, p => {
      p.moveTo(-12, -38); p.lineTo(-17, 4);
      p.quadraticCurveTo(-21, 29, -10, 47);
      p.quadraticCurveTo(1, 65, 10, 57);
      p.lineTo(7, 19);
      p.lineTo(17, 51);
      p.quadraticCurveTo(23, 61, 29, 50);
      p.lineTo(22, 11);
      p.quadraticCurveTo(39, 44, 43, 31);
      p.lineTo(25, -17);
      p.quadraticCurveTo(12, -36, 11, -45);
    }, C.gold, 2.5, .9);
    ctx.restore();
  }

  function shake(ctx, t) {
    glow(ctx, 0, 20, 226, '73,109,133', .08);
    // The head and neck stay still. Motion belongs to shoulders and hands.
    ellipse(ctx, 0, -142, 47, 61, -.02, C.copper, 2.6, .85);
    path(ctx, p => {
      p.moveTo(-31, -91); p.lineTo(-34, -44);
      p.moveTo(31, -91); p.lineTo(34, -44);
    }, C.gold, 2.5, .83);
    const s = Math.sin(t * 9) * 4;
    path(ctx, p => {
      p.moveTo(-34, -44);
      p.bezierCurveTo(-74, -25 + s, -124, -37 + s, -152, 6 + s);
      p.quadraticCurveTo(-179, 56, -188, 99);
      p.moveTo(34, -44);
      p.bezierCurveTo(74, -25 - s, 124, -37 - s, 152, 6 - s);
      p.quadraticCurveTo(179, 56, 188, 99);
      p.moveTo(-103, 17); p.quadraticCurveTo(-98, 110, -104, 189);
      p.moveTo(103, 17); p.quadraticCurveTo(98, 110, 104, 189);
    }, C.gold, 2.7, .9);
    path(ctx, p => {
      p.moveTo(-34, -44); p.quadraticCurveTo(0, -16, 34, -44);
      p.moveTo(-74, 192); p.quadraticCurveTo(0, 204, 74, 192);
    }, C.copper, 1.8, .45);
    hand(ctx, -190, 130, -1, t); hand(ctx, 190, 130, 1, t);
    for (const side of [-1, 1]) for (let k = 0; k < 3; k++) {
      const drift = Math.sin(t * 9 - k * .4) * 4;
      path(ctx, p => {
        p.moveTo(side * (225 + k * 21) + drift, 79 - k * 9);
        p.quadraticCurveTo(side * (249 + k * 22) + drift, 116, side * (232 + k * 21) + drift, 154 + k * 6);
      }, C.blue, 1.8, .6 - k * .14);
    }
  }

  function paper(ctx, t) {
    const squeeze = phase(t, .45, 2.55);
    const drop = phase(t, 2.9, 4.5);
    const cy = mix(-45, 133, drop);
    glow(ctx, 0, 140, 126, '73,109,133', .08);
    // An open wire basket; the back rim is below the floating sheet.
    path(ctx, p => p.ellipse(0, 133, 130, 31, 0, Math.PI, TAU), C.blue, 2.3, .55);
    path(ctx, p => {
      p.moveTo(-129, 134); p.lineTo(-101, 216);
      p.quadraticCurveTo(0, 249, 101, 216); p.lineTo(129, 134);
      p.moveTo(-73, 158); p.lineTo(-62, 223);
      p.moveTo(73, 158); p.lineTo(62, 223);
      p.moveTo(0, 165); p.lineTo(0, 230);
    }, C.blue, 2, .63);
    const box = [[-105,-134],[-36,-134],[36,-134],[105,-134],[105,-45],[105,44],[105,134],[36,134],[-36,134],[-105,134],[-105,44],[-105,-45]];
    const ball = box.map((_, i) => {
      const a = i / box.length * TAU - Math.PI * .75;
      const radius = 52 + seeded(i + 6) * 18;
      return [Math.cos(a) * radius, Math.sin(a) * radius];
    });
    ctx.save(); ctx.translate(0, cy);
    path(ctx, p => {
      box.forEach((v, i) => {
        const x = mix(v[0], ball[i][0], squeeze), y = mix(v[1], ball[i][1], squeeze);
        if (i === 0) p.moveTo(x, y); else p.lineTo(x, y);
      }); p.closePath();
    }, C.gold, 2.9, .93);
    for (let i = 0; i < 8; i++) {
      const y = -92 + i * 25;
      const x1 = mix(-72, (seeded(i * 4 + 81) - .5) * 100, squeeze);
      const y1 = mix(y, (seeded(i * 4 + 82) - .5) * 90, squeeze);
      const x2 = mix(i % 3 === 2 ? 24 : 73, (seeded(i * 4 + 83) - .5) * 105, squeeze);
      const y2 = mix(y, (seeded(i * 4 + 84) - .5) * 95, squeeze);
      path(ctx, p => {
        p.moveTo(x1, y1);
        p.lineTo(mix((x1 + x2) / 2, (seeded(i + 101) - .5) * 96, squeeze), mix(y, (seeded(i + 202) - .5) * 98, squeeze));
        p.lineTo(x2, y2);
      }, i % 2 ? C.copper : C.blue, 1.5, .58);
    }
    ctx.restore();
    path(ctx, p => p.ellipse(0, 133, 130, 31, 0, 0, Math.PI), C.blue, 2.5, .85);
    const settle = phase(t, 4.1, 4.8) * (1 - phase(t, 4.8, 5.8));
    ring(ctx, 0, 133, 84 + settle * 27, C.gold, 1.2, settle * .2, .1, Math.PI - .1);
  }

  function nature(ctx, t) {
    const reveal = .75 + phase(t, 0, 2) * .25;
    glow(ctx, 0, -7, 221, '73,109,133', .1);
    ring(ctx, 0, -7, 229, C.blue, 1.2, .22, -1.2, 1.05);
    ring(ctx, 0, -7, 229, C.blue, 1.2, .22, 2, 4.15);
    path(ctx, p => {
      p.moveTo(0, 177);
      p.bezierCurveTo(-167, 104, -180, -81, 0, -211);
      p.bezierCurveTo(180, -81, 167, 104, 0, 177);
    }, C.gold, 2.6, .76 * reveal);
    path(ctx, p => {
      p.moveTo(-5, 220); p.bezierCurveTo(4, 103, 2, -92, 0, -211);
    }, C.gold, 2.8, .94);
    const levels = [
      { sy: 139, ex: 83, ey: 74 }, { sy: 99, ex: 116, ey: 17 },
      { sy: 54, ex: 122, ey: -37 }, { sy: 7, ex: 104, ey: -91 },
      { sy: -42, ex: 76, ey: -140 }, { sy: -94, ex: 42, ey: -178 }
    ];
    for (const side of [-1, 1]) levels.forEach((v, k) => {
      const ex = v.ex * side;
      path(ctx, p => {
        p.moveTo(1, v.sy); p.quadraticCurveTo(ex * .64, v.sy - 24, ex, v.ey);
      }, k % 2 ? C.copper : C.blue, 2, (.62 + k * .02) * reveal);
      for (let n = 1; n <= 3; n++) {
        const f = n / 4;
        const bx = ex * f;
        const by = mix(v.sy, v.ey, f) + 10 * Math.sin(f * Math.PI);
        const tx = bx + side * (20 - k * 1.3);
        const ty = by - (24 - k * 1.5);
        path(ctx, p => { p.moveTo(bx, by); p.quadraticCurveTo(tx - side * 9, by - 8, tx, ty); }, C.copper, 1.3, .47 * reveal);
        path(ctx, p => {
          p.moveTo(mix(bx, tx, .55), mix(by, ty, .55));
          p.lineTo(mix(bx, tx, .55) + side * 9, mix(by, ty, .55) - 2);
        }, C.blue, 1.1, .36 * reveal);
      }
      dot(ctx, ex, v.ey, k % 2 ? 2 : 2.4, k % 2 ? C.blue : C.gold, .7);
    });
    dot(ctx, 0, -211, 3.7, C.pale, .9);
  }

  function book(ctx, x, y, angle, color = C.gold) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(angle);
    path(ctx, p => {
      p.moveTo(-66, -86); p.lineTo(61, -86); p.quadraticCurveTo(68, -86, 68, -79);
      p.lineTo(68, 80); p.lineTo(-63, 80); p.quadraticCurveTo(-74, 76, -74, 67);
      p.lineTo(-74, -72); p.quadraticCurveTo(-74, -86, -66, -86);
      p.moveTo(-58, -85); p.lineTo(-58, 77);
      p.moveTo(-69, 65); p.lineTo(67, 65);
    }, color, 2.5, .9);
    path(ctx, p => { p.moveTo(-35, -43); p.lineTo(39, -43); p.moveTo(-35, -32); p.lineTo(11, -32); }, C.copper, 1.6, .5);
    ctx.restore();
  }

  function order(ctx, t) {
    const p = phase(t, .5, 3.8);
    glow(ctx, 0, 20, 264, '73,109,133', .06);
    path(ctx, c => {
      c.moveTo(-306, 144); c.lineTo(-255, -160); c.lineTo(251, -160); c.lineTo(307, 144); c.closePath();
      c.moveTo(-306, 144); c.lineTo(-306, 159); c.lineTo(307, 159); c.lineTo(307, 144);
    }, C.blue, 2, .58);
    ctx.save();
    ctx.translate(mix(5, -137, p), mix(25, -12, p)); ctx.rotate(mix(.4, -.04, p));
    path(ctx, c => { c.rect(-77, -92, 154, 184); }, C.blue, 1.5, .55);
    ctx.restore();
    book(ctx, mix(-141, -136, p), mix(2, -14, p), mix(-.31, -.04, p));
    ctx.save(); ctx.translate(mix(55, 163, p), mix(-65, -60, p));
    ellipse(ctx, 0, 0, 42, 39, 0, C.gold, 2.7, .9);
    ellipse(ctx, 0, 0, 31, 28, 0, C.copper, 1.5, .58);
    path(ctx, c => { c.moveTo(40, -13); c.bezierCurveTo(72, -18, 72, 20, 40, 17); }, C.gold, 2.5, .9);
    ctx.restore();
    ctx.save(); ctx.translate(mix(73, 139, p), mix(59, 74, p)); ctx.rotate(mix(-.68, 0, p));
    path(ctx, c => {
      c.moveTo(-76, -5); c.lineTo(60, -5); c.lineTo(76, 0); c.lineTo(60, 5); c.lineTo(-76, 5); c.closePath();
      c.moveTo(60, -5); c.lineTo(60, 5); c.moveTo(-65, -5); c.lineTo(-65, 5);
    }, C.gold, 2.2, .9);
    ctx.restore();
    const aligned = phase(t, 3.25, 4.35);
    path(ctx, c => { c.moveTo(-220, 102); c.lineTo(-59, 102); }, C.gold, 1.1, aligned * .35);
    dot(ctx, 261, -160, 3, C.pale, .5 + aligned * .35);
  }

  function outro(ctx, t) {
    const open = phase(t, 0, 3.5);
    glow(ctx, 0, 0, 237, '172,120,89', .14);
    for (let i = 0; i < 5; i++) {
      const rx = 155 + i * 13 + open * 8;
      const ry = 128 + i * 15 + open * 8;
      ellipse(ctx, 0, 0, rx, ry, -.12, i === 2 ? C.gold : (i % 2 ? C.blue : C.copper), i === 2 ? 2.8 : 1.5, i === 2 ? .8 : .25);
    }
    const a = -.53;
    const x = Math.cos(a) * (181 + open * 8), y = Math.sin(a) * (158 + open * 8);
    glow(ctx, x, y, 40, '218,162,125', .25);
    dot(ctx, x, y, 4, C.pale, .95);
    dot(ctx, 0, 0, 3, C.gold, .6);
    ring(ctx, 0, 0, 238, C.blue, 1.2, .24, .24, 2.65);
  }

  const illustrations = { intro, breath, cool, ear, shake, paper, nature, order, outro };
  window.drawIllustration = function drawIllustration(ctx, id, t = 0) {
    const fn = illustrations[id];
    if (!fn) return;
    ctx.save();
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    fn(ctx, Math.max(0, Number.isFinite(t) ? t : 0));
    ctx.restore();
  };
})();
