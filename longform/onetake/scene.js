import * as T from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const D=window.FILM_DATA, TL=D.timeline, CH=TL.chapters, DUR=TL.duration;
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const mix=(a,b,p)=>a+(b-a)*p;
// Minimum-jerk interpolation: position, velocity and acceleration agree at joins.
const mj=x=>{x=clamp(x);return x*x*x*(10+x*(-15+6*x));};
const at=(t,a,b)=>mj((t-a)/(b-a));
const bell=(t,a,b)=>Math.sin(Math.PI*clamp((t-a)/(b-a)))**2;
const v=(x=0,y=0,z=0)=>new T.Vector3(x,y,z);
const hash=x=>{const q=Math.sin(x*127.1+311.7)*43758.5453;return q-Math.floor(q);};
const spring=(t,start,duration=1.1)=>{const x=mj((t-start)/duration),f=z=>1-Math.exp(-7*z)*(Math.cos(9*z)+7/9*Math.sin(9*z));return f(x)/f(1);};
const pointLerp=(a,b,p)=>v(mix(a.x,b.x,p),mix(a.y,b.y,p),mix(a.z,b.z,p));
const stage=document.getElementById('stage'), hud=document.getElementById('hud');
const renderer=new T.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true,powerPreference:'high-performance'});
renderer.setPixelRatio(window.devicePixelRatio||1);renderer.setSize(1920,1080,false);
renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=.82;
renderer.setClearColor(0x06060e,1);stage.insertBefore(renderer.domElement,hud);
const scene=new T.Scene();scene.background=new T.Color(0x06060e);scene.fog=new T.FogExp2(0x06060e,.006);
const camera=new T.PerspectiveCamera(34,16/9,.1,350);
const ambient=new T.HemisphereLight(0xc8dbef,0x17121d,.26);scene.add(ambient);
const key=new T.DirectionalLight(0xffe6cd,2.5);scene.add(key,key.target);
const rim=new T.DirectionalLight(0x749fca,2.6);scene.add(rim,rim.target);
const fill=new T.PointLight(0xdab38a,12,30,2);scene.add(fill);
const mat={
 gold:new T.MeshPhysicalMaterial({color:0xcaa57b,metalness:.82,roughness:.23,clearcoat:.6,clearcoatRoughness:.18}),
 ivory:new T.MeshPhysicalMaterial({color:0x8c9a9f,metalness:.18,roughness:.27,clearcoat:.55,clearcoatRoughness:.22}),
 pearl:new T.MeshPhysicalMaterial({color:0x9aafb9,metalness:.32,roughness:.24,clearcoat:1,iridescence:.22,iridescenceIOR:1.3}),
 blue:new T.MeshPhysicalMaterial({color:0x587f96,metalness:.35,roughness:.28,clearcoat:.8}),
 dark:new T.MeshStandardMaterial({color:0x131925,metalness:.4,roughness:.46}),
 paper:new T.MeshPhysicalMaterial({color:0xdacdb5,metalness:0,roughness:.76,side:T.DoubleSide}),
 glass:new T.MeshPhysicalMaterial({color:0x7794aa,metalness:.18,roughness:.2,transparent:true,opacity:.24,side:T.DoubleSide,depthWrite:false}),
 rose:new T.MeshPhysicalMaterial({color:0xab8173,metalness:.4,roughness:.3,clearcoat:.6}),
 light:new T.MeshBasicMaterial({color:0xf1c69b}),
 faint:new T.MeshBasicMaterial({color:0x6586a3,transparent:true,opacity:.21,depthWrite:false}),
};
const modelGroups=[];
function group(parent=scene){const g=new T.Group();parent.add(g);return g;}
function sphere(parent,r,m=mat.ivory,x=0,y=0,z=0){const q=new T.Mesh(new T.SphereGeometry(r,32,24),m);q.position.set(x,y,z);parent.add(q);return q;}
function box(parent,w,h,d,m=mat.ivory,r=.08){const q=new T.Mesh(new RoundedBoxGeometry(w,h,d,3,r),m);parent.add(q);return q;}
function curve(points,closed=false){return new T.CatmullRomCurve3(points.map(p=>Array.isArray(p)?v(...p):p),closed,'centripetal',.5);}
function tube(parent,points,r=.025,m=mat.gold,closed=false,segments=120){const c=points instanceof T.Curve?points:curve(points,closed);const q=new T.Mesh(new T.TubeGeometry(c,segments,r,8,closed),m);parent.add(q);return q;}
function ring(parent,r,t=.018,m=mat.gold,x=0,y=0,z=0){const q=new T.Mesh(new T.TorusGeometry(r,t,8,128),m);q.position.set(x,y,z);parent.add(q);return q;}
function softGlow(parent,color=0x507fa8,size=4){
 const m=new T.ShaderMaterial({transparent:true,depthWrite:false,blending:T.AdditiveBlending,uniforms:{color:{value:new T.Color(color)}},vertexShader:'varying vec2 uv0;void main(){uv0=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'varying vec2 uv0;uniform vec3 color;void main(){float d=length(uv0-.5)*2.;float a=exp(-d*d*5.)*.085;gl_FragColor=vec4(color,a);}' });
 const q=new T.Mesh(new T.PlaneGeometry(size,size),m);parent.add(q);return q;
}
function contact(parent,w=2,h=.8){const q=softGlow(parent,0x080d16,1);q.material.blending=T.NormalBlending;q.material.fragmentShader='varying vec2 uv0;uniform vec3 color;void main(){float d=length(uv0-.5)*2.;gl_FragColor=vec4(vec3(0.),exp(-d*d*4.)*.6);}';q.scale.set(w,h,1);q.position.z=-.12;return q;}
function shapeMesh(parent,points,depth=.16,m=mat.ivory,bevel=.09){const s=new T.Shape();s.moveTo(points[0][0],points[0][1]);for(let i=1;i<points.length;i++)s.lineTo(points[i][0],points[i][1]);s.closePath();const g=new T.ExtrudeGeometry(s,{depth,bevelEnabled:true,bevelSegments:4,steps:1,bevelSize:bevel,bevelThickness:bevel,curveSegments:32});const q=new T.Mesh(g,m);parent.add(q);return q;}
function svgCurve(points,closed=true){return curve(points.map(p=>[p[0],p[1],p[2]||0]),closed);}
const centers=[v(0,0,0),v(0,0,0),v(18,.4,-2),v(38,.5,-5),v(57,0,-3),v(77,0,-1),v(97,-.3,1),v(117,.2,-2),v(138,-.3,-4),v(154,.8,-10)];
const chapterIndex=new Map(CH.map((c,i)=>[c.id,i]));
const transitions=CH.slice(1).map((c,i)=>({from:i,to:i+1,start:c.start-(c.id==='title'?2.2:2.7),end:c.start+1.05}));
function pose(t){
 let idx=0;
 for(const tr of transitions){if(t<tr.start)break;if(t<tr.end)return {a:tr.from,b:tr.to,p:at(t,tr.start,tr.end),moving:true,tr};idx=tr.to;}
 return {a:idx,b:idx,p:0,moving:false};
}
function centerAt(t){const s=pose(t),a=centers[s.a],b=centers[s.b],p=s.p;const q=pointLerp(a,b,p);if(s.a!==s.b&&s.b!==1){q.y+=Math.sin(Math.PI*p)*.5;q.z+=Math.sin(Math.PI*p)*1.7;}return q;}
function chapterAt(t){let i=0;for(let k=1;k<CH.length;k++)if(t>=CH[k].start-1e-8)i=k;return CH[i];}
function focusOffset(id,t){
 if(id==='breath')return v(1.55*(at(t,56.9,61)-at(t,84,90)),.25*(at(t,56.9,61)-at(t,84,90)),-2.6*(at(t,56.9,61)-at(t,84,90)));
 if(id==='cold')return v(.7*(at(t,104.7,108.3)-at(t,127.6,130.8)),0,0);
 if(id==='fractal')return v(.7*(at(t,293,297)-at(t,313,318)),.1,-2*(at(t,293,297)-at(t,313,318)));
 return v();
}
function cameraAt(t){
 const lead=t+.18,st=pose(lead),p=centerAt(lead),a=focusOffset(CH[st.a].id,lead),b=focusOffset(CH[st.b].id,lead),o=pointLerp(a,b,st.p);
 const target=v(p.x+o.x,p.y+.15+o.y,p.z);
 let distance=16+o.z;if(st.a===1||st.b===1)distance+=1.0*(st.a===1?1-st.p:st.p);
 const impact=t-246.323188406;const recoil=impact>=0&&impact<.8?.035*Math.exp(-6*impact)*Math.sin(23*impact):0;
 const xlean=st.moving?.20*Math.sin(Math.PI*st.p):0;
 return {position:v(target.x+.22+xlean,target.y+.65+recoil,target.z+distance),target};
}

// One wall and its microscopic marks remain in the same world for the whole take.
const wall=new T.Mesh(new T.PlaneGeometry(190,16),new T.MeshBasicMaterial({color:0x06060e,toneMapped:false}));wall.position.set(77,0,-26);scene.add(wall);
const rail=tube(scene,centers.slice(2,9).map(p=>v(p.x,p.y-4.5,p.z-1.2)),.012,mat.faint,false,360);
for(let i=0;i<45;i++){const x=-6+i*3.8;const q=ring(scene,.028,.007,mat.faint,x,-4.5,-5.6);}
const dustPositions=new Float32Array(600*3);for(let i=0;i<600;i++){dustPositions[i*3]=-10+hash(i+5)*180;dustPositions[i*3+1]=(hash(i+901)-.5)*13;dustPositions[i*3+2]=-5+hash(i+811)*4;}
const dg=new T.BufferGeometry();dg.setAttribute('position',new T.BufferAttribute(dustPositions,3));scene.add(new T.Points(dg,new T.PointsMaterial({color:0x66849c,size:.022,sizeAttenuation:true,transparent:true,opacity:.32,depthWrite:false})));

// A single, closed, indexed tube is reshaped throughout the film. Its material never fades out.
const N=512,R=8;
function sample(fn){const a=new Float32Array(N*3);for(let i=0;i<N;i++){const p=fn(i/N);a.set([p.x,p.y,p.z],i*3);}return a;}
function sampleCurve(points){const c=svgCurve(points,true);return sample(u=>c.getPointAt(u));}
const facePoints=[[-.7,-2.65],[-.83,-1.85],[-1.43,-.85],[-1.58,.4],[-1.32,1.75],[-.55,2.6],[.64,2.5],[1.22,1.67],[1.28,.78],[1.72,.2],[1.35,.06],[1.32,-.25],[1.42,-.52],[1.19,-.75],[.88,-.81],[.49,-1.45],[.48,-2.65]];
const earPoints=[[-.52,-2.5],[-1.05,-1.62],[-1.28,-.15],[-1.22,1.41],[-.55,2.4],[.64,2.45],[1.26,1.65],[1.38,.6],[1.1,-.31],[.58,-.95],[.54,-1.87],[.08,-2.48]];
const bodyOutline=[[-.45,2.45],[-.82,1.6],[-1.8,1.16],[-2.15,.3],[-2.38,-1.12],[-2.17,-2.28],[-1.8,-2.2],[-1.54,-.2],[-1.17,-.8],[-1.07,-2.65],[1.07,-2.65],[1.17,-.8],[1.54,-.2],[1.8,-2.2],[2.17,-2.28],[2.38,-1.12],[2.15,.3],[1.8,1.16],[.82,1.6],[.45,2.45]];
const shapes=[
 sample(u=>{const a=u*Math.PI*2;return v((2.3+.5*Math.cos(5*a))*Math.sin(3*a),(1.9+.35*Math.cos(3*a))*Math.cos(2*a),.7*Math.sin(5*a));}),
 sample(u=>{const a=u*Math.PI*2;return v(3.65*Math.cos(a),2.58*Math.sin(a),.22*Math.sin(2*a));}),
 sample(u=>{const a=u*Math.PI*2;return v(Math.sign(Math.cos(a))*(.3+2.25*Math.abs(Math.cos(a))**.72),2.38*Math.sin(a),.15*Math.sin(2*a));}),
 sampleCurve(facePoints),sampleCurve(earPoints),sampleCurve(bodyOutline),
 sampleCurve([[-2.65,-1.75],[-2.65,1.75],[2.65,1.75],[2.65,-1.75]]),
 sample(u=>{const a=u*Math.PI*2,x=3.3*Math.cos(a),y=1.6*Math.sin(a)*(.75+.25*Math.cos(a));return v(x,y+.16*Math.sin(a*2),.22*Math.sin(a)**2);}),
 sampleCurve([[-3.3,-1.85],[-3.3,1.85],[3.3,1.85],[3.3,-1.85]]),
 sample(u=>{const a=u*Math.PI*2;return v(2.3*Math.cos(a),1.7*Math.sin(a),.34*Math.sin(2*a));})
];
function roundedContour(w,h,r){const c=new T.Shape();c.moveTo(w/2-r,h/2);c.lineTo(-w/2+r,h/2);c.quadraticCurveTo(-w/2,h/2,-w/2,h/2-r);c.lineTo(-w/2,-h/2+r);c.quadraticCurveTo(-w/2,-h/2,-w/2+r,-h/2);c.lineTo(w/2-r,-h/2);c.quadraticCurveTo(w/2,-h/2,w/2,-h/2+r);c.lineTo(w/2,h/2-r);c.quadraticCurveTo(w/2,h/2,w/2-r,h/2);return sample(u=>{const p=c.getPointAt(u);return v(p.x,p.y,0);});}
shapes[2]=sampleCurve([[.075,2.64],[.075,1.65],[.61,.93],[1.18,.08],[1.76,-1.12],[1.46,-.98],[.95,-.04],[.46,.98],[0,1.47],[-.46,.98],[-.95,-.04],[-1.46,-.98],[-1.76,-1.12],[-1.18,.08],[-.61,.93],[-.075,1.65],[-.075,2.64]]);
shapes[6]=roundedContour(5.3,3.62,.15);shapes[8]=roundedContour(6.6,3.7,.13);
for(let i=0;i<N;i++){const k=i*3,y=shapes[8][k+1];shapes[8][k+1]=y*Math.cos(.51);shapes[8][k+2]=y*Math.sin(.51)+.04;}
const heroGeometry=new T.BufferGeometry();const heroP=new Float32Array(N*R*3),heroN=new Float32Array(N*R*3),heroUV=new Float32Array(N*R*2),heroIndices=[];
for(let i=0;i<N;i++)for(let j=0;j<R;j++){heroUV.set([i/N,j/R],(i*R+j)*2);const a=i*R+j,b=((i+1)%N)*R+j,c=((i+1)%N)*R+(j+1)%R,d=i*R+(j+1)%R;heroIndices.push(a,b,d,b,c,d);}
heroGeometry.setAttribute('position',new T.BufferAttribute(heroP,3));heroGeometry.setAttribute('normal',new T.BufferAttribute(heroN,3));heroGeometry.setAttribute('uv',new T.BufferAttribute(heroUV,2));heroGeometry.setIndex(heroIndices);
function actualSheetContour(){
 paperMesh.updateWorldMatrix(true,false);const arr=paperGeometry.attributes.position.array,points=[],left=33*45;
 const ids=[];for(let c=30;c>=0;c--)ids.push(left+c);for(let c=31;c>=0;c--)ids.push(c);for(let r=1;r<=44;r++)ids.push(r*33);for(let c=1;c<=32;c++)ids.push(44*33+c);for(let c=1;c<=32;c++)ids.push(left+44*33+c);for(let r=43;r>=0;r--)ids.push(left+r*33+32);ids.push(left+31);
 for(const id of ids)points.push(v(arr[id*3],arr[id*3+1],arr[id*3+2]+.015).applyMatrix4(paperMesh.matrixWorld));
 points.push(points[0].clone());const lengths=[0];for(let i=1;i<points.length;i++)lengths.push(lengths.at(-1)+points[i].distanceTo(points[i-1]));const total=lengths.at(-1),result=new Float32Array(N*3);let j=1;
 for(let i=0;i<N;i++){const d=i/N*total;while(j<lengths.length-1&&lengths[j]<d)j++;const f=(d-lengths[j-1])/Math.max(1e-8,lengths[j]-lengths[j-1]),a=points[j-1],b=points[j];result.set([mix(a.x,b.x,f),mix(a.y,b.y,f),mix(a.z,b.z,f)],i*3);}return result;
}
const hero=new T.Mesh(heroGeometry,mat.gold);hero.frustumCulled=false;scene.add(hero);
const heroPoints=new Float32Array(N*3);
const bead=sphere(scene,.105,mat.light);const beadGlow=softGlow(scene,0xe3b17d,1.15);
function breathingScale(t){
 if(t<33.6333)return 1;
 if(t<36.7333)return 1+.12*at(t,33.6333,36.7333);
 if(t<39.2333)return 1.12+.055*at(t,36.7333,38.1667);
 if(t<48.7333)return mix(1.175,.98,at(t,39.2333,48.7333));
 return 1+.024*Math.sin((t-48.7333)*Math.PI/3.5);
}
function updateHero(t){
 const s=pose(t),p=s.p,c=centerAt(t),A=shapes[s.a],B=shapes[s.b];
 const breathe=mix(CH[s.a].id==='breath'?breathingScale(t):1,CH[s.b].id==='breath'?breathingScale(t):1,p);
 const tension=1-at(t,9,19);const sheetWeight=(s.a===6||s.a===7?1-p:0)+(s.b===6||s.b===7?p:0),sheet=sheetWeight>0?actualSheetContour():null;const sheetOffset=s.a===7&&s.b===8?c.clone().sub(centers[7]):v();
 for(let i=0;i<N;i++){
  const k=i*3;let x=mix(A[k],B[k],p),y=mix(A[k+1],B[k+1],p),z=mix(A[k+2],B[k+2],p);
  if(s.a===0&&s.b===0){x+=Math.sin(t*5+i*.11)*.028*tension;y+=Math.cos(t*4.4+i*.09)*.022*tension;}
  if(s.a===5&&s.b===5){const q=bell(t,190,211);x+=Math.sign(x)*Math.sin(t*10.5)*.08*q*clamp((1.7-y)/2.5);}
  const coldWeight=(s.a===3?1-p:0)+(s.b===3?p:0),earWeight=(s.a===4?1-p:0)+(s.b===4?p:0),bodyWeight=(s.a===5?1-p:0)+(s.b===5?p:0);x-=.65*(at(t,104.8,108.2)*(1-at(t,127.5,131.2)))*coldWeight;z+=.19*earWeight+.14*bodyWeight;const finish=s.a===9?mix(1,.65,at(t,393.5,398.2)):1;heroPoints[k]=x*breathe*finish;heroPoints[k+1]=y*breathe*finish;heroPoints[k+2]=z;if(sheet){heroPoints[k]=mix(heroPoints[k],sheet[k]+sheetOffset.x-c.x,sheetWeight);heroPoints[k+1]=mix(heroPoints[k+1],sheet[k+1]+sheetOffset.y-c.y,sheetWeight);heroPoints[k+2]=mix(heroPoints[k+2],sheet[k+2]+sheetOffset.z-c.z,sheetWeight);}
 }
 for(let i=0;i<N;i++){
  const k=i*3,prev=((i+N-1)%N)*3,next=((i+1)%N)*3;let tx=heroPoints[next]-heroPoints[prev],ty=heroPoints[next+1]-heroPoints[prev+1],tz=heroPoints[next+2]-heroPoints[prev+2];const len=Math.hypot(tx,ty,tz);tx/=len;ty/=len;tz/=len;
  let nx=-ty,ny=tx,nz=0;const nl=Math.hypot(nx,ny)||1;nx/=nl;ny/=nl;let bx=ty*nz-tz*ny,by=tz*nx-tx*nz,bz=tx*ny-ty*nx;
  for(let j=0;j<R;j++){const a=j/R*Math.PI*2,co=Math.cos(a),si=Math.sin(a),xx=nx*co+bx*si,yy=ny*co+by*si,zz=nz*co+bz*si;const q=(i*R+j)*3;heroP[q]=heroPoints[k]+xx*.035;heroP[q+1]=heroPoints[k+1]+yy*.035;heroP[q+2]=heroPoints[k+2]+zz*.035;heroN[q]=xx;heroN[q+1]=yy;heroN[q+2]=zz;}
 }
 heroGeometry.attributes.position.needsUpdate=true;heroGeometry.attributes.normal.needsUpdate=true;hero.position.copy(c);
 const bi=Math.floor(((t*.032+.13)%1)*N)*3;bead.position.set(c.x+heroPoints[bi],c.y+heroPoints[bi+1],c.z+heroPoints[bi+2]);beadGlow.position.copy(bead.position);beadGlow.position.z+=.02;
}
function station(id){const g=group();const index=chapterIndex.get(id);g.position.copy(centers[index]);modelGroups.push({id,index,group:g});return g;}

// BREATH — thin luminous bronchi, satin membranes, and pearl-like alveolar clusters.
const lungs=station('breath'), lungBody=group(lungs), alveoli=group(lungs);alveoli.position.set(3.25,.05,.65);
const lobes=[];
for(const side of [-1,1]){
 const q=sphere(lungBody,1,mat.glass,side*1.25,-.05,-.08);q.scale.set(1.13,2.07,.55);q.rotation.z=side*-.11;lobes.push(q);
 const roots=Array.from({length:5},(_,j)=>v(side*(.38+j*.16),1.2-j*.54,.18));tube(lungBody,[v(0,2.6,.15),v(0,1.8,.18),...roots,v(side*1.3,-1.8,.18)],.062,mat.ivory);
 function branch(a,angle,len,depth,seed){const b=v(a.x+Math.cos(angle)*len,a.y+Math.sin(angle)*len,.18+hash(seed)*.22);const ex=(b.x-side*1.25)/1.03,ey=(b.y+.05)/1.92,q=ex*ex+ey*ey;if(q>.88){const f=Math.sqrt(.88/q);b.x=side*1.25+(b.x-side*1.25)*f;b.y=-.05+(b.y+.05)*f;}tube(lungBody,[a,pointLerp(a,b,.46).add(v(0,.06,.04)),b],.011+depth*.007,depth>1?mat.gold:mat.blue,false,18);if(depth>0){branch(b,angle+.52,len*.62,depth-1,seed+13);branch(b,angle-.55,len*.60,depth-1,seed+27);}}
 for(let j=0;j<5;j++)branch(roots[j],side===1?-.55-j*.18:Math.PI+.55+j*.18,.77,3,j+side*43);
}
const alveolarCells=[];
for(let i=0;i<39;i++){
 const a=i*2.399963,y=1-2*(i+.5)/39,r=Math.sqrt(1-y*y),p=v(Math.cos(a)*r*1.37,y*1.35,Math.sin(a)*r*.6);const q=sphere(alveoli,.29+hash(i+11)*.10,mat.pearl,p.x,p.y,p.z);alveolarCells.push(q);
 if(i%3===0){const fine=ring(q,1.008,.012,mat.gold);fine.rotation.x=.5+hash(i)*1.2;fine.scale.setScalar(q.geometry.parameters.radius);}
}
tube(lungs,[[1.3,.5,.3],[2.15,.35,.4],[2.9,.1,.65]],.05,mat.gold);
const airParticles=[];for(let i=0;i<22;i++)airParticles.push(sphere(lungBody,.027,i%2?mat.light:mat.blue));

// COOL TOUCH — a porcelain profile and a woven blue cloth, with an explicit experimental graph.
const cold=station('cold'),faceGroup=group(cold);
const faceCurve=svgCurve(facePoints,true),facePoly=faceCurve.getPoints(120).map(p=>[p.x,p.y]);
const profile=shapeMesh(faceGroup,facePoly,.16,mat.ivory,.07);profile.position.z=-.25;
const faceInset=tube(faceGroup,faceCurve,.018,mat.gold,true,160);faceInset.position.z=.02;
tube(faceGroup,[[.89,1.06,.08],[1.05,.99,.1],[1.15,1.01,.08]],.022,mat.dark);
const clothGeometry=new T.PlaneGeometry(1.35,.87,26,18);const clothBase=clothGeometry.attributes.position.array.slice();
const clothMat=mat.blue.clone();clothMat.roughness=.8;clothMat.onBeforeCompile=shader=>{shader.vertexShader='varying vec2 weaveUv;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nweaveUv=uv;');shader.fragmentShader='varying vec2 weaveUv;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\nfloat weave=sin(weaveUv.x*280.)*sin(weaveUv.y*200.);diffuseColor.rgb*=.97+.035*weave;');};
const cloth=new T.Mesh(clothGeometry,clothMat);cloth.position.set(.67,-.6,.32);faceGroup.add(cloth);
const waterRings=[];for(let i=0;i<4;i++){const q=ring(cold,1.5+i*.3,.012,i%2?mat.blue:mat.faint,-.05,-.6,-.45);q.rotation.x=.28;waterRings.push(q);}
const pathway=group(cold);
tube(pathway,[[.9,-.25,.25],[1.65,.35,.65],[2.3,.85,.45],[2.68,.23,.5],[3.4,-.5,.25]],.025,mat.gold);
const stem=sphere(pathway,.28,mat.blue,2.3,.8,.4);stem.scale.set(.7,1.8,.7);
const heartShape=new T.Shape();heartShape.moveTo(0,-.85);heartShape.bezierCurveTo(-1,.0,-.98,.82,-.48,.82);heartShape.bezierCurveTo(-.2,.84,-.07,.64,0,.5);heartShape.bezierCurveTo(.07,.64,.2,.84,.48,.82);heartShape.bezierCurveTo(.98,.82,1,.0,0,-.85);
const heart=new T.Mesh(new T.ExtrudeGeometry(heartShape,{depth:.24,bevelEnabled:true,bevelSize:.12,bevelThickness:.12,bevelSegments:5,steps:1,curveSegments:30}),mat.rose);heart.position.set(3.55,-.6,.1);pathway.add(heart);
tube(pathway,[[3.34,.17,.2],[3.3,.7,.2],[3.7,.78,.18],[3.8,.36,.2]],.09,mat.blue);
const nerveBeads=[sphere(pathway,.06,mat.light),sphere(pathway,.06,mat.blue)];

