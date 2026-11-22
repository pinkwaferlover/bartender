// Rig the Apollo Belvedere scan (CC0) as Dionysus: trim the plinth/trunk, place bones,
// geodesic skin weights, region tags (skin/hair/cloak), and pack into a JS file that loads from file://.
import fs from 'fs';
const d=JSON.parse(fs.readFileSync(process.argv[2]));const out=process.argv[3];
let P=d.P,I=d.I;const N=P.length/3;
const v=i=>[P[i*3],P[i*3+1],P[i*3+2]];
// 1. trim plinth and tree-trunk support (hidden behind the counter anyway)
const keepT=[];for(let t=0;t<I.length;t+=3){const a=v(I[t]),b=v(I[t+1]),c=v(I[t+2]);const cx=(a[0]+b[0]+c[0])/3,cy=(a[1]+b[1]+c[1])/3;
  if(cy<0.17)continue;const el=Math.max(Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]),Math.hypot(b[0]-c[0],b[1]-c[1],b[2]-c[2]),Math.hypot(a[0]-c[0],a[1]-c[1],a[2]-c[2]));if(el>0.12)continue;if(cx<-0.19&&cy<1.1)continue;if(cx>-0.37&&cx<-0.18&&cy<1.19&&cy>0.95)continue;keepT.push(I[t],I[t+1],I[t+2])}
const used=new Int32Array(N).fill(-1);const Q=[];for(const i of keepT)if(used[i]<0){used[i]=Q.length/3;Q.push(...v(i))}
I=keepT.map(i=>used[i]);P=Q;
{const m=P.length/3,par=new Int32Array(m).map((_,i)=>i);const f=x=>{while(par[x]!==x){par[x]=par[par[x]];x=par[x]}return x};for(let t=0;t<I.length;t+=3){par[f(I[t])]=f(I[t+1]);par[f(I[t+1])]=f(I[t+2])}
 const cnt=new Map();for(let i=0;i<m;i++){const r=f(i);cnt.set(r,(cnt.get(r)||0)+1)}const big=[...cnt.entries()].filter(e=>e[1]>400).map(e=>e[0]);const keep=new Set(big);
 const T2=[];for(let t=0;t<I.length;t+=3)if(keep.has(f(I[t])))T2.push(I[t],I[t+1],I[t+2]);const u2=new Int32Array(m).fill(-1),Q2=[];for(const i of T2)if(u2[i]<0){u2[i]=Q2.length/3;Q2.push(P[i*3],P[i*3+1],P[i*3+2])}I=T2.map(i=>u2[i]);P=Q2;console.log('components kept',big.length,'of',cnt.size)}
const n=P.length/3;console.log('verts',n,'tris',I.length/3);
// 2. bones (statue space, metres). head joint, parent
const B=[
 ['hips',-1,[-.03,1.02,.02],[-.03,1.25,.02]],
 ['spine',0,[-.03,1.25,.02],[-.04,1.45,.03]],
 ['chest',1,[-.04,1.45,.03],[-.06,1.84,.04]],
 ['neck',2,[-.06,1.86,.05],[-.065,1.95,.07]],
 ['head',3,[-.065,1.95,.07],[-.075,2.3,.11]],
 ['upperR',2,[-.235,1.84,.04],[-.36,1.49,.05]],
 ['foreR',5,[-.36,1.49,.05],[-.45,1.22,.12]],
 ['handR',6,[-.45,1.22,.12],[-.53,1.1,.15]],
 ['upperL',2,[.13,1.86,.05],[.45,1.79,.2]],
 ['foreL',8,[.45,1.79,.2],[.8,1.8,.35]],
 ['handL',9,[.8,1.8,.35],[.92,1.81,.38]],
];
const NB=B.length;
const segT=(p,a,b)=>{const ab=[b[0]-a[0],b[1]-a[1],b[2]-a[2]],ap=[p[0]-a[0],p[1]-a[1],p[2]-a[2]];return (ap[0]*ab[0]+ap[1]*ab[1]+ap[2]*ab[2])/(ab[0]**2+ab[1]**2+ab[2]**2)};
const segD=(p,a,b)=>{const ab=[b[0]-a[0],b[1]-a[1],b[2]-a[2]],ap=[p[0]-a[0],p[1]-a[1],p[2]-a[2]];const L=ab[0]**2+ab[1]**2+ab[2]**2;let t=(ap[0]*ab[0]+ap[1]*ab[1]+ap[2]*ab[2])/L;t=Math.max(0,Math.min(1,t));
  return Math.hypot(ap[0]-ab[0]*t,ap[1]-ab[1]*t,ap[2]-ab[2]*t)};
