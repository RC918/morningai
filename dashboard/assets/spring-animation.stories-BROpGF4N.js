import{j as h}from"./jsx-runtime-D_zvdyIk.js";import{r as y}from"./index-Dz3UJJSw.js";import"./_commonjsHelpers-CqkleIqs.js";const es=y.createContext({});function ts(e){const t=y.useRef(null);return t.current===null&&(t.current=e()),t.current}const ss=typeof window<"u",aa=ss?y.useLayoutEffect:y.useEffect,pt=y.createContext(null);function is(e,t){e.indexOf(t)===-1&&e.push(t)}function ns(e,t){const s=e.indexOf(t);s>-1&&e.splice(s,1)}const Z=(e,t,s)=>s>t?t:s<e?e:s;let as=()=>{};const J={},ra=e=>/^-?(?:\d+(?:\.\d+)?|\.\d+)$/u.test(e);function oa(e){return typeof e=="object"&&e!==null}const la=e=>/^0[^.\s]+$/u.test(e);function rs(e){let t;return()=>(t===void 0&&(t=e()),t)}const G=e=>e,Hr=(e,t)=>s=>t(e(s)),qe=(...e)=>e.reduce(Hr),$e=(e,t,s)=>{const i=t-e;return i===0?1:(s-e)/i};class os{constructor(){this.subscriptions=[]}add(t){return is(this.subscriptions,t),()=>ns(this.subscriptions,t)}notify(t,s,i){const n=this.subscriptions.length;if(n)if(n===1)this.subscriptions[0](t,s,i);else for(let r=0;r<n;r++){const a=this.subscriptions[r];a&&a(t,s,i)}}getSize(){return this.subscriptions.length}clear(){this.subscriptions.length=0}}const X=e=>e*1e3,z=e=>e/1e3;function ca(e,t){return t?e*(1e3/t):0}const da=(e,t,s)=>(((1-3*s+3*t)*e+(3*s-6*t))*e+3*t)*e,Ur=1e-7,Wr=12;function Kr(e,t,s,i,n){let r,a,o=0;do a=t+(s-t)/2,r=da(a,i,n)-e,r>0?s=a:t=a;while(Math.abs(r)>Ur&&++o<Wr);return a}function Ze(e,t,s,i){if(e===t&&s===i)return G;const n=r=>Kr(r,0,1,e,s);return r=>r===0||r===1?r:da(n(r),t,i)}const ua=e=>t=>t<=.5?e(2*t)/2:(2-e(2*(1-t)))/2,ha=e=>t=>1-e(1-t),ma=Ze(.33,1.53,.69,.99),ls=ha(ma),pa=ua(ls),fa=e=>(e*=2)<1?.5*ls(e):.5*(2-Math.pow(2,-10*(e-1))),cs=e=>1-Math.sin(Math.acos(e)),ga=ha(cs),ya=ua(cs),$r=Ze(.42,0,1,1),zr=Ze(0,0,.58,1),xa=Ze(.42,0,.58,1),Gr=e=>Array.isArray(e)&&typeof e[0]!="number",ba=e=>Array.isArray(e)&&typeof e[0]=="number",_r={linear:G,easeIn:$r,easeInOut:xa,easeOut:zr,circIn:cs,circInOut:ya,circOut:ga,backIn:ls,backInOut:pa,backOut:ma,anticipate:fa},Xr=e=>typeof e=="string",Is=e=>{if(ba(e)){as(e.length===4);const[t,s,i,n]=e;return Ze(t,s,i,n)}else if(Xr(e))return _r[e];return e},et=["setup","read","resolveKeyframes","preUpdate","update","preRender","render","postRender"];function Yr(e,t){let s=new Set,i=new Set,n=!1,r=!1;const a=new WeakSet;let o={delta:0,timestamp:0,isProcessing:!1};function l(c){a.has(c)&&(d.schedule(c),e()),c(o)}const d={schedule:(c,u=!1,m=!1)=>{const f=m&&n?s:i;return u&&a.add(c),f.has(c)||f.add(c),c},cancel:c=>{i.delete(c),a.delete(c)},process:c=>{if(o=c,n){r=!0;return}n=!0,[s,i]=[i,s],s.forEach(l),s.clear(),n=!1,r&&(r=!1,d.process(c))}};return d}const qr=40;function va(e,t){let s=!1,i=!0;const n={delta:0,timestamp:0,isProcessing:!1},r=()=>s=!0,a=et.reduce((v,P)=>(v[P]=Yr(r),v),{}),{setup:o,read:l,resolveKeyframes:d,preUpdate:c,update:u,preRender:m,render:p,postRender:f}=a,g=()=>{const v=J.useManualTiming?n.timestamp:performance.now();s=!1,J.useManualTiming||(n.delta=i?1e3/60:Math.max(Math.min(v-n.timestamp,qr),1)),n.timestamp=v,n.isProcessing=!0,o.process(n),l.process(n),d.process(n),c.process(n),u.process(n),m.process(n),p.process(n),f.process(n),n.isProcessing=!1,s&&t&&(i=!1,e(g))},b=()=>{s=!0,i=!0,n.isProcessing||e(g)};return{schedule:et.reduce((v,P)=>{const S=a[P];return v[P]=(k,A=!1,N=!1)=>(s||b(),S.schedule(k,A,N)),v},{}),cancel:v=>{for(let P=0;P<et.length;P++)a[et[P]].cancel(v)},state:n,steps:a}}const{schedule:V,cancel:he,state:I,steps:xt}=va(typeof requestAnimationFrame<"u"?requestAnimationFrame:G,!0);let nt;function Zr(){nt=void 0}const U={now:()=>(nt===void 0&&U.set(I.isProcessing||J.useManualTiming?I.timestamp:performance.now()),nt),set:e=>{nt=e,queueMicrotask(Zr)}},wa=e=>t=>typeof t=="string"&&t.startsWith(e),ds=wa("--"),Jr=wa("var(--"),us=e=>Jr(e)?Qr.test(e.split("/*")[0].trim()):!1,Qr=/var\(--(?:[\w-]+\s*|[\w-]+\s*,(?:\s*[^)(\s]|\s*\((?:[^)(]|\([^)(]*\))*\))+\s*)\)$/iu,Re={test:e=>typeof e=="number",parse:parseFloat,transform:e=>e},ze={...Re,transform:e=>Z(0,1,e)},tt={...Re,default:1},Be=e=>Math.round(e*1e5)/1e5,hs=/-?(?:\d+(?:\.\d+)?|\.\d+)/gu;function eo(e){return e==null}const to=/^(?:#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\))$/iu,ms=(e,t)=>s=>!!(typeof s=="string"&&to.test(s)&&s.startsWith(e)||t&&!eo(s)&&Object.prototype.hasOwnProperty.call(s,t)),Sa=(e,t,s)=>i=>{if(typeof i!="string")return i;const[n,r,a,o]=i.match(hs);return{[e]:parseFloat(n),[t]:parseFloat(r),[s]:parseFloat(a),alpha:o!==void 0?parseFloat(o):1}},so=e=>Z(0,255,e),bt={...Re,transform:e=>Math.round(so(e))},xe={test:ms("rgb","red"),parse:Sa("red","green","blue"),transform:({red:e,green:t,blue:s,alpha:i=1})=>"rgba("+bt.transform(e)+", "+bt.transform(t)+", "+bt.transform(s)+", "+Be(ze.transform(i))+")"};function io(e){let t="",s="",i="",n="";return e.length>5?(t=e.substring(1,3),s=e.substring(3,5),i=e.substring(5,7),n=e.substring(7,9)):(t=e.substring(1,2),s=e.substring(2,3),i=e.substring(3,4),n=e.substring(4,5),t+=t,s+=s,i+=i,n+=n),{red:parseInt(t,16),green:parseInt(s,16),blue:parseInt(i,16),alpha:n?parseInt(n,16)/255:1}}const Rt={test:ms("#"),parse:io,transform:xe.transform},Je=e=>({test:t=>typeof t=="string"&&t.endsWith(e)&&t.split(" ").length===1,parse:parseFloat,transform:t=>`${t}${e}`}),ee=Je("deg"),Y=Je("%"),T=Je("px"),no=Je("vh"),ao=Je("vw"),Os={...Y,parse:e=>Y.parse(e)/100,transform:e=>Y.transform(e*100)},Ne={test:ms("hsl","hue"),parse:Sa("hue","saturation","lightness"),transform:({hue:e,saturation:t,lightness:s,alpha:i=1})=>"hsla("+Math.round(e)+", "+Y.transform(Be(t))+", "+Y.transform(Be(s))+", "+Be(ze.transform(i))+")"},R={test:e=>xe.test(e)||Rt.test(e)||Ne.test(e),parse:e=>xe.test(e)?xe.parse(e):Ne.test(e)?Ne.parse(e):Rt.parse(e),transform:e=>typeof e=="string"?e:e.hasOwnProperty("red")?xe.transform(e):Ne.transform(e),getAnimatableNone:e=>{const t=R.parse(e);return t.alpha=0,R.transform(t)}},ro=/(?:#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\))/giu;function oo(e){var t,s;return isNaN(e)&&typeof e=="string"&&(((t=e.match(hs))==null?void 0:t.length)||0)+(((s=e.match(ro))==null?void 0:s.length)||0)>0}const Ta="number",Na="color",lo="var",co="var(",Bs="${}",uo=/var\s*\(\s*--(?:[\w-]+\s*|[\w-]+\s*,(?:\s*[^)(\s]|\s*\((?:[^)(]|\([^)(]*\))*\))+\s*)\)|#[\da-f]{3,8}|(?:rgb|hsl)a?\((?:-?[\d.]+%?[,\s]+){2}-?[\d.]+%?\s*(?:[,/]\s*)?(?:\b\d+(?:\.\d+)?|\.\d+)?%?\)|-?(?:\d+(?:\.\d+)?|\.\d+)/giu;function Ge(e){const t=e.toString(),s=[],i={color:[],number:[],var:[]},n=[];let r=0;const o=t.replace(uo,l=>(R.test(l)?(i.color.push(r),n.push(Na),s.push(R.parse(l))):l.startsWith(co)?(i.var.push(r),n.push(lo),s.push(l)):(i.number.push(r),n.push(Ta),s.push(parseFloat(l))),++r,Bs)).split(Bs);return{values:s,split:o,indexes:i,types:n}}function Pa(e){return Ge(e).values}function ka(e){const{split:t,types:s}=Ge(e),i=t.length;return n=>{let r="";for(let a=0;a<i;a++)if(r+=t[a],n[a]!==void 0){const o=s[a];o===Ta?r+=Be(n[a]):o===Na?r+=R.transform(n[a]):r+=n[a]}return r}}const ho=e=>typeof e=="number"?0:R.test(e)?R.getAnimatableNone(e):e;function mo(e){const t=Pa(e);return ka(e)(t.map(ho))}const me={test:oo,parse:Pa,createTransformer:ka,getAnimatableNone:mo};function vt(e,t,s){return s<0&&(s+=1),s>1&&(s-=1),s<1/6?e+(t-e)*6*s:s<1/2?t:s<2/3?e+(t-e)*(2/3-s)*6:e}function po({hue:e,saturation:t,lightness:s,alpha:i}){e/=360,t/=100,s/=100;let n=0,r=0,a=0;if(!t)n=r=a=s;else{const o=s<.5?s*(1+t):s+t-s*t,l=2*s-o;n=vt(l,o,e+1/3),r=vt(l,o,e),a=vt(l,o,e-1/3)}return{red:Math.round(n*255),green:Math.round(r*255),blue:Math.round(a*255),alpha:i}}function lt(e,t){return s=>s>0?t:e}const M=(e,t,s)=>e+(t-e)*s,wt=(e,t,s)=>{const i=e*e,n=s*(t*t-i)+i;return n<0?0:Math.sqrt(n)},fo=[Rt,xe,Ne],go=e=>fo.find(t=>t.test(e));function Hs(e){const t=go(e);if(!t)return!1;let s=t.parse(e);return t===Ne&&(s=po(s)),s}const Us=(e,t)=>{const s=Hs(e),i=Hs(t);if(!s||!i)return lt(e,t);const n={...s};return r=>(n.red=wt(s.red,i.red,r),n.green=wt(s.green,i.green,r),n.blue=wt(s.blue,i.blue,r),n.alpha=M(s.alpha,i.alpha,r),xe.transform(n))},Et=new Set(["none","hidden"]);function yo(e,t){return Et.has(e)?s=>s<=0?e:t:s=>s>=1?t:e}function xo(e,t){return s=>M(e,t,s)}function ps(e){return typeof e=="number"?xo:typeof e=="string"?us(e)?lt:R.test(e)?Us:wo:Array.isArray(e)?Aa:typeof e=="object"?R.test(e)?Us:bo:lt}function Aa(e,t){const s=[...e],i=s.length,n=e.map((r,a)=>ps(r)(r,t[a]));return r=>{for(let a=0;a<i;a++)s[a]=n[a](r);return s}}function bo(e,t){const s={...e,...t},i={};for(const n in s)e[n]!==void 0&&t[n]!==void 0&&(i[n]=ps(e[n])(e[n],t[n]));return n=>{for(const r in i)s[r]=i[r](n);return s}}function vo(e,t){const s=[],i={color:0,var:0,number:0};for(let n=0;n<t.values.length;n++){const r=t.types[n],a=e.indexes[r][i[r]],o=e.values[a]??0;s[n]=o,i[r]++}return s}const wo=(e,t)=>{const s=me.createTransformer(t),i=Ge(e),n=Ge(t);return i.indexes.var.length===n.indexes.var.length&&i.indexes.color.length===n.indexes.color.length&&i.indexes.number.length>=n.indexes.number.length?Et.has(e)&&!n.values.length||Et.has(t)&&!i.values.length?yo(e,t):qe(Aa(vo(i,n),n.values),s):lt(e,t)};function Ca(e,t,s){return typeof e=="number"&&typeof t=="number"&&typeof s=="number"?M(e,t,s):ps(e)(e,t)}const So=e=>{const t=({timestamp:s})=>e(s);return{start:(s=!0)=>V.update(t,s),stop:()=>he(t),now:()=>I.isProcessing?I.timestamp:U.now()}},Va=(e,t,s=10)=>{let i="";const n=Math.max(Math.round(t/s),2);for(let r=0;r<n;r++)i+=Math.round(e(r/(n-1))*1e4)/1e4+", ";return`linear(${i.substring(0,i.length-2)})`},ct=2e4;function fs(e){let t=0;const s=50;let i=e.next(t);for(;!i.done&&t<ct;)t+=s,i=e.next(t);return t>=ct?1/0:t}function To(e,t=100,s){const i=s({...e,keyframes:[0,t]}),n=Math.min(fs(i),ct);return{type:"keyframes",ease:r=>i.next(n*r).value/t,duration:z(n)}}const No=5;function Ma(e,t,s){const i=Math.max(t-No,0);return ca(s-e(i),t-i)}const j={stiffness:100,damping:10,mass:1,velocity:0,duration:800,bounce:.3,visualDuration:.3,restSpeed:{granular:.01,default:2},restDelta:{granular:.005,default:.5},minDuration:.01,maxDuration:10,minDamping:.05,maxDamping:1},St=.001;function Po({duration:e=j.duration,bounce:t=j.bounce,velocity:s=j.velocity,mass:i=j.mass}){let n,r,a=1-t;a=Z(j.minDamping,j.maxDamping,a),e=Z(j.minDuration,j.maxDuration,z(e)),a<1?(n=d=>{const c=d*a,u=c*e,m=c-s,p=Lt(d,a),f=Math.exp(-u);return St-m/p*f},r=d=>{const u=d*a*e,m=u*s+s,p=Math.pow(a,2)*Math.pow(d,2)*e,f=Math.exp(-u),g=Lt(Math.pow(d,2),a);return(-n(d)+St>0?-1:1)*((m-p)*f)/g}):(n=d=>{const c=Math.exp(-d*e),u=(d-s)*e+1;return-St+c*u},r=d=>{const c=Math.exp(-d*e),u=(s-d)*(e*e);return c*u});const o=5/e,l=Ao(n,r,o);if(e=X(e),isNaN(l))return{stiffness:j.stiffness,damping:j.damping,duration:e};{const d=Math.pow(l,2)*i;return{stiffness:d,damping:a*2*Math.sqrt(i*d),duration:e}}}const ko=12;function Ao(e,t,s){let i=s;for(let n=1;n<ko;n++)i=i-e(i)/t(i);return i}function Lt(e,t){return e*Math.sqrt(1-t*t)}const Co=["duration","bounce"],Vo=["stiffness","damping","mass"];function Ws(e,t){return t.some(s=>e[s]!==void 0)}function Mo(e){let t={velocity:j.velocity,stiffness:j.stiffness,damping:j.damping,mass:j.mass,isResolvedFromDuration:!1,...e};if(!Ws(e,Vo)&&Ws(e,Co))if(e.visualDuration){const s=e.visualDuration,i=2*Math.PI/(s*1.2),n=i*i,r=2*Z(.05,1,1-(e.bounce||0))*Math.sqrt(n);t={...t,mass:j.mass,stiffness:n,damping:r}}else{const s=Po(e);t={...t,...s,mass:j.mass},t.isResolvedFromDuration=!0}return t}function dt(e=j.visualDuration,t=j.bounce){const s=typeof e!="object"?{visualDuration:e,keyframes:[0,1],bounce:t}:e;let{restSpeed:i,restDelta:n}=s;const r=s.keyframes[0],a=s.keyframes[s.keyframes.length-1],o={done:!1,value:r},{stiffness:l,damping:d,mass:c,duration:u,velocity:m,isResolvedFromDuration:p}=Mo({...s,velocity:-z(s.velocity||0)}),f=m||0,g=d/(2*Math.sqrt(l*c)),b=a-r,x=z(Math.sqrt(l/c)),w=Math.abs(b)<5;i||(i=w?j.restSpeed.granular:j.restSpeed.default),n||(n=w?j.restDelta.granular:j.restDelta.default);let v;if(g<1){const S=Lt(x,g);v=k=>{const A=Math.exp(-g*x*k);return a-A*((f+g*x*b)/S*Math.sin(S*k)+b*Math.cos(S*k))}}else if(g===1)v=S=>a-Math.exp(-x*S)*(b+(f+x*b)*S);else{const S=x*Math.sqrt(g*g-1);v=k=>{const A=Math.exp(-g*x*k),N=Math.min(S*k,300);return a-A*((f+g*x*b)*Math.sinh(N)+S*b*Math.cosh(N))/S}}const P={calculatedDuration:p&&u||null,next:S=>{const k=v(S);if(p)o.done=S>=u;else{let A=S===0?f:0;g<1&&(A=S===0?X(f):Ma(v,S,k));const N=Math.abs(A)<=i,L=Math.abs(a-k)<=n;o.done=N&&L}return o.value=o.done?a:k,o},toString:()=>{const S=Math.min(fs(P),ct),k=Va(A=>P.next(S*A).value,S,30);return S+"ms "+k},toTransition:()=>{}};return P}dt.applyToOptions=e=>{const t=To(e,100,dt);return e.ease=t.ease,e.duration=X(t.duration),e.type="keyframes",e};function Ft({keyframes:e,velocity:t=0,power:s=.8,timeConstant:i=325,bounceDamping:n=10,bounceStiffness:r=500,modifyTarget:a,min:o,max:l,restDelta:d=.5,restSpeed:c}){const u=e[0],m={done:!1,value:u},p=N=>o!==void 0&&N<o||l!==void 0&&N>l,f=N=>o===void 0?l:l===void 0||Math.abs(o-N)<Math.abs(l-N)?o:l;let g=s*t;const b=u+g,x=a===void 0?b:a(b);x!==b&&(g=x-u);const w=N=>-g*Math.exp(-N/i),v=N=>x+w(N),P=N=>{const L=w(N),B=v(N);m.done=Math.abs(L)<=d,m.value=m.done?x:B};let S,k;const A=N=>{p(m.value)&&(S=N,k=dt({keyframes:[m.value,f(m.value)],velocity:Ma(v,N,m.value),damping:n,stiffness:r,restDelta:d,restSpeed:c}))};return A(0),{calculatedDuration:null,next:N=>{let L=!1;return!k&&S===void 0&&(L=!0,P(N),A(N)),S!==void 0&&N>=S?k.next(N-S):(!L&&P(N),m)}}}function jo(e,t,s){const i=[],n=s||J.mix||Ca,r=e.length-1;for(let a=0;a<r;a++){let o=n(e[a],e[a+1]);if(t){const l=Array.isArray(t)?t[a]||G:t;o=qe(l,o)}i.push(o)}return i}function Do(e,t,{clamp:s=!0,ease:i,mixer:n}={}){const r=e.length;if(as(r===t.length),r===1)return()=>t[0];if(r===2&&t[0]===t[1])return()=>t[1];const a=e[0]===e[1];e[0]>e[r-1]&&(e=[...e].reverse(),t=[...t].reverse());const o=jo(t,i,n),l=o.length,d=c=>{if(a&&c<e[0])return t[0];let u=0;if(l>1)for(;u<e.length-2&&!(c<e[u+1]);u++);const m=$e(e[u],e[u+1],c);return o[u](m)};return s?c=>d(Z(e[0],e[r-1],c)):d}function Ro(e,t){const s=e[e.length-1];for(let i=1;i<=t;i++){const n=$e(0,t,i);e.push(M(s,1,n))}}function Eo(e){const t=[0];return Ro(t,e.length-1),t}function Lo(e,t){return e.map(s=>s*t)}function Fo(e,t){return e.map(()=>t||xa).splice(0,e.length-1)}function He({duration:e=300,keyframes:t,times:s,ease:i="easeInOut"}){const n=Gr(i)?i.map(Is):Is(i),r={done:!1,value:t[0]},a=Lo(s&&s.length===t.length?s:Eo(t),e),o=Do(a,t,{ease:Array.isArray(n)?n:Fo(t,n)});return{calculatedDuration:e,next:l=>(r.value=o(l),r.done=l>=e,r)}}const Io=e=>e!==null;function gs(e,{repeat:t,repeatType:s="loop"},i,n=1){const r=e.filter(Io),o=n<0||t&&s!=="loop"&&t%2===1?0:r.length-1;return!o||i===void 0?r[o]:i}const Oo={decay:Ft,inertia:Ft,tween:He,keyframes:He,spring:dt};function ja(e){typeof e.type=="string"&&(e.type=Oo[e.type])}class ys{constructor(){this.updateFinished()}get finished(){return this._finished}updateFinished(){this._finished=new Promise(t=>{this.resolve=t})}notifyFinished(){this.resolve()}then(t,s){return this.finished.then(t,s)}}const Bo=e=>e/100;class xs extends ys{constructor(t){super(),this.state="idle",this.startTime=null,this.isStopped=!1,this.currentTime=0,this.holdTime=null,this.playbackSpeed=1,this.stop=()=>{var i,n;const{motionValue:s}=this.options;s&&s.updatedAt!==U.now()&&this.tick(U.now()),this.isStopped=!0,this.state!=="idle"&&(this.teardown(),(n=(i=this.options).onStop)==null||n.call(i))},this.options=t,this.initAnimation(),this.play(),t.autoplay===!1&&this.pause()}initAnimation(){const{options:t}=this;ja(t);const{type:s=He,repeat:i=0,repeatDelay:n=0,repeatType:r,velocity:a=0}=t;let{keyframes:o}=t;const l=s||He;l!==He&&typeof o[0]!="number"&&(this.mixKeyframes=qe(Bo,Ca(o[0],o[1])),o=[0,100]);const d=l({...t,keyframes:o});r==="mirror"&&(this.mirroredGenerator=l({...t,keyframes:[...o].reverse(),velocity:-a})),d.calculatedDuration===null&&(d.calculatedDuration=fs(d));const{calculatedDuration:c}=d;this.calculatedDuration=c,this.resolvedDuration=c+n,this.totalDuration=this.resolvedDuration*(i+1)-n,this.generator=d}updateTime(t){const s=Math.round(t-this.startTime)*this.playbackSpeed;this.holdTime!==null?this.currentTime=this.holdTime:this.currentTime=s}tick(t,s=!1){const{generator:i,totalDuration:n,mixKeyframes:r,mirroredGenerator:a,resolvedDuration:o,calculatedDuration:l}=this;if(this.startTime===null)return i.next(0);const{delay:d=0,keyframes:c,repeat:u,repeatType:m,repeatDelay:p,type:f,onUpdate:g,finalKeyframe:b}=this.options;this.speed>0?this.startTime=Math.min(this.startTime,t):this.speed<0&&(this.startTime=Math.min(t-n/this.speed,this.startTime)),s?this.currentTime=t:this.updateTime(t);const x=this.currentTime-d*(this.playbackSpeed>=0?1:-1),w=this.playbackSpeed>=0?x<0:x>n;this.currentTime=Math.max(x,0),this.state==="finished"&&this.holdTime===null&&(this.currentTime=n);let v=this.currentTime,P=i;if(u){const N=Math.min(this.currentTime,n)/o;let L=Math.floor(N),B=N%1;!B&&N>=1&&(B=1),B===1&&L--,L=Math.min(L,u+1),!!(L%2)&&(m==="reverse"?(B=1-B,p&&(B-=p/o)):m==="mirror"&&(P=a)),v=Z(0,1,B)*o}const S=w?{done:!1,value:c[0]}:P.next(v);r&&(S.value=r(S.value));let{done:k}=S;!w&&l!==null&&(k=this.playbackSpeed>=0?this.currentTime>=n:this.currentTime<=0);const A=this.holdTime===null&&(this.state==="finished"||this.state==="running"&&k);return A&&f!==Ft&&(S.value=gs(c,this.options,b,this.speed)),g&&g(S.value),A&&this.finish(),S}then(t,s){return this.finished.then(t,s)}get duration(){return z(this.calculatedDuration)}get iterationDuration(){const{delay:t=0}=this.options||{};return this.duration+z(t)}get time(){return z(this.currentTime)}set time(t){var s;t=X(t),this.currentTime=t,this.startTime===null||this.holdTime!==null||this.playbackSpeed===0?this.holdTime=t:this.driver&&(this.startTime=this.driver.now()-t/this.playbackSpeed),(s=this.driver)==null||s.start(!1)}get speed(){return this.playbackSpeed}set speed(t){this.updateTime(U.now());const s=this.playbackSpeed!==t;this.playbackSpeed=t,s&&(this.time=z(this.currentTime))}play(){var n,r;if(this.isStopped)return;const{driver:t=So,startTime:s}=this.options;this.driver||(this.driver=t(a=>this.tick(a))),(r=(n=this.options).onPlay)==null||r.call(n);const i=this.driver.now();this.state==="finished"?(this.updateFinished(),this.startTime=i):this.holdTime!==null?this.startTime=i-this.holdTime:this.startTime||(this.startTime=s??i),this.state==="finished"&&this.speed<0&&(this.startTime+=this.calculatedDuration),this.holdTime=null,this.state="running",this.driver.start()}pause(){this.state="paused",this.updateTime(U.now()),this.holdTime=this.currentTime}complete(){this.state!=="running"&&this.play(),this.state="finished",this.holdTime=null}finish(){var t,s;this.notifyFinished(),this.teardown(),this.state="finished",(s=(t=this.options).onComplete)==null||s.call(t)}cancel(){var t,s;this.holdTime=null,this.startTime=0,this.tick(0),this.teardown(),(s=(t=this.options).onCancel)==null||s.call(t)}teardown(){this.state="idle",this.stopDriver(),this.startTime=this.holdTime=null}stopDriver(){this.driver&&(this.driver.stop(),this.driver=void 0)}sample(t){return this.startTime=0,this.tick(t,!0)}attachTimeline(t){var s;return this.options.allowFlatten&&(this.options.type="keyframes",this.options.ease="linear",this.initAnimation()),(s=this.driver)==null||s.stop(),t.observe(this)}}function Ho(e){for(let t=1;t<e.length;t++)e[t]??(e[t]=e[t-1])}const be=e=>e*180/Math.PI,It=e=>{const t=be(Math.atan2(e[1],e[0]));return Ot(t)},Uo={x:4,y:5,translateX:4,translateY:5,scaleX:0,scaleY:3,scale:e=>(Math.abs(e[0])+Math.abs(e[3]))/2,rotate:It,rotateZ:It,skewX:e=>be(Math.atan(e[1])),skewY:e=>be(Math.atan(e[2])),skew:e=>(Math.abs(e[1])+Math.abs(e[2]))/2},Ot=e=>(e=e%360,e<0&&(e+=360),e),Ks=It,$s=e=>Math.sqrt(e[0]*e[0]+e[1]*e[1]),zs=e=>Math.sqrt(e[4]*e[4]+e[5]*e[5]),Wo={x:12,y:13,z:14,translateX:12,translateY:13,translateZ:14,scaleX:$s,scaleY:zs,scale:e=>($s(e)+zs(e))/2,rotateX:e=>Ot(be(Math.atan2(e[6],e[5]))),rotateY:e=>Ot(be(Math.atan2(-e[2],e[0]))),rotateZ:Ks,rotate:Ks,skewX:e=>be(Math.atan(e[4])),skewY:e=>be(Math.atan(e[1])),skew:e=>(Math.abs(e[1])+Math.abs(e[4]))/2};function Bt(e){return e.includes("scale")?1:0}function Ht(e,t){if(!e||e==="none")return Bt(t);const s=e.match(/^matrix3d\(([-\d.e\s,]+)\)$/u);let i,n;if(s)i=Wo,n=s;else{const o=e.match(/^matrix\(([-\d.e\s,]+)\)$/u);i=Uo,n=o}if(!n)return Bt(t);const r=i[t],a=n[1].split(",").map($o);return typeof r=="function"?r(a):a[r]}const Ko=(e,t)=>{const{transform:s="none"}=getComputedStyle(e);return Ht(s,t)};function $o(e){return parseFloat(e.trim())}const Ee=["transformPerspective","x","y","z","translateX","translateY","translateZ","scale","scaleX","scaleY","rotate","rotateX","rotateY","rotateZ","skew","skewX","skewY"],Le=new Set(Ee),Gs=e=>e===Re||e===T,zo=new Set(["x","y","z"]),Go=Ee.filter(e=>!zo.has(e));function _o(e){const t=[];return Go.forEach(s=>{const i=e.getValue(s);i!==void 0&&(t.push([s,i.get()]),i.set(s.startsWith("scale")?1:0))}),t}const ve={width:({x:e},{paddingLeft:t="0",paddingRight:s="0"})=>e.max-e.min-parseFloat(t)-parseFloat(s),height:({y:e},{paddingTop:t="0",paddingBottom:s="0"})=>e.max-e.min-parseFloat(t)-parseFloat(s),top:(e,{top:t})=>parseFloat(t),left:(e,{left:t})=>parseFloat(t),bottom:({y:e},{top:t})=>parseFloat(t)+(e.max-e.min),right:({x:e},{left:t})=>parseFloat(t)+(e.max-e.min),x:(e,{transform:t})=>Ht(t,"x"),y:(e,{transform:t})=>Ht(t,"y")};ve.translateX=ve.x;ve.translateY=ve.y;const we=new Set;let Ut=!1,Wt=!1,Kt=!1;function Da(){if(Wt){const e=Array.from(we).filter(i=>i.needsMeasurement),t=new Set(e.map(i=>i.element)),s=new Map;t.forEach(i=>{const n=_o(i);n.length&&(s.set(i,n),i.render())}),e.forEach(i=>i.measureInitialState()),t.forEach(i=>{i.render();const n=s.get(i);n&&n.forEach(([r,a])=>{var o;(o=i.getValue(r))==null||o.set(a)})}),e.forEach(i=>i.measureEndState()),e.forEach(i=>{i.suspendedScrollY!==void 0&&window.scrollTo(0,i.suspendedScrollY)})}Wt=!1,Ut=!1,we.forEach(e=>e.complete(Kt)),we.clear()}function Ra(){we.forEach(e=>{e.readKeyframes(),e.needsMeasurement&&(Wt=!0)})}function Xo(){Kt=!0,Ra(),Da(),Kt=!1}class bs{constructor(t,s,i,n,r,a=!1){this.state="pending",this.isAsync=!1,this.needsMeasurement=!1,this.unresolvedKeyframes=[...t],this.onComplete=s,this.name=i,this.motionValue=n,this.element=r,this.isAsync=a}scheduleResolve(){this.state="scheduled",this.isAsync?(we.add(this),Ut||(Ut=!0,V.read(Ra),V.resolveKeyframes(Da))):(this.readKeyframes(),this.complete())}readKeyframes(){const{unresolvedKeyframes:t,name:s,element:i,motionValue:n}=this;if(t[0]===null){const r=n==null?void 0:n.get(),a=t[t.length-1];if(r!==void 0)t[0]=r;else if(i&&s){const o=i.readValue(s,a);o!=null&&(t[0]=o)}t[0]===void 0&&(t[0]=a),n&&r===void 0&&n.set(t[0])}Ho(t)}setFinalKeyframe(){}measureInitialState(){}renderEndStyles(){}measureEndState(){}complete(t=!1){this.state="complete",this.onComplete(this.unresolvedKeyframes,this.finalKeyframe,t),we.delete(this)}cancel(){this.state==="scheduled"&&(we.delete(this),this.state="pending")}resume(){this.state==="pending"&&this.scheduleResolve()}}const Yo=e=>e.startsWith("--");function qo(e,t,s){Yo(t)?e.style.setProperty(t,s):e.style[t]=s}const Zo=rs(()=>window.ScrollTimeline!==void 0),Jo={};function Qo(e,t){const s=rs(e);return()=>Jo[t]??s()}const Ea=Qo(()=>{try{document.createElement("div").animate({opacity:0},{easing:"linear(0, 1)"})}catch{return!1}return!0},"linearEasing"),Oe=([e,t,s,i])=>`cubic-bezier(${e}, ${t}, ${s}, ${i})`,_s={linear:"linear",ease:"ease",easeIn:"ease-in",easeOut:"ease-out",easeInOut:"ease-in-out",circIn:Oe([0,.65,.55,1]),circOut:Oe([.55,0,1,.45]),backIn:Oe([.31,.01,.66,-.59]),backOut:Oe([.33,1.53,.69,.99])};function La(e,t){if(e)return typeof e=="function"?Ea()?Va(e,t):"ease-out":ba(e)?Oe(e):Array.isArray(e)?e.map(s=>La(s,t)||_s.easeOut):_s[e]}function el(e,t,s,{delay:i=0,duration:n=300,repeat:r=0,repeatType:a="loop",ease:o="easeOut",times:l}={},d=void 0){const c={[t]:s};l&&(c.offset=l);const u=La(o,n);Array.isArray(u)&&(c.easing=u);const m={delay:i,duration:n,easing:Array.isArray(u)?"linear":u,fill:"both",iterations:r+1,direction:a==="reverse"?"alternate":"normal"};return d&&(m.pseudoElement=d),e.animate(c,m)}function Fa(e){return typeof e=="function"&&"applyToOptions"in e}function tl({type:e,...t}){return Fa(e)&&Ea()?e.applyToOptions(t):(t.duration??(t.duration=300),t.ease??(t.ease="easeOut"),t)}class sl extends ys{constructor(t){if(super(),this.finishedTime=null,this.isStopped=!1,!t)return;const{element:s,name:i,keyframes:n,pseudoElement:r,allowFlatten:a=!1,finalKeyframe:o,onComplete:l}=t;this.isPseudoElement=!!r,this.allowFlatten=a,this.options=t,as(typeof t.type!="string");const d=tl(t);this.animation=el(s,i,n,d,r),d.autoplay===!1&&this.animation.pause(),this.animation.onfinish=()=>{if(this.finishedTime=this.time,!r){const c=gs(n,this.options,o,this.speed);this.updateMotionValue?this.updateMotionValue(c):qo(s,i,c),this.animation.cancel()}l==null||l(),this.notifyFinished()}}play(){this.isStopped||(this.animation.play(),this.state==="finished"&&this.updateFinished())}pause(){this.animation.pause()}complete(){var t,s;(s=(t=this.animation).finish)==null||s.call(t)}cancel(){try{this.animation.cancel()}catch{}}stop(){if(this.isStopped)return;this.isStopped=!0;const{state:t}=this;t==="idle"||t==="finished"||(this.updateMotionValue?this.updateMotionValue():this.commitStyles(),this.isPseudoElement||this.cancel())}commitStyles(){var t,s;this.isPseudoElement||(s=(t=this.animation).commitStyles)==null||s.call(t)}get duration(){var s,i;const t=((i=(s=this.animation.effect)==null?void 0:s.getComputedTiming)==null?void 0:i.call(s).duration)||0;return z(Number(t))}get iterationDuration(){const{delay:t=0}=this.options||{};return this.duration+z(t)}get time(){return z(Number(this.animation.currentTime)||0)}set time(t){this.finishedTime=null,this.animation.currentTime=X(t)}get speed(){return this.animation.playbackRate}set speed(t){t<0&&(this.finishedTime=null),this.animation.playbackRate=t}get state(){return this.finishedTime!==null?"finished":this.animation.playState}get startTime(){return Number(this.animation.startTime)}set startTime(t){this.animation.startTime=t}attachTimeline({timeline:t,observe:s}){var i;return this.allowFlatten&&((i=this.animation.effect)==null||i.updateTiming({easing:"linear"})),this.animation.onfinish=null,t&&Zo()?(this.animation.timeline=t,G):s(this)}}const Ia={anticipate:fa,backInOut:pa,circInOut:ya};function il(e){return e in Ia}function nl(e){typeof e.ease=="string"&&il(e.ease)&&(e.ease=Ia[e.ease])}const Xs=10;class al extends sl{constructor(t){nl(t),ja(t),super(t),t.startTime&&(this.startTime=t.startTime),this.options=t}updateMotionValue(t){const{motionValue:s,onUpdate:i,onComplete:n,element:r,...a}=this.options;if(!s)return;if(t!==void 0){s.set(t);return}const o=new xs({...a,autoplay:!1}),l=X(this.finishedTime??this.time);s.setWithVelocity(o.sample(l-Xs).value,o.sample(l).value,Xs),o.stop()}}const Ys=(e,t)=>t==="zIndex"?!1:!!(typeof e=="number"||Array.isArray(e)||typeof e=="string"&&(me.test(e)||e==="0")&&!e.startsWith("url("));function rl(e){const t=e[0];if(e.length===1)return!0;for(let s=0;s<e.length;s++)if(e[s]!==t)return!0}function ol(e,t,s,i){const n=e[0];if(n===null)return!1;if(t==="display"||t==="visibility")return!0;const r=e[e.length-1],a=Ys(n,t),o=Ys(r,t);return!a||!o?!1:rl(e)||(s==="spring"||Fa(s))&&i}function $t(e){e.duration=0,e.type="keyframes"}const ll=new Set(["opacity","clipPath","filter","transform"]),cl=rs(()=>Object.hasOwnProperty.call(Element.prototype,"animate"));function dl(e){var c;const{motionValue:t,name:s,repeatDelay:i,repeatType:n,damping:r,type:a}=e;if(!(((c=t==null?void 0:t.owner)==null?void 0:c.current)instanceof HTMLElement))return!1;const{onUpdate:l,transformTemplate:d}=t.owner.getProps();return cl()&&s&&ll.has(s)&&(s!=="transform"||!d)&&!l&&!i&&n!=="mirror"&&r!==0&&a!=="inertia"}const ul=40;class hl extends ys{constructor({autoplay:t=!0,delay:s=0,type:i="keyframes",repeat:n=0,repeatDelay:r=0,repeatType:a="loop",keyframes:o,name:l,motionValue:d,element:c,...u}){var f;super(),this.stop=()=>{var g,b;this._animation&&(this._animation.stop(),(g=this.stopTimeline)==null||g.call(this)),(b=this.keyframeResolver)==null||b.cancel()},this.createdAt=U.now();const m={autoplay:t,delay:s,type:i,repeat:n,repeatDelay:r,repeatType:a,name:l,motionValue:d,element:c,...u},p=(c==null?void 0:c.KeyframeResolver)||bs;this.keyframeResolver=new p(o,(g,b,x)=>this.onKeyframesResolved(g,b,m,!x),l,d,c),(f=this.keyframeResolver)==null||f.scheduleResolve()}onKeyframesResolved(t,s,i,n){this.keyframeResolver=void 0;const{name:r,type:a,velocity:o,delay:l,isHandoff:d,onUpdate:c}=i;this.resolvedAt=U.now(),ol(t,r,a,o)||((J.instantAnimations||!l)&&(c==null||c(gs(t,i,s))),t[0]=t[t.length-1],$t(i),i.repeat=0);const m={startTime:n?this.resolvedAt?this.resolvedAt-this.createdAt>ul?this.resolvedAt:this.createdAt:this.createdAt:void 0,finalKeyframe:s,...i,keyframes:t},p=!d&&dl(m)?new al({...m,element:m.motionValue.owner.current}):new xs(m);p.finished.then(()=>this.notifyFinished()).catch(G),this.pendingTimeline&&(this.stopTimeline=p.attachTimeline(this.pendingTimeline),this.pendingTimeline=void 0),this._animation=p}get finished(){return this._animation?this.animation.finished:this._finished}then(t,s){return this.finished.finally(t).then(()=>{})}get animation(){var t;return this._animation||((t=this.keyframeResolver)==null||t.resume(),Xo()),this._animation}get duration(){return this.animation.duration}get iterationDuration(){return this.animation.iterationDuration}get time(){return this.animation.time}set time(t){this.animation.time=t}get speed(){return this.animation.speed}get state(){return this.animation.state}set speed(t){this.animation.speed=t}get startTime(){return this.animation.startTime}attachTimeline(t){return this._animation?this.stopTimeline=this.animation.attachTimeline(t):this.pendingTimeline=t,()=>this.stop()}play(){this.animation.play()}pause(){this.animation.pause()}complete(){this.animation.complete()}cancel(){var t;this._animation&&this.animation.cancel(),(t=this.keyframeResolver)==null||t.cancel()}}const ml=/^var\(--(?:([\w-]+)|([\w-]+), ?([a-zA-Z\d ()%#.,-]+))\)/u;function pl(e){const t=ml.exec(e);if(!t)return[,];const[,s,i,n]=t;return[`--${s??i}`,n]}function Oa(e,t,s=1){const[i,n]=pl(e);if(!i)return;const r=window.getComputedStyle(t).getPropertyValue(i);if(r){const a=r.trim();return ra(a)?parseFloat(a):a}return us(n)?Oa(n,t,s+1):n}function vs(e,t){return(e==null?void 0:e[t])??(e==null?void 0:e.default)??e}const Ba=new Set(["width","height","top","left","right","bottom",...Ee]),fl={test:e=>e==="auto",parse:e=>e},Ha=e=>t=>t.test(e),Ua=[Re,T,Y,ee,ao,no,fl],qs=e=>Ua.find(Ha(e));function gl(e){return typeof e=="number"?e===0:e!==null?e==="none"||e==="0"||la(e):!0}const yl=new Set(["brightness","contrast","saturate","opacity"]);function xl(e){const[t,s]=e.slice(0,-1).split("(");if(t==="drop-shadow")return e;const[i]=s.match(hs)||[];if(!i)return e;const n=s.replace(i,"");let r=yl.has(t)?1:0;return i!==s&&(r*=100),t+"("+r+n+")"}const bl=/\b([a-z-]*)\(.*?\)/gu,zt={...me,getAnimatableNone:e=>{const t=e.match(bl);return t?t.map(xl).join(" "):e}},Zs={...Re,transform:Math.round},vl={rotate:ee,rotateX:ee,rotateY:ee,rotateZ:ee,scale:tt,scaleX:tt,scaleY:tt,scaleZ:tt,skew:ee,skewX:ee,skewY:ee,distance:T,translateX:T,translateY:T,translateZ:T,x:T,y:T,z:T,perspective:T,transformPerspective:T,opacity:ze,originX:Os,originY:Os,originZ:T},ws={borderWidth:T,borderTopWidth:T,borderRightWidth:T,borderBottomWidth:T,borderLeftWidth:T,borderRadius:T,radius:T,borderTopLeftRadius:T,borderTopRightRadius:T,borderBottomRightRadius:T,borderBottomLeftRadius:T,width:T,maxWidth:T,height:T,maxHeight:T,top:T,right:T,bottom:T,left:T,padding:T,paddingTop:T,paddingRight:T,paddingBottom:T,paddingLeft:T,margin:T,marginTop:T,marginRight:T,marginBottom:T,marginLeft:T,backgroundPositionX:T,backgroundPositionY:T,...vl,zIndex:Zs,fillOpacity:ze,strokeOpacity:ze,numOctaves:Zs},wl={...ws,color:R,backgroundColor:R,outlineColor:R,fill:R,stroke:R,borderColor:R,borderTopColor:R,borderRightColor:R,borderBottomColor:R,borderLeftColor:R,filter:zt,WebkitFilter:zt},Wa=e=>wl[e];function Ka(e,t){let s=Wa(e);return s!==zt&&(s=me),s.getAnimatableNone?s.getAnimatableNone(t):void 0}const Sl=new Set(["auto","none","0"]);function Tl(e,t,s){let i=0,n;for(;i<e.length&&!n;){const r=e[i];typeof r=="string"&&!Sl.has(r)&&Ge(r).values.length&&(n=e[i]),i++}if(n&&s)for(const r of t)e[r]=Ka(s,n)}class Nl extends bs{constructor(t,s,i,n,r){super(t,s,i,n,r,!0)}readKeyframes(){const{unresolvedKeyframes:t,element:s,name:i}=this;if(!s||!s.current)return;super.readKeyframes();for(let l=0;l<t.length;l++){let d=t[l];if(typeof d=="string"&&(d=d.trim(),us(d))){const c=Oa(d,s.current);c!==void 0&&(t[l]=c),l===t.length-1&&(this.finalKeyframe=d)}}if(this.resolveNoneKeyframes(),!Ba.has(i)||t.length!==2)return;const[n,r]=t,a=qs(n),o=qs(r);if(a!==o)if(Gs(a)&&Gs(o))for(let l=0;l<t.length;l++){const d=t[l];typeof d=="string"&&(t[l]=parseFloat(d))}else ve[i]&&(this.needsMeasurement=!0)}resolveNoneKeyframes(){const{unresolvedKeyframes:t,name:s}=this,i=[];for(let n=0;n<t.length;n++)(t[n]===null||gl(t[n]))&&i.push(n);i.length&&Tl(t,i,s)}measureInitialState(){const{element:t,unresolvedKeyframes:s,name:i}=this;if(!t||!t.current)return;i==="height"&&(this.suspendedScrollY=window.pageYOffset),this.measuredOrigin=ve[i](t.measureViewportBox(),window.getComputedStyle(t.current)),s[0]=this.measuredOrigin;const n=s[s.length-1];n!==void 0&&t.getValue(i,n).jump(n,!1)}measureEndState(){var o;const{element:t,name:s,unresolvedKeyframes:i}=this;if(!t||!t.current)return;const n=t.getValue(s);n&&n.jump(this.measuredOrigin,!1);const r=i.length-1,a=i[r];i[r]=ve[s](t.measureViewportBox(),window.getComputedStyle(t.current)),a!==null&&this.finalKeyframe===void 0&&(this.finalKeyframe=a),(o=this.removedTransforms)!=null&&o.length&&this.removedTransforms.forEach(([l,d])=>{t.getValue(l).set(d)}),this.resolveNoneKeyframes()}}function Pl(e,t,s){if(e instanceof EventTarget)return[e];if(typeof e=="string"){let i=document;const n=(s==null?void 0:s[e])??i.querySelectorAll(e);return n?Array.from(n):[]}return Array.from(e)}const $a=(e,t)=>t&&typeof e=="number"?t.transform(e):e;function za(e){return oa(e)&&"offsetHeight"in e}const Js=30,kl=e=>!isNaN(parseFloat(e));class Al{constructor(t,s={}){this.canTrackVelocity=null,this.events={},this.updateAndNotify=i=>{var r;const n=U.now();if(this.updatedAt!==n&&this.setPrevFrameValue(),this.prev=this.current,this.setCurrent(i),this.current!==this.prev&&((r=this.events.change)==null||r.notify(this.current),this.dependents))for(const a of this.dependents)a.dirty()},this.hasAnimated=!1,this.setCurrent(t),this.owner=s.owner}setCurrent(t){this.current=t,this.updatedAt=U.now(),this.canTrackVelocity===null&&t!==void 0&&(this.canTrackVelocity=kl(this.current))}setPrevFrameValue(t=this.current){this.prevFrameValue=t,this.prevUpdatedAt=this.updatedAt}onChange(t){return this.on("change",t)}on(t,s){this.events[t]||(this.events[t]=new os);const i=this.events[t].add(s);return t==="change"?()=>{i(),V.read(()=>{this.events.change.getSize()||this.stop()})}:i}clearListeners(){for(const t in this.events)this.events[t].clear()}attach(t,s){this.passiveEffect=t,this.stopPassiveEffect=s}set(t){this.passiveEffect?this.passiveEffect(t,this.updateAndNotify):this.updateAndNotify(t)}setWithVelocity(t,s,i){this.set(s),this.prev=void 0,this.prevFrameValue=t,this.prevUpdatedAt=this.updatedAt-i}jump(t,s=!0){this.updateAndNotify(t),this.prev=t,this.prevUpdatedAt=this.prevFrameValue=void 0,s&&this.stop(),this.stopPassiveEffect&&this.stopPassiveEffect()}dirty(){var t;(t=this.events.change)==null||t.notify(this.current)}addDependent(t){this.dependents||(this.dependents=new Set),this.dependents.add(t)}removeDependent(t){this.dependents&&this.dependents.delete(t)}get(){return this.current}getPrevious(){return this.prev}getVelocity(){const t=U.now();if(!this.canTrackVelocity||this.prevFrameValue===void 0||t-this.updatedAt>Js)return 0;const s=Math.min(this.updatedAt-this.prevUpdatedAt,Js);return ca(parseFloat(this.current)-parseFloat(this.prevFrameValue),s)}start(t){return this.stop(),new Promise(s=>{this.hasAnimated=!0,this.animation=t(s),this.events.animationStart&&this.events.animationStart.notify()}).then(()=>{this.events.animationComplete&&this.events.animationComplete.notify(),this.clearAnimation()})}stop(){this.animation&&(this.animation.stop(),this.events.animationCancel&&this.events.animationCancel.notify()),this.clearAnimation()}isAnimating(){return!!this.animation}clearAnimation(){delete this.animation}destroy(){var t,s;(t=this.dependents)==null||t.clear(),(s=this.events.destroy)==null||s.notify(),this.clearListeners(),this.stop(),this.stopPassiveEffect&&this.stopPassiveEffect()}}function Me(e,t){return new Al(e,t)}const{schedule:Ss}=va(queueMicrotask,!1),_={x:!1,y:!1};function Ga(){return _.x||_.y}function Cl(e){return e==="x"||e==="y"?_[e]?null:(_[e]=!0,()=>{_[e]=!1}):_.x||_.y?null:(_.x=_.y=!0,()=>{_.x=_.y=!1})}function _a(e,t){const s=Pl(e),i=new AbortController,n={passive:!0,...t,signal:i.signal};return[s,n,()=>i.abort()]}function Qs(e){return!(e.pointerType==="touch"||Ga())}function Vl(e,t,s={}){const[i,n,r]=_a(e,s),a=o=>{if(!Qs(o))return;const{target:l}=o,d=t(l,o);if(typeof d!="function"||!l)return;const c=u=>{Qs(u)&&(d(u),l.removeEventListener("pointerleave",c))};l.addEventListener("pointerleave",c,n)};return i.forEach(o=>{o.addEventListener("pointerenter",a,n)}),r}const Xa=(e,t)=>t?e===t?!0:Xa(e,t.parentElement):!1,Ts=e=>e.pointerType==="mouse"?typeof e.button!="number"||e.button<=0:e.isPrimary!==!1,Ml=new Set(["BUTTON","INPUT","SELECT","TEXTAREA","A"]);function jl(e){return Ml.has(e.tagName)||e.tabIndex!==-1}const at=new WeakSet;function ei(e){return t=>{t.key==="Enter"&&e(t)}}function Tt(e,t){e.dispatchEvent(new PointerEvent("pointer"+t,{isPrimary:!0,bubbles:!0}))}const Dl=(e,t)=>{const s=e.currentTarget;if(!s)return;const i=ei(()=>{if(at.has(s))return;Tt(s,"down");const n=ei(()=>{Tt(s,"up")}),r=()=>Tt(s,"cancel");s.addEventListener("keyup",n,t),s.addEventListener("blur",r,t)});s.addEventListener("keydown",i,t),s.addEventListener("blur",()=>s.removeEventListener("keydown",i),t)};function ti(e){return Ts(e)&&!Ga()}function Rl(e,t,s={}){const[i,n,r]=_a(e,s),a=o=>{const l=o.currentTarget;if(!ti(o))return;at.add(l);const d=t(l,o),c=(p,f)=>{window.removeEventListener("pointerup",u),window.removeEventListener("pointercancel",m),at.has(l)&&at.delete(l),ti(p)&&typeof d=="function"&&d(p,{success:f})},u=p=>{c(p,l===window||l===document||s.useGlobalTarget||Xa(l,p.target))},m=p=>{c(p,!1)};window.addEventListener("pointerup",u,n),window.addEventListener("pointercancel",m,n)};return i.forEach(o=>{(s.useGlobalTarget?window:o).addEventListener("pointerdown",a,n),za(o)&&(o.addEventListener("focus",d=>Dl(d,n)),!jl(o)&&!o.hasAttribute("tabindex")&&(o.tabIndex=0))}),r}function Ya(e){return oa(e)&&"ownerSVGElement"in e}function El(e){return Ya(e)&&e.tagName==="svg"}const O=e=>!!(e&&e.getVelocity),Ll=[...Ua,R,me],Fl=e=>Ll.find(Ha(e)),Ns=y.createContext({transformPagePoint:e=>e,isStatic:!1,reducedMotion:"never"});function si(e,t){if(typeof e=="function")return e(t);e!=null&&(e.current=t)}function Il(...e){return t=>{let s=!1;const i=e.map(n=>{const r=si(n,t);return!s&&typeof r=="function"&&(s=!0),r});if(s)return()=>{for(let n=0;n<i.length;n++){const r=i[n];typeof r=="function"?r():si(e[n],null)}}}}function Ol(...e){return y.useCallback(Il(...e),e)}class Bl extends y.Component{getSnapshotBeforeUpdate(t){const s=this.props.childRef.current;if(s&&t.isPresent&&!this.props.isPresent){const i=s.offsetParent,n=za(i)&&i.offsetWidth||0,r=this.props.sizeRef.current;r.height=s.offsetHeight||0,r.width=s.offsetWidth||0,r.top=s.offsetTop,r.left=s.offsetLeft,r.right=n-r.width-r.left}return null}componentDidUpdate(){}render(){return this.props.children}}function Hl({children:e,isPresent:t,anchorX:s,root:i}){const n=y.useId(),r=y.useRef(null),a=y.useRef({width:0,height:0,top:0,left:0,right:0}),{nonce:o}=y.useContext(Ns),l=Ol(r,e==null?void 0:e.ref);return y.useInsertionEffect(()=>{const{width:d,height:c,top:u,left:m,right:p}=a.current;if(t||!r.current||!d||!c)return;const f=s==="left"?`left: ${m}`:`right: ${p}`;r.current.dataset.motionPopId=n;const g=document.createElement("style");o&&(g.nonce=o);const b=i??document.head;return b.appendChild(g),g.sheet&&g.sheet.insertRule(`
          [data-motion-pop-id="${n}"] {
            position: absolute !important;
            width: ${d}px !important;
            height: ${c}px !important;
            ${f}px !important;
            top: ${u}px !important;
          }
        `),()=>{b.contains(g)&&b.removeChild(g)}},[t]),h.jsx(Bl,{isPresent:t,childRef:r,sizeRef:a,children:y.cloneElement(e,{ref:l})})}const Ul=({children:e,initial:t,isPresent:s,onExitComplete:i,custom:n,presenceAffectsLayout:r,mode:a,anchorX:o,root:l})=>{const d=ts(Wl),c=y.useId();let u=!0,m=y.useMemo(()=>(u=!1,{id:c,initial:t,isPresent:s,custom:n,onExitComplete:p=>{d.set(p,!0);for(const f of d.values())if(!f)return;i&&i()},register:p=>(d.set(p,!1),()=>d.delete(p))}),[s,d,i]);return r&&u&&(m={...m}),y.useMemo(()=>{d.forEach((p,f)=>d.set(f,!1))},[s]),y.useEffect(()=>{!s&&!d.size&&i&&i()},[s]),a==="popLayout"&&(e=h.jsx(Hl,{isPresent:s,anchorX:o,root:l,children:e})),h.jsx(pt.Provider,{value:m,children:e})};function Wl(){return new Map}function qa(e=!0){const t=y.useContext(pt);if(t===null)return[!0,null];const{isPresent:s,onExitComplete:i,register:n}=t,r=y.useId();y.useEffect(()=>{if(e)return n(r)},[e]);const a=y.useCallback(()=>e&&i&&i(r),[r,i,e]);return!s&&i?[!1,a]:[!0]}const st=e=>e.key||"";function ii(e){const t=[];return y.Children.forEach(e,s=>{y.isValidElement(s)&&t.push(s)}),t}const Se=({children:e,custom:t,initial:s=!0,onExitComplete:i,presenceAffectsLayout:n=!0,mode:r="sync",propagate:a=!1,anchorX:o="left",root:l})=>{const[d,c]=qa(a),u=y.useMemo(()=>ii(e),[e]),m=a&&!d?[]:u.map(st),p=y.useRef(!0),f=y.useRef(u),g=ts(()=>new Map),[b,x]=y.useState(u),[w,v]=y.useState(u);aa(()=>{p.current=!1,f.current=u;for(let k=0;k<w.length;k++){const A=st(w[k]);m.includes(A)?g.delete(A):g.get(A)!==!0&&g.set(A,!1)}},[w,m.length,m.join("-")]);const P=[];if(u!==b){let k=[...u];for(let A=0;A<w.length;A++){const N=w[A],L=st(N);m.includes(L)||(k.splice(A,0,N),P.push(N))}return r==="wait"&&P.length&&(k=P),v(ii(k)),x(u),null}const{forceRender:S}=y.useContext(es);return h.jsx(h.Fragment,{children:w.map(k=>{const A=st(k),N=a&&!d?!1:u===w||m.includes(A),L=()=>{if(g.has(A))g.set(A,!0);else return;let B=!0;g.forEach(Q=>{Q||(B=!1)}),B&&(S==null||S(),v(f.current),a&&(c==null||c()),i&&i())};return h.jsx(Ul,{isPresent:N,initial:!p.current||s?void 0:!1,custom:t,presenceAffectsLayout:n,mode:r,root:l,onExitComplete:N?void 0:L,anchorX:o,children:k},A)})})},Za=y.createContext({strict:!1}),ni={animation:["animate","variants","whileHover","whileTap","exit","whileInView","whileFocus","whileDrag"],exit:["exit"],drag:["drag","dragControls"],focus:["whileFocus"],hover:["whileHover","onHoverStart","onHoverEnd"],tap:["whileTap","onTap","onTapStart","onTapCancel"],pan:["onPan","onPanStart","onPanSessionStart","onPanEnd"],inView:["whileInView","onViewportEnter","onViewportLeave"],layout:["layout","layoutId"]},je={};for(const e in ni)je[e]={isEnabled:t=>ni[e].some(s=>!!t[s])};function Kl(e){for(const t in e)je[t]={...je[t],...e[t]}}const $l=new Set(["animate","exit","variants","initial","style","values","variants","transition","transformTemplate","custom","inherit","onBeforeLayoutMeasure","onAnimationStart","onAnimationComplete","onUpdate","onDragStart","onDrag","onDragEnd","onMeasureDragConstraints","onDirectionLock","onDragTransitionEnd","_dragX","_dragY","onHoverStart","onHoverEnd","onViewportEnter","onViewportLeave","globalTapTarget","ignoreStrict","viewport"]);function ut(e){return e.startsWith("while")||e.startsWith("drag")&&e!=="draggable"||e.startsWith("layout")||e.startsWith("onTap")||e.startsWith("onPan")||e.startsWith("onLayout")||$l.has(e)}let Ja=e=>!ut(e);function zl(e){typeof e=="function"&&(Ja=t=>t.startsWith("on")?!ut(t):e(t))}try{zl(require("@emotion/is-prop-valid").default)}catch{}function Gl(e,t,s){const i={};for(const n in e)n==="values"&&typeof e.values=="object"||(Ja(n)||s===!0&&ut(n)||!t&&!ut(n)||e.draggable&&n.startsWith("onDrag"))&&(i[n]=e[n]);return i}const ft=y.createContext({});function gt(e){return e!==null&&typeof e=="object"&&typeof e.start=="function"}function _e(e){return typeof e=="string"||Array.isArray(e)}const Ps=["animate","whileInView","whileFocus","whileHover","whileTap","whileDrag","exit"],ks=["initial",...Ps];function yt(e){return gt(e.animate)||ks.some(t=>_e(e[t]))}function Qa(e){return!!(yt(e)||e.variants)}function _l(e,t){if(yt(e)){const{initial:s,animate:i}=e;return{initial:s===!1||_e(s)?s:void 0,animate:_e(i)?i:void 0}}return e.inherit!==!1?t:{}}function Xl(e){const{initial:t,animate:s}=_l(e,y.useContext(ft));return y.useMemo(()=>({initial:t,animate:s}),[ai(t),ai(s)])}function ai(e){return Array.isArray(e)?e.join(" "):e}const Xe={};function Yl(e){for(const t in e)Xe[t]=e[t],ds(t)&&(Xe[t].isCSSVariable=!0)}function er(e,{layout:t,layoutId:s}){return Le.has(e)||e.startsWith("origin")||(t||s!==void 0)&&(!!Xe[e]||e==="opacity")}const ql={x:"translateX",y:"translateY",z:"translateZ",transformPerspective:"perspective"},Zl=Ee.length;function Jl(e,t,s){let i="",n=!0;for(let r=0;r<Zl;r++){const a=Ee[r],o=e[a];if(o===void 0)continue;let l=!0;if(typeof o=="number"?l=o===(a.startsWith("scale")?1:0):l=parseFloat(o)===0,!l||s){const d=$a(o,ws[a]);if(!l){n=!1;const c=ql[a]||a;i+=`${c}(${d}) `}s&&(t[a]=d)}}return i=i.trim(),s?i=s(t,n?"":i):n&&(i="none"),i}function As(e,t,s){const{style:i,vars:n,transformOrigin:r}=e;let a=!1,o=!1;for(const l in t){const d=t[l];if(Le.has(l)){a=!0;continue}else if(ds(l)){n[l]=d;continue}else{const c=$a(d,ws[l]);l.startsWith("origin")?(o=!0,r[l]=c):i[l]=c}}if(t.transform||(a||s?i.transform=Jl(t,e.transform,s):i.transform&&(i.transform="none")),o){const{originX:l="50%",originY:d="50%",originZ:c=0}=r;i.transformOrigin=`${l} ${d} ${c}`}}const Cs=()=>({style:{},transform:{},transformOrigin:{},vars:{}});function tr(e,t,s){for(const i in t)!O(t[i])&&!er(i,s)&&(e[i]=t[i])}function Ql({transformTemplate:e},t){return y.useMemo(()=>{const s=Cs();return As(s,t,e),Object.assign({},s.vars,s.style)},[t])}function ec(e,t){const s=e.style||{},i={};return tr(i,s,e),Object.assign(i,Ql(e,t)),i}function tc(e,t){const s={},i=ec(e,t);return e.drag&&e.dragListener!==!1&&(s.draggable=!1,i.userSelect=i.WebkitUserSelect=i.WebkitTouchCallout="none",i.touchAction=e.drag===!0?"none":`pan-${e.drag==="x"?"y":"x"}`),e.tabIndex===void 0&&(e.onTap||e.onTapStart||e.whileTap)&&(s.tabIndex=0),s.style=i,s}const sc={offset:"stroke-dashoffset",array:"stroke-dasharray"},ic={offset:"strokeDashoffset",array:"strokeDasharray"};function nc(e,t,s=1,i=0,n=!0){e.pathLength=1;const r=n?sc:ic;e[r.offset]=T.transform(-i);const a=T.transform(t),o=T.transform(s);e[r.array]=`${a} ${o}`}function sr(e,{attrX:t,attrY:s,attrScale:i,pathLength:n,pathSpacing:r=1,pathOffset:a=0,...o},l,d,c){if(As(e,o,d),l){e.style.viewBox&&(e.attrs.viewBox=e.style.viewBox);return}e.attrs=e.style,e.style={};const{attrs:u,style:m}=e;u.transform&&(m.transform=u.transform,delete u.transform),(m.transform||u.transformOrigin)&&(m.transformOrigin=u.transformOrigin??"50% 50%",delete u.transformOrigin),m.transform&&(m.transformBox=(c==null?void 0:c.transformBox)??"fill-box",delete u.transformBox),t!==void 0&&(u.x=t),s!==void 0&&(u.y=s),i!==void 0&&(u.scale=i),n!==void 0&&nc(u,n,r,a,!1)}const ir=()=>({...Cs(),attrs:{}}),nr=e=>typeof e=="string"&&e.toLowerCase()==="svg";function ac(e,t,s,i){const n=y.useMemo(()=>{const r=ir();return sr(r,t,nr(i),e.transformTemplate,e.style),{...r.attrs,style:{...r.style}}},[t]);if(e.style){const r={};tr(r,e.style,e),n.style={...r,...n.style}}return n}const rc=["animate","circle","defs","desc","ellipse","g","image","line","filter","marker","mask","metadata","path","pattern","polygon","polyline","rect","stop","switch","symbol","svg","text","tspan","use","view"];function Vs(e){return typeof e!="string"||e.includes("-")?!1:!!(rc.indexOf(e)>-1||/[A-Z]/u.test(e))}function oc(e,t,s,{latestValues:i},n,r=!1){const o=(Vs(e)?ac:tc)(t,i,n,e),l=Gl(t,typeof e=="string",r),d=e!==y.Fragment?{...l,...o,ref:s}:{},{children:c}=t,u=y.useMemo(()=>O(c)?c.get():c,[c]);return y.createElement(e,{...d,children:u})}function ri(e){const t=[{},{}];return e==null||e.values.forEach((s,i)=>{t[0][i]=s.get(),t[1][i]=s.getVelocity()}),t}function Ms(e,t,s,i){if(typeof t=="function"){const[n,r]=ri(i);t=t(s!==void 0?s:e.custom,n,r)}if(typeof t=="string"&&(t=e.variants&&e.variants[t]),typeof t=="function"){const[n,r]=ri(i);t=t(s!==void 0?s:e.custom,n,r)}return t}function rt(e){return O(e)?e.get():e}function lc({scrapeMotionValuesFromProps:e,createRenderState:t},s,i,n){return{latestValues:cc(s,i,n,e),renderState:t()}}function cc(e,t,s,i){const n={},r=i(e,{});for(const m in r)n[m]=rt(r[m]);let{initial:a,animate:o}=e;const l=yt(e),d=Qa(e);t&&d&&!l&&e.inherit!==!1&&(a===void 0&&(a=t.initial),o===void 0&&(o=t.animate));let c=s?s.initial===!1:!1;c=c||a===!1;const u=c?o:a;if(u&&typeof u!="boolean"&&!gt(u)){const m=Array.isArray(u)?u:[u];for(let p=0;p<m.length;p++){const f=Ms(e,m[p]);if(f){const{transitionEnd:g,transition:b,...x}=f;for(const w in x){let v=x[w];if(Array.isArray(v)){const P=c?v.length-1:0;v=v[P]}v!==null&&(n[w]=v)}for(const w in g)n[w]=g[w]}}}return n}const ar=e=>(t,s)=>{const i=y.useContext(ft),n=y.useContext(pt),r=()=>lc(e,t,i,n);return s?r():ts(r)};function js(e,t,s){var r;const{style:i}=e,n={};for(const a in i)(O(i[a])||t.style&&O(t.style[a])||er(a,e)||((r=s==null?void 0:s.getValue(a))==null?void 0:r.liveStyle)!==void 0)&&(n[a]=i[a]);return n}const dc=ar({scrapeMotionValuesFromProps:js,createRenderState:Cs});function rr(e,t,s){const i=js(e,t,s);for(const n in e)if(O(e[n])||O(t[n])){const r=Ee.indexOf(n)!==-1?"attr"+n.charAt(0).toUpperCase()+n.substring(1):n;i[r]=e[n]}return i}const uc=ar({scrapeMotionValuesFromProps:rr,createRenderState:ir}),hc=Symbol.for("motionComponentSymbol");function Pe(e){return e&&typeof e=="object"&&Object.prototype.hasOwnProperty.call(e,"current")}function mc(e,t,s){return y.useCallback(i=>{i&&e.onMount&&e.onMount(i),t&&(i?t.mount(i):t.unmount()),s&&(typeof s=="function"?s(i):Pe(s)&&(s.current=i))},[t])}const Ds=e=>e.replace(/([a-z])([A-Z])/gu,"$1-$2").toLowerCase(),pc="framerAppearId",or="data-"+Ds(pc),lr=y.createContext({});function fc(e,t,s,i,n){var g,b;const{visualElement:r}=y.useContext(ft),a=y.useContext(Za),o=y.useContext(pt),l=y.useContext(Ns).reducedMotion,d=y.useRef(null);i=i||a.renderer,!d.current&&i&&(d.current=i(e,{visualState:t,parent:r,props:s,presenceContext:o,blockInitialAnimation:o?o.initial===!1:!1,reducedMotionConfig:l}));const c=d.current,u=y.useContext(lr);c&&!c.projection&&n&&(c.type==="html"||c.type==="svg")&&gc(d.current,s,n,u);const m=y.useRef(!1);y.useInsertionEffect(()=>{c&&m.current&&c.update(s,o)});const p=s[or],f=y.useRef(!!p&&!((g=window.MotionHandoffIsComplete)!=null&&g.call(window,p))&&((b=window.MotionHasOptimisedAnimation)==null?void 0:b.call(window,p)));return aa(()=>{c&&(m.current=!0,window.MotionIsMounted=!0,c.updateFeatures(),c.scheduleRenderMicrotask(),f.current&&c.animationState&&c.animationState.animateChanges())}),y.useEffect(()=>{c&&(!f.current&&c.animationState&&c.animationState.animateChanges(),f.current&&(queueMicrotask(()=>{var x;(x=window.MotionHandoffMarkAsComplete)==null||x.call(window,p)}),f.current=!1),c.enteringChildren=void 0)}),c}function gc(e,t,s,i){const{layoutId:n,layout:r,drag:a,dragConstraints:o,layoutScroll:l,layoutRoot:d,layoutCrossfade:c}=t;e.projection=new s(e.latestValues,t["data-framer-portal-id"]?void 0:cr(e.parent)),e.projection.setOptions({layoutId:n,layout:r,alwaysMeasureLayout:!!a||o&&Pe(o),visualElement:e,animationType:typeof r=="string"?r:"both",initialPromotionConfig:i,crossfade:c,layoutScroll:l,layoutRoot:d})}function cr(e){if(e)return e.options.allowProjection!==!1?e.projection:cr(e.parent)}function Nt(e,{forwardMotionProps:t=!1}={},s,i){s&&Kl(s);const n=Vs(e)?uc:dc;function r(o,l){let d;const c={...y.useContext(Ns),...o,layoutId:yc(o)},{isStatic:u}=c,m=Xl(o),p=n(o,u);if(!u&&ss){xc();const f=bc(c);d=f.MeasureLayout,m.visualElement=fc(e,p,c,i,f.ProjectionNode)}return h.jsxs(ft.Provider,{value:m,children:[d&&m.visualElement?h.jsx(d,{visualElement:m.visualElement,...c}):null,oc(e,o,mc(p,m.visualElement,l),p,u,t)]})}r.displayName=`motion.${typeof e=="string"?e:`create(${e.displayName??e.name??""})`}`;const a=y.forwardRef(r);return a[hc]=e,a}function yc({layoutId:e}){const t=y.useContext(es).id;return t&&e!==void 0?t+"-"+e:e}function xc(e,t){y.useContext(Za).strict}function bc(e){const{drag:t,layout:s}=je;if(!t&&!s)return{};const i={...t,...s};return{MeasureLayout:t!=null&&t.isEnabled(e)||s!=null&&s.isEnabled(e)?i.MeasureLayout:void 0,ProjectionNode:i.ProjectionNode}}function vc(e,t){if(typeof Proxy>"u")return Nt;const s=new Map,i=(r,a)=>Nt(r,a,e,t),n=(r,a)=>i(r,a);return new Proxy(n,{get:(r,a)=>a==="create"?i:(s.has(a)||s.set(a,Nt(a,void 0,e,t)),s.get(a))})}function dr({top:e,left:t,right:s,bottom:i}){return{x:{min:t,max:s},y:{min:e,max:i}}}function wc({x:e,y:t}){return{top:t.min,right:e.max,bottom:t.max,left:e.min}}function Sc(e,t){if(!t)return e;const s=t({x:e.left,y:e.top}),i=t({x:e.right,y:e.bottom});return{top:s.y,left:s.x,bottom:i.y,right:i.x}}function Pt(e){return e===void 0||e===1}function Gt({scale:e,scaleX:t,scaleY:s}){return!Pt(e)||!Pt(t)||!Pt(s)}function ye(e){return Gt(e)||ur(e)||e.z||e.rotate||e.rotateX||e.rotateY||e.skewX||e.skewY}function ur(e){return oi(e.x)||oi(e.y)}function oi(e){return e&&e!=="0%"}function ht(e,t,s){const i=e-s,n=t*i;return s+n}function li(e,t,s,i,n){return n!==void 0&&(e=ht(e,n,i)),ht(e,s,i)+t}function _t(e,t=0,s=1,i,n){e.min=li(e.min,t,s,i,n),e.max=li(e.max,t,s,i,n)}function hr(e,{x:t,y:s}){_t(e.x,t.translate,t.scale,t.originPoint),_t(e.y,s.translate,s.scale,s.originPoint)}const ci=.999999999999,di=1.0000000000001;function Tc(e,t,s,i=!1){const n=s.length;if(!n)return;t.x=t.y=1;let r,a;for(let o=0;o<n;o++){r=s[o],a=r.projectionDelta;const{visualElement:l}=r.options;l&&l.props.style&&l.props.style.display==="contents"||(i&&r.options.layoutScroll&&r.scroll&&r!==r.root&&Ae(e,{x:-r.scroll.offset.x,y:-r.scroll.offset.y}),a&&(t.x*=a.x.scale,t.y*=a.y.scale,hr(e,a)),i&&ye(r.latestValues)&&Ae(e,r.latestValues))}t.x<di&&t.x>ci&&(t.x=1),t.y<di&&t.y>ci&&(t.y=1)}function ke(e,t){e.min=e.min+t,e.max=e.max+t}function ui(e,t,s,i,n=.5){const r=M(e.min,e.max,n);_t(e,t,s,r,i)}function Ae(e,t){ui(e.x,t.x,t.scaleX,t.scale,t.originX),ui(e.y,t.y,t.scaleY,t.scale,t.originY)}function mr(e,t){return dr(Sc(e.getBoundingClientRect(),t))}function Nc(e,t,s){const i=mr(e,s),{scroll:n}=t;return n&&(ke(i.x,n.offset.x),ke(i.y,n.offset.y)),i}const hi=()=>({translate:0,scale:1,origin:0,originPoint:0}),Ce=()=>({x:hi(),y:hi()}),mi=()=>({min:0,max:0}),D=()=>({x:mi(),y:mi()}),Xt={current:null},pr={current:!1};function Pc(){if(pr.current=!0,!!ss)if(window.matchMedia){const e=window.matchMedia("(prefers-reduced-motion)"),t=()=>Xt.current=e.matches;e.addEventListener("change",t),t()}else Xt.current=!1}const kc=new WeakMap;function Ac(e,t,s){for(const i in t){const n=t[i],r=s[i];if(O(n))e.addValue(i,n);else if(O(r))e.addValue(i,Me(n,{owner:e}));else if(r!==n)if(e.hasValue(i)){const a=e.getValue(i);a.liveStyle===!0?a.jump(n):a.hasAnimated||a.set(n)}else{const a=e.getStaticValue(i);e.addValue(i,Me(a!==void 0?a:n,{owner:e}))}}for(const i in s)t[i]===void 0&&e.removeValue(i);return t}const pi=["AnimationStart","AnimationComplete","Update","BeforeLayoutMeasure","LayoutMeasure","LayoutAnimationStart","LayoutAnimationComplete"];class Cc{scrapeMotionValuesFromProps(t,s,i){return{}}constructor({parent:t,props:s,presenceContext:i,reducedMotionConfig:n,blockInitialAnimation:r,visualState:a},o={}){this.current=null,this.children=new Set,this.isVariantNode=!1,this.isControllingVariants=!1,this.shouldReduceMotion=null,this.values=new Map,this.KeyframeResolver=bs,this.features={},this.valueSubscriptions=new Map,this.prevMotionValues={},this.events={},this.propEventSubscriptions={},this.notifyUpdate=()=>this.notify("Update",this.latestValues),this.render=()=>{this.current&&(this.triggerBuild(),this.renderInstance(this.current,this.renderState,this.props.style,this.projection))},this.renderScheduledAt=0,this.scheduleRender=()=>{const m=U.now();this.renderScheduledAt<m&&(this.renderScheduledAt=m,V.render(this.render,!1,!0))};const{latestValues:l,renderState:d}=a;this.latestValues=l,this.baseTarget={...l},this.initialValues=s.initial?{...l}:{},this.renderState=d,this.parent=t,this.props=s,this.presenceContext=i,this.depth=t?t.depth+1:0,this.reducedMotionConfig=n,this.options=o,this.blockInitialAnimation=!!r,this.isControllingVariants=yt(s),this.isVariantNode=Qa(s),this.isVariantNode&&(this.variantChildren=new Set),this.manuallyAnimateOnMount=!!(t&&t.current);const{willChange:c,...u}=this.scrapeMotionValuesFromProps(s,{},this);for(const m in u){const p=u[m];l[m]!==void 0&&O(p)&&p.set(l[m])}}mount(t){var s;this.current=t,kc.set(t,this),this.projection&&!this.projection.instance&&this.projection.mount(t),this.parent&&this.isVariantNode&&!this.isControllingVariants&&(this.removeFromVariantTree=this.parent.addVariantChild(this)),this.values.forEach((i,n)=>this.bindToMotionValue(n,i)),pr.current||Pc(),this.shouldReduceMotion=this.reducedMotionConfig==="never"?!1:this.reducedMotionConfig==="always"?!0:Xt.current,(s=this.parent)==null||s.addChild(this),this.update(this.props,this.presenceContext)}unmount(){var t;this.projection&&this.projection.unmount(),he(this.notifyUpdate),he(this.render),this.valueSubscriptions.forEach(s=>s()),this.valueSubscriptions.clear(),this.removeFromVariantTree&&this.removeFromVariantTree(),(t=this.parent)==null||t.removeChild(this);for(const s in this.events)this.events[s].clear();for(const s in this.features){const i=this.features[s];i&&(i.unmount(),i.isMounted=!1)}this.current=null}addChild(t){this.children.add(t),this.enteringChildren??(this.enteringChildren=new Set),this.enteringChildren.add(t)}removeChild(t){this.children.delete(t),this.enteringChildren&&this.enteringChildren.delete(t)}bindToMotionValue(t,s){this.valueSubscriptions.has(t)&&this.valueSubscriptions.get(t)();const i=Le.has(t);i&&this.onBindTransform&&this.onBindTransform();const n=s.on("change",a=>{this.latestValues[t]=a,this.props.onUpdate&&V.preRender(this.notifyUpdate),i&&this.projection&&(this.projection.isTransformDirty=!0),this.scheduleRender()});let r;window.MotionCheckAppearSync&&(r=window.MotionCheckAppearSync(this,t,s)),this.valueSubscriptions.set(t,()=>{n(),r&&r(),s.owner&&s.stop()})}sortNodePosition(t){return!this.current||!this.sortInstanceNodePosition||this.type!==t.type?0:this.sortInstanceNodePosition(this.current,t.current)}updateFeatures(){let t="animation";for(t in je){const s=je[t];if(!s)continue;const{isEnabled:i,Feature:n}=s;if(!this.features[t]&&n&&i(this.props)&&(this.features[t]=new n(this)),this.features[t]){const r=this.features[t];r.isMounted?r.update():(r.mount(),r.isMounted=!0)}}}triggerBuild(){this.build(this.renderState,this.latestValues,this.props)}measureViewportBox(){return this.current?this.measureInstanceViewportBox(this.current,this.props):D()}getStaticValue(t){return this.latestValues[t]}setStaticValue(t,s){this.latestValues[t]=s}update(t,s){(t.transformTemplate||this.props.transformTemplate)&&this.scheduleRender(),this.prevProps=this.props,this.props=t,this.prevPresenceContext=this.presenceContext,this.presenceContext=s;for(let i=0;i<pi.length;i++){const n=pi[i];this.propEventSubscriptions[n]&&(this.propEventSubscriptions[n](),delete this.propEventSubscriptions[n]);const r="on"+n,a=t[r];a&&(this.propEventSubscriptions[n]=this.on(n,a))}this.prevMotionValues=Ac(this,this.scrapeMotionValuesFromProps(t,this.prevProps,this),this.prevMotionValues),this.handleChildMotionValue&&this.handleChildMotionValue()}getProps(){return this.props}getVariant(t){return this.props.variants?this.props.variants[t]:void 0}getDefaultTransition(){return this.props.transition}getTransformPagePoint(){return this.props.transformPagePoint}getClosestVariantNode(){return this.isVariantNode?this:this.parent?this.parent.getClosestVariantNode():void 0}addVariantChild(t){const s=this.getClosestVariantNode();if(s)return s.variantChildren&&s.variantChildren.add(t),()=>s.variantChildren.delete(t)}addValue(t,s){const i=this.values.get(t);s!==i&&(i&&this.removeValue(t),this.bindToMotionValue(t,s),this.values.set(t,s),this.latestValues[t]=s.get())}removeValue(t){this.values.delete(t);const s=this.valueSubscriptions.get(t);s&&(s(),this.valueSubscriptions.delete(t)),delete this.latestValues[t],this.removeValueFromRenderState(t,this.renderState)}hasValue(t){return this.values.has(t)}getValue(t,s){if(this.props.values&&this.props.values[t])return this.props.values[t];let i=this.values.get(t);return i===void 0&&s!==void 0&&(i=Me(s===null?void 0:s,{owner:this}),this.addValue(t,i)),i}readValue(t,s){let i=this.latestValues[t]!==void 0||!this.current?this.latestValues[t]:this.getBaseTargetFromProps(this.props,t)??this.readValueFromInstance(this.current,t,this.options);return i!=null&&(typeof i=="string"&&(ra(i)||la(i))?i=parseFloat(i):!Fl(i)&&me.test(s)&&(i=Ka(t,s)),this.setBaseTarget(t,O(i)?i.get():i)),O(i)?i.get():i}setBaseTarget(t,s){this.baseTarget[t]=s}getBaseTarget(t){var r;const{initial:s}=this.props;let i;if(typeof s=="string"||typeof s=="object"){const a=Ms(this.props,s,(r=this.presenceContext)==null?void 0:r.custom);a&&(i=a[t])}if(s&&i!==void 0)return i;const n=this.getBaseTargetFromProps(this.props,t);return n!==void 0&&!O(n)?n:this.initialValues[t]!==void 0&&i===void 0?void 0:this.baseTarget[t]}on(t,s){return this.events[t]||(this.events[t]=new os),this.events[t].add(s)}notify(t,...s){this.events[t]&&this.events[t].notify(...s)}scheduleRenderMicrotask(){Ss.render(this.render)}}class fr extends Cc{constructor(){super(...arguments),this.KeyframeResolver=Nl}sortInstanceNodePosition(t,s){return t.compareDocumentPosition(s)&2?1:-1}getBaseTargetFromProps(t,s){return t.style?t.style[s]:void 0}removeValueFromRenderState(t,{vars:s,style:i}){delete s[t],delete i[t]}handleChildMotionValue(){this.childSubscription&&(this.childSubscription(),delete this.childSubscription);const{children:t}=this.props;O(t)&&(this.childSubscription=t.on("change",s=>{this.current&&(this.current.textContent=`${s}`)}))}}function gr(e,{style:t,vars:s},i,n){const r=e.style;let a;for(a in t)r[a]=t[a];n==null||n.applyProjectionStyles(r,i);for(a in s)r.setProperty(a,s[a])}function Vc(e){return window.getComputedStyle(e)}class Mc extends fr{constructor(){super(...arguments),this.type="html",this.renderInstance=gr}readValueFromInstance(t,s){var i;if(Le.has(s))return(i=this.projection)!=null&&i.isProjecting?Bt(s):Ko(t,s);{const n=Vc(t),r=(ds(s)?n.getPropertyValue(s):n[s])||0;return typeof r=="string"?r.trim():r}}measureInstanceViewportBox(t,{transformPagePoint:s}){return mr(t,s)}build(t,s,i){As(t,s,i.transformTemplate)}scrapeMotionValuesFromProps(t,s,i){return js(t,s,i)}}const yr=new Set(["baseFrequency","diffuseConstant","kernelMatrix","kernelUnitLength","keySplines","keyTimes","limitingConeAngle","markerHeight","markerWidth","numOctaves","targetX","targetY","surfaceScale","specularConstant","specularExponent","stdDeviation","tableValues","viewBox","gradientTransform","pathLength","startOffset","textLength","lengthAdjust"]);function jc(e,t,s,i){gr(e,t,void 0,i);for(const n in t.attrs)e.setAttribute(yr.has(n)?n:Ds(n),t.attrs[n])}class Dc extends fr{constructor(){super(...arguments),this.type="svg",this.isSVGTag=!1,this.measureInstanceViewportBox=D}getBaseTargetFromProps(t,s){return t[s]}readValueFromInstance(t,s){if(Le.has(s)){const i=Wa(s);return i&&i.default||0}return s=yr.has(s)?s:Ds(s),t.getAttribute(s)}scrapeMotionValuesFromProps(t,s,i){return rr(t,s,i)}build(t,s,i){sr(t,s,this.isSVGTag,i.transformTemplate,i.style)}renderInstance(t,s,i,n){jc(t,s,i,n)}mount(t){this.isSVGTag=nr(t.tagName),super.mount(t)}}const Rc=(e,t)=>Vs(e)?new Dc(t):new Mc(t,{allowProjection:e!==y.Fragment});function Ve(e,t,s){const i=e.getProps();return Ms(i,t,s!==void 0?s:i.custom,e)}const Yt=e=>Array.isArray(e);function Ec(e,t,s){e.hasValue(t)?e.getValue(t).set(s):e.addValue(t,Me(s))}function Lc(e){return Yt(e)?e[e.length-1]||0:e}function Fc(e,t){const s=Ve(e,t);let{transitionEnd:i={},transition:n={},...r}=s||{};r={...r,...i};for(const a in r){const o=Lc(r[a]);Ec(e,a,o)}}function Ic(e){return!!(O(e)&&e.add)}function qt(e,t){const s=e.getValue("willChange");if(Ic(s))return s.add(t);if(!s&&J.WillChange){const i=new J.WillChange("auto");e.addValue("willChange",i),i.add(t)}}function xr(e){return e.props[or]}const Oc=e=>e!==null;function Bc(e,{repeat:t,repeatType:s="loop"},i){const n=e.filter(Oc),r=t&&s!=="loop"&&t%2===1?0:n.length-1;return n[r]}const Hc={type:"spring",stiffness:500,damping:25,restSpeed:10},Uc=e=>({type:"spring",stiffness:550,damping:e===0?2*Math.sqrt(550):30,restSpeed:10}),Wc={type:"keyframes",duration:.8},Kc={type:"keyframes",ease:[.25,.1,.35,1],duration:.3},$c=(e,{keyframes:t})=>t.length>2?Wc:Le.has(e)?e.startsWith("scale")?Uc(t[1]):Hc:Kc;function zc({when:e,delay:t,delayChildren:s,staggerChildren:i,staggerDirection:n,repeat:r,repeatType:a,repeatDelay:o,from:l,elapsed:d,...c}){return!!Object.keys(c).length}const Rs=(e,t,s,i={},n,r)=>a=>{const o=vs(i,e)||{},l=o.delay||i.delay||0;let{elapsed:d=0}=i;d=d-X(l);const c={keyframes:Array.isArray(s)?s:[null,s],ease:"easeOut",velocity:t.getVelocity(),...o,delay:-d,onUpdate:m=>{t.set(m),o.onUpdate&&o.onUpdate(m)},onComplete:()=>{a(),o.onComplete&&o.onComplete()},name:e,motionValue:t,element:r?void 0:n};zc(o)||Object.assign(c,$c(e,c)),c.duration&&(c.duration=X(c.duration)),c.repeatDelay&&(c.repeatDelay=X(c.repeatDelay)),c.from!==void 0&&(c.keyframes[0]=c.from);let u=!1;if((c.type===!1||c.duration===0&&!c.repeatDelay)&&($t(c),c.delay===0&&(u=!0)),(J.instantAnimations||J.skipAnimations)&&(u=!0,$t(c),c.delay=0),c.allowFlatten=!o.type&&!o.ease,u&&!r&&t.get()!==void 0){const m=Bc(c.keyframes,o);if(m!==void 0){V.update(()=>{c.onUpdate(m),c.onComplete()});return}}return o.isSync?new xs(c):new hl(c)};function Gc({protectedKeys:e,needsAnimating:t},s){const i=e.hasOwnProperty(s)&&t[s]!==!0;return t[s]=!1,i}function br(e,t,{delay:s=0,transitionOverride:i,type:n}={}){let{transition:r=e.getDefaultTransition(),transitionEnd:a,...o}=t;i&&(r=i);const l=[],d=n&&e.animationState&&e.animationState.getState()[n];for(const c in o){const u=e.getValue(c,e.latestValues[c]??null),m=o[c];if(m===void 0||d&&Gc(d,c))continue;const p={delay:s,...vs(r||{},c)},f=u.get();if(f!==void 0&&!u.isAnimating&&!Array.isArray(m)&&m===f&&!p.velocity)continue;let g=!1;if(window.MotionHandoffAnimation){const x=xr(e);if(x){const w=window.MotionHandoffAnimation(x,c,V);w!==null&&(p.startTime=w,g=!0)}}qt(e,c),u.start(Rs(c,u,m,e.shouldReduceMotion&&Ba.has(c)?{type:!1}:p,e,g));const b=u.animation;b&&l.push(b)}return a&&Promise.all(l).then(()=>{V.update(()=>{a&&Fc(e,a)})}),l}function vr(e,t,s,i=0,n=1){const r=Array.from(e).sort((d,c)=>d.sortNodePosition(c)).indexOf(t),a=e.size,o=(a-1)*i;return typeof s=="function"?s(r,a):n===1?r*i:o-r*i}function Zt(e,t,s={}){var l;const i=Ve(e,t,s.type==="exit"?(l=e.presenceContext)==null?void 0:l.custom:void 0);let{transition:n=e.getDefaultTransition()||{}}=i||{};s.transitionOverride&&(n=s.transitionOverride);const r=i?()=>Promise.all(br(e,i,s)):()=>Promise.resolve(),a=e.variantChildren&&e.variantChildren.size?(d=0)=>{const{delayChildren:c=0,staggerChildren:u,staggerDirection:m}=n;return _c(e,t,d,c,u,m,s)}:()=>Promise.resolve(),{when:o}=n;if(o){const[d,c]=o==="beforeChildren"?[r,a]:[a,r];return d().then(()=>c())}else return Promise.all([r(),a(s.delay)])}function _c(e,t,s=0,i=0,n=0,r=1,a){const o=[];for(const l of e.variantChildren)l.notify("AnimationStart",t),o.push(Zt(l,t,{...a,delay:s+(typeof i=="function"?0:i)+vr(e.variantChildren,l,i,n,r)}).then(()=>l.notify("AnimationComplete",t)));return Promise.all(o)}function Xc(e,t,s={}){e.notify("AnimationStart",t);let i;if(Array.isArray(t)){const n=t.map(r=>Zt(e,r,s));i=Promise.all(n)}else if(typeof t=="string")i=Zt(e,t,s);else{const n=typeof t=="function"?Ve(e,t,s.custom):t;i=Promise.all(br(e,n,s))}return i.then(()=>{e.notify("AnimationComplete",t)})}function wr(e,t){if(!Array.isArray(t))return!1;const s=t.length;if(s!==e.length)return!1;for(let i=0;i<s;i++)if(t[i]!==e[i])return!1;return!0}const Yc=ks.length;function Sr(e){if(!e)return;if(!e.isControllingVariants){const s=e.parent?Sr(e.parent)||{}:{};return e.props.initial!==void 0&&(s.initial=e.props.initial),s}const t={};for(let s=0;s<Yc;s++){const i=ks[s],n=e.props[i];(_e(n)||n===!1)&&(t[i]=n)}return t}const qc=[...Ps].reverse(),Zc=Ps.length;function Jc(e){return t=>Promise.all(t.map(({animation:s,options:i})=>Xc(e,s,i)))}function Qc(e){let t=Jc(e),s=fi(),i=!0;const n=l=>(d,c)=>{var m;const u=Ve(e,c,l==="exit"?(m=e.presenceContext)==null?void 0:m.custom:void 0);if(u){const{transition:p,transitionEnd:f,...g}=u;d={...d,...g,...f}}return d};function r(l){t=l(e)}function a(l){const{props:d}=e,c=Sr(e.parent)||{},u=[],m=new Set;let p={},f=1/0;for(let b=0;b<Zc;b++){const x=qc[b],w=s[x],v=d[x]!==void 0?d[x]:c[x],P=_e(v),S=x===l?w.isActive:null;S===!1&&(f=b);let k=v===c[x]&&v!==d[x]&&P;if(k&&i&&e.manuallyAnimateOnMount&&(k=!1),w.protectedKeys={...p},!w.isActive&&S===null||!v&&!w.prevProp||gt(v)||typeof v=="boolean")continue;const A=ed(w.prevProp,v);let N=A||x===l&&w.isActive&&!k&&P||b>f&&P,L=!1;const B=Array.isArray(v)?v:[v];let Q=B.reduce(n(x),{});S===!1&&(Q={});const{prevResolvedValues:Es={}}=w,Or={...Es,...Q},Ls=F=>{N=!0,m.has(F)&&(L=!0,m.delete(F)),w.needsAnimating[F]=!0;const W=e.getValue(F);W&&(W.liveStyle=!1)};for(const F in Or){const W=Q[F],fe=Es[F];if(p.hasOwnProperty(F))continue;let Te=!1;Yt(W)&&Yt(fe)?Te=!wr(W,fe):Te=W!==fe,Te?W!=null?Ls(F):m.add(F):W!==void 0&&m.has(F)?Ls(F):w.protectedKeys[F]=!0}w.prevProp=v,w.prevResolvedValues=Q,w.isActive&&(p={...p,...Q}),i&&e.blockInitialAnimation&&(N=!1);const Fs=k&&A;N&&(!Fs||L)&&u.push(...B.map(F=>{const W={type:x};if(typeof F=="string"&&i&&!Fs&&e.manuallyAnimateOnMount&&e.parent){const{parent:fe}=e,Te=Ve(fe,F);if(fe.enteringChildren&&Te){const{delayChildren:Br}=Te.transition||{};W.delay=vr(fe.enteringChildren,e,Br)}}return{animation:F,options:W}}))}if(m.size){const b={};if(typeof d.initial!="boolean"){const x=Ve(e,Array.isArray(d.initial)?d.initial[0]:d.initial);x&&x.transition&&(b.transition=x.transition)}m.forEach(x=>{const w=e.getBaseTarget(x),v=e.getValue(x);v&&(v.liveStyle=!0),b[x]=w??null}),u.push({animation:b})}let g=!!u.length;return i&&(d.initial===!1||d.initial===d.animate)&&!e.manuallyAnimateOnMount&&(g=!1),i=!1,g?t(u):Promise.resolve()}function o(l,d){var u;if(s[l].isActive===d)return Promise.resolve();(u=e.variantChildren)==null||u.forEach(m=>{var p;return(p=m.animationState)==null?void 0:p.setActive(l,d)}),s[l].isActive=d;const c=a(l);for(const m in s)s[m].protectedKeys={};return c}return{animateChanges:a,setActive:o,setAnimateFunction:r,getState:()=>s,reset:()=>{s=fi()}}}function ed(e,t){return typeof t=="string"?t!==e:Array.isArray(t)?!wr(t,e):!1}function ge(e=!1){return{isActive:e,protectedKeys:{},needsAnimating:{},prevResolvedValues:{}}}function fi(){return{animate:ge(!0),whileInView:ge(),whileHover:ge(),whileTap:ge(),whileDrag:ge(),whileFocus:ge(),exit:ge()}}class pe{constructor(t){this.isMounted=!1,this.node=t}update(){}}class td extends pe{constructor(t){super(t),t.animationState||(t.animationState=Qc(t))}updateAnimationControlsSubscription(){const{animate:t}=this.node.getProps();gt(t)&&(this.unmountControls=t.subscribe(this.node))}mount(){this.updateAnimationControlsSubscription()}update(){const{animate:t}=this.node.getProps(),{animate:s}=this.node.prevProps||{};t!==s&&this.updateAnimationControlsSubscription()}unmount(){var t;this.node.animationState.reset(),(t=this.unmountControls)==null||t.call(this)}}let sd=0;class id extends pe{constructor(){super(...arguments),this.id=sd++}update(){if(!this.node.presenceContext)return;const{isPresent:t,onExitComplete:s}=this.node.presenceContext,{isPresent:i}=this.node.prevPresenceContext||{};if(!this.node.animationState||t===i)return;const n=this.node.animationState.setActive("exit",!t);s&&!t&&n.then(()=>{s(this.id)})}mount(){const{register:t,onExitComplete:s}=this.node.presenceContext||{};s&&s(this.id),t&&(this.unmount=t(this.id))}unmount(){}}const nd={animation:{Feature:td},exit:{Feature:id}};function Ye(e,t,s,i={passive:!0}){return e.addEventListener(t,s,i),()=>e.removeEventListener(t,s)}function Qe(e){return{point:{x:e.pageX,y:e.pageY}}}const ad=e=>t=>Ts(t)&&e(t,Qe(t));function Ue(e,t,s,i){return Ye(e,t,ad(s),i)}const Tr=1e-4,rd=1-Tr,od=1+Tr,Nr=.01,ld=0-Nr,cd=0+Nr;function H(e){return e.max-e.min}function dd(e,t,s){return Math.abs(e-t)<=s}function gi(e,t,s,i=.5){e.origin=i,e.originPoint=M(t.min,t.max,e.origin),e.scale=H(s)/H(t),e.translate=M(s.min,s.max,e.origin)-e.originPoint,(e.scale>=rd&&e.scale<=od||isNaN(e.scale))&&(e.scale=1),(e.translate>=ld&&e.translate<=cd||isNaN(e.translate))&&(e.translate=0)}function We(e,t,s,i){gi(e.x,t.x,s.x,i?i.originX:void 0),gi(e.y,t.y,s.y,i?i.originY:void 0)}function yi(e,t,s){e.min=s.min+t.min,e.max=e.min+H(t)}function ud(e,t,s){yi(e.x,t.x,s.x),yi(e.y,t.y,s.y)}function xi(e,t,s){e.min=t.min-s.min,e.max=e.min+H(t)}function Ke(e,t,s){xi(e.x,t.x,s.x),xi(e.y,t.y,s.y)}function $(e){return[e("x"),e("y")]}const Pr=({current:e})=>e?e.ownerDocument.defaultView:null,bi=(e,t)=>Math.abs(e-t);function hd(e,t){const s=bi(e.x,t.x),i=bi(e.y,t.y);return Math.sqrt(s**2+i**2)}class kr{constructor(t,s,{transformPagePoint:i,contextWindow:n=window,dragSnapToOrigin:r=!1,distanceThreshold:a=3}={}){if(this.startEvent=null,this.lastMoveEvent=null,this.lastMoveEventInfo=null,this.handlers={},this.contextWindow=window,this.updatePoint=()=>{if(!(this.lastMoveEvent&&this.lastMoveEventInfo))return;const m=At(this.lastMoveEventInfo,this.history),p=this.startEvent!==null,f=hd(m.offset,{x:0,y:0})>=this.distanceThreshold;if(!p&&!f)return;const{point:g}=m,{timestamp:b}=I;this.history.push({...g,timestamp:b});const{onStart:x,onMove:w}=this.handlers;p||(x&&x(this.lastMoveEvent,m),this.startEvent=this.lastMoveEvent),w&&w(this.lastMoveEvent,m)},this.handlePointerMove=(m,p)=>{this.lastMoveEvent=m,this.lastMoveEventInfo=kt(p,this.transformPagePoint),V.update(this.updatePoint,!0)},this.handlePointerUp=(m,p)=>{this.end();const{onEnd:f,onSessionEnd:g,resumeAnimation:b}=this.handlers;if(this.dragSnapToOrigin&&b&&b(),!(this.lastMoveEvent&&this.lastMoveEventInfo))return;const x=At(m.type==="pointercancel"?this.lastMoveEventInfo:kt(p,this.transformPagePoint),this.history);this.startEvent&&f&&f(m,x),g&&g(m,x)},!Ts(t))return;this.dragSnapToOrigin=r,this.handlers=s,this.transformPagePoint=i,this.distanceThreshold=a,this.contextWindow=n||window;const o=Qe(t),l=kt(o,this.transformPagePoint),{point:d}=l,{timestamp:c}=I;this.history=[{...d,timestamp:c}];const{onSessionStart:u}=s;u&&u(t,At(l,this.history)),this.removeListeners=qe(Ue(this.contextWindow,"pointermove",this.handlePointerMove),Ue(this.contextWindow,"pointerup",this.handlePointerUp),Ue(this.contextWindow,"pointercancel",this.handlePointerUp))}updateHandlers(t){this.handlers=t}end(){this.removeListeners&&this.removeListeners(),he(this.updatePoint)}}function kt(e,t){return t?{point:t(e.point)}:e}function vi(e,t){return{x:e.x-t.x,y:e.y-t.y}}function At({point:e},t){return{point:e,delta:vi(e,Ar(t)),offset:vi(e,md(t)),velocity:pd(t,.1)}}function md(e){return e[0]}function Ar(e){return e[e.length-1]}function pd(e,t){if(e.length<2)return{x:0,y:0};let s=e.length-1,i=null;const n=Ar(e);for(;s>=0&&(i=e[s],!(n.timestamp-i.timestamp>X(t)));)s--;if(!i)return{x:0,y:0};const r=z(n.timestamp-i.timestamp);if(r===0)return{x:0,y:0};const a={x:(n.x-i.x)/r,y:(n.y-i.y)/r};return a.x===1/0&&(a.x=0),a.y===1/0&&(a.y=0),a}function fd(e,{min:t,max:s},i){return t!==void 0&&e<t?e=i?M(t,e,i.min):Math.max(e,t):s!==void 0&&e>s&&(e=i?M(s,e,i.max):Math.min(e,s)),e}function wi(e,t,s){return{min:t!==void 0?e.min+t:void 0,max:s!==void 0?e.max+s-(e.max-e.min):void 0}}function gd(e,{top:t,left:s,bottom:i,right:n}){return{x:wi(e.x,s,n),y:wi(e.y,t,i)}}function Si(e,t){let s=t.min-e.min,i=t.max-e.max;return t.max-t.min<e.max-e.min&&([s,i]=[i,s]),{min:s,max:i}}function yd(e,t){return{x:Si(e.x,t.x),y:Si(e.y,t.y)}}function xd(e,t){let s=.5;const i=H(e),n=H(t);return n>i?s=$e(t.min,t.max-i,e.min):i>n&&(s=$e(e.min,e.max-n,t.min)),Z(0,1,s)}function bd(e,t){const s={};return t.min!==void 0&&(s.min=t.min-e.min),t.max!==void 0&&(s.max=t.max-e.min),s}const Jt=.35;function vd(e=Jt){return e===!1?e=0:e===!0&&(e=Jt),{x:Ti(e,"left","right"),y:Ti(e,"top","bottom")}}function Ti(e,t,s){return{min:Ni(e,t),max:Ni(e,s)}}function Ni(e,t){return typeof e=="number"?e:e[t]||0}const wd=new WeakMap;class Sd{constructor(t){this.openDragLock=null,this.isDragging=!1,this.currentDirection=null,this.originPoint={x:0,y:0},this.constraints=!1,this.hasMutatedConstraints=!1,this.elastic=D(),this.latestPointerEvent=null,this.latestPanInfo=null,this.visualElement=t}start(t,{snapToCursor:s=!1,distanceThreshold:i}={}){const{presenceContext:n}=this.visualElement;if(n&&n.isPresent===!1)return;const r=u=>{const{dragSnapToOrigin:m}=this.getProps();m?this.pauseAnimation():this.stopAnimation(),s&&this.snapToCursor(Qe(u).point)},a=(u,m)=>{const{drag:p,dragPropagation:f,onDragStart:g}=this.getProps();if(p&&!f&&(this.openDragLock&&this.openDragLock(),this.openDragLock=Cl(p),!this.openDragLock))return;this.latestPointerEvent=u,this.latestPanInfo=m,this.isDragging=!0,this.currentDirection=null,this.resolveConstraints(),this.visualElement.projection&&(this.visualElement.projection.isAnimationBlocked=!0,this.visualElement.projection.target=void 0),$(x=>{let w=this.getAxisMotionValue(x).get()||0;if(Y.test(w)){const{projection:v}=this.visualElement;if(v&&v.layout){const P=v.layout.layoutBox[x];P&&(w=H(P)*(parseFloat(w)/100))}}this.originPoint[x]=w}),g&&V.postRender(()=>g(u,m)),qt(this.visualElement,"transform");const{animationState:b}=this.visualElement;b&&b.setActive("whileDrag",!0)},o=(u,m)=>{this.latestPointerEvent=u,this.latestPanInfo=m;const{dragPropagation:p,dragDirectionLock:f,onDirectionLock:g,onDrag:b}=this.getProps();if(!p&&!this.openDragLock)return;const{offset:x}=m;if(f&&this.currentDirection===null){this.currentDirection=Td(x),this.currentDirection!==null&&g&&g(this.currentDirection);return}this.updateAxis("x",m.point,x),this.updateAxis("y",m.point,x),this.visualElement.render(),b&&b(u,m)},l=(u,m)=>{this.latestPointerEvent=u,this.latestPanInfo=m,this.stop(u,m),this.latestPointerEvent=null,this.latestPanInfo=null},d=()=>$(u=>{var m;return this.getAnimationState(u)==="paused"&&((m=this.getAxisMotionValue(u).animation)==null?void 0:m.play())}),{dragSnapToOrigin:c}=this.getProps();this.panSession=new kr(t,{onSessionStart:r,onStart:a,onMove:o,onSessionEnd:l,resumeAnimation:d},{transformPagePoint:this.visualElement.getTransformPagePoint(),dragSnapToOrigin:c,distanceThreshold:i,contextWindow:Pr(this.visualElement)})}stop(t,s){const i=t||this.latestPointerEvent,n=s||this.latestPanInfo,r=this.isDragging;if(this.cancel(),!r||!n||!i)return;const{velocity:a}=n;this.startAnimation(a);const{onDragEnd:o}=this.getProps();o&&V.postRender(()=>o(i,n))}cancel(){this.isDragging=!1;const{projection:t,animationState:s}=this.visualElement;t&&(t.isAnimationBlocked=!1),this.panSession&&this.panSession.end(),this.panSession=void 0;const{dragPropagation:i}=this.getProps();!i&&this.openDragLock&&(this.openDragLock(),this.openDragLock=null),s&&s.setActive("whileDrag",!1)}updateAxis(t,s,i){const{drag:n}=this.getProps();if(!i||!it(t,n,this.currentDirection))return;const r=this.getAxisMotionValue(t);let a=this.originPoint[t]+i[t];this.constraints&&this.constraints[t]&&(a=fd(a,this.constraints[t],this.elastic[t])),r.set(a)}resolveConstraints(){var r;const{dragConstraints:t,dragElastic:s}=this.getProps(),i=this.visualElement.projection&&!this.visualElement.projection.layout?this.visualElement.projection.measure(!1):(r=this.visualElement.projection)==null?void 0:r.layout,n=this.constraints;t&&Pe(t)?this.constraints||(this.constraints=this.resolveRefConstraints()):t&&i?this.constraints=gd(i.layoutBox,t):this.constraints=!1,this.elastic=vd(s),n!==this.constraints&&i&&this.constraints&&!this.hasMutatedConstraints&&$(a=>{this.constraints!==!1&&this.getAxisMotionValue(a)&&(this.constraints[a]=bd(i.layoutBox[a],this.constraints[a]))})}resolveRefConstraints(){const{dragConstraints:t,onMeasureDragConstraints:s}=this.getProps();if(!t||!Pe(t))return!1;const i=t.current,{projection:n}=this.visualElement;if(!n||!n.layout)return!1;const r=Nc(i,n.root,this.visualElement.getTransformPagePoint());let a=yd(n.layout.layoutBox,r);if(s){const o=s(wc(a));this.hasMutatedConstraints=!!o,o&&(a=dr(o))}return a}startAnimation(t){const{drag:s,dragMomentum:i,dragElastic:n,dragTransition:r,dragSnapToOrigin:a,onDragTransitionEnd:o}=this.getProps(),l=this.constraints||{},d=$(c=>{if(!it(c,s,this.currentDirection))return;let u=l&&l[c]||{};a&&(u={min:0,max:0});const m=n?200:1e6,p=n?40:1e7,f={type:"inertia",velocity:i?t[c]:0,bounceStiffness:m,bounceDamping:p,timeConstant:750,restDelta:1,restSpeed:10,...r,...u};return this.startAxisValueAnimation(c,f)});return Promise.all(d).then(o)}startAxisValueAnimation(t,s){const i=this.getAxisMotionValue(t);return qt(this.visualElement,t),i.start(Rs(t,i,0,s,this.visualElement,!1))}stopAnimation(){$(t=>this.getAxisMotionValue(t).stop())}pauseAnimation(){$(t=>{var s;return(s=this.getAxisMotionValue(t).animation)==null?void 0:s.pause()})}getAnimationState(t){var s;return(s=this.getAxisMotionValue(t).animation)==null?void 0:s.state}getAxisMotionValue(t){const s=`_drag${t.toUpperCase()}`,i=this.visualElement.getProps(),n=i[s];return n||this.visualElement.getValue(t,(i.initial?i.initial[t]:void 0)||0)}snapToCursor(t){$(s=>{const{drag:i}=this.getProps();if(!it(s,i,this.currentDirection))return;const{projection:n}=this.visualElement,r=this.getAxisMotionValue(s);if(n&&n.layout){const{min:a,max:o}=n.layout.layoutBox[s];r.set(t[s]-M(a,o,.5))}})}scalePositionWithinConstraints(){if(!this.visualElement.current)return;const{drag:t,dragConstraints:s}=this.getProps(),{projection:i}=this.visualElement;if(!Pe(s)||!i||!this.constraints)return;this.stopAnimation();const n={x:0,y:0};$(a=>{const o=this.getAxisMotionValue(a);if(o&&this.constraints!==!1){const l=o.get();n[a]=xd({min:l,max:l},this.constraints[a])}});const{transformTemplate:r}=this.visualElement.getProps();this.visualElement.current.style.transform=r?r({},""):"none",i.root&&i.root.updateScroll(),i.updateLayout(),this.resolveConstraints(),$(a=>{if(!it(a,t,null))return;const o=this.getAxisMotionValue(a),{min:l,max:d}=this.constraints[a];o.set(M(l,d,n[a]))})}addListeners(){if(!this.visualElement.current)return;wd.set(this.visualElement,this);const t=this.visualElement.current,s=Ue(t,"pointerdown",l=>{const{drag:d,dragListener:c=!0}=this.getProps();d&&c&&this.start(l)}),i=()=>{const{dragConstraints:l}=this.getProps();Pe(l)&&l.current&&(this.constraints=this.resolveRefConstraints())},{projection:n}=this.visualElement,r=n.addEventListener("measure",i);n&&!n.layout&&(n.root&&n.root.updateScroll(),n.updateLayout()),V.read(i);const a=Ye(window,"resize",()=>this.scalePositionWithinConstraints()),o=n.addEventListener("didUpdate",(({delta:l,hasLayoutChanged:d})=>{this.isDragging&&d&&($(c=>{const u=this.getAxisMotionValue(c);u&&(this.originPoint[c]+=l[c].translate,u.set(u.get()+l[c].translate))}),this.visualElement.render())}));return()=>{a(),s(),r(),o&&o()}}getProps(){const t=this.visualElement.getProps(),{drag:s=!1,dragDirectionLock:i=!1,dragPropagation:n=!1,dragConstraints:r=!1,dragElastic:a=Jt,dragMomentum:o=!0}=t;return{...t,drag:s,dragDirectionLock:i,dragPropagation:n,dragConstraints:r,dragElastic:a,dragMomentum:o}}}function it(e,t,s){return(t===!0||t===e)&&(s===null||s===e)}function Td(e,t=10){let s=null;return Math.abs(e.y)>t?s="y":Math.abs(e.x)>t&&(s="x"),s}class Nd extends pe{constructor(t){super(t),this.removeGroupControls=G,this.removeListeners=G,this.controls=new Sd(t)}mount(){const{dragControls:t}=this.node.getProps();t&&(this.removeGroupControls=t.subscribe(this.controls)),this.removeListeners=this.controls.addListeners()||G}unmount(){this.removeGroupControls(),this.removeListeners()}}const Pi=e=>(t,s)=>{e&&V.postRender(()=>e(t,s))};class Pd extends pe{constructor(){super(...arguments),this.removePointerDownListener=G}onPointerDown(t){this.session=new kr(t,this.createPanHandlers(),{transformPagePoint:this.node.getTransformPagePoint(),contextWindow:Pr(this.node)})}createPanHandlers(){const{onPanSessionStart:t,onPanStart:s,onPan:i,onPanEnd:n}=this.node.getProps();return{onSessionStart:Pi(t),onStart:Pi(s),onMove:i,onEnd:(r,a)=>{delete this.session,n&&V.postRender(()=>n(r,a))}}}mount(){this.removePointerDownListener=Ue(this.node.current,"pointerdown",t=>this.onPointerDown(t))}update(){this.session&&this.session.updateHandlers(this.createPanHandlers())}unmount(){this.removePointerDownListener(),this.session&&this.session.end()}}const ot={hasAnimatedSinceResize:!0,hasEverUpdated:!1};function ki(e,t){return t.max===t.min?0:e/(t.max-t.min)*100}const Ie={correct:(e,t)=>{if(!t.target)return e;if(typeof e=="string")if(T.test(e))e=parseFloat(e);else return e;const s=ki(e,t.target.x),i=ki(e,t.target.y);return`${s}% ${i}%`}},kd={correct:(e,{treeScale:t,projectionDelta:s})=>{const i=e,n=me.parse(e);if(n.length>5)return i;const r=me.createTransformer(e),a=typeof n[0]!="number"?1:0,o=s.x.scale*t.x,l=s.y.scale*t.y;n[0+a]/=o,n[1+a]/=l;const d=M(o,l,.5);return typeof n[2+a]=="number"&&(n[2+a]/=d),typeof n[3+a]=="number"&&(n[3+a]/=d),r(n)}};let Ct=!1;class Ad extends y.Component{componentDidMount(){const{visualElement:t,layoutGroup:s,switchLayoutGroup:i,layoutId:n}=this.props,{projection:r}=t;Yl(Cd),r&&(s.group&&s.group.add(r),i&&i.register&&n&&i.register(r),Ct&&r.root.didUpdate(),r.addEventListener("animationComplete",()=>{this.safeToRemove()}),r.setOptions({...r.options,onExitComplete:()=>this.safeToRemove()})),ot.hasEverUpdated=!0}getSnapshotBeforeUpdate(t){const{layoutDependency:s,visualElement:i,drag:n,isPresent:r}=this.props,{projection:a}=i;return a&&(a.isPresent=r,Ct=!0,n||t.layoutDependency!==s||s===void 0||t.isPresent!==r?a.willUpdate():this.safeToRemove(),t.isPresent!==r&&(r?a.promote():a.relegate()||V.postRender(()=>{const o=a.getStack();(!o||!o.members.length)&&this.safeToRemove()}))),null}componentDidUpdate(){const{projection:t}=this.props.visualElement;t&&(t.root.didUpdate(),Ss.postRender(()=>{!t.currentAnimation&&t.isLead()&&this.safeToRemove()}))}componentWillUnmount(){const{visualElement:t,layoutGroup:s,switchLayoutGroup:i}=this.props,{projection:n}=t;Ct=!0,n&&(n.scheduleCheckAfterUnmount(),s&&s.group&&s.group.remove(n),i&&i.deregister&&i.deregister(n))}safeToRemove(){const{safeToRemove:t}=this.props;t&&t()}render(){return null}}function Cr(e){const[t,s]=qa(),i=y.useContext(es);return h.jsx(Ad,{...e,layoutGroup:i,switchLayoutGroup:y.useContext(lr),isPresent:t,safeToRemove:s})}const Cd={borderRadius:{...Ie,applyTo:["borderTopLeftRadius","borderTopRightRadius","borderBottomLeftRadius","borderBottomRightRadius"]},borderTopLeftRadius:Ie,borderTopRightRadius:Ie,borderBottomLeftRadius:Ie,borderBottomRightRadius:Ie,boxShadow:kd};function Vd(e,t,s){const i=O(e)?e:Me(e);return i.start(Rs("",i,t,s)),i.animation}const Md=(e,t)=>e.depth-t.depth;class jd{constructor(){this.children=[],this.isDirty=!1}add(t){is(this.children,t),this.isDirty=!0}remove(t){ns(this.children,t),this.isDirty=!0}forEach(t){this.isDirty&&this.children.sort(Md),this.isDirty=!1,this.children.forEach(t)}}function Dd(e,t){const s=U.now(),i=({timestamp:n})=>{const r=n-s;r>=t&&(he(i),e(r-t))};return V.setup(i,!0),()=>he(i)}const Vr=["TopLeft","TopRight","BottomLeft","BottomRight"],Rd=Vr.length,Ai=e=>typeof e=="string"?parseFloat(e):e,Ci=e=>typeof e=="number"||T.test(e);function Ed(e,t,s,i,n,r){n?(e.opacity=M(0,s.opacity??1,Ld(i)),e.opacityExit=M(t.opacity??1,0,Fd(i))):r&&(e.opacity=M(t.opacity??1,s.opacity??1,i));for(let a=0;a<Rd;a++){const o=`border${Vr[a]}Radius`;let l=Vi(t,o),d=Vi(s,o);if(l===void 0&&d===void 0)continue;l||(l=0),d||(d=0),l===0||d===0||Ci(l)===Ci(d)?(e[o]=Math.max(M(Ai(l),Ai(d),i),0),(Y.test(d)||Y.test(l))&&(e[o]+="%")):e[o]=d}(t.rotate||s.rotate)&&(e.rotate=M(t.rotate||0,s.rotate||0,i))}function Vi(e,t){return e[t]!==void 0?e[t]:e.borderRadius}const Ld=Mr(0,.5,ga),Fd=Mr(.5,.95,G);function Mr(e,t,s){return i=>i<e?0:i>t?1:s($e(e,t,i))}function Mi(e,t){e.min=t.min,e.max=t.max}function K(e,t){Mi(e.x,t.x),Mi(e.y,t.y)}function ji(e,t){e.translate=t.translate,e.scale=t.scale,e.originPoint=t.originPoint,e.origin=t.origin}function Di(e,t,s,i,n){return e-=t,e=ht(e,1/s,i),n!==void 0&&(e=ht(e,1/n,i)),e}function Id(e,t=0,s=1,i=.5,n,r=e,a=e){if(Y.test(t)&&(t=parseFloat(t),t=M(a.min,a.max,t/100)-a.min),typeof t!="number")return;let o=M(r.min,r.max,i);e===r&&(o-=t),e.min=Di(e.min,t,s,o,n),e.max=Di(e.max,t,s,o,n)}function Ri(e,t,[s,i,n],r,a){Id(e,t[s],t[i],t[n],t.scale,r,a)}const Od=["x","scaleX","originX"],Bd=["y","scaleY","originY"];function Ei(e,t,s,i){Ri(e.x,t,Od,s?s.x:void 0,i?i.x:void 0),Ri(e.y,t,Bd,s?s.y:void 0,i?i.y:void 0)}function Li(e){return e.translate===0&&e.scale===1}function jr(e){return Li(e.x)&&Li(e.y)}function Fi(e,t){return e.min===t.min&&e.max===t.max}function Hd(e,t){return Fi(e.x,t.x)&&Fi(e.y,t.y)}function Ii(e,t){return Math.round(e.min)===Math.round(t.min)&&Math.round(e.max)===Math.round(t.max)}function Dr(e,t){return Ii(e.x,t.x)&&Ii(e.y,t.y)}function Oi(e){return H(e.x)/H(e.y)}function Bi(e,t){return e.translate===t.translate&&e.scale===t.scale&&e.originPoint===t.originPoint}class Ud{constructor(){this.members=[]}add(t){is(this.members,t),t.scheduleRender()}remove(t){if(ns(this.members,t),t===this.prevLead&&(this.prevLead=void 0),t===this.lead){const s=this.members[this.members.length-1];s&&this.promote(s)}}relegate(t){const s=this.members.findIndex(n=>t===n);if(s===0)return!1;let i;for(let n=s;n>=0;n--){const r=this.members[n];if(r.isPresent!==!1){i=r;break}}return i?(this.promote(i),!0):!1}promote(t,s){const i=this.lead;if(t!==i&&(this.prevLead=i,this.lead=t,t.show(),i)){i.instance&&i.scheduleRender(),t.scheduleRender(),t.resumeFrom=i,s&&(t.resumeFrom.preserveOpacity=!0),i.snapshot&&(t.snapshot=i.snapshot,t.snapshot.latestValues=i.animationValues||i.latestValues),t.root&&t.root.isUpdating&&(t.isLayoutDirty=!0);const{crossfade:n}=t.options;n===!1&&i.hide()}}exitAnimationComplete(){this.members.forEach(t=>{const{options:s,resumingFrom:i}=t;s.onExitComplete&&s.onExitComplete(),i&&i.options.onExitComplete&&i.options.onExitComplete()})}scheduleRender(){this.members.forEach(t=>{t.instance&&t.scheduleRender(!1)})}removeLeadSnapshot(){this.lead&&this.lead.snapshot&&(this.lead.snapshot=void 0)}}function Wd(e,t,s){let i="";const n=e.x.translate/t.x,r=e.y.translate/t.y,a=(s==null?void 0:s.z)||0;if((n||r||a)&&(i=`translate3d(${n}px, ${r}px, ${a}px) `),(t.x!==1||t.y!==1)&&(i+=`scale(${1/t.x}, ${1/t.y}) `),s){const{transformPerspective:d,rotate:c,rotateX:u,rotateY:m,skewX:p,skewY:f}=s;d&&(i=`perspective(${d}px) ${i}`),c&&(i+=`rotate(${c}deg) `),u&&(i+=`rotateX(${u}deg) `),m&&(i+=`rotateY(${m}deg) `),p&&(i+=`skewX(${p}deg) `),f&&(i+=`skewY(${f}deg) `)}const o=e.x.scale*t.x,l=e.y.scale*t.y;return(o!==1||l!==1)&&(i+=`scale(${o}, ${l})`),i||"none"}const Vt=["","X","Y","Z"],Kd=1e3;let $d=0;function Mt(e,t,s,i){const{latestValues:n}=t;n[e]&&(s[e]=n[e],t.setStaticValue(e,0),i&&(i[e]=0))}function Rr(e){if(e.hasCheckedOptimisedAppear=!0,e.root===e)return;const{visualElement:t}=e.options;if(!t)return;const s=xr(t);if(window.MotionHasOptimisedAnimation(s,"transform")){const{layout:n,layoutId:r}=e.options;window.MotionCancelOptimisedAnimation(s,"transform",V,!(n||r))}const{parent:i}=e;i&&!i.hasCheckedOptimisedAppear&&Rr(i)}function Er({attachResizeListener:e,defaultParent:t,measureScroll:s,checkIsScrollRoot:i,resetTransform:n}){return class{constructor(a={},o=t==null?void 0:t()){this.id=$d++,this.animationId=0,this.animationCommitId=0,this.children=new Set,this.options={},this.isTreeAnimating=!1,this.isAnimationBlocked=!1,this.isLayoutDirty=!1,this.isProjectionDirty=!1,this.isSharedProjectionDirty=!1,this.isTransformDirty=!1,this.updateManuallyBlocked=!1,this.updateBlockedByResize=!1,this.isUpdating=!1,this.isSVG=!1,this.needsReset=!1,this.shouldResetTransform=!1,this.hasCheckedOptimisedAppear=!1,this.treeScale={x:1,y:1},this.eventHandlers=new Map,this.hasTreeAnimated=!1,this.updateScheduled=!1,this.scheduleUpdate=()=>this.update(),this.projectionUpdateScheduled=!1,this.checkUpdateFailed=()=>{this.isUpdating&&(this.isUpdating=!1,this.clearAllSnapshots())},this.updateProjection=()=>{this.projectionUpdateScheduled=!1,this.nodes.forEach(_d),this.nodes.forEach(Zd),this.nodes.forEach(Jd),this.nodes.forEach(Xd)},this.resolvedRelativeTargetAt=0,this.hasProjected=!1,this.isVisible=!0,this.animationProgress=0,this.sharedNodes=new Map,this.latestValues=a,this.root=o?o.root||o:this,this.path=o?[...o.path,o]:[],this.parent=o,this.depth=o?o.depth+1:0;for(let l=0;l<this.path.length;l++)this.path[l].shouldResetTransform=!0;this.root===this&&(this.nodes=new jd)}addEventListener(a,o){return this.eventHandlers.has(a)||this.eventHandlers.set(a,new os),this.eventHandlers.get(a).add(o)}notifyListeners(a,...o){const l=this.eventHandlers.get(a);l&&l.notify(...o)}hasListeners(a){return this.eventHandlers.has(a)}mount(a){if(this.instance)return;this.isSVG=Ya(a)&&!El(a),this.instance=a;const{layoutId:o,layout:l,visualElement:d}=this.options;if(d&&!d.current&&d.mount(a),this.root.nodes.add(this),this.parent&&this.parent.children.add(this),this.root.hasTreeAnimated&&(l||o)&&(this.isLayoutDirty=!0),e){let c,u=0;const m=()=>this.root.updateBlockedByResize=!1;V.read(()=>{u=window.innerWidth}),e(a,()=>{const p=window.innerWidth;p!==u&&(u=p,this.root.updateBlockedByResize=!0,c&&c(),c=Dd(m,250),ot.hasAnimatedSinceResize&&(ot.hasAnimatedSinceResize=!1,this.nodes.forEach(Wi)))})}o&&this.root.registerSharedNode(o,this),this.options.animate!==!1&&d&&(o||l)&&this.addEventListener("didUpdate",({delta:c,hasLayoutChanged:u,hasRelativeLayoutChanged:m,layout:p})=>{if(this.isTreeAnimationBlocked()){this.target=void 0,this.relativeTarget=void 0;return}const f=this.options.transition||d.getDefaultTransition()||iu,{onLayoutAnimationStart:g,onLayoutAnimationComplete:b}=d.getProps(),x=!this.targetLayout||!Dr(this.targetLayout,p),w=!u&&m;if(this.options.layoutRoot||this.resumeFrom||w||u&&(x||!this.currentAnimation)){this.resumeFrom&&(this.resumingFrom=this.resumeFrom,this.resumingFrom.resumingFrom=void 0);const v={...vs(f,"layout"),onPlay:g,onComplete:b};(d.shouldReduceMotion||this.options.layoutRoot)&&(v.delay=0,v.type=!1),this.startAnimation(v),this.setAnimationOrigin(c,w)}else u||Wi(this),this.isLead()&&this.options.onExitComplete&&this.options.onExitComplete();this.targetLayout=p})}unmount(){this.options.layoutId&&this.willUpdate(),this.root.nodes.remove(this);const a=this.getStack();a&&a.remove(this),this.parent&&this.parent.children.delete(this),this.instance=void 0,this.eventHandlers.clear(),he(this.updateProjection)}blockUpdate(){this.updateManuallyBlocked=!0}unblockUpdate(){this.updateManuallyBlocked=!1}isUpdateBlocked(){return this.updateManuallyBlocked||this.updateBlockedByResize}isTreeAnimationBlocked(){return this.isAnimationBlocked||this.parent&&this.parent.isTreeAnimationBlocked()||!1}startUpdate(){this.isUpdateBlocked()||(this.isUpdating=!0,this.nodes&&this.nodes.forEach(Qd),this.animationId++)}getTransformTemplate(){const{visualElement:a}=this.options;return a&&a.getProps().transformTemplate}willUpdate(a=!0){if(this.root.hasTreeAnimated=!0,this.root.isUpdateBlocked()){this.options.onExitComplete&&this.options.onExitComplete();return}if(window.MotionCancelOptimisedAnimation&&!this.hasCheckedOptimisedAppear&&Rr(this),!this.root.isUpdating&&this.root.startUpdate(),this.isLayoutDirty)return;this.isLayoutDirty=!0;for(let c=0;c<this.path.length;c++){const u=this.path[c];u.shouldResetTransform=!0,u.updateScroll("snapshot"),u.options.layoutRoot&&u.willUpdate(!1)}const{layoutId:o,layout:l}=this.options;if(o===void 0&&!l)return;const d=this.getTransformTemplate();this.prevTransformTemplateValue=d?d(this.latestValues,""):void 0,this.updateSnapshot(),a&&this.notifyListeners("willUpdate")}update(){if(this.updateScheduled=!1,this.isUpdateBlocked()){this.unblockUpdate(),this.clearAllSnapshots(),this.nodes.forEach(Hi);return}if(this.animationId<=this.animationCommitId){this.nodes.forEach(Ui);return}this.animationCommitId=this.animationId,this.isUpdating?(this.isUpdating=!1,this.nodes.forEach(qd),this.nodes.forEach(zd),this.nodes.forEach(Gd)):this.nodes.forEach(Ui),this.clearAllSnapshots();const o=U.now();I.delta=Z(0,1e3/60,o-I.timestamp),I.timestamp=o,I.isProcessing=!0,xt.update.process(I),xt.preRender.process(I),xt.render.process(I),I.isProcessing=!1}didUpdate(){this.updateScheduled||(this.updateScheduled=!0,Ss.read(this.scheduleUpdate))}clearAllSnapshots(){this.nodes.forEach(Yd),this.sharedNodes.forEach(eu)}scheduleUpdateProjection(){this.projectionUpdateScheduled||(this.projectionUpdateScheduled=!0,V.preRender(this.updateProjection,!1,!0))}scheduleCheckAfterUnmount(){V.postRender(()=>{this.isLayoutDirty?this.root.didUpdate():this.root.checkUpdateFailed()})}updateSnapshot(){this.snapshot||!this.instance||(this.snapshot=this.measure(),this.snapshot&&!H(this.snapshot.measuredBox.x)&&!H(this.snapshot.measuredBox.y)&&(this.snapshot=void 0))}updateLayout(){if(!this.instance||(this.updateScroll(),!(this.options.alwaysMeasureLayout&&this.isLead())&&!this.isLayoutDirty))return;if(this.resumeFrom&&!this.resumeFrom.instance)for(let l=0;l<this.path.length;l++)this.path[l].updateScroll();const a=this.layout;this.layout=this.measure(!1),this.layoutCorrected=D(),this.isLayoutDirty=!1,this.projectionDelta=void 0,this.notifyListeners("measure",this.layout.layoutBox);const{visualElement:o}=this.options;o&&o.notify("LayoutMeasure",this.layout.layoutBox,a?a.layoutBox:void 0)}updateScroll(a="measure"){let o=!!(this.options.layoutScroll&&this.instance);if(this.scroll&&this.scroll.animationId===this.root.animationId&&this.scroll.phase===a&&(o=!1),o&&this.instance){const l=i(this.instance);this.scroll={animationId:this.root.animationId,phase:a,isRoot:l,offset:s(this.instance),wasRoot:this.scroll?this.scroll.isRoot:l}}}resetTransform(){if(!n)return;const a=this.isLayoutDirty||this.shouldResetTransform||this.options.alwaysMeasureLayout,o=this.projectionDelta&&!jr(this.projectionDelta),l=this.getTransformTemplate(),d=l?l(this.latestValues,""):void 0,c=d!==this.prevTransformTemplateValue;a&&this.instance&&(o||ye(this.latestValues)||c)&&(n(this.instance,d),this.shouldResetTransform=!1,this.scheduleRender())}measure(a=!0){const o=this.measurePageBox();let l=this.removeElementScroll(o);return a&&(l=this.removeTransform(l)),nu(l),{animationId:this.root.animationId,measuredBox:o,layoutBox:l,latestValues:{},source:this.id}}measurePageBox(){var d;const{visualElement:a}=this.options;if(!a)return D();const o=a.measureViewportBox();if(!(((d=this.scroll)==null?void 0:d.wasRoot)||this.path.some(au))){const{scroll:c}=this.root;c&&(ke(o.x,c.offset.x),ke(o.y,c.offset.y))}return o}removeElementScroll(a){var l;const o=D();if(K(o,a),(l=this.scroll)!=null&&l.wasRoot)return o;for(let d=0;d<this.path.length;d++){const c=this.path[d],{scroll:u,options:m}=c;c!==this.root&&u&&m.layoutScroll&&(u.wasRoot&&K(o,a),ke(o.x,u.offset.x),ke(o.y,u.offset.y))}return o}applyTransform(a,o=!1){const l=D();K(l,a);for(let d=0;d<this.path.length;d++){const c=this.path[d];!o&&c.options.layoutScroll&&c.scroll&&c!==c.root&&Ae(l,{x:-c.scroll.offset.x,y:-c.scroll.offset.y}),ye(c.latestValues)&&Ae(l,c.latestValues)}return ye(this.latestValues)&&Ae(l,this.latestValues),l}removeTransform(a){const o=D();K(o,a);for(let l=0;l<this.path.length;l++){const d=this.path[l];if(!d.instance||!ye(d.latestValues))continue;Gt(d.latestValues)&&d.updateSnapshot();const c=D(),u=d.measurePageBox();K(c,u),Ei(o,d.latestValues,d.snapshot?d.snapshot.layoutBox:void 0,c)}return ye(this.latestValues)&&Ei(o,this.latestValues),o}setTargetDelta(a){this.targetDelta=a,this.root.scheduleUpdateProjection(),this.isProjectionDirty=!0}setOptions(a){this.options={...this.options,...a,crossfade:a.crossfade!==void 0?a.crossfade:!0}}clearMeasurements(){this.scroll=void 0,this.layout=void 0,this.snapshot=void 0,this.prevTransformTemplateValue=void 0,this.targetDelta=void 0,this.target=void 0,this.isLayoutDirty=!1}forceRelativeParentToResolveTarget(){this.relativeParent&&this.relativeParent.resolvedRelativeTargetAt!==I.timestamp&&this.relativeParent.resolveTargetDelta(!0)}resolveTargetDelta(a=!1){var m;const o=this.getLead();this.isProjectionDirty||(this.isProjectionDirty=o.isProjectionDirty),this.isTransformDirty||(this.isTransformDirty=o.isTransformDirty),this.isSharedProjectionDirty||(this.isSharedProjectionDirty=o.isSharedProjectionDirty);const l=!!this.resumingFrom||this!==o;if(!(a||l&&this.isSharedProjectionDirty||this.isProjectionDirty||(m=this.parent)!=null&&m.isProjectionDirty||this.attemptToResolveRelativeTarget||this.root.updateBlockedByResize))return;const{layout:c,layoutId:u}=this.options;if(!(!this.layout||!(c||u))){if(this.resolvedRelativeTargetAt=I.timestamp,!this.targetDelta&&!this.relativeTarget){const p=this.getClosestProjectingParent();p&&p.layout&&this.animationProgress!==1?(this.relativeParent=p,this.forceRelativeParentToResolveTarget(),this.relativeTarget=D(),this.relativeTargetOrigin=D(),Ke(this.relativeTargetOrigin,this.layout.layoutBox,p.layout.layoutBox),K(this.relativeTarget,this.relativeTargetOrigin)):this.relativeParent=this.relativeTarget=void 0}if(!(!this.relativeTarget&&!this.targetDelta)&&(this.target||(this.target=D(),this.targetWithTransforms=D()),this.relativeTarget&&this.relativeTargetOrigin&&this.relativeParent&&this.relativeParent.target?(this.forceRelativeParentToResolveTarget(),ud(this.target,this.relativeTarget,this.relativeParent.target)):this.targetDelta?(this.resumingFrom?this.target=this.applyTransform(this.layout.layoutBox):K(this.target,this.layout.layoutBox),hr(this.target,this.targetDelta)):K(this.target,this.layout.layoutBox),this.attemptToResolveRelativeTarget)){this.attemptToResolveRelativeTarget=!1;const p=this.getClosestProjectingParent();p&&!!p.resumingFrom==!!this.resumingFrom&&!p.options.layoutScroll&&p.target&&this.animationProgress!==1?(this.relativeParent=p,this.forceRelativeParentToResolveTarget(),this.relativeTarget=D(),this.relativeTargetOrigin=D(),Ke(this.relativeTargetOrigin,this.target,p.target),K(this.relativeTarget,this.relativeTargetOrigin)):this.relativeParent=this.relativeTarget=void 0}}}getClosestProjectingParent(){if(!(!this.parent||Gt(this.parent.latestValues)||ur(this.parent.latestValues)))return this.parent.isProjecting()?this.parent:this.parent.getClosestProjectingParent()}isProjecting(){return!!((this.relativeTarget||this.targetDelta||this.options.layoutRoot)&&this.layout)}calcProjection(){var f;const a=this.getLead(),o=!!this.resumingFrom||this!==a;let l=!0;if((this.isProjectionDirty||(f=this.parent)!=null&&f.isProjectionDirty)&&(l=!1),o&&(this.isSharedProjectionDirty||this.isTransformDirty)&&(l=!1),this.resolvedRelativeTargetAt===I.timestamp&&(l=!1),l)return;const{layout:d,layoutId:c}=this.options;if(this.isTreeAnimating=!!(this.parent&&this.parent.isTreeAnimating||this.currentAnimation||this.pendingAnimation),this.isTreeAnimating||(this.targetDelta=this.relativeTarget=void 0),!this.layout||!(d||c))return;K(this.layoutCorrected,this.layout.layoutBox);const u=this.treeScale.x,m=this.treeScale.y;Tc(this.layoutCorrected,this.treeScale,this.path,o),a.layout&&!a.target&&(this.treeScale.x!==1||this.treeScale.y!==1)&&(a.target=a.layout.layoutBox,a.targetWithTransforms=D());const{target:p}=a;if(!p){this.prevProjectionDelta&&(this.createProjectionDeltas(),this.scheduleRender());return}!this.projectionDelta||!this.prevProjectionDelta?this.createProjectionDeltas():(ji(this.prevProjectionDelta.x,this.projectionDelta.x),ji(this.prevProjectionDelta.y,this.projectionDelta.y)),We(this.projectionDelta,this.layoutCorrected,p,this.latestValues),(this.treeScale.x!==u||this.treeScale.y!==m||!Bi(this.projectionDelta.x,this.prevProjectionDelta.x)||!Bi(this.projectionDelta.y,this.prevProjectionDelta.y))&&(this.hasProjected=!0,this.scheduleRender(),this.notifyListeners("projectionUpdate",p))}hide(){this.isVisible=!1}show(){this.isVisible=!0}scheduleRender(a=!0){var o;if((o=this.options.visualElement)==null||o.scheduleRender(),a){const l=this.getStack();l&&l.scheduleRender()}this.resumingFrom&&!this.resumingFrom.instance&&(this.resumingFrom=void 0)}createProjectionDeltas(){this.prevProjectionDelta=Ce(),this.projectionDelta=Ce(),this.projectionDeltaWithTransform=Ce()}setAnimationOrigin(a,o=!1){const l=this.snapshot,d=l?l.latestValues:{},c={...this.latestValues},u=Ce();(!this.relativeParent||!this.relativeParent.options.layoutRoot)&&(this.relativeTarget=this.relativeTargetOrigin=void 0),this.attemptToResolveRelativeTarget=!o;const m=D(),p=l?l.source:void 0,f=this.layout?this.layout.source:void 0,g=p!==f,b=this.getStack(),x=!b||b.members.length<=1,w=!!(g&&!x&&this.options.crossfade===!0&&!this.path.some(su));this.animationProgress=0;let v;this.mixTargetDelta=P=>{const S=P/1e3;Ki(u.x,a.x,S),Ki(u.y,a.y,S),this.setTargetDelta(u),this.relativeTarget&&this.relativeTargetOrigin&&this.layout&&this.relativeParent&&this.relativeParent.layout&&(Ke(m,this.layout.layoutBox,this.relativeParent.layout.layoutBox),tu(this.relativeTarget,this.relativeTargetOrigin,m,S),v&&Hd(this.relativeTarget,v)&&(this.isProjectionDirty=!1),v||(v=D()),K(v,this.relativeTarget)),g&&(this.animationValues=c,Ed(c,d,this.latestValues,S,w,x)),this.root.scheduleUpdateProjection(),this.scheduleRender(),this.animationProgress=S},this.mixTargetDelta(this.options.layoutRoot?1e3:0)}startAnimation(a){var o,l,d;this.notifyListeners("animationStart"),(o=this.currentAnimation)==null||o.stop(),(d=(l=this.resumingFrom)==null?void 0:l.currentAnimation)==null||d.stop(),this.pendingAnimation&&(he(this.pendingAnimation),this.pendingAnimation=void 0),this.pendingAnimation=V.update(()=>{ot.hasAnimatedSinceResize=!0,this.motionValue||(this.motionValue=Me(0)),this.currentAnimation=Vd(this.motionValue,[0,1e3],{...a,velocity:0,isSync:!0,onUpdate:c=>{this.mixTargetDelta(c),a.onUpdate&&a.onUpdate(c)},onStop:()=>{},onComplete:()=>{a.onComplete&&a.onComplete(),this.completeAnimation()}}),this.resumingFrom&&(this.resumingFrom.currentAnimation=this.currentAnimation),this.pendingAnimation=void 0})}completeAnimation(){this.resumingFrom&&(this.resumingFrom.currentAnimation=void 0,this.resumingFrom.preserveOpacity=void 0);const a=this.getStack();a&&a.exitAnimationComplete(),this.resumingFrom=this.currentAnimation=this.animationValues=void 0,this.notifyListeners("animationComplete")}finishAnimation(){this.currentAnimation&&(this.mixTargetDelta&&this.mixTargetDelta(Kd),this.currentAnimation.stop()),this.completeAnimation()}applyTransformsToTarget(){const a=this.getLead();let{targetWithTransforms:o,target:l,layout:d,latestValues:c}=a;if(!(!o||!l||!d)){if(this!==a&&this.layout&&d&&Lr(this.options.animationType,this.layout.layoutBox,d.layoutBox)){l=this.target||D();const u=H(this.layout.layoutBox.x);l.x.min=a.target.x.min,l.x.max=l.x.min+u;const m=H(this.layout.layoutBox.y);l.y.min=a.target.y.min,l.y.max=l.y.min+m}K(o,l),Ae(o,c),We(this.projectionDeltaWithTransform,this.layoutCorrected,o,c)}}registerSharedNode(a,o){this.sharedNodes.has(a)||this.sharedNodes.set(a,new Ud),this.sharedNodes.get(a).add(o);const d=o.options.initialPromotionConfig;o.promote({transition:d?d.transition:void 0,preserveFollowOpacity:d&&d.shouldPreserveFollowOpacity?d.shouldPreserveFollowOpacity(o):void 0})}isLead(){const a=this.getStack();return a?a.lead===this:!0}getLead(){var o;const{layoutId:a}=this.options;return a?((o=this.getStack())==null?void 0:o.lead)||this:this}getPrevLead(){var o;const{layoutId:a}=this.options;return a?(o=this.getStack())==null?void 0:o.prevLead:void 0}getStack(){const{layoutId:a}=this.options;if(a)return this.root.sharedNodes.get(a)}promote({needsReset:a,transition:o,preserveFollowOpacity:l}={}){const d=this.getStack();d&&d.promote(this,l),a&&(this.projectionDelta=void 0,this.needsReset=!0),o&&this.setOptions({transition:o})}relegate(){const a=this.getStack();return a?a.relegate(this):!1}resetSkewAndRotation(){const{visualElement:a}=this.options;if(!a)return;let o=!1;const{latestValues:l}=a;if((l.z||l.rotate||l.rotateX||l.rotateY||l.rotateZ||l.skewX||l.skewY)&&(o=!0),!o)return;const d={};l.z&&Mt("z",a,d,this.animationValues);for(let c=0;c<Vt.length;c++)Mt(`rotate${Vt[c]}`,a,d,this.animationValues),Mt(`skew${Vt[c]}`,a,d,this.animationValues);a.render();for(const c in d)a.setStaticValue(c,d[c]),this.animationValues&&(this.animationValues[c]=d[c]);a.scheduleRender()}applyProjectionStyles(a,o){if(!this.instance||this.isSVG)return;if(!this.isVisible){a.visibility="hidden";return}const l=this.getTransformTemplate();if(this.needsReset){this.needsReset=!1,a.visibility="",a.opacity="",a.pointerEvents=rt(o==null?void 0:o.pointerEvents)||"",a.transform=l?l(this.latestValues,""):"none";return}const d=this.getLead();if(!this.projectionDelta||!this.layout||!d.target){this.options.layoutId&&(a.opacity=this.latestValues.opacity!==void 0?this.latestValues.opacity:1,a.pointerEvents=rt(o==null?void 0:o.pointerEvents)||""),this.hasProjected&&!ye(this.latestValues)&&(a.transform=l?l({},""):"none",this.hasProjected=!1);return}a.visibility="";const c=d.animationValues||d.latestValues;this.applyTransformsToTarget();let u=Wd(this.projectionDeltaWithTransform,this.treeScale,c);l&&(u=l(c,u)),a.transform=u;const{x:m,y:p}=this.projectionDelta;a.transformOrigin=`${m.origin*100}% ${p.origin*100}% 0`,d.animationValues?a.opacity=d===this?c.opacity??this.latestValues.opacity??1:this.preserveOpacity?this.latestValues.opacity:c.opacityExit:a.opacity=d===this?c.opacity!==void 0?c.opacity:"":c.opacityExit!==void 0?c.opacityExit:0;for(const f in Xe){if(c[f]===void 0)continue;const{correct:g,applyTo:b,isCSSVariable:x}=Xe[f],w=u==="none"?c[f]:g(c[f],d);if(b){const v=b.length;for(let P=0;P<v;P++)a[b[P]]=w}else x?this.options.visualElement.renderState.vars[f]=w:a[f]=w}this.options.layoutId&&(a.pointerEvents=d===this?rt(o==null?void 0:o.pointerEvents)||"":"none")}clearSnapshot(){this.resumeFrom=this.snapshot=void 0}resetTree(){this.root.nodes.forEach(a=>{var o;return(o=a.currentAnimation)==null?void 0:o.stop()}),this.root.nodes.forEach(Hi),this.root.sharedNodes.clear()}}}function zd(e){e.updateLayout()}function Gd(e){var s;const t=((s=e.resumeFrom)==null?void 0:s.snapshot)||e.snapshot;if(e.isLead()&&e.layout&&t&&e.hasListeners("didUpdate")){const{layoutBox:i,measuredBox:n}=e.layout,{animationType:r}=e.options,a=t.source!==e.layout.source;r==="size"?$(u=>{const m=a?t.measuredBox[u]:t.layoutBox[u],p=H(m);m.min=i[u].min,m.max=m.min+p}):Lr(r,t.layoutBox,i)&&$(u=>{const m=a?t.measuredBox[u]:t.layoutBox[u],p=H(i[u]);m.max=m.min+p,e.relativeTarget&&!e.currentAnimation&&(e.isProjectionDirty=!0,e.relativeTarget[u].max=e.relativeTarget[u].min+p)});const o=Ce();We(o,i,t.layoutBox);const l=Ce();a?We(l,e.applyTransform(n,!0),t.measuredBox):We(l,i,t.layoutBox);const d=!jr(o);let c=!1;if(!e.resumeFrom){const u=e.getClosestProjectingParent();if(u&&!u.resumeFrom){const{snapshot:m,layout:p}=u;if(m&&p){const f=D();Ke(f,t.layoutBox,m.layoutBox);const g=D();Ke(g,i,p.layoutBox),Dr(f,g)||(c=!0),u.options.layoutRoot&&(e.relativeTarget=g,e.relativeTargetOrigin=f,e.relativeParent=u)}}}e.notifyListeners("didUpdate",{layout:i,snapshot:t,delta:l,layoutDelta:o,hasLayoutChanged:d,hasRelativeLayoutChanged:c})}else if(e.isLead()){const{onExitComplete:i}=e.options;i&&i()}e.options.transition=void 0}function _d(e){e.parent&&(e.isProjecting()||(e.isProjectionDirty=e.parent.isProjectionDirty),e.isSharedProjectionDirty||(e.isSharedProjectionDirty=!!(e.isProjectionDirty||e.parent.isProjectionDirty||e.parent.isSharedProjectionDirty)),e.isTransformDirty||(e.isTransformDirty=e.parent.isTransformDirty))}function Xd(e){e.isProjectionDirty=e.isSharedProjectionDirty=e.isTransformDirty=!1}function Yd(e){e.clearSnapshot()}function Hi(e){e.clearMeasurements()}function Ui(e){e.isLayoutDirty=!1}function qd(e){const{visualElement:t}=e.options;t&&t.getProps().onBeforeLayoutMeasure&&t.notify("BeforeLayoutMeasure"),e.resetTransform()}function Wi(e){e.finishAnimation(),e.targetDelta=e.relativeTarget=e.target=void 0,e.isProjectionDirty=!0}function Zd(e){e.resolveTargetDelta()}function Jd(e){e.calcProjection()}function Qd(e){e.resetSkewAndRotation()}function eu(e){e.removeLeadSnapshot()}function Ki(e,t,s){e.translate=M(t.translate,0,s),e.scale=M(t.scale,1,s),e.origin=t.origin,e.originPoint=t.originPoint}function $i(e,t,s,i){e.min=M(t.min,s.min,i),e.max=M(t.max,s.max,i)}function tu(e,t,s,i){$i(e.x,t.x,s.x,i),$i(e.y,t.y,s.y,i)}function su(e){return e.animationValues&&e.animationValues.opacityExit!==void 0}const iu={duration:.45,ease:[.4,0,.1,1]},zi=e=>typeof navigator<"u"&&navigator.userAgent&&navigator.userAgent.toLowerCase().includes(e),Gi=zi("applewebkit/")&&!zi("chrome/")?Math.round:G;function _i(e){e.min=Gi(e.min),e.max=Gi(e.max)}function nu(e){_i(e.x),_i(e.y)}function Lr(e,t,s){return e==="position"||e==="preserve-aspect"&&!dd(Oi(t),Oi(s),.2)}function au(e){var t;return e!==e.root&&((t=e.scroll)==null?void 0:t.wasRoot)}const ru=Er({attachResizeListener:(e,t)=>Ye(e,"resize",t),measureScroll:()=>({x:document.documentElement.scrollLeft||document.body.scrollLeft,y:document.documentElement.scrollTop||document.body.scrollTop}),checkIsScrollRoot:()=>!0}),jt={current:void 0},Fr=Er({measureScroll:e=>({x:e.scrollLeft,y:e.scrollTop}),defaultParent:()=>{if(!jt.current){const e=new ru({});e.mount(window),e.setOptions({layoutScroll:!0}),jt.current=e}return jt.current},resetTransform:(e,t)=>{e.style.transform=t!==void 0?t:"none"},checkIsScrollRoot:e=>window.getComputedStyle(e).position==="fixed"}),ou={pan:{Feature:Pd},drag:{Feature:Nd,ProjectionNode:Fr,MeasureLayout:Cr}};function Xi(e,t,s){const{props:i}=e;e.animationState&&i.whileHover&&e.animationState.setActive("whileHover",s==="Start");const n="onHover"+s,r=i[n];r&&V.postRender(()=>r(t,Qe(t)))}class lu extends pe{mount(){const{current:t}=this.node;t&&(this.unmount=Vl(t,(s,i)=>(Xi(this.node,i,"Start"),n=>Xi(this.node,n,"End"))))}unmount(){}}class cu extends pe{constructor(){super(...arguments),this.isActive=!1}onFocus(){let t=!1;try{t=this.node.current.matches(":focus-visible")}catch{t=!0}!t||!this.node.animationState||(this.node.animationState.setActive("whileFocus",!0),this.isActive=!0)}onBlur(){!this.isActive||!this.node.animationState||(this.node.animationState.setActive("whileFocus",!1),this.isActive=!1)}mount(){this.unmount=qe(Ye(this.node.current,"focus",()=>this.onFocus()),Ye(this.node.current,"blur",()=>this.onBlur()))}unmount(){}}function Yi(e,t,s){const{props:i}=e;if(e.current instanceof HTMLButtonElement&&e.current.disabled)return;e.animationState&&i.whileTap&&e.animationState.setActive("whileTap",s==="Start");const n="onTap"+(s==="End"?"":s),r=i[n];r&&V.postRender(()=>r(t,Qe(t)))}class du extends pe{mount(){const{current:t}=this.node;t&&(this.unmount=Rl(t,(s,i)=>(Yi(this.node,i,"Start"),(n,{success:r})=>Yi(this.node,n,r?"End":"Cancel")),{useGlobalTarget:this.node.props.globalTapTarget}))}unmount(){}}const Qt=new WeakMap,Dt=new WeakMap,uu=e=>{const t=Qt.get(e.target);t&&t(e)},hu=e=>{e.forEach(uu)};function mu({root:e,...t}){const s=e||document;Dt.has(s)||Dt.set(s,{});const i=Dt.get(s),n=JSON.stringify(t);return i[n]||(i[n]=new IntersectionObserver(hu,{root:e,...t})),i[n]}function pu(e,t,s){const i=mu(t);return Qt.set(e,s),i.observe(e),()=>{Qt.delete(e),i.unobserve(e)}}const fu={some:0,all:1};class gu extends pe{constructor(){super(...arguments),this.hasEnteredView=!1,this.isInView=!1}startObserver(){this.unmount();const{viewport:t={}}=this.node.getProps(),{root:s,margin:i,amount:n="some",once:r}=t,a={root:s?s.current:void 0,rootMargin:i,threshold:typeof n=="number"?n:fu[n]},o=l=>{const{isIntersecting:d}=l;if(this.isInView===d||(this.isInView=d,r&&!d&&this.hasEnteredView))return;d&&(this.hasEnteredView=!0),this.node.animationState&&this.node.animationState.setActive("whileInView",d);const{onViewportEnter:c,onViewportLeave:u}=this.node.getProps(),m=d?c:u;m&&m(l)};return pu(this.node.current,a,o)}mount(){this.startObserver()}update(){if(typeof IntersectionObserver>"u")return;const{props:t,prevProps:s}=this.node;["amount","margin","root"].some(yu(t,s))&&this.startObserver()}unmount(){}}function yu({viewport:e={}},{viewport:t={}}={}){return s=>e[s]!==t[s]}const xu={inView:{Feature:gu},tap:{Feature:du},focus:{Feature:cu},hover:{Feature:lu}},bu={layout:{ProjectionNode:Fr,MeasureLayout:Cr}},vu={...nd,...xu,...ou,...bu},C=vc(vu,Rc),Fe=()=>typeof window>"u"?!1:window.matchMedia("(prefers-reduced-motion: reduce)").matches,mt={gentle:{type:"spring",stiffness:120,damping:14,mass:.5,duration:.6},default:{type:"spring",stiffness:170,damping:26,mass:1,duration:.5},bouncy:{type:"spring",stiffness:260,damping:20,mass:.8,duration:.7},snappy:{type:"spring",stiffness:300,damping:30,mass:.6,duration:.4},smooth:{type:"spring",stiffness:100,damping:20,mass:1.2,duration:.8},wobbly:{type:"spring",stiffness:180,damping:12,mass:1,duration:.9}},E=(e="default")=>Fe()?{duration:0}:mt[e]||mt.default,De=(e="fade",t="default")=>{if(Fe())return{initial:{opacity:1},animate:{opacity:1},exit:{opacity:1}};const s=E(t),i={fade:{initial:{opacity:0},animate:{opacity:1,transition:s},exit:{opacity:0,transition:{...s,duration:s.duration*.6}}},scale:{initial:{opacity:0,scale:.8},animate:{opacity:1,scale:1,transition:s},exit:{opacity:0,scale:.9,transition:{...s,duration:s.duration*.5}}},pop:{initial:{scale:1},animate:{scale:[1,.95,1],transition:{...s,times:[0,.4,1]}}},bounce:{initial:{scale:1},animate:{scale:[1,1.1,.95,1.02,1],transition:{...mt.bouncy,times:[0,.2,.5,.8,1]}}},slideUp:{initial:{opacity:0,y:100},animate:{opacity:1,y:0,transition:s},exit:{opacity:0,y:50,transition:{...s,duration:s.duration*.6}}},slideDown:{initial:{opacity:0,y:-20,scale:.95},animate:{opacity:1,y:0,scale:1,transition:s},exit:{opacity:0,y:-10,scale:.98,transition:{...s,duration:s.duration*.5}}},slideLeft:{initial:{opacity:0,x:50},animate:{opacity:1,x:0,transition:s},exit:{opacity:0,x:-50,transition:s}},slideRight:{initial:{opacity:0,x:-50},animate:{opacity:1,x:0,transition:s},exit:{opacity:0,x:50,transition:s}},expand:{initial:{opacity:0,height:0,scale:.95},animate:{opacity:1,height:"auto",scale:1,transition:s},exit:{opacity:0,height:0,scale:.95,transition:{...s,duration:s.duration*.6}}},rotate:{initial:{rotate:0},animate:{rotate:360,transition:{...s,repeat:1/0,repeatType:"loop"}}},shake:{initial:{x:0},animate:{x:[0,-10,10,-10,10,-5,5,0],transition:{duration:.5,times:[0,.1,.2,.3,.4,.5,.6,1]}}},pulse:{initial:{scale:1,opacity:1},animate:{scale:[1,1.05,1],opacity:[1,.8,1],transition:{...s,repeat:1/0,repeatDelay:1}}}};return i[e]||i.fade},qi={light:{intensity:.3,duration:10},medium:{intensity:.5,duration:15},heavy:{intensity:.7,duration:20},success:{intensity:.6,duration:25,pattern:[10,5,10]},warning:{intensity:.7,duration:30,pattern:[15,10,15]},error:{intensity:.8,duration:35,pattern:[20,10,20,10,20]},selection:{intensity:.4,duration:8}},Ir=(e="light")=>{if(Fe())return{};const t={light:{scale:[1,.98,1],transition:{duration:.1,times:[0,.5,1]}},medium:{scale:[1,.96,1],transition:{duration:.15,times:[0,.5,1]}},heavy:{scale:[1,.94,1.02,1],transition:{duration:.2,times:[0,.4,.7,1]}},success:{scale:[1,.95,1.05,1],transition:{duration:.4,times:[0,.2,.6,1],ease:"easeOut"}},warning:{x:[0,-3,3,-3,3,0],transition:{duration:.3,times:[0,.2,.4,.6,.8,1]}},error:{x:[0,-5,5,-5,5,-3,3,0],transition:{duration:.5,times:[0,.1,.2,.3,.4,.6,.8,1]}},selection:{scale:[1,.99,1],transition:{duration:.08,times:[0,.5,1]}}};return t[e]||t.light},q=async(e,t="light")=>{if(!e||Fe())return Promise.resolve();Ir(t);const s=qi[t]||qi.light;return e.classList.add(`haptic-${t}`),new Promise(i=>{setTimeout(()=>{e.classList.remove(`haptic-${t}`),i()},s.duration)})},wu=(e,t={})=>{if(Fe())return{duration:0};const{isMobile:s=!1,isLowPower:i=!1,connectionSpeed:n="fast",userPreference:r="default"}=t;let a="default";return i||n==="slow"?a="snappy":s?a="smooth":r==="playful"?a="bouncy":r==="minimal"&&(a="gentle"),De(e,a)},Su=()=>{const e=/iPhone|iPad|iPod|Android/i.test(navigator.userAgent),t=navigator.deviceMemory?navigator.deviceMemory<4:!1;let s="fast";if(navigator.connection){const i=navigator.connection.effectiveType;i==="slow-2g"||i==="2g"?s="slow":i==="3g"&&(s="medium")}return{isMobile:e,isLowPower:t,connectionSpeed:s,userPreference:localStorage.getItem("animationPreference")||"default"}},Tu=(e="default",t=.05)=>{if(Fe())return{staggerChildren:0};const s=E(e);return{staggerChildren:t,delayChildren:.1,transition:s}};let te={totalAnimations:0,activeAnimations:0,droppedFrames:0,averageFPS:60};const Nu=e=>{te.totalAnimations++,te.activeAnimations++;let t=performance.now(),s=0,i=[],n=null,r=!0;const a=()=>{if(!r)return;const o=performance.now(),l=o-t;if(l>0){const d=1e3/l;i.push(d),d<55&&te.droppedFrames++}if(t=o,s++,s<60&&r)n=requestAnimationFrame(a);else{const d=i.reduce((c,u)=>c+u,0)/i.length;te.averageFPS=(te.averageFPS+d)/2,te.activeAnimations--,n=null}};return n=requestAnimationFrame(a),()=>{r=!1,n!==null&&(cancelAnimationFrame(n),te.activeAnimations--)}},Zi=()=>({...te}),Mu={title:"Design System/Spring Animation System",parameters:{layout:"padded",docs:{description:{component:"Apple-level spring animation system with haptic feedback simulation and contextual animations."}}}},se={render:()=>{const[e,t]=y.useState(null),s=[{name:"gentle",label:"Gentle",description:"溫和的彈性動畫",color:"bg-blue-100 dark:bg-blue-900"},{name:"default",label:"Default",description:"標準 iOS 動畫（推薦）",color:"bg-green-100 dark:bg-green-900"},{name:"bouncy",label:"Bouncy",description:"活潑、有趣的彈性",color:"bg-purple-100 dark:bg-purple-900"},{name:"snappy",label:"Snappy",description:"快速、響應式",color:"bg-orange-100 dark:bg-orange-900"},{name:"smooth",label:"Smooth",description:"優雅、流暢",color:"bg-pink-100 dark:bg-pink-900"},{name:"wobbly",label:"Wobbly",description:"誇張的彈性效果",color:"bg-yellow-100 dark:bg-yellow-900"}];return h.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[h.jsxs("div",{children:[h.jsx("h2",{className:"text-2xl font-bold mb-2",children:"6 種彈性預設"}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"點擊查看不同彈性動畫的效果"})]}),h.jsx("div",{className:"grid grid-cols-2 md:grid-cols-3 gap-6",children:s.map(i=>h.jsxs(C.button,{onClick:()=>t(i.name),whileHover:{scale:1.05},whileTap:{scale:.95},transition:E(i.name),className:`${i.color} p-6 rounded-xl shadow-md text-left relative overflow-hidden`,children:[h.jsxs("div",{className:"relative z-10",children:[h.jsx("h3",{className:"text-lg font-semibold mb-1",children:i.label}),h.jsx("p",{className:"text-sm text-gray-600 dark:text-gray-300",children:i.description})]}),h.jsx(Se,{children:e===i.name&&h.jsx(C.div,{initial:{scale:0,opacity:0},animate:{scale:1,opacity:1},exit:{scale:0,opacity:0},transition:E(i.name),className:"absolute inset-0 bg-white/20 dark:bg-black/20"})})]},i.name))}),h.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("h3",{className:"text-lg font-semibold mb-4",children:"技術參數"}),h.jsx("div",{className:"grid grid-cols-2 md:grid-cols-3 gap-4",children:Object.entries(mt).map(([i,n])=>h.jsxs("div",{className:"p-4 bg-gray-50 dark:bg-gray-700 rounded-lg",children:[h.jsx("h4",{className:"font-semibold capitalize mb-2",children:i}),h.jsxs("div",{className:"text-sm space-y-1 text-gray-600 dark:text-gray-300",children:[h.jsxs("div",{children:["Stiffness: ",n.stiffness]}),h.jsxs("div",{children:["Damping: ",n.damping]}),h.jsxs("div",{children:["Mass: ",n.mass]}),h.jsxs("div",{children:["Duration: ",n.duration,"s"]})]})]},i))})]})]})}},ie={render:()=>{var i,n;const[e,t]=y.useState(null),s=[{name:"fade",label:"Fade",description:"淡入淡出"},{name:"scale",label:"Scale",description:"縮放"},{name:"pop",label:"Pop",description:"彈出"},{name:"bounce",label:"Bounce",description:"彈跳"},{name:"slideUp",label:"Slide Up",description:"向上滑動"},{name:"slideDown",label:"Slide Down",description:"向下滑動"},{name:"slideLeft",label:"Slide Left",description:"向左滑動"},{name:"slideRight",label:"Slide Right",description:"向右滑動"},{name:"shake",label:"Shake",description:"搖晃"},{name:"pulse",label:"Pulse",description:"脈衝"}];return h.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[h.jsxs("div",{children:[h.jsx("h2",{className:"text-2xl font-bold mb-2",children:"動畫變體"}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"點擊按鈕查看不同的動畫效果"})]}),h.jsx("div",{className:"grid grid-cols-2 md:grid-cols-5 gap-4",children:s.map(r=>h.jsx("button",{onClick:()=>t(r.name),className:"px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors",children:r.label},r.name))}),h.jsx("div",{className:"bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[300px] flex items-center justify-center",children:h.jsx(Se,{mode:"wait",children:e&&h.jsxs(C.div,{variants:De(e,"default"),initial:"initial",animate:"animate",exit:"exit",className:"bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl",children:[h.jsx("h3",{className:"text-2xl font-bold mb-2",children:(i=s.find(r=>r.name===e))==null?void 0:i.label}),h.jsx("p",{className:"text-blue-100",children:(n=s.find(r=>r.name===e))==null?void 0:n.description})]},e)})})]})}},ne={render:()=>{const e=[{type:"light",label:"Light",description:"輕微",color:"bg-gray-500"},{type:"medium",label:"Medium",description:"中等",color:"bg-blue-500"},{type:"heavy",label:"Heavy",description:"重度",color:"bg-purple-500"},{type:"success",label:"Success",description:"成功",color:"bg-green-500"},{type:"warning",label:"Warning",description:"警告",color:"bg-yellow-500"},{type:"error",label:"Error",description:"錯誤",color:"bg-red-500"},{type:"selection",label:"Selection",description:"選擇",color:"bg-indigo-500"}];return h.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[h.jsxs("div",{children:[h.jsx("h2",{className:"text-2xl font-bold mb-2",children:"觸覺反饋模擬"}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"點擊按鈕體驗不同強度的觸覺反饋"})]}),h.jsx("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-6",children:e.map(t=>h.jsxs(C.button,{onClick:s=>q(s.currentTarget,t.type),whileHover:{scale:1.05},whileTap:Ir(t.type),className:`${t.color} text-white p-6 rounded-xl shadow-md`,children:[h.jsx("h3",{className:"text-lg font-semibold mb-1",children:t.label}),h.jsx("p",{className:"text-sm opacity-90",children:t.description})]},t.type))}),h.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("h3",{className:"text-lg font-semibold mb-4",children:"CSS 類名範例"}),h.jsx("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-4",children:e.map(t=>h.jsxs("button",{className:`haptic-${t.type} ${t.color} text-white px-4 py-3 rounded-lg`,children:[".haptic-",t.type]},`css-${t.type}`))})]})]})}},ae={render:()=>h.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[h.jsxs("div",{children:[h.jsx("h2",{className:"text-2xl font-bold mb-2",children:"按鈕互動"}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"Apple 風格的按鈕按壓效果"})]}),h.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Framer Motion 按鈕"}),h.jsxs("div",{className:"flex flex-wrap gap-4",children:[h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("snappy"),onClick:e=>q(e.currentTarget,"medium"),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"Primary Button"}),h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("bouncy"),onClick:e=>q(e.currentTarget,"success"),className:"px-6 py-3 bg-green-600 text-white rounded-lg shadow-md",children:"Success Button"}),h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("default"),onClick:e=>q(e.currentTarget,"warning"),className:"px-6 py-3 bg-yellow-600 text-white rounded-lg shadow-md",children:"Warning Button"}),h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("wobbly"),onClick:e=>q(e.currentTarget,"error"),className:"px-6 py-3 bg-red-600 text-white rounded-lg shadow-md",children:"Error Button"})]})]}),h.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("h3",{className:"text-lg font-semibold mb-4",children:"CSS 類名按鈕"}),h.jsxs("div",{className:"flex flex-wrap gap-4",children:[h.jsx("button",{className:"btn-spring-press px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"Standard Press"}),h.jsx("button",{className:"btn-spring-press-heavy px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md",children:"Heavy Press"}),h.jsx("button",{className:"spring-hover-lift px-6 py-3 bg-indigo-600 text-white rounded-lg shadow-md",children:"Hover Lift"}),h.jsx("button",{className:"spring-hover-scale px-6 py-3 bg-pink-600 text-white rounded-lg shadow-md",children:"Hover Scale"})]})]})]})},re={render:()=>{const[e,t]=y.useState(!1);return h.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[h.jsxs("div",{children:[h.jsx("h2",{className:"text-2xl font-bold mb-2",children:"模態對話框動畫"}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"iOS 風格的 Sheet 動畫"})]}),h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("snappy"),onClick:()=>t(!0),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"打開 Modal"}),h.jsx(Se,{children:e&&h.jsxs(h.Fragment,{children:[h.jsx(C.div,{initial:{opacity:0},animate:{opacity:1},exit:{opacity:0},onClick:()=>t(!1),className:"fixed inset-0 bg-black/40 z-40"}),h.jsxs(C.div,{variants:De("slideUp","default"),initial:"initial",animate:"animate",exit:"exit",className:"fixed inset-x-4 bottom-4 bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-2xl z-50 max-w-md mx-auto",children:[h.jsx("h3",{className:"text-xl font-bold mb-4",children:"iOS 風格 Sheet"}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400 mb-6",children:"這是一個使用彈性動畫的模態對話框，模擬 iOS 的 Sheet 效果。"}),h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("snappy"),onClick:()=>t(!1),className:"w-full px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"關閉"})]})]})})]})}},oe={render:()=>{const[e,t]=y.useState(!0),s=[{id:1,title:"項目 1",description:"這是第一個項目"},{id:2,title:"項目 2",description:"這是第二個項目"},{id:3,title:"項目 3",description:"這是第三個項目"},{id:4,title:"項目 4",description:"這是第四個項目"},{id:5,title:"項目 5",description:"這是第五個項目"}];return h.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[h.jsxs("div",{children:[h.jsx("h2",{className:"text-2xl font-bold mb-2",children:"列表交錯動畫"}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"子元素依序出現的動畫效果"})]}),h.jsxs(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("snappy"),onClick:()=>t(!e),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:[e?"隱藏":"顯示","列表"]}),h.jsx(Se,{children:e&&h.jsx(C.div,{variants:{animate:{transition:Tu("default",.08)}},initial:"initial",animate:"animate",exit:"exit",className:"space-y-4",children:s.map(i=>h.jsxs(C.div,{variants:De("slideUp","default"),className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("h3",{className:"text-lg font-semibold mb-2",children:i.title}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:i.description})]},i.id))})}),h.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("h3",{className:"text-lg font-semibold mb-4",children:"CSS 交錯動畫"}),h.jsx("div",{className:"stagger-children space-y-4",children:s.map(i=>h.jsxs("div",{className:"bg-gray-50 dark:bg-gray-700 p-4 rounded-lg",children:[h.jsx("h4",{className:"font-semibold",children:i.title}),h.jsx("p",{className:"text-sm text-gray-600 dark:text-gray-300",children:i.description})]},i.id))})]})]})}},le={render:()=>{const[e,t]=y.useState(!1),[s,i]=y.useState(!1),n=y.useRef(null),r=y.useRef(null);return y.useEffect(()=>{e&&n.current&&q(n.current,"success")},[e]),y.useEffect(()=>{s&&r.current&&q(r.current,"error")},[s]),h.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[h.jsxs("div",{children:[h.jsx("h2",{className:"text-2xl font-bold mb-2",children:"成功/錯誤反饋"}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"帶有觸覺反饋的狀態提示"})]}),h.jsxs("div",{className:"flex gap-4",children:[h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("snappy"),onClick:()=>{t(!0),setTimeout(()=>t(!1),3e3)},className:"px-6 py-3 bg-green-600 text-white rounded-lg shadow-md",children:"顯示成功"}),h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("snappy"),onClick:()=>{i(!0),setTimeout(()=>i(!1),3e3)},className:"px-6 py-3 bg-red-600 text-white rounded-lg shadow-md",children:"顯示錯誤"})]}),h.jsxs("div",{className:"space-y-4",children:[h.jsx(Se,{children:e&&h.jsxs(C.div,{ref:n,variants:De("bounce","bouncy"),initial:"initial",animate:"animate",exit:"exit",className:"bg-green-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3",children:[h.jsx("div",{className:"text-2xl",children:"✓"}),h.jsxs("div",{children:[h.jsx("h3",{className:"font-semibold",children:"操作成功！"}),h.jsx("p",{className:"text-sm opacity-90",children:"您的更改已保存"})]})]})}),h.jsx(Se,{children:s&&h.jsxs(C.div,{ref:r,variants:De("shake","wobbly"),initial:"initial",animate:"animate",exit:"exit",className:"bg-red-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3",children:[h.jsx("div",{className:"text-2xl",children:"✗"}),h.jsxs("div",{children:[h.jsx("h3",{className:"font-semibold",children:"操作失敗！"}),h.jsx("p",{className:"text-sm opacity-90",children:"請稍後再試"})]})]})})]})]})}},ce={render:()=>{const[e,t]=y.useState(Su()),[s,i]=y.useState(0);return h.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[h.jsxs("div",{children:[h.jsx("h2",{className:"text-2xl font-bold mb-2",children:"上下文感知動畫"}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"根據用戶環境自動調整動畫"})]}),h.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("h3",{className:"text-lg font-semibold mb-4",children:"當前上下文"}),h.jsxs("div",{className:"grid grid-cols-2 gap-4 text-sm",children:[h.jsxs("div",{children:[h.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"設備類型："}),h.jsx("span",{className:"font-semibold ml-2",children:e.isMobile?"移動設備":"桌面設備"})]}),h.jsxs("div",{children:[h.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"低電量模式："}),h.jsx("span",{className:"font-semibold ml-2",children:e.isLowPower?"是":"否"})]}),h.jsxs("div",{children:[h.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"網絡速度："}),h.jsx("span",{className:"font-semibold ml-2",children:e.connectionSpeed})]}),h.jsxs("div",{children:[h.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"用戶偏好："}),h.jsx("span",{className:"font-semibold ml-2",children:e.userPreference})]})]})]}),h.jsx("div",{className:"bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[200px] flex items-center justify-center",children:h.jsxs(C.div,{...wu("slideUp",e),initial:"initial",animate:"animate",className:"bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl",children:[h.jsx("h3",{className:"text-2xl font-bold",children:"上下文感知動畫"}),h.jsx("p",{className:"text-blue-100 mt-2",children:"根據您的環境自動調整"})]},s)}),h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("snappy"),onClick:()=>i(n=>n+1),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"重新播放動畫"})]})}},de={render:()=>{const[e,t]=y.useState(Zi()),[s,i]=y.useState(!1),n=()=>{i(!0),Nu(),setTimeout(()=>{i(!1),t(Zi())},1e3)};return h.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[h.jsxs("div",{children:[h.jsx("h2",{className:"text-2xl font-bold mb-2",children:"性能監控"}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"追蹤動畫性能指標"})]}),h.jsxs("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-4",children:[h.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("div",{className:"text-3xl font-bold text-blue-600",children:e.totalAnimations}),h.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"總動畫數"})]}),h.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("div",{className:"text-3xl font-bold text-green-600",children:e.activeAnimations}),h.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"活躍動畫"})]}),h.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("div",{className:"text-3xl font-bold text-yellow-600",children:e.droppedFrames}),h.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"掉幀數"})]}),h.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("div",{className:"text-3xl font-bold text-purple-600",children:e.averageFPS.toFixed(1)}),h.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"平均 FPS"})]})]}),h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("snappy"),onClick:n,disabled:s,className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md disabled:opacity-50",children:s?"動畫中...":"開始動畫"}),h.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[h.jsx("h3",{className:"text-lg font-semibold mb-4",children:"性能建議"}),h.jsxs("div",{className:"space-y-2 text-sm",children:[e.averageFPS<55&&h.jsx("div",{className:"text-red-600 dark:text-red-400",children:"⚠️ 平均 FPS 低於 55，建議降級到更簡單的動畫"}),e.activeAnimations>5&&h.jsx("div",{className:"text-yellow-600 dark:text-yellow-400",children:"⚠️ 同時活躍動畫過多，可能影響性能"}),e.droppedFrames>10&&h.jsx("div",{className:"text-orange-600 dark:text-orange-400",children:"⚠️ 掉幀數較多，建議優化動畫"}),e.averageFPS>=55&&e.activeAnimations<=5&&e.droppedFrames<=10&&h.jsx("div",{className:"text-green-600 dark:text-green-400",children:"✓ 性能良好，動畫流暢"})]})]})]})}},ue={render:()=>{const[e,t]=y.useState(!1);return h.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[h.jsxs("div",{children:[h.jsx("h2",{className:"text-2xl font-bold mb-2",children:"完整演示"}),h.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"綜合展示彈性動畫系統的各種功能"})]}),h.jsxs(C.div,{layout:!0,onClick:()=>t(!e),className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md cursor-pointer",whileHover:{scale:1.02},transition:E("default"),children:[h.jsx(C.h3,{layout:"position",className:"text-xl font-bold mb-2",children:"互動卡片"}),h.jsx(C.p,{layout:"position",className:"text-gray-600 dark:text-gray-400",children:"點擊展開查看更多內容"}),h.jsx(Se,{children:e&&h.jsxs(C.div,{initial:{opacity:0,height:0},animate:{opacity:1,height:"auto"},exit:{opacity:0,height:0},transition:E("default"),className:"mt-4 pt-4 border-t border-gray-200 dark:border-gray-700",children:[h.jsx("p",{className:"text-gray-600 dark:text-gray-400 mb-4",children:"這是展開的內容區域，使用了彈性動畫來創造流暢的展開效果。"}),h.jsxs("div",{className:"flex gap-2",children:[h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("snappy"),onClick:s=>{s.stopPropagation(),q(s.currentTarget,"success")},className:"px-4 py-2 bg-green-600 text-white rounded-lg text-sm",children:"確認"}),h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("snappy"),onClick:s=>{s.stopPropagation(),t(!1)},className:"px-4 py-2 bg-gray-600 text-white rounded-lg text-sm",children:"取消"})]})]})})]}),h.jsx("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-4",children:["Primary","Success","Warning","Error"].map((s,i)=>h.jsx(C.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:E("snappy"),onClick:n=>{const r=["medium","success","warning","error"][i];q(n.currentTarget,r)},className:`px-6 py-3 text-white rounded-lg shadow-md ${["bg-blue-600","bg-green-600","bg-yellow-600","bg-red-600"][i]}`,children:s},s))})]})}};var Ji,Qi,en;se.parameters={...se.parameters,docs:{...(Ji=se.parameters)==null?void 0:Ji.docs,source:{originalSource:`{
  render: () => {
    const [activePreset, setActivePreset] = useState<string | null>(null);
    const presets = [{
      name: 'gentle',
      label: 'Gentle',
      description: '溫和的彈性動畫',
      color: 'bg-blue-100 dark:bg-blue-900'
    }, {
      name: 'default',
      label: 'Default',
      description: '標準 iOS 動畫（推薦）',
      color: 'bg-green-100 dark:bg-green-900'
    }, {
      name: 'bouncy',
      label: 'Bouncy',
      description: '活潑、有趣的彈性',
      color: 'bg-purple-100 dark:bg-purple-900'
    }, {
      name: 'snappy',
      label: 'Snappy',
      description: '快速、響應式',
      color: 'bg-orange-100 dark:bg-orange-900'
    }, {
      name: 'smooth',
      label: 'Smooth',
      description: '優雅、流暢',
      color: 'bg-pink-100 dark:bg-pink-900'
    }, {
      name: 'wobbly',
      label: 'Wobbly',
      description: '誇張的彈性效果',
      color: 'bg-yellow-100 dark:bg-yellow-900'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">6 種彈性預設</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊查看不同彈性動畫的效果</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          {presets.map(preset => <motion.button key={preset.name} onClick={() => setActivePreset(preset.name)} whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig(preset.name as keyof typeof springPresets)} className={\`\${preset.color} p-6 rounded-xl shadow-md text-left relative overflow-hidden\`}>
              <div className="relative z-10">
                <h3 className="text-lg font-semibold mb-1">{preset.label}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">{preset.description}</p>
              </div>
              
              <AnimatePresence>
                {activePreset === preset.name && <motion.div initial={{
              scale: 0,
              opacity: 0
            }} animate={{
              scale: 1,
              opacity: 1
            }} exit={{
              scale: 0,
              opacity: 0
            }} transition={getSpringConfig(preset.name as keyof typeof springPresets)} className="absolute inset-0 bg-white/20 dark:bg-black/20" />}
              </AnimatePresence>
            </motion.button>)}
        </div>
        
        {/* 技術參數展示 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">技術參數</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(springPresets).map(([name, config]) => <div key={name} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h4 className="font-semibold capitalize mb-2">{name}</h4>
                <div className="text-sm space-y-1 text-gray-600 dark:text-gray-300">
                  <div>Stiffness: {config.stiffness}</div>
                  <div>Damping: {config.damping}</div>
                  <div>Mass: {config.mass}</div>
                  <div>Duration: {config.duration}s</div>
                </div>
              </div>)}
          </div>
        </div>
      </div>;
  }
}`,...(en=(Qi=se.parameters)==null?void 0:Qi.docs)==null?void 0:en.source}}};var tn,sn,nn;ie.parameters={...ie.parameters,docs:{...(tn=ie.parameters)==null?void 0:tn.docs,source:{originalSource:`{
  render: () => {
    const [activeVariant, setActiveVariant] = useState<string | null>(null);
    const variants = [{
      name: 'fade',
      label: 'Fade',
      description: '淡入淡出'
    }, {
      name: 'scale',
      label: 'Scale',
      description: '縮放'
    }, {
      name: 'pop',
      label: 'Pop',
      description: '彈出'
    }, {
      name: 'bounce',
      label: 'Bounce',
      description: '彈跳'
    }, {
      name: 'slideUp',
      label: 'Slide Up',
      description: '向上滑動'
    }, {
      name: 'slideDown',
      label: 'Slide Down',
      description: '向下滑動'
    }, {
      name: 'slideLeft',
      label: 'Slide Left',
      description: '向左滑動'
    }, {
      name: 'slideRight',
      label: 'Slide Right',
      description: '向右滑動'
    }, {
      name: 'shake',
      label: 'Shake',
      description: '搖晃'
    }, {
      name: 'pulse',
      label: 'Pulse',
      description: '脈衝'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">動畫變體</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊按鈕查看不同的動畫效果</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {variants.map(variant => <button key={variant.name} onClick={() => setActiveVariant(variant.name)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              {variant.label}
            </button>)}
        </div>
        
        {/* 動畫展示區域 */}
        <div className="bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[300px] flex items-center justify-center">
          <AnimatePresence mode="wait">
            {activeVariant && <motion.div key={activeVariant} variants={getSpringVariants(activeVariant, 'default')} initial="initial" animate="animate" exit="exit" className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl">
                <h3 className="text-2xl font-bold mb-2">
                  {variants.find(v => v.name === activeVariant)?.label}
                </h3>
                <p className="text-blue-100">
                  {variants.find(v => v.name === activeVariant)?.description}
                </p>
              </motion.div>}
          </AnimatePresence>
        </div>
      </div>;
  }
}`,...(nn=(sn=ie.parameters)==null?void 0:sn.docs)==null?void 0:nn.source}}};var an,rn,on;ne.parameters={...ne.parameters,docs:{...(an=ne.parameters)==null?void 0:an.docs,source:{originalSource:`{
  render: () => {
    const haptics = [{
      type: 'light',
      label: 'Light',
      description: '輕微',
      color: 'bg-gray-500'
    }, {
      type: 'medium',
      label: 'Medium',
      description: '中等',
      color: 'bg-blue-500'
    }, {
      type: 'heavy',
      label: 'Heavy',
      description: '重度',
      color: 'bg-purple-500'
    }, {
      type: 'success',
      label: 'Success',
      description: '成功',
      color: 'bg-green-500'
    }, {
      type: 'warning',
      label: 'Warning',
      description: '警告',
      color: 'bg-yellow-500'
    }, {
      type: 'error',
      label: 'Error',
      description: '錯誤',
      color: 'bg-red-500'
    }, {
      type: 'selection',
      label: 'Selection',
      description: '選擇',
      color: 'bg-indigo-500'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">觸覺反饋模擬</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊按鈕體驗不同強度的觸覺反饋</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {haptics.map(haptic => <motion.button key={haptic.type} onClick={e => triggerHaptic(e.currentTarget, haptic.type as any)} whileHover={{
          scale: 1.05
        }} whileTap={getHapticAnimation(haptic.type as any)} className={\`\${haptic.color} text-white p-6 rounded-xl shadow-md\`}>
              <h3 className="text-lg font-semibold mb-1">{haptic.label}</h3>
              <p className="text-sm opacity-90">{haptic.description}</p>
            </motion.button>)}
        </div>
        
        {/* CSS 類名範例 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 類名範例</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {haptics.map(haptic => <button key={\`css-\${haptic.type}\`} className={\`haptic-\${haptic.type} \${haptic.color} text-white px-4 py-3 rounded-lg\`}>
                .haptic-{haptic.type}
              </button>)}
          </div>
        </div>
      </div>;
  }
}`,...(on=(rn=ne.parameters)==null?void 0:rn.docs)==null?void 0:on.source}}};var ln,cn,dn;ae.parameters={...ae.parameters,docs:{...(ln=ae.parameters)==null?void 0:ln.docs,source:{originalSource:`{
  render: () => {
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">按鈕互動</h2>
          <p className="text-gray-600 dark:text-gray-400">Apple 風格的按鈕按壓效果</p>
        </div>
        
        {/* Framer Motion 按鈕 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">Framer Motion 按鈕</h3>
          <div className="flex flex-wrap gap-4">
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('snappy')} onClick={e => triggerHaptic(e.currentTarget, 'medium')} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
              Primary Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('bouncy')} onClick={e => triggerHaptic(e.currentTarget, 'success')} className="px-6 py-3 bg-green-600 text-white rounded-lg shadow-md">
              Success Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('default')} onClick={e => triggerHaptic(e.currentTarget, 'warning')} className="px-6 py-3 bg-yellow-600 text-white rounded-lg shadow-md">
              Warning Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('wobbly')} onClick={e => triggerHaptic(e.currentTarget, 'error')} className="px-6 py-3 bg-red-600 text-white rounded-lg shadow-md">
              Error Button
            </motion.button>
          </div>
        </div>
        
        {/* CSS 類名按鈕 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 類名按鈕</h3>
          <div className="flex flex-wrap gap-4">
            <button className="btn-spring-press px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
              Standard Press
            </button>
            
            <button className="btn-spring-press-heavy px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md">
              Heavy Press
            </button>
            
            <button className="spring-hover-lift px-6 py-3 bg-indigo-600 text-white rounded-lg shadow-md">
              Hover Lift
            </button>
            
            <button className="spring-hover-scale px-6 py-3 bg-pink-600 text-white rounded-lg shadow-md">
              Hover Scale
            </button>
          </div>
        </div>
      </div>;
  }
}`,...(dn=(cn=ae.parameters)==null?void 0:cn.docs)==null?void 0:dn.source}}};var un,hn,mn;re.parameters={...re.parameters,docs:{...(un=re.parameters)==null?void 0:un.docs,source:{originalSource:`{
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">模態對話框動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">iOS 風格的 Sheet 動畫</p>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setIsOpen(true)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          打開 Modal
        </motion.button>
        
        <AnimatePresence>
          {isOpen && <>
              {/* 背景遮罩 */}
              <motion.div initial={{
            opacity: 0
          }} animate={{
            opacity: 1
          }} exit={{
            opacity: 0
          }} onClick={() => setIsOpen(false)} className="fixed inset-0 bg-black/40 z-40" />
              
              {/* 對話框 */}
              <motion.div variants={getSpringVariants('slideUp', 'default')} initial="initial" animate="animate" exit="exit" className="fixed inset-x-4 bottom-4 bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-2xl z-50 max-w-md mx-auto">
                <h3 className="text-xl font-bold mb-4">iOS 風格 Sheet</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  這是一個使用彈性動畫的模態對話框，模擬 iOS 的 Sheet 效果。
                </p>
                <motion.button whileHover={{
              scale: 1.05
            }} whileTap={{
              scale: 0.95
            }} transition={getSpringConfig('snappy')} onClick={() => setIsOpen(false)} className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
                  關閉
                </motion.button>
              </motion.div>
            </>}
        </AnimatePresence>
      </div>;
  }
}`,...(mn=(hn=re.parameters)==null?void 0:hn.docs)==null?void 0:mn.source}}};var pn,fn,gn;oe.parameters={...oe.parameters,docs:{...(pn=oe.parameters)==null?void 0:pn.docs,source:{originalSource:`{
  render: () => {
    const [show, setShow] = useState(true);
    const items = [{
      id: 1,
      title: '項目 1',
      description: '這是第一個項目'
    }, {
      id: 2,
      title: '項目 2',
      description: '這是第二個項目'
    }, {
      id: 3,
      title: '項目 3',
      description: '這是第三個項目'
    }, {
      id: 4,
      title: '項目 4',
      description: '這是第四個項目'
    }, {
      id: 5,
      title: '項目 5',
      description: '這是第五個項目'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">列表交錯動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">子元素依序出現的動畫效果</p>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setShow(!show)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          {show ? '隱藏' : '顯示'}列表
        </motion.button>
        
        <AnimatePresence>
          {show && <motion.div variants={{
          animate: {
            transition: getStaggerConfig('default', 0.08)
          }
        }} initial="initial" animate="animate" exit="exit" className="space-y-4">
              {items.map(item => <motion.div key={item.id} variants={getSpringVariants('slideUp', 'default')} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
                  <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                  <p className="text-gray-600 dark:text-gray-400">{item.description}</p>
                </motion.div>)}
            </motion.div>}
        </AnimatePresence>
        
        {/* CSS 交錯動畫 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 交錯動畫</h3>
          <div className="stagger-children space-y-4">
            {items.map(item => <div key={item.id} className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 className="font-semibold">{item.title}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">{item.description}</p>
              </div>)}
          </div>
        </div>
      </div>;
  }
}`,...(gn=(fn=oe.parameters)==null?void 0:fn.docs)==null?void 0:gn.source}}};var yn,xn,bn;le.parameters={...le.parameters,docs:{...(yn=le.parameters)==null?void 0:yn.docs,source:{originalSource:`{
  render: () => {
    const [showSuccess, setShowSuccess] = useState(false);
    const [showError, setShowError] = useState(false);
    const successRef = useRef<HTMLDivElement>(null);
    const errorRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
      if (showSuccess && successRef.current) {
        triggerHaptic(successRef.current, 'success');
      }
    }, [showSuccess]);
    useEffect(() => {
      if (showError && errorRef.current) {
        triggerHaptic(errorRef.current, 'error');
      }
    }, [showError]);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">成功/錯誤反饋</h2>
          <p className="text-gray-600 dark:text-gray-400">帶有觸覺反饋的狀態提示</p>
        </div>
        
        <div className="flex gap-4">
          <motion.button whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={() => {
          setShowSuccess(true);
          setTimeout(() => setShowSuccess(false), 3000);
        }} className="px-6 py-3 bg-green-600 text-white rounded-lg shadow-md">
            顯示成功
          </motion.button>
          
          <motion.button whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={() => {
          setShowError(true);
          setTimeout(() => setShowError(false), 3000);
        }} className="px-6 py-3 bg-red-600 text-white rounded-lg shadow-md">
            顯示錯誤
          </motion.button>
        </div>
        
        <div className="space-y-4">
          <AnimatePresence>
            {showSuccess && <motion.div ref={successRef} variants={getSpringVariants('bounce', 'bouncy')} initial="initial" animate="animate" exit="exit" className="bg-green-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3">
                <div className="text-2xl">✓</div>
                <div>
                  <h3 className="font-semibold">操作成功！</h3>
                  <p className="text-sm opacity-90">您的更改已保存</p>
                </div>
              </motion.div>}
          </AnimatePresence>
          
          <AnimatePresence>
            {showError && <motion.div ref={errorRef} variants={getSpringVariants('shake', 'wobbly')} initial="initial" animate="animate" exit="exit" className="bg-red-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3">
                <div className="text-2xl">✗</div>
                <div>
                  <h3 className="font-semibold">操作失敗！</h3>
                  <p className="text-sm opacity-90">請稍後再試</p>
                </div>
              </motion.div>}
          </AnimatePresence>
        </div>
      </div>;
  }
}`,...(bn=(xn=le.parameters)==null?void 0:xn.docs)==null?void 0:bn.source}}};var vn,wn,Sn;ce.parameters={...ce.parameters,docs:{...(vn=ce.parameters)==null?void 0:vn.docs,source:{originalSource:`{
  render: () => {
    const [context, setContext] = useState(getUserContext());
    const [animationKey, setAnimationKey] = useState(0);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">上下文感知動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">根據用戶環境自動調整動畫</p>
        </div>
        
        {/* 當前上下文 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">當前上下文</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">設備類型：</span>
              <span className="font-semibold ml-2">{context.isMobile ? '移動設備' : '桌面設備'}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">低電量模式：</span>
              <span className="font-semibold ml-2">{context.isLowPower ? '是' : '否'}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">網絡速度：</span>
              <span className="font-semibold ml-2">{context.connectionSpeed}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">用戶偏好：</span>
              <span className="font-semibold ml-2">{context.userPreference}</span>
            </div>
          </div>
        </div>
        
        {/* 動畫展示 */}
        <div className="bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[200px] flex items-center justify-center">
          <motion.div key={animationKey} {...getContextualAnimation('slideUp', context)} initial="initial" animate="animate" className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl">
            <h3 className="text-2xl font-bold">上下文感知動畫</h3>
            <p className="text-blue-100 mt-2">根據您的環境自動調整</p>
          </motion.div>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setAnimationKey(k => k + 1)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          重新播放動畫
        </motion.button>
      </div>;
  }
}`,...(Sn=(wn=ce.parameters)==null?void 0:wn.docs)==null?void 0:Sn.source}}};var Tn,Nn,Pn;de.parameters={...de.parameters,docs:{...(Tn=de.parameters)==null?void 0:Tn.docs,source:{originalSource:`{
  render: () => {
    const [metrics, setMetrics] = useState(getAnimationMetrics());
    const [isAnimating, setIsAnimating] = useState(false);
    const startAnimation = () => {
      setIsAnimating(true);
      trackAnimation('demo-animation');
      setTimeout(() => {
        setIsAnimating(false);
        setMetrics(getAnimationMetrics());
      }, 1000);
    };
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">性能監控</h2>
          <p className="text-gray-600 dark:text-gray-400">追蹤動畫性能指標</p>
        </div>
        
        {/* 性能指標 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-blue-600">{metrics.totalAnimations}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">總動畫數</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-green-600">{metrics.activeAnimations}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">活躍動畫</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-yellow-600">{metrics.droppedFrames}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">掉幀數</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-purple-600">{metrics.averageFPS.toFixed(1)}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">平均 FPS</div>
          </div>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={startAnimation} disabled={isAnimating} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md disabled:opacity-50">
          {isAnimating ? '動畫中...' : '開始動畫'}
        </motion.button>
        
        {/* 性能建議 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">性能建議</h3>
          <div className="space-y-2 text-sm">
            {metrics.averageFPS < 55 && <div className="text-red-600 dark:text-red-400">
                ⚠️ 平均 FPS 低於 55，建議降級到更簡單的動畫
              </div>}
            {metrics.activeAnimations > 5 && <div className="text-yellow-600 dark:text-yellow-400">
                ⚠️ 同時活躍動畫過多，可能影響性能
              </div>}
            {metrics.droppedFrames > 10 && <div className="text-orange-600 dark:text-orange-400">
                ⚠️ 掉幀數較多，建議優化動畫
              </div>}
            {metrics.averageFPS >= 55 && metrics.activeAnimations <= 5 && metrics.droppedFrames <= 10 && <div className="text-green-600 dark:text-green-400">
                ✓ 性能良好，動畫流暢
              </div>}
          </div>
        </div>
      </div>;
  }
}`,...(Pn=(Nn=de.parameters)==null?void 0:Nn.docs)==null?void 0:Pn.source}}};var kn,An,Cn;ue.parameters={...ue.parameters,docs:{...(kn=ue.parameters)==null?void 0:kn.docs,source:{originalSource:`{
  render: () => {
    const [isCardOpen, setIsCardOpen] = useState(false);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">完整演示</h2>
          <p className="text-gray-600 dark:text-gray-400">綜合展示彈性動畫系統的各種功能</p>
        </div>
        
        {/* 互動卡片 */}
        <motion.div layout onClick={() => setIsCardOpen(!isCardOpen)} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md cursor-pointer" whileHover={{
        scale: 1.02
      }} transition={getSpringConfig('default')}>
          <motion.h3 layout="position" className="text-xl font-bold mb-2">
            互動卡片
          </motion.h3>
          <motion.p layout="position" className="text-gray-600 dark:text-gray-400">
            點擊展開查看更多內容
          </motion.p>
          
          <AnimatePresence>
            {isCardOpen && <motion.div initial={{
            opacity: 0,
            height: 0
          }} animate={{
            opacity: 1,
            height: 'auto'
          }} exit={{
            opacity: 0,
            height: 0
          }} transition={getSpringConfig('default')} className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  這是展開的內容區域，使用了彈性動畫來創造流暢的展開效果。
                </p>
                <div className="flex gap-2">
                  <motion.button whileHover={{
                scale: 1.05
              }} whileTap={{
                scale: 0.95
              }} transition={getSpringConfig('snappy')} onClick={e => {
                e.stopPropagation();
                triggerHaptic(e.currentTarget, 'success');
              }} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm">
                    確認
                  </motion.button>
                  <motion.button whileHover={{
                scale: 1.05
              }} whileTap={{
                scale: 0.95
              }} transition={getSpringConfig('snappy')} onClick={e => {
                e.stopPropagation();
                setIsCardOpen(false);
              }} className="px-4 py-2 bg-gray-600 text-white rounded-lg text-sm">
                    取消
                  </motion.button>
                </div>
              </motion.div>}
          </AnimatePresence>
        </motion.div>
        
        {/* 功能按鈕組 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {['Primary', 'Success', 'Warning', 'Error'].map((type, i) => <motion.button key={type} whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={e => {
          const hapticType = ['medium', 'success', 'warning', 'error'][i];
          triggerHaptic(e.currentTarget, hapticType as any);
        }} className={\`px-6 py-3 text-white rounded-lg shadow-md \${['bg-blue-600', 'bg-green-600', 'bg-yellow-600', 'bg-red-600'][i]}\`}>
              {type}
            </motion.button>)}
        </div>
      </div>;
  }
}`,...(Cn=(An=ue.parameters)==null?void 0:An.docs)==null?void 0:Cn.source}}};var Vn,Mn,jn;se.parameters={...se.parameters,docs:{...(Vn=se.parameters)==null?void 0:Vn.docs,source:{originalSource:`{
  render: () => {
    const [activePreset, setActivePreset] = useState<string | null>(null);
    const presets = [{
      name: 'gentle',
      label: 'Gentle',
      description: '溫和的彈性動畫',
      color: 'bg-blue-100 dark:bg-blue-900'
    }, {
      name: 'default',
      label: 'Default',
      description: '標準 iOS 動畫（推薦）',
      color: 'bg-green-100 dark:bg-green-900'
    }, {
      name: 'bouncy',
      label: 'Bouncy',
      description: '活潑、有趣的彈性',
      color: 'bg-purple-100 dark:bg-purple-900'
    }, {
      name: 'snappy',
      label: 'Snappy',
      description: '快速、響應式',
      color: 'bg-orange-100 dark:bg-orange-900'
    }, {
      name: 'smooth',
      label: 'Smooth',
      description: '優雅、流暢',
      color: 'bg-pink-100 dark:bg-pink-900'
    }, {
      name: 'wobbly',
      label: 'Wobbly',
      description: '誇張的彈性效果',
      color: 'bg-yellow-100 dark:bg-yellow-900'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">6 種彈性預設</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊查看不同彈性動畫的效果</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          {presets.map(preset => <motion.button key={preset.name} onClick={() => setActivePreset(preset.name)} whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig(preset.name as keyof typeof springPresets)} className={\`\${preset.color} p-6 rounded-xl shadow-md text-left relative overflow-hidden\`}>
              <div className="relative z-10">
                <h3 className="text-lg font-semibold mb-1">{preset.label}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">{preset.description}</p>
              </div>
              
              <AnimatePresence>
                {activePreset === preset.name && <motion.div initial={{
              scale: 0,
              opacity: 0
            }} animate={{
              scale: 1,
              opacity: 1
            }} exit={{
              scale: 0,
              opacity: 0
            }} transition={getSpringConfig(preset.name as keyof typeof springPresets)} className="absolute inset-0 bg-white/20 dark:bg-black/20" />}
              </AnimatePresence>
            </motion.button>)}
        </div>
        
        {/* 技術參數展示 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">技術參數</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(springPresets).map(([name, config]) => <div key={name} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h4 className="font-semibold capitalize mb-2">{name}</h4>
                <div className="text-sm space-y-1 text-gray-600 dark:text-gray-300">
                  <div>Stiffness: {config.stiffness}</div>
                  <div>Damping: {config.damping}</div>
                  <div>Mass: {config.mass}</div>
                  <div>Duration: {config.duration}s</div>
                </div>
              </div>)}
          </div>
        </div>
      </div>;
  }
}`,...(jn=(Mn=se.parameters)==null?void 0:Mn.docs)==null?void 0:jn.source}}};var Dn,Rn,En;ie.parameters={...ie.parameters,docs:{...(Dn=ie.parameters)==null?void 0:Dn.docs,source:{originalSource:`{
  render: () => {
    const [activeVariant, setActiveVariant] = useState<string | null>(null);
    const variants = [{
      name: 'fade',
      label: 'Fade',
      description: '淡入淡出'
    }, {
      name: 'scale',
      label: 'Scale',
      description: '縮放'
    }, {
      name: 'pop',
      label: 'Pop',
      description: '彈出'
    }, {
      name: 'bounce',
      label: 'Bounce',
      description: '彈跳'
    }, {
      name: 'slideUp',
      label: 'Slide Up',
      description: '向上滑動'
    }, {
      name: 'slideDown',
      label: 'Slide Down',
      description: '向下滑動'
    }, {
      name: 'slideLeft',
      label: 'Slide Left',
      description: '向左滑動'
    }, {
      name: 'slideRight',
      label: 'Slide Right',
      description: '向右滑動'
    }, {
      name: 'shake',
      label: 'Shake',
      description: '搖晃'
    }, {
      name: 'pulse',
      label: 'Pulse',
      description: '脈衝'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">動畫變體</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊按鈕查看不同的動畫效果</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {variants.map(variant => <button key={variant.name} onClick={() => setActiveVariant(variant.name)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              {variant.label}
            </button>)}
        </div>
        
        {/* 動畫展示區域 */}
        <div className="bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[300px] flex items-center justify-center">
          <AnimatePresence mode="wait">
            {activeVariant && <motion.div key={activeVariant} variants={getSpringVariants(activeVariant, 'default')} initial="initial" animate="animate" exit="exit" className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl">
                <h3 className="text-2xl font-bold mb-2">
                  {variants.find(v => v.name === activeVariant)?.label}
                </h3>
                <p className="text-blue-100">
                  {variants.find(v => v.name === activeVariant)?.description}
                </p>
              </motion.div>}
          </AnimatePresence>
        </div>
      </div>;
  }
}`,...(En=(Rn=ie.parameters)==null?void 0:Rn.docs)==null?void 0:En.source}}};var Ln,Fn,In;ne.parameters={...ne.parameters,docs:{...(Ln=ne.parameters)==null?void 0:Ln.docs,source:{originalSource:`{
  render: () => {
    const haptics = [{
      type: 'light',
      label: 'Light',
      description: '輕微',
      color: 'bg-gray-500'
    }, {
      type: 'medium',
      label: 'Medium',
      description: '中等',
      color: 'bg-blue-500'
    }, {
      type: 'heavy',
      label: 'Heavy',
      description: '重度',
      color: 'bg-purple-500'
    }, {
      type: 'success',
      label: 'Success',
      description: '成功',
      color: 'bg-green-500'
    }, {
      type: 'warning',
      label: 'Warning',
      description: '警告',
      color: 'bg-yellow-500'
    }, {
      type: 'error',
      label: 'Error',
      description: '錯誤',
      color: 'bg-red-500'
    }, {
      type: 'selection',
      label: 'Selection',
      description: '選擇',
      color: 'bg-indigo-500'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">觸覺反饋模擬</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊按鈕體驗不同強度的觸覺反饋</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {haptics.map(haptic => <motion.button key={haptic.type} onClick={e => triggerHaptic(e.currentTarget, haptic.type as any)} whileHover={{
          scale: 1.05
        }} whileTap={getHapticAnimation(haptic.type as any)} className={\`\${haptic.color} text-white p-6 rounded-xl shadow-md\`}>
              <h3 className="text-lg font-semibold mb-1">{haptic.label}</h3>
              <p className="text-sm opacity-90">{haptic.description}</p>
            </motion.button>)}
        </div>
        
        {/* CSS 類名範例 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 類名範例</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {haptics.map(haptic => <button key={\`css-\${haptic.type}\`} className={\`haptic-\${haptic.type} \${haptic.color} text-white px-4 py-3 rounded-lg\`}>
                .haptic-{haptic.type}
              </button>)}
          </div>
        </div>
      </div>;
  }
}`,...(In=(Fn=ne.parameters)==null?void 0:Fn.docs)==null?void 0:In.source}}};var On,Bn,Hn;ae.parameters={...ae.parameters,docs:{...(On=ae.parameters)==null?void 0:On.docs,source:{originalSource:`{
  render: () => {
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">按鈕互動</h2>
          <p className="text-gray-600 dark:text-gray-400">Apple 風格的按鈕按壓效果</p>
        </div>
        
        {/* Framer Motion 按鈕 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">Framer Motion 按鈕</h3>
          <div className="flex flex-wrap gap-4">
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('snappy')} onClick={e => triggerHaptic(e.currentTarget, 'medium')} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
              Primary Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('bouncy')} onClick={e => triggerHaptic(e.currentTarget, 'success')} className="px-6 py-3 bg-green-600 text-white rounded-lg shadow-md">
              Success Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('default')} onClick={e => triggerHaptic(e.currentTarget, 'warning')} className="px-6 py-3 bg-yellow-600 text-white rounded-lg shadow-md">
              Warning Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('wobbly')} onClick={e => triggerHaptic(e.currentTarget, 'error')} className="px-6 py-3 bg-red-600 text-white rounded-lg shadow-md">
              Error Button
            </motion.button>
          </div>
        </div>
        
        {/* CSS 類名按鈕 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 類名按鈕</h3>
          <div className="flex flex-wrap gap-4">
            <button className="btn-spring-press px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
              Standard Press
            </button>
            
            <button className="btn-spring-press-heavy px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md">
              Heavy Press
            </button>
            
            <button className="spring-hover-lift px-6 py-3 bg-indigo-600 text-white rounded-lg shadow-md">
              Hover Lift
            </button>
            
            <button className="spring-hover-scale px-6 py-3 bg-pink-600 text-white rounded-lg shadow-md">
              Hover Scale
            </button>
          </div>
        </div>
      </div>;
  }
}`,...(Hn=(Bn=ae.parameters)==null?void 0:Bn.docs)==null?void 0:Hn.source}}};var Un,Wn,Kn;re.parameters={...re.parameters,docs:{...(Un=re.parameters)==null?void 0:Un.docs,source:{originalSource:`{
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">模態對話框動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">iOS 風格的 Sheet 動畫</p>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setIsOpen(true)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          打開 Modal
        </motion.button>
        
        <AnimatePresence>
          {isOpen && <>
              {/* 背景遮罩 */}
              <motion.div initial={{
            opacity: 0
          }} animate={{
            opacity: 1
          }} exit={{
            opacity: 0
          }} onClick={() => setIsOpen(false)} className="fixed inset-0 bg-black/40 z-40" />
              
              {/* 對話框 */}
              <motion.div variants={getSpringVariants('slideUp', 'default')} initial="initial" animate="animate" exit="exit" className="fixed inset-x-4 bottom-4 bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-2xl z-50 max-w-md mx-auto">
                <h3 className="text-xl font-bold mb-4">iOS 風格 Sheet</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  這是一個使用彈性動畫的模態對話框，模擬 iOS 的 Sheet 效果。
                </p>
                <motion.button whileHover={{
              scale: 1.05
            }} whileTap={{
              scale: 0.95
            }} transition={getSpringConfig('snappy')} onClick={() => setIsOpen(false)} className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
                  關閉
                </motion.button>
              </motion.div>
            </>}
        </AnimatePresence>
      </div>;
  }
}`,...(Kn=(Wn=re.parameters)==null?void 0:Wn.docs)==null?void 0:Kn.source}}};var $n,zn,Gn;oe.parameters={...oe.parameters,docs:{...($n=oe.parameters)==null?void 0:$n.docs,source:{originalSource:`{
  render: () => {
    const [show, setShow] = useState(true);
    const items = [{
      id: 1,
      title: '項目 1',
      description: '這是第一個項目'
    }, {
      id: 2,
      title: '項目 2',
      description: '這是第二個項目'
    }, {
      id: 3,
      title: '項目 3',
      description: '這是第三個項目'
    }, {
      id: 4,
      title: '項目 4',
      description: '這是第四個項目'
    }, {
      id: 5,
      title: '項目 5',
      description: '這是第五個項目'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">列表交錯動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">子元素依序出現的動畫效果</p>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setShow(!show)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          {show ? '隱藏' : '顯示'}列表
        </motion.button>
        
        <AnimatePresence>
          {show && <motion.div variants={{
          animate: {
            transition: getStaggerConfig('default', 0.08)
          }
        }} initial="initial" animate="animate" exit="exit" className="space-y-4">
              {items.map(item => <motion.div key={item.id} variants={getSpringVariants('slideUp', 'default')} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
                  <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                  <p className="text-gray-600 dark:text-gray-400">{item.description}</p>
                </motion.div>)}
            </motion.div>}
        </AnimatePresence>
        
        {/* CSS 交錯動畫 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 交錯動畫</h3>
          <div className="stagger-children space-y-4">
            {items.map(item => <div key={item.id} className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 className="font-semibold">{item.title}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">{item.description}</p>
              </div>)}
          </div>
        </div>
      </div>;
  }
}`,...(Gn=(zn=oe.parameters)==null?void 0:zn.docs)==null?void 0:Gn.source}}};var _n,Xn,Yn;le.parameters={...le.parameters,docs:{...(_n=le.parameters)==null?void 0:_n.docs,source:{originalSource:`{
  render: () => {
    const [showSuccess, setShowSuccess] = useState(false);
    const [showError, setShowError] = useState(false);
    const successRef = useRef<HTMLDivElement>(null);
    const errorRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
      if (showSuccess && successRef.current) {
        triggerHaptic(successRef.current, 'success');
      }
    }, [showSuccess]);
    useEffect(() => {
      if (showError && errorRef.current) {
        triggerHaptic(errorRef.current, 'error');
      }
    }, [showError]);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">成功/錯誤反饋</h2>
          <p className="text-gray-600 dark:text-gray-400">帶有觸覺反饋的狀態提示</p>
        </div>
        
        <div className="flex gap-4">
          <motion.button whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={() => {
          setShowSuccess(true);
          setTimeout(() => setShowSuccess(false), 3000);
        }} className="px-6 py-3 bg-green-600 text-white rounded-lg shadow-md">
            顯示成功
          </motion.button>
          
          <motion.button whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={() => {
          setShowError(true);
          setTimeout(() => setShowError(false), 3000);
        }} className="px-6 py-3 bg-red-600 text-white rounded-lg shadow-md">
            顯示錯誤
          </motion.button>
        </div>
        
        <div className="space-y-4">
          <AnimatePresence>
            {showSuccess && <motion.div ref={successRef} variants={getSpringVariants('bounce', 'bouncy')} initial="initial" animate="animate" exit="exit" className="bg-green-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3">
                <div className="text-2xl">✓</div>
                <div>
                  <h3 className="font-semibold">操作成功！</h3>
                  <p className="text-sm opacity-90">您的更改已保存</p>
                </div>
              </motion.div>}
          </AnimatePresence>
          
          <AnimatePresence>
            {showError && <motion.div ref={errorRef} variants={getSpringVariants('shake', 'wobbly')} initial="initial" animate="animate" exit="exit" className="bg-red-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3">
                <div className="text-2xl">✗</div>
                <div>
                  <h3 className="font-semibold">操作失敗！</h3>
                  <p className="text-sm opacity-90">請稍後再試</p>
                </div>
              </motion.div>}
          </AnimatePresence>
        </div>
      </div>;
  }
}`,...(Yn=(Xn=le.parameters)==null?void 0:Xn.docs)==null?void 0:Yn.source}}};var qn,Zn,Jn;ce.parameters={...ce.parameters,docs:{...(qn=ce.parameters)==null?void 0:qn.docs,source:{originalSource:`{
  render: () => {
    const [context, setContext] = useState(getUserContext());
    const [animationKey, setAnimationKey] = useState(0);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">上下文感知動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">根據用戶環境自動調整動畫</p>
        </div>
        
        {/* 當前上下文 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">當前上下文</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">設備類型：</span>
              <span className="font-semibold ml-2">{context.isMobile ? '移動設備' : '桌面設備'}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">低電量模式：</span>
              <span className="font-semibold ml-2">{context.isLowPower ? '是' : '否'}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">網絡速度：</span>
              <span className="font-semibold ml-2">{context.connectionSpeed}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">用戶偏好：</span>
              <span className="font-semibold ml-2">{context.userPreference}</span>
            </div>
          </div>
        </div>
        
        {/* 動畫展示 */}
        <div className="bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[200px] flex items-center justify-center">
          <motion.div key={animationKey} {...getContextualAnimation('slideUp', context)} initial="initial" animate="animate" className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl">
            <h3 className="text-2xl font-bold">上下文感知動畫</h3>
            <p className="text-blue-100 mt-2">根據您的環境自動調整</p>
          </motion.div>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setAnimationKey(k => k + 1)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          重新播放動畫
        </motion.button>
      </div>;
  }
}`,...(Jn=(Zn=ce.parameters)==null?void 0:Zn.docs)==null?void 0:Jn.source}}};var Qn,ea,ta;de.parameters={...de.parameters,docs:{...(Qn=de.parameters)==null?void 0:Qn.docs,source:{originalSource:`{
  render: () => {
    const [metrics, setMetrics] = useState(getAnimationMetrics());
    const [isAnimating, setIsAnimating] = useState(false);
    const startAnimation = () => {
      setIsAnimating(true);
      trackAnimation('demo-animation');
      setTimeout(() => {
        setIsAnimating(false);
        setMetrics(getAnimationMetrics());
      }, 1000);
    };
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">性能監控</h2>
          <p className="text-gray-600 dark:text-gray-400">追蹤動畫性能指標</p>
        </div>
        
        {/* 性能指標 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-blue-600">{metrics.totalAnimations}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">總動畫數</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-green-600">{metrics.activeAnimations}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">活躍動畫</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-yellow-600">{metrics.droppedFrames}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">掉幀數</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-purple-600">{metrics.averageFPS.toFixed(1)}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">平均 FPS</div>
          </div>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={startAnimation} disabled={isAnimating} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md disabled:opacity-50">
          {isAnimating ? '動畫中...' : '開始動畫'}
        </motion.button>
        
        {/* 性能建議 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">性能建議</h3>
          <div className="space-y-2 text-sm">
            {metrics.averageFPS < 55 && <div className="text-red-600 dark:text-red-400">
                ⚠️ 平均 FPS 低於 55，建議降級到更簡單的動畫
              </div>}
            {metrics.activeAnimations > 5 && <div className="text-yellow-600 dark:text-yellow-400">
                ⚠️ 同時活躍動畫過多，可能影響性能
              </div>}
            {metrics.droppedFrames > 10 && <div className="text-orange-600 dark:text-orange-400">
                ⚠️ 掉幀數較多，建議優化動畫
              </div>}
            {metrics.averageFPS >= 55 && metrics.activeAnimations <= 5 && metrics.droppedFrames <= 10 && <div className="text-green-600 dark:text-green-400">
                ✓ 性能良好，動畫流暢
              </div>}
          </div>
        </div>
      </div>;
  }
}`,...(ta=(ea=de.parameters)==null?void 0:ea.docs)==null?void 0:ta.source}}};var sa,ia,na;ue.parameters={...ue.parameters,docs:{...(sa=ue.parameters)==null?void 0:sa.docs,source:{originalSource:`{
  render: () => {
    const [isCardOpen, setIsCardOpen] = useState(false);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">完整演示</h2>
          <p className="text-gray-600 dark:text-gray-400">綜合展示彈性動畫系統的各種功能</p>
        </div>
        
        {/* 互動卡片 */}
        <motion.div layout onClick={() => setIsCardOpen(!isCardOpen)} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md cursor-pointer" whileHover={{
        scale: 1.02
      }} transition={getSpringConfig('default')}>
          <motion.h3 layout="position" className="text-xl font-bold mb-2">
            互動卡片
          </motion.h3>
          <motion.p layout="position" className="text-gray-600 dark:text-gray-400">
            點擊展開查看更多內容
          </motion.p>
          
          <AnimatePresence>
            {isCardOpen && <motion.div initial={{
            opacity: 0,
            height: 0
          }} animate={{
            opacity: 1,
            height: 'auto'
          }} exit={{
            opacity: 0,
            height: 0
          }} transition={getSpringConfig('default')} className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  這是展開的內容區域，使用了彈性動畫來創造流暢的展開效果。
                </p>
                <div className="flex gap-2">
                  <motion.button whileHover={{
                scale: 1.05
              }} whileTap={{
                scale: 0.95
              }} transition={getSpringConfig('snappy')} onClick={e => {
                e.stopPropagation();
                triggerHaptic(e.currentTarget, 'success');
              }} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm">
                    確認
                  </motion.button>
                  <motion.button whileHover={{
                scale: 1.05
              }} whileTap={{
                scale: 0.95
              }} transition={getSpringConfig('snappy')} onClick={e => {
                e.stopPropagation();
                setIsCardOpen(false);
              }} className="px-4 py-2 bg-gray-600 text-white rounded-lg text-sm">
                    取消
                  </motion.button>
                </div>
              </motion.div>}
          </AnimatePresence>
        </motion.div>
        
        {/* 功能按鈕組 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {['Primary', 'Success', 'Warning', 'Error'].map((type, i) => <motion.button key={type} whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={e => {
          const hapticType = ['medium', 'success', 'warning', 'error'][i];
          triggerHaptic(e.currentTarget, hapticType as any);
        }} className={\`px-6 py-3 text-white rounded-lg shadow-md \${['bg-blue-600', 'bg-green-600', 'bg-yellow-600', 'bg-red-600'][i]}\`}>
              {type}
            </motion.button>)}
        </div>
      </div>;
  }
}`,...(na=(ia=ue.parameters)==null?void 0:ia.docs)==null?void 0:na.source}}};const ju=["SpringPresets","AnimationVariants","HapticFeedback","ButtonInteractions","ModalAnimations","ListStaggerAnimation","FeedbackAnimations","ContextualAnimations","PerformanceMonitoring","CompleteDemo"];export{ie as AnimationVariants,ae as ButtonInteractions,ue as CompleteDemo,ce as ContextualAnimations,le as FeedbackAnimations,ne as HapticFeedback,oe as ListStaggerAnimation,re as ModalAnimations,de as PerformanceMonitoring,se as SpringPresets,ju as __namedExportsOrder,Mu as default};