// TOUCH — sculpted ear folds; fingertips approach and leave continuously.
const ear=station('ear');
const outerEar=tube(ear,svgCurve(earPoints,true),.18,mat.ivory,true,180);outerEar.position.z=-.13;
const innerEar=tube(ear,[[-.55,-1.6,.12],[-.85,-.55,.19],[-.75,.9,.2],[-.2,1.75,.15],[.57,1.68,.2],[.78,.7,.28],[.4,.15,.4],[-.11,-.3,.37],[.05,-.91,.3]],.16,mat.ivory,false,140);
tube(ear,[[-.25,1.7,.25],[-.14,.81,.36],[.31,.16,.4]],.045,mat.gold,false,80);
const bowl=sphere(ear,.8,mat.glass,.05,-.47,-.1);bowl.scale.set(.87,1.3,.27);
const fingers=group(ear);const finger1=sphere(fingers,.25,mat.ivory,-1.2,-1.77,.5);finger1.scale.set(2.5,.8,.8);const finger2=sphere(fingers,.2,mat.ivory,-1.03,-2.3,.2);finger2.scale.set(2.4,.75,.75);
const touchHalo=ring(ear,.42,.015,mat.blue,-.56,-1.9,.45);
const earNerves=[];for(let i=0;i<12;i++){const a=i/12*Math.PI*2;const p=v(Math.cos(a)*.8,Math.sin(a)*1.8,.32);earNerves.push(sphere(ear,.028,i%3?mat.blue:mat.light,p.x,p.y,p.z));}