// adjacency
const adj=Array.from({length:n},()=>new Map());for(let t=0;t<I.length;t+=3)for(let k=0;k<3;k++){const a=I[t+k],b=I[t+(k+1)%3];const pa=v(a),pb=v(b);const L=Math.hypot(pa[0]-pb[0],pa[1]-pb[1],pa[2]-pb[2]);adj[a].set(b,L);adj[b].set(a,L)}
// euclidean distance to every bone
const E=new Float32Array(n*NB);for(let i=0;i<n;i++){const p=v(i);for(let b=0;b<NB;b++)E[i*NB+b]=segD(p,B[b][2],B[b][3])}
// legs and everything below the hips belong to the hips
// geodesic distance per bone from seeds (verts clearly nearest that bone)
class Heap{constructor(){this.a=[]}push(x){const a=this.a;a.push(x);let i=a.length-1;while(i){const p=(i-1)>>1;if(a[p][0]<=a[i][0])break;[a[p],a[i]]=[a[i],a[p]];i=p}}pop(){const a=this.a,top=a[0],last=a.pop();if(a.length){a[0]=last;let i=0;for(;;){let l=2*i+1,r=l+1,m=i;if(l<a.length&&a[l][0]<a[m][0])m=l;if(r<a.length&&a[r][0]<a[m][0])m=r;if(m===i)break;[a[m],a[i]]=[a[i],a[m]];i=m}}return top}get size(){return this.a.length}}
const G=new Float32Array(n*NB).fill(1e3);
for(let b=0;b<NB;b++){const h=new Heap();for(let i=0;i<n;i++){const e=E[i*NB+b];let best=1e9;for(let c=0;c<NB;c++)if(c!==b)best=Math.min(best,E[i*NB+c]);
   const tt=segT(v(i),B[b][2],B[b][3]);const lim=b>=5?(tt>0.3&&tt<1.05):(tt>-0.05&&tt<1.05);if(lim&&e<0.075&&e<best*0.7){G[i*NB+b]=0;h.push([0,i])}}
  while(h.size){const[dd,i]=h.pop();if(dd>G[i*NB+b])continue;for(const[j,L]of adj[i]){const nd=dd+L;if(nd<G[j*NB+b]){G[j*NB+b]=nd;h.push([nd,j])}}}}
// weights
const W=new Float32Array(n*NB);
for(let i=0;i<n;i++){const p=v(i);let s=0;
  if(p[1]<1.12){W[i*NB]=1;continue}
  for(let b=0;b<NB;b++){let g=G[i*NB+b];if(g>=1e3)g=E[i*NB+b]*3+.2;const w=1/Math.pow(g+0.02,4);W[i*NB+b]=w;s+=w}
  if(p[1]<1.97){s-=W[i*NB+4];W[i*NB+4]=0}if(p[1]>2.01){s-=W[i*NB+3];W[i*NB+3]=0}
  for(let b=0;b<NB;b++)W[i*NB+b]/=s}
// cloak hanging under the left arm: share with the chest so it drapes rather than flies
for(let i=0;i<n;i++){const p=v(i);if(p[0]>0.18&&p[1]<1.74&&p[1]>0.9){const k=Math.max(0,Math.min(1,(1.74-p[1])/0.6))*0.5;for(let b=0;b<NB;b++)W[i*NB+b]*=(1-k);W[i*NB+2]+=k}}
// smooth
for(let it=0;it<8;it++){const W2=new Float32Array(W);for(let i=0;i<n;i++){if(!adj[i].size)continue;for(let b=0;b<NB;b++){let s=W[i*NB+b];for(const j of adj[i].keys())s+=W[j*NB+b];W2[i*NB+b]=s/(adj[i].size+1)}}W.set(W2);for(let i=0;i<n;i++){const y=P[i*3+1];let c=0;if(y<1.97){c+=W[i*NB+4];W[i*NB+4]=0}if(y>2.01){c+=W[i*NB+3];W[i*NB+3]=0}if(c){const s=1-c;for(let b=0;b<NB;b++)W[i*NB+b]/=s}}}
// drop bridging scraps: anything tied to both the right arm and the hips (trunk remains under the hand)
{const armW=i=>W[i*NB+5]+W[i*NB+6]+W[i*NB+7];const bad=i=>{const y=P[i*3+1],x=P[i*3];return (armW(i)>0.08&&W[i*NB]>0.08)||(armW(i)>0.05&&y<1.13&&x>-0.41)};
 const T=[];for(let t=0;t<I.length;t+=3)if(!bad(I[t])&&!bad(I[t+1])&&!bad(I[t+2]))T.push(I[t],I[t+1],I[t+2]);console.log('dropped tris',(I.length-T.length)/3);I=T}
