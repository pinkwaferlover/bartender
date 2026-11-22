const GL={
 rocks:{g:'M18 38 L22 108 Q23 114 30 114 L70 114 Q77 114 78 108 L82 38 Z',l:'M20.4 60 L22.8 107 Q24 111 30 111 L70 111 Q76 111 77.2 107 L79.6 60 Z',foam:'M20.4 60 L20.9 70 L79.1 70 L79.6 60 Z',ice:'<rect x="30" y="66" width="18" height="18" rx="4" fill="#fff" opacity=".35" transform="rotate(-8 39 75)"/><rect x="50" y="74" width="18" height="18" rx="4" fill="#fff" opacity=".3" transform="rotate(10 59 83)"/>',rim:[76,38],cherry:[56,100],top:44},
 highball:{g:'M28 10 L31 110 Q32 116 37 116 L63 116 Q68 116 69 110 L72 10 Z',l:'M28.7 30 L31.2 108 Q32 113 37 113 L63 113 Q68 113 68.8 108 L71.3 30 Z',foam:'M28.7 30 L29 40 L71 40 L71.3 30 Z',ice:'<rect x="36" y="40" width="16" height="16" rx="4" fill="#fff" opacity=".33" transform="rotate(-10 44 48)"/><rect x="48" y="62" width="16" height="16" rx="4" fill="#fff" opacity=".3" transform="rotate(12 56 70)"/><rect x="36" y="84" width="16" height="16" rx="4" fill="#fff" opacity=".28"/>',rim:[68,10],cherry:[50,100],top:38},
 coupe:{g:'M12 28 Q14 70 50 72 Q86 70 88 28 Z M48 71 h4 v36 h-4 Z M28 109 Q50 103 72 109 Q50 114 28 109 Z',l:'M15 38 Q18 67 50 68 Q82 67 85 38 Z',foam:'M15 38 Q15.6 44 16.8 48 L83.2 48 Q84.4 44 85 38 Z',rim:[84,28],cherry:[50,60],top:48},
 martini:{g:'M10 22 L50 68 L90 22 Z M48 66 h4 v40 h-4 Z M28 109 Q50 103 72 109 Q50 114 28 109 Z',l:'M18 31 L50 64 L82 31 Z',foam:'M18 31 L22.4 36 L77.6 36 L82 31 Z',rim:[86,22],cherry:[50,54],top:48},
 mug:{g:'M22 36 L24 108 Q25 114 32 114 L62 114 Q69 114 70 108 L72 36 Z M70 50 Q90 50 90 70 Q90 92 69 94 L69 86 Q82 84 82 70 Q82 58 70 58 Z',l:'M23.3 48 L25 107 Q26 111 32 111 L62 111 Q67 111 68 107 L70.7 48 Z',foam:'M23.3 48 L23.8 62 L70.2 62 L70.7 48 Z',rim:[68,36],cherry:[48,100],top:42}
};
const WHEEL={lemon:['#f2cf2e','#fbe58a'],lime:['#86c03a','#c6e48a'],grapefruit:['#ef7f63','#f9bba8']};
function garnSide(g,G){const[x,y]=G.rim;
 if(g==='orange')return`<path d="M${x-12} ${y+5} Q${x-2} ${y-12} ${x+12} ${y-3} Q${x} ${y-4} ${x-7} ${y+9} Z" fill="#ef8a22"/>`;
 if(WHEEL[g])return`<circle cx="${x}" cy="${y}" r="11" fill="${WHEEL[g][0]}"/><circle cx="${x}" cy="${y}" r="7.5" fill="${WHEEL[g][1]}"/>`;
 if(g==='cherry'){const[a,b]=G.cherry;return`<circle cx="${a}" cy="${b}" r="6" fill="#9b1020"/><path d="M${a} ${b-5} q2 -9 8 -12 l1 1.6 q-5 3 -7 10.4 z" fill="#5a2a10"/>`}
 if(g==='mint')return`<ellipse cx="${x-6}" cy="${y-9}" rx="5" ry="10" fill="#4c9a48" transform="rotate(-28 ${x-6} ${y-9})"/><ellipse cx="${x+4}" cy="${y-11}" rx="5" ry="10" fill="#5fae55" transform="rotate(22 ${x+4} ${y-11})"/>`;
 if(g==='ginger')return`<rect x="${x-8}" y="${y-9}" width="16" height="12" rx="4" fill="#e6c27a" transform="rotate(-14 ${x} ${y-3})"/>`;
 if(g==='foam')return`<path d="${G.foam}" fill="#f6eedd"/>`;
 if(g==='cream')return`<path d="${G.foam}" fill="#f2e7d1"/>`;
 return'';}