// ACTIVITY — a light skeletal gesture instead of a rigid mannequin.
const body=station('shake'),bodyCore=group(body);
const head=sphere(bodyCore,.48,mat.ivory,0,2.48,0);head.scale.set(.85,1.13,.8);
tube(bodyCore,[[0,2.04,0],[0,1.35,0],[0,.1,-.13],[0,-2.4,-.1]],.035,mat.gold);
const arms=[];
for(const side of [-1,1]){
 tube(bodyCore,[[side*.3,1.75,0],[side*.75,1.42,.1],[side*1.5,1.1,.03]],.10,mat.ivory);
 for(let j=0;j<9;j++)tube(bodyCore,[[side*.1,1.02-j*.27,.03],[side*.75,1.06-j*.25,.18],[side*(1.1-j*.018),.68-j*.23,.02]],.014,j%3?mat.ivory:mat.blue,false,32);
 const g=group(bodyCore);g.position.set(side*1.4,1.1,0);const upper=tube(g,[[0,0,0],[side*.24,-.72,.08],[side*.45,-1.45,0]],.10,mat.ivory,false,48);const lower=group(g);lower.position.set(side*.45,-1.45,0);tube(lower,[[0,0,0],[side*.10,-.6,.03],[side*.15,-1.35,.08]],.075,mat.ivory,false,48);sphere(lower,.14,mat.pearl,side*.15,-1.37,.08);arms.push({side,g,lower});
}
const shoulderFibers=[];for(let i=0;i<18;i++){const x=(i/17-.5)*2.2;shoulderFibers.push(tube(bodyCore,[[x*.4,1.55,-.08],[x,1.08,-.1],[x*.8,.3,-.08]],.008,mat.gold,false,22));}