// top 4
const SI=new Uint8Array(n*4),SW=new Uint8Array(n*4);
for(let i=0;i<n;i++){const o=[...Array(NB).keys()].sort((a,b)=>W[i*NB+b]-W[i*NB+a]).slice(0,4);let s=o.reduce((a,b)=>a+W[i*NB+b],0);let acc=0;
  o.forEach((b,k)=>{SI[i*4+k]=b;const q=k<3?Math.round(W[i*NB+b]/s*255):255-acc;SW[i*4+k]=Math.max(0,q);acc+=SW[i*4+k]})}
// regions: 0 skin, 1 hair, 2 cloth (cloak), 3 sandal
const R=new Uint8Array(n);const hc=[-.085,2.14,.148],f=[.98,0,.19],EY=[[.011,2.141,.133],[-.01,2.141,.201]];
for(const e of EY){let best=1e9,bi=-1;for(let i=0;i<n;i++){const p=v(i);if(Math.hypot(p[0]-e[0],p[1]-e[1],p[2]-e[2])>0.018)continue;const fw=(p[0]-hc[0])*f[0]+(p[2]-hc[2])*f[2];if(fw<best){best=fw;bi=i}}if(bi>=0){const p=v(bi);const c=[p[0]+f[0]*.004,p[1],p[2]+f[2]*.004];e[0]=c[0];e[1]=c[1];e[2]=c[2]}console.log('eye',e.map(x=>x.toFixed(3)))}
for(let i=0;i<n;i++){const[x,y,z]=v(i);const dx=x-hc[0],dy=y-hc[1],dz=z-hc[2];const dist=Math.hypot(dx,dy,dz);
  if(dist<0.19&&y>2.02){const fwd=dx*f[0]+dz*f[2];const lat=dx*-f[2]+dz*f[0];const face=fwd>0.03&&y<2.185&&!((lat>.068||lat<-.085)&&y>2.07);if(!face)R[i]=1}
  if(x>0.18&&y<1.76&&y>0.9)R[i]=2;
  if(y>1.83&&y<1.97&&z>0.02&&x>-0.25&&x<0.2&&!(R[i]))R[i]=2;
  if(z<-0.06&&y>1.0&&y<1.98&&x>-0.22&&!R[i])R[i]=2;
  if(y<0.4&&R[i]===0)R[i]=3;
  for(const e of EY)if(Math.hypot(x-e[0],y-e[1],z-e[2])<0.0095)R[i]=4}
// pack
const mn=[1e9,1e9,1e9],mx=[-1e9,-1e9,-1e9];for(let i=0;i<n;i++)for(let a=0;a<3;a++){mn[a]=Math.min(mn[a],P[i*3+a]);mx[a]=Math.max(mx[a],P[i*3+a])}
const qp=new Uint16Array(n*3);for(let i=0;i<n;i++)for(let a=0;a<3;a++)qp[i*3+a]=Math.round((P[i*3+a]-mn[a])/(mx[a]-mn[a])*65535);
const b64=a=>Buffer.from(a.buffer,a.byteOffset,a.byteLength).toString('base64');
const js=`/* Dionysus body: "Apollo Belvedere" scan by SMK – National Gallery of Denmark, CC0 Public Domain, via Sketchfab (sketchfab.com/3d-models/apollo-belvedere-fe5c0cffdc2a4f3985872212c692af0c).
   Trimmed, simplified and rigged for this prototype. Regions: 0 skin, 1 hair, 2 cloak, 3 sandal, 4 eye. */
window.DIO_MESH=${JSON.stringify({n,min:mn,max:mx,bones:B.map(b=>({name:b[0],parent:b[1],head:b[2],tail:b[3]})),pos:b64(qp),idx:b64(new Uint16Array(I)),si:b64(SI),sw:b64(SW),reg:b64(R)})};\n`;
fs.writeFileSync(out,js);console.log('bytes',js.length);