function glassSide(r,h,o={}){const G=GL[r.glass];let s=`<svg viewBox="0 0 100 120" width="${Math.round(h*100/120)}" height="${h}" aria-hidden="true"${o.ghost?' class="ghost"':''}>`;
 s+=`<path d="${G.g}" fill="var(--glass)"/><path d="${G.l}" fill="${r.colour}"/>`;
 if(r.ice&&G.ice)s+=G.ice; s+=garnSide(r.garnish,G); return s+'</svg>';}
function arc(cx,cy,rr,f0,f1){if(f1-f0<=0.0005)return'';if(f1-f0>=0.9995)return`M${cx-rr} ${cy} a${rr} ${rr} 0 1 0 ${rr*2} 0 a${rr} ${rr} 0 1 0 ${-rr*2} 0 Z`;
 const p=f=>[(cx+rr*Math.sin(2*Math.PI*f)).toFixed(2),(cy-rr*Math.cos(2*Math.PI*f)).toFixed(2)];const[a,b]=p(f0),[c,d]=p(f1);
 return`M${cx} ${cy} L${a} ${b} A${rr} ${rr} 0 ${f1-f0>0.5?1:0} 1 ${c} ${d} Z`;}
const RIM={rocks:44,highball:38,coupe:48,martini:48,mug:41};
function glassTop(r,size,frac=1,o={}){const rim=RIM[r.glass],L=rim-7;let s=`<svg viewBox="0 0 100 100" width="${size}" height="${size}" aria-hidden="true"${o.ghost?' class="ghost"':''}>`;
 if(r.glass==='mug')s+=`<rect x="82" y="42" width="16" height="16" rx="7" fill="var(--glass)"/>`;
 s+=`<circle cx="50" cy="50" r="${rim}" fill="var(--glass)"/>`;
 const top=(r.garnish==='foam'||r.garnish==='cream')?(r.garnish==='foam'?'#f6eedd':'#f2e7d1'):null;
 if(frac<0.999)s+=`<circle cx="50" cy="50" r="${L}" fill="${r.colour}" opacity=".16"/>`;
 s+=`<path d="${arc(50,50,L,0,frac)}" fill="${r.colour}"/>`;
 if(top)s+=`<path d="${arc(50,50,L-6,0,frac)}" fill="${top}"/>`;
 if(r.ice&&!top&&frac>0.999)s+=`<rect x="36" y="36" width="15" height="15" rx="4" fill="#fff" opacity=".32" transform="rotate(-12 43 43)"/><rect x="52" y="50" width="15" height="15" rx="4" fill="#fff" opacity=".28" transform="rotate(16 59 57)"/>`;
 const g=r.garnish;
 if(g==='orange')s+=`<path d="M58 22 Q80 26 82 46 Q74 34 60 30 Z" fill="#ef8a22"/>`;
 if(WHEEL[g])s+=`<circle cx="70" cy="30" r="13" fill="${WHEEL[g][0]}"/><circle cx="70" cy="30" r="9" fill="${WHEEL[g][1]}"/>`;
 if(g==='cherry')s+=`<circle cx="44" cy="56" r="7" fill="#9b1020"/>`;
 if(g==='mint')s+=`<ellipse cx="62" cy="34" rx="6" ry="11" fill="#4c9a48" transform="rotate(30 62 34)"/><ellipse cx="72" cy="40" rx="6" ry="11" fill="#5fae55" transform="rotate(80 72 40)"/><ellipse cx="60" cy="44" rx="5" ry="9" fill="#3f8a3c" transform="rotate(-20 60 44)"/>`;
 if(g==='ginger')s+=`<rect x="62" y="24" width="18" height="13" rx="4" fill="#e6c27a" transform="rotate(20 71 30)"/>`;
 return s+'</svg>';}