// PAPER and LEAF share a genuinely continuous sheet mesh and the same world-space object.
const paperStation=station('paper'),paperSupport=group(paperStation),paperObject=group(paperSupport);
const leftSheet=new T.PlaneGeometry(2.575,3.5,32,44).translate(-1.2875,0,0),rightSheet=new T.PlaneGeometry(2.575,3.5,32,44).translate(1.2875,0,0);const leftSheetSize=leftSheet.attributes.position.count*3;const paperGeometry=mergeGeometries([leftSheet,rightSheet]),paperBase=paperGeometry.attributes.position.array.slice();
const paperMesh=new T.Mesh(paperGeometry,mat.paper);paperObject.add(paperMesh);paperMesh.frustumCulled=false;
const inkCanvas=document.createElement('canvas');inkCanvas.width=2048;inkCanvas.height=1400;const ink=inkCanvas.getContext('2d');
ink.fillStyle='#d8c9ad';ink.fillRect(0,0,2048,1400);ink.strokeStyle='rgba(86,72,57,.12)';ink.lineWidth=1;for(let j=0;j<1100;j++){const x=hash(j)*2048,y=hash(j+371)*1400;ink.beginPath();ink.moveTo(x,y);ink.lineTo(x+hash(j+7)*35,y+.8);ink.stroke();}ink.fillStyle='#6a5c4d';ink.font='52px "PingFang SC"';ink.fillText('先写下来。',210,340);ink.fillStyle='rgba(91,79,65,.32)';for(let j=0;j<8;j++)ink.fillRect(210,460+j*72,650+hash(j+8)*700,5);
const paperTexture=new T.CanvasTexture(inkCanvas);paperTexture.colorSpace=T.SRGBColorSpace;paperTexture.anisotropy=8;paperMesh.material=mat.paper.clone();paperMesh.material.map=paperTexture;
const paperUniforms={uLeaf:{value:0},uInk:{value:0}};
paperMesh.material.onBeforeCompile=shader=>{Object.assign(shader.uniforms,paperUniforms);shader.fragmentShader='uniform float uLeaf;uniform float uInk;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\nfloat reveal=1.-smoothstep(uInk-.025,uInk+.025,1.-vMapUv.y);diffuseColor.rgb=mix(vec3(.64,.57,.46),diffuseColor.rgb,reveal);vec3 green=vec3(.045,.095,.087)*(1.+.12*sin(vMapUv.x*13.));diffuseColor.rgb=mix(diffuseColor.rgb,green,uLeaf);');};
const basket=group(paperStation);basket.position.set(3.7,-2.1,-.3);ring(basket,.55,.035,mat.gold,0,.5,0).rotation.x=Math.PI/2;ring(basket,.40,.025,mat.blue,0,-.45,0).rotation.x=Math.PI/2;for(let i=0;i<24;i++){const a=i/24*Math.PI*2;tube(basket,[[Math.cos(a)*.4,-.45,Math.sin(a)*.4],[Math.cos(a)*.55,.5,Math.sin(a)*.55]],.012,mat.gold,false,8);}
const secondPaper=box(paperStation,2.25,1.5,.045,mat.paper,.025);secondPaper.position.set(-3,-.6,-.3);
const scrap=group(paperStation);for(let i=0;i<7;i++){const q=box(scrap,.24,.65,.018,mat.paper,.015);q.position.set((hash(i)-.5)*1.4,(hash(i+12)-.5)*1.2,hash(i+31)*.2);q.rotation.z=(hash(i+47)-.5)*2;}
const leafStation=station('fractal'),leafDetail=group(leafStation);
const leafGeometry=new T.PlaneGeometry(6.2,3.6,64,44),leafBase=leafGeometry.attributes.position.array.slice();
const leafMesh=new T.Mesh(leafGeometry,mat.glass.clone());leafMesh.material.color.set(0x738d83);leafMesh.material.opacity=.08;leafDetail.add(leafMesh);
const veins=group(leafDetail);veins.position.z=.24;
tube(veins,[[-3.15,0,.16],[-1.3,.12,.25],[1,.05,.2],[3.16,0,.02]],.028,mat.gold,false,150);
for(let side of [-1,1])for(let j=0;j<12;j++){
 const x=-2.72+j*.44,extent=1.45*Math.sin(Math.PI*(j+.7)/13),end=v(x+.43,side*extent,.16);
 tube(veins,[v(x,0,.17),v(x+.12,side*extent*.5,.25),end],.014,mat.gold,false,40);
 for(let k=0;k<4;k++){const f=(k+1)/5,a=v(x+.43*f,side*extent*f,.18),b=v(x+.43*f+.25,side*(extent*f+.2),.18);tube(veins,[a,b],.006,mat.blue,false,8);}
}
const fern=group(leafStation);fern.position.set(.9,-.2,.34);
function fernBranch(a,angle,len,depth,seed){const b=v(a.x+Math.cos(angle)*len,a.y+Math.sin(angle)*len,a.z+.015);tube(fern,[a,b],.008+depth*.003,depth>1?mat.gold:mat.blue,false,8);if(depth){fernBranch(b,angle+.56,len*.62,depth-1,seed+1);fernBranch(b,angle-.56,len*.62,depth-1,seed+2);}}
fernBranch(v(-2.8,-1.7,0),.56,1.25,6,1);

