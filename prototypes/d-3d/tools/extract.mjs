import {NodeIO} from '@gltf-transform/core';import {ALL_EXTENSIONS} from '@gltf-transform/extensions';import fs from 'fs';
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);const doc=await io.read(process.argv[2]);
const P=[],I=[];for(const node of doc.getRoot().listNodes()){const mesh=node.getMesh();if(!mesh)continue;const m=node.getWorldMatrix();
 for(const prim of mesh.listPrimitives()){const pos=prim.getAttribute('POSITION');const idx=prim.getIndices();const base=P.length/3;const el=[0,0,0];
  for(let i=0;i<pos.getCount();i++){pos.getElement(i,el);const x=el[0],y=el[1],z=el[2];P.push(m[0]*x+m[4]*y+m[8]*z+m[12],m[1]*x+m[5]*y+m[9]*z+m[13],m[2]*x+m[6]*y+m[10]*z+m[14])}
  for(let i=0;i<idx.getCount();i++)I.push(base+idx.getScalar(i))}}
// weld
const key=new Map(),remap=[],Q=[];for(let i=0;i<P.length/3;i++){const k=P.slice(i*3,i*3+3).map(v=>Math.round(v*2e4)).join(',');let j=key.get(k);if(j===undefined){j=Q.length/3;key.set(k,j);Q.push(P[i*3],P[i*3+1],P[i*3+2])}remap.push(j)}
const J=I.map(i=>remap[i]);let mn=[1e9,1e9,1e9],mx=[-1e9,-1e9,-1e9];for(let i=0;i<Q.length;i+=3)for(let a=0;a<3;a++){mn[a]=Math.min(mn[a],Q[i+a]);mx[a]=Math.max(mx[a],Q[i+a])}
console.log('verts',Q.length/3,'tris',J.length/3,'min',mn,'max',mx);fs.writeFileSync(process.argv[3],JSON.stringify({P:Q.map(v=>+v.toFixed(5)),I:J}));