const BOT={whisky:'M23 6 h14 v14 q0 4 6 7 q9 5 9 14 v51 q0 4 -4 4 h-36 q-4 0 -4 -4 v-51 q0 -9 9 -14 q6 -3 6 -7 Z',gin:'M24 6 h12 v16 l8 8 v62 q0 4 -4 4 h-20 q-4 0 -4 -4 v-62 l8 -8 Z',
 rum:'M25 6 h10 v22 q16 6 16 22 v42 q0 4 -4 4 h-34 q-4 0 -4 -4 v-42 q0 -16 16 -22 Z',tequila:'M25 6 h10 v18 l12 10 v58 q0 4 -4 4 h-26 q-4 0 -4 -4 v-58 l12 -10 Z',
 vodka:'M26 6 h8 v22 q8 4 8 12 v52 q0 4 -4 4 h-16 q-4 0 -4 -4 v-52 q0 -8 8 -12 Z',brandy:'M25 6 h10 v24 q20 10 20 34 q0 32 -25 32 q-25 0 -25 -32 q0 -24 20 -34 Z',
 aperitif:'M26 6 h8 v26 q12 6 12 20 v40 q0 4 -4 4 h-24 q-4 0 -4 -4 v-40 q0 -14 12 -20 Z',bitters:'M27 20 h6 v24 q14 6 14 22 q0 30 -17 30 q-17 0 -17 -30 q0 -16 14 -22 Z'};
function bottle(shape,colour,h,o={}){return`<svg viewBox="0 0 60 100" width="${h*.6}" height="${h}" aria-hidden="true"${o.ghost?' class="ghost"':''}><rect x="${shape==='bitters'?26:23}" y="${shape==='bitters'?14:2}" width="${shape==='bitters'?8:14}" height="8" rx="2" fill="var(--ink)" opacity=".7"/><path d="${BOT[shape]}" fill="${colour}"/></svg>`}
function ingIco(k,h,o={}){const[,kind,c,sh]=ING[k]||['','other','#ccc','drop'];
 if(BOT[sh])return bottle(sh,c,h,o);
 let s=`<svg viewBox="0 0 60 60" width="${h}" height="${h}" aria-hidden="true"${o.ghost?' class="ghost"':''}>`;
 if(sh==='fruit')s+=`<circle cx="30" cy="30" r="22" fill="${c}"/><circle cx="30" cy="30" r="15" fill="#fff" opacity=".35"/>`;
 else if(sh==='leaf')s+=`<path d="M10 50 C10 24 28 10 52 8 C50 34 36 50 10 50 Z" fill="${c}"/>`;
 else if(sh==='egg')s+=`<ellipse cx="30" cy="32" rx="17" ry="22" fill="${c}"/><ellipse cx="30" cy="32" rx="17" ry="22" fill="none"/>`;
 else if(sh==='mixer')s+=`<rect x="18" y="6" width="24" height="48" rx="8" fill="${c}"/><circle cx="26" cy="22" r="2.5" fill="#fff" opacity=".7"/><circle cx="33" cy="34" r="2" fill="#fff" opacity=".7"/><circle cx="27" cy="42" r="1.8" fill="#fff" opacity=".7"/>`;
 else s+=`<path d="M30 6 C30 6 12 28 12 38 a18 18 0 0 0 36 0 C48 28 30 6 30 6 Z" fill="${c}"/>`;
 return s+'</svg>';}
function feelIco(f,h){const c=`var(${FEEL[f][1]})`;let s=`<svg viewBox="0 0 60 60" width="${h}" height="${h}" aria-hidden="true">`;
 if(f==='sweet')s+=`<path d="M30 5 C30 5 11 28 11 38 a19 19 0 0 0 38 0 C49 28 30 5 30 5 Z" fill="${c}"/>`;
 if(f==='balanced')s+=`<path d="M30 8 a22 22 0 0 0 0 44 Z" fill="${c}"/><path d="M30 8 a22 22 0 0 1 0 44 Z" fill="${c}" opacity=".4"/>`;
 if(f==='bitter')s+=`<path d="M30 6 L52 30 L30 54 L8 30 Z" fill="${c}"/><path d="M30 20 L40 30 L30 40 L20 30 Z" fill="#fff" opacity=".3"/>`;
 if(f==='decadent')s+=`<rect x="10" y="36" width="40" height="16" rx="7" fill="${c}"/><rect x="12" y="22" width="36" height="14" rx="6" fill="${c}" opacity=".6"/><rect x="15" y="9" width="30" height="13" rx="6" fill="#efe0c4"/>`;
 if(f==='strong')s+=`<path d="M30 4 C38 18 49 24 49 38 a19 19 0 0 1 -38 0 C11 28 19 22 22 13 C26 22 31 22 30 4 Z" fill="${c}"/>`;
 if(f==='fresh')s+=`<path d="M8 52 C8 24 28 8 54 6 C52 34 36 52 8 52 Z" fill="${c}"/>`;
 return s+'</svg>';}
const SPSHAPE={whisky:'whisky',gin:'gin',rum:'rum',tequila:'tequila',vodka:'vodka',brandy:'brandy',aperitif:'aperitif'};
const spIco=(k,h,o)=>bottle(SPSHAPE[k],SPIRIT[k][1],h,o);