// ORDER — bevelled objects sit on a tilted, textured work surface.
const deskStation=station('order'),desk=group(deskStation);desk.rotation.x=.51;
const wood=mat.dark.clone();wood.color.set(0x31303a);wood.roughness=.52;
wood.onBeforeCompile=shader=>{shader.vertexShader='varying vec2 grainUv;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\ngrainUv=uv;');shader.fragmentShader='varying vec2 grainUv;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\nfloat grain=sin(grainUv.x*220.+sin(grainUv.y*18.)*2.)*.0025;diffuseColor.rgb+=vec3(grain*.6,grain*.42,grain*.3);');};
const deskTop=box(desk,7.8,4.8,.25,wood,.16);deskTop.position.z=-.22;
for(const y of [-1,1])tube(desk,[[-3.6,y*2.15,-.03],[0,y*2.15,-.03],[3.6,y*2.15,-.03]],.013,mat.gold,false,80);
const books=[];for(let i=0;i<3;i++){const g=group(desk);const pages=box(g,1.45,1.85,.16,mat.paper,.035);box(g,1.53,1.94,.045,i%2?mat.blue:mat.gold,.035).position.z=.10;for(let k=0;k<5;k++)tube(g,[[-.67,-.88,-.05+k*.025],[.67,-.88,-.05+k*.025]],.004,mat.faint,false,8);books.push(g);}
const cup=group(desk);const cupProfile=[[.0,0],[.34,0],[.44,.08],[.47,.78],[.44,.85],[.39,.84],[.40,.12],[.1,.1]].map(p=>new T.Vector2(...p));const cupMesh=new T.Mesh(new T.LatheGeometry(cupProfile,64),mat.ivory);cupMesh.rotation.x=Math.PI/2;cup.add(cupMesh);tube(cup,[[.43,0,.18],[.76,0,.24],[.78,0,.64],[.45,0,.72]],.065,mat.ivory,false,70);const tea=new T.Mesh(new T.CircleGeometry(.39,64),new T.MeshPhysicalMaterial({color:0x7b5138,metalness:.35,roughness:.16}));tea.position.z=.72;cup.add(tea);
const pencils=[];for(let i=0;i<3;i++){const g=group(desk);tube(g,[[0,-.75,.08],[0,.75,.08]],.035,i%2?mat.gold:mat.blue,false,8);sphere(g,.035,mat.ivory,0,.77,.08);pencils.push(g);}
const deskPaper=box(desk,1.3,.9,.02,mat.paper,.02);const bookShadows=books.map(()=>contact(desk,1.7,2.2)),cupShadow=contact(desk,1.25,.95);
const orderBoundary=ring(desk,2.4,.008,mat.faint);orderBoundary.scale.set(1.35,.7,1);orderBoundary.position.z=.04;
const finalMark=group();finalMark.position.copy(centers[9]);scene.add(finalMark);
const finalRings=[];for(let i=0;i<3;i++){const q=ring(finalMark,2.05+i*.15,.012,i%2?mat.blue:mat.gold);q.rotation.x=.15+i*.1;finalRings.push(q);}

