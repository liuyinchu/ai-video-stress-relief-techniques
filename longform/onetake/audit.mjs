import fs from 'node:fs/promises';
import {openShot} from '../../node_modules/multiplane/src/capture.mjs';
const shot=await openShot('longform/onetake/index.html',1,{root:process.cwd(),raster:'gpu',staticReuse:false});
try{
 const report=await shot.page.evaluate(()=>{
  const o=window.ONETAKE, duration=400.8333333333333,dt=1/60;
  let maxSpeed=0,maxAcc=0,oldV=null,oldP=null;
  const cameraTrace=[];
  for(let f=0;f<=24050;f++){
   const t=f*dt,p=o.cameraAt(t).position;
   if(oldP){const velocity=p.clone().sub(oldP).multiplyScalar(60);maxSpeed=Math.max(maxSpeed,velocity.length());if(oldV)maxAcc=Math.max(maxAcc,velocity.clone().sub(oldV).multiplyScalar(60).length());oldV=velocity;}
   oldP=p;if(f%30===0)cameraTrace.push({t,position:p.toArray()});
  }
  const eps=.0001,joins=[];
  for(const tr of o.transitions)for(const edge of [tr.start,tr.end]){
   const left=o.cameraAt(edge-eps).position,center=o.cameraAt(edge).position,right=o.cameraAt(edge+eps).position;
   joins.push({time:edge,positionGap:left.distanceTo(right),velocityGap:center.clone().sub(left).divideScalar(eps).distanceTo(right.clone().sub(center).divideScalar(eps))});
  }
  const holds=[50,140,170,219,266,323,363,390].map(t=>({time:t,displacement:o.cameraAt(t-.3).position.distanceTo(o.cameraAt(t+.3).position)}));
  const uuid=o.hero.uuid,visibility=[];let finite=true;
  for(const tr of o.transitions){let minVisible=1,maxBounds=0;
   for(let t=tr.start-.1;t<=tr.end+.1;t+=.12){o.render(t);let visible=0;const ps=o.heroPoints;
    for(let j=0;j<ps.length;j+=12){const q=o.hero.position.clone().add({x:ps[j],y:ps[j+1],z:ps[j+2]}).project(o.camera);finite&&=Number.isFinite(q.x)&&Number.isFinite(q.y);if(Math.abs(q.x)<1&&Math.abs(q.y)<.86&&q.z<1)visible++;maxBounds=Math.max(maxBounds,Math.abs(q.x),Math.abs(q.y));}
    minVisible=Math.min(minVisible,visible/(ps.length/12));if(o.hero.uuid!==uuid||!o.hero.visible||o.hero.material.opacity!==1)throw Error('Persistent hero was replaced or hidden.');
   }visibility.push({from:tr.from,to:tr.to,minVisibleFraction:minVisible,maxNDCBounds:maxBounds});
  }
  return {duration,fps:60,frames:24050,heroIdentityPreserved:true,heroOpacity:1,finite,maxCameraSpeed:maxSpeed,maxCameraAcceleration:maxAcc,cameraJoins:joins,lockedHolds:holds,transitions:visibility,cameraTrace};
 });
 report.passed=report.finite&&report.heroIdentityPreserved&&report.transitions.every(t=>t.minVisibleFraction>=.95)&&report.lockedHolds.every(h=>h.displacement<.000001)&&report.cameraJoins.every(j=>j.positionGap<.01&&j.velocityGap<.1);
 await fs.writeFile('longform/onetake/output/motion-audit.json',JSON.stringify(report,null,2));
 console.log(JSON.stringify({passed:report.passed,maxCameraSpeed:report.maxCameraSpeed,maxCameraAcceleration:report.maxCameraAcceleration,minHeroVisibility:Math.min(...report.transitions.map(t=>t.minVisibleFraction)),lockedHolds:report.lockedHolds}));
 if(!report.passed)process.exitCode=1;
}finally{await shot.close();}