// Label positions are projected from the same camera, rather than independent slides.
const labels=[];
function label(text,parent,pos,show){const e=document.createElement('div');e.className='label';e.textContent=text;document.getElementById('labels').appendChild(e);labels.push({e,parent,pos:v(...pos),show});}
label('肺泡',alveoli,[0,-1.95,.2],t=>bell(t,57,92));
label('三叉神经',cold,[1.45,1.85,.3],t=>bell(t,105,129));label('脑干',cold,[2.3,1.45,.3],t=>bell(t,105,129));label('心率',cold,[3.55,-1.95,.3],t=>bell(t,105,129));
label('触觉',ear,[-2.2,-2.45,.3],t=>bell(t,153,185));
label('保留',paperStation,[-3,-1.8,.2],t=>bell(t,257.7,279.7));label('丢弃',paperStation,[2.5,-1.8,.2],t=>bell(t,257.7,279.7));
const recallNames=['呼吸','凉意','触觉','活动','写下','自然','整理'];
modelGroups.forEach((m,j)=>label(recallNames[j],m.group,[0,-3.0,0],t=>at(t,382+j*.35,384.5+j*.35)*(1-at(t,392.8,394.8))));

function paperDeform(t){
 const arr=paperGeometry.attributes.position.array;
 const cr=at(t,244.233333,245.766667),toss=at(t,245.766667,246.323188),restore=at(t,247.0,248.5);
 const crumple=cr*(1-restore),tear=at(t,248.933333,253.433333)*(1-at(t,256,258.8));
 for(let i=0;i<arr.length;i+=3){const x=paperBase[i],y=paperBase[i+1],u=x/5.15+.5,w=y/3.5+.5;
  const az=u*Math.PI*2,pol=w*Math.PI;const n=1+.16*Math.sin(19*u+13*w)*Math.sin(21*w-7*u);const rad=.62*n;
  const opening=at(tear,(1-w)*.65,(1-w)*.65+.35),side=i<leftSheetSize?-1:1;arr[i]=mix(x,rad*Math.sin(pol)*Math.cos(az),crumple)+side*opening*.38;
  arr[i+1]=mix(y,rad*Math.cos(pol),crumple)+Math.sin(x*3.1)*.025*(1-crumple);
  arr[i+2]=mix(.035*Math.sin(x*2+y),rad*Math.sin(pol)*Math.sin(az),crumple)+opening*.15*Math.sin(y*4);
 }
 paperGeometry.attributes.position.needsUpdate=true;paperGeometry.computeVertexNormals();
 const flight=toss*(1-restore);paperObject.position.set(3.7*flight,-1.5*flight+Math.sin(Math.PI*toss)*1.6*(1-restore),.9*flight);paperObject.rotation.set(.06+flight*1.3,flight*.9,.03+flight*2.4);
 // The same paper surface travels to the nature station and becomes a leaf.
 const carry=at(t,279.35,283.15)*(1-at(t,375.5,383));if(carry>0){const delta=centers[7].clone().sub(centers[6]);paperSupport.position.copy(delta.multiplyScalar(carry));paperObject.position.lerp(v(0,0,.08),carry);paperObject.rotation.set(mix(paperObject.rotation.x,0,carry),mix(paperObject.rotation.y,0,carry),mix(paperObject.rotation.z,.02,carry));
  for(let i=0;i<arr.length;i+=3){const x=paperBase[i],y=paperBase[i+1],u=x/2.575,edge=Math.max(.001,1-u*u);arr[i]=mix(x,x*1.23,carry);arr[i+1]=mix(y,y*edge,carry);arr[i+2]=mix(arr[i+2],.18*Math.sin(u*Math.PI)**2+.08*(y/1.75)**2,carry);}
  paperGeometry.attributes.position.needsUpdate=true;paperGeometry.computeVertexNormals();
 }
 const settle=at(t,258,260);paperSupport.scale.setScalar(mix(mix(1,.72,settle),1,carry));paperUniforms.uLeaf.value=carry;paperUniforms.uInk.value=at(t,239.9,243.1);paperSupport.position.x+=1.45*settle*(1-carry);
 secondPaper.scale.setScalar(.001+.999*at(t,257.8,260.2));scrap.scale.setScalar(.001+tear*.75);scrap.position.set(.2,-.1,.3);
}
function updateModels(t){
 for(const m of modelGroups){const start=CH[m.index].start;let g=.001+.999*at(t,start-1.4,start+1.6);m.group.position.copy(centers[m.index]);m.group.rotation.set(0,0,0);m.group.scale.setScalar(g);
  if(t>375.5){const j=m.index-2,progress=at(t,375.5+j*.42,382.6+j*.42),a=-Math.PI/2+j/7*Math.PI*2,target=centers[9].clone().add(v(Math.cos(a)*4.0,Math.sin(a)*2.9,-.1));m.group.position.lerp(target,progress);m.group.position.z+=Math.sin(Math.PI*progress)*2.5;m.group.scale.setScalar(mix(g,.23,progress));m.group.rotation.y=.18*Math.sin(Math.PI*progress);const finish=at(t,393.5,398.2);m.group.position.lerp(centers[9],finish);m.group.scale.multiplyScalar(1-.998*finish);}
 }
 lungBody.scale.setScalar(breathingScale(t));const magnify=at(t,56.9,60.7);alveoli.scale.setScalar(.23+.77*magnify);alveoli.rotation.y=.10*Math.sin(t*.2);for(let i=0;i<alveolarCells.length;i++)alveolarCells[i].scale.setScalar(1+.018*Math.sin(t*.8+i*.6));
 airParticles.forEach((q,i)=>{const f=(t*.18+i/airParticles.length)%1,side=i%2?1:-1;q.position.set(side*(.05+1.45*f*f),2.45-3.65*f,.35);q.scale.setScalar(.001+Math.sin(Math.PI*f));});
 const graph=at(t,104.8,108.2)*(1-at(t,127.5,131.2));pathway.scale.setScalar(.001+.999*graph);faceGroup.position.x=-.65*graph;
 heart.scale.setScalar(1+.035*Math.sin(t*(t<117?5.4:4.4)));waterRings.forEach((q,i)=>{const pulse=(t*.13+i*.25)%1;q.scale.setScalar(.8+pulse*.28);});
 for(let i=0;i<clothBase.length;i+=3){const x=clothBase[i],y=clothBase[i+1];clothGeometry.attributes.position.array[i+2]=.1*Math.cos(x*2.4)+.026*Math.sin(y*27+x*3);}
 clothGeometry.attributes.position.needsUpdate=true;clothGeometry.computeVertexNormals();
 nerveBeads.forEach((q,i)=>{const f=(t*.3+i*.5)%1;q.position.copy(curve([[.9,-.25,.25],[1.65,.35,.65],[2.3,.85,.45],[2.68,.23,.5],[3.4,-.5,.25]]).getPoint(f));q.scale.setScalar(.001+Math.sin(Math.PI*f));});
 const touch=bell(t,151.8,162.6)+.4*bell(t,175.5,184.8);fingers.position.set(-.32+.24*touch,.04*Math.sin(t*1.2)*touch,.08*touch);touchHalo.scale.setScalar(1+.1*Math.sin(t*2));earNerves.forEach((q,i)=>q.scale.setScalar(1+.28*Math.sin(t*.9+i)));
 const movement=bell(t,190,210);arms.forEach(({side,g,lower})=>{g.rotation.z=side*(.035+Math.sin(t*9.3)*.075*movement);lower.rotation.z=Math.sin(t*11+side)*.11*movement;});shoulderFibers.forEach((q,i)=>q.scale.y=1-.08*at(t,211,217)+Math.sin(t*.6+i*.1)*.004);
 paperSupport.position.set(0,0,0);paperSupport.scale.setScalar(1);paperDeform(t);
 const leafArray=leafGeometry.attributes.position.array;for(let i=0;i<leafArray.length;i+=3){const x=leafBase[i],y=leafBase[i+1],u=x/3.1;leafArray[i+1]=y*Math.max(.001,1-u*u);leafArray[i+2]=.16*Math.sin(u*Math.PI)**2+.08*(y/1.8)**2;}
 leafGeometry.attributes.position.needsUpdate=true;leafGeometry.computeVertexNormals();
 const carryLeaf=at(t,279.35,283.15);if(t>=279.35&&t<375.5){leafStation.position.copy(centers[6]).lerp(centers[7],carryLeaf);leafStation.position.x-=1.15*(1-carryLeaf);}fern.scale.setScalar(.001);leafDetail.scale.setScalar(1);leafDetail.position.y=0;veins.children.forEach((mesh,i)=>{const n=mesh.geometry.index.count,g=i===0?1:at(t,280.5+(i%5)*.25,284.2+(i%5)*.3);mesh.geometry.setDrawRange(0,Math.max(0,Math.floor(n*g/3)*3));});
 books.forEach((q,i)=>{const p=spring(t,334.198+i*.35,2.7);q.position.set(mix(-2.3+i*1.75,-2.5,p),mix(.65-i*.52,.63,p),-.01+i*.23*p);q.rotation.z=mix((i-1)*.35,-.06,p);});
 const cp=spring(t,339.5,2.889814815);cup.position.set(mix(.1,2.25,cp),mix(-1.1,1.1,cp),-.08);cup.rotation.z=mix(-.2,0,cp);
 pencils.forEach((q,i)=>{const p=at(t,337+i*.25,341+i*.25);q.position.set(mix(-.4+i*.6,1.55+i*.18,p),mix(.4-i*.4,-.8,p),.11);q.rotation.z=mix(.7+i*.3,.12,p);});
 const clear=at(t,333.6,336.6);deskPaper.position.set(mix(1.7,4.1,clear),mix(-.6,-2.7,clear),mix(.12,-.4,clear));deskPaper.rotation.z=.3+clear*1.1;
 bookShadows.forEach((q,i)=>{q.position.set(books[i].position.x,books[i].position.y,-.075);q.rotation.z=books[i].rotation.z;});cupShadow.position.set(cup.position.x+.1,cup.position.y,-.073);
 finalMark.scale.setScalar((.001+.999*at(t,377.2,383.8))*mix(1,.65,at(t,393.5,398.2)));finalRings.forEach((q,i)=>q.rotation.z=.15*Math.sin(t*.12+i));
}

const heading=document.getElementById('chapter'),eyebrow=document.getElementById('eyebrow'),caption=document.getElementById('caption'),note=document.getElementById('note'),titleEl=document.getElementById('title');
const ENG={hook:'THE BODY FIRST',title:'ROOM TO BREATHE',breath:'01 / BREATH',cold:'02 / COOL TOUCH',ear:'03 / SOFT TOUCH',shake:'04 / SMALL MOVEMENTS',paper:'05 / WRITE IT DOWN',fractal:'06 / NATURE',order:'07 / A SMALL ORDER',closing:'ROOM TO CHOOSE'};
const keywords=['双吸长呼','迷走神经','三叉神经','舒服','轻轻','分形','一平米','放松','写下','节奏'];
function cueAt(t){let found=null;for(const c of D.captions){if(c.start<=t+1e-8&&t+1e-8<c.end){found=c;break;}if(c.start>t)break;}return found;}
function setHUD(t){
 const c=chapterAt(t),cue=cueAt(t),isTitle=c.id==='title';eyebrow.textContent=ENG[c.id];heading.textContent=isTitle?'':c.id==='hook'?'身体先紧绷起来':c.id==='closing'?'给自己一点空间':c.title;
 const kw=cue&&keywords.find(k=>cue.text.includes(k));caption.textContent='';if(cue){if(kw){const k=cue.text.indexOf(kw);caption.append(document.createTextNode(cue.text.slice(0,k)));const span=document.createElement('span');span.textContent=kw;caption.append(span,document.createTextNode(cue.text.slice(k+kw.length)));}else caption.textContent=cue.text;}
 note.textContent=t>=106.03&&t<127.8?'冷刺激 + 屏息：实验机制示意':t>=127.93&&t<136.6?'凉毛巾不等于实验条件':'';
 const finalTitle=t>=390;const titleAmt=finalTitle?at(t,390,393.2):at(t,20.45,22.1)*(1-at(t,24.0,26.6));titleEl.querySelector('strong').textContent=finalTitle?'先缓一缓':'先让身体缓一缓';titleEl.querySelector('strong').style.fontSize=finalTitle?'63px':'88px';titleEl.querySelector('small').textContent=finalTitle?'ONE SMALL THING AT A TIME':'ROOM TO BREATHE';titleEl.querySelector('small').style.fontSize=finalTitle?'12px':'17px';titleEl.querySelector('small').style.letterSpacing=finalTitle?'3px':'8px';titleEl.style.transform=`translateY(${(1-titleAmt)*10}px)`;titleEl.style.clipPath=`inset(0 ${(1-titleAmt)*100}% 0 0)`;
 scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);
 for(const l of labels){const alpha=l.show(t),pos=l.parent.localToWorld(l.pos.clone()).project(camera);l.e.style.left=`${(pos.x*.5+.5)*1920}px`;l.e.style.top=`${(-pos.y*.5+.5)*1080}px`;l.e.style.opacity=String(alpha);l.e.style.display=alpha<.001||pos.z>1?'none':'block';}
}
function render(t){t=clamp(t,0,DUR);updateModels(t);updateHero(t);const ca=cameraAt(t);camera.position.copy(ca.position);camera.up.set(0,1,0);camera.lookAt(ca.target);key.position.set(ca.target.x-6,ca.target.y+7,ca.target.z+10);key.target.position.copy(ca.target);rim.position.set(ca.target.x+5,ca.target.y+3,ca.target.z+2);rim.target.position.copy(ca.target);fill.position.set(ca.target.x-3,ca.target.y-1,ca.target.z+4);setHUD(t);renderer.render(scene,camera);}
const cuts=[...new Set(D.captions.flatMap(c=>[c.start,c.end]).concat(CH.map(c=>c.start)))].sort((a,b)=>a-b);
function blurAt(t){if(cuts.some(c=>Math.abs(t-c)<1/60+1e-7))return 1;if(pose(t).moving)return 5;if(t>244.2&&t<246.7)return 5;if(t>189&&t<211)return 3;if(t>375.5&&t<385)return 3;return 1;}
window.ONETAKE={render,cameraAt,centerAt,pose,heroPoints,hero,scene,camera,transitions,modelGroups,renderer};
Shot.define({duration:DUR,fps:60,cuts,fonts:[['500 43px "PingFang SC"',D.captions.map(c=>c.text).join('')],['500 88px "PingFang SC"','先让身体缓一缓']],
 async setup(){await document.fonts.ready;const pmrem=new T.PMREMGenerator(renderer);const room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;room.dispose();pmrem.dispose();render(0);},
 post:{motionBlur:5,maxMotionBlur:5,shutter:.45,grain:0},blurAt,
 meta:{title:'先让身体缓一缓 · 连续镜头版',version:'onetake-v2',duration:DUR,render_core:'Multiplane 0.3.13 + Three.js 0.180.0',motion:'single persistent mesh, world-space continuity, minimum-jerk camera',audio:'approved mix unchanged'},render});
