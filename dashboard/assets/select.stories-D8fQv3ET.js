import{j as i}from"./jsx-runtime-D_zvdyIk.js";import{R as Oe,r as m}from"./index-Dz3UJJSw.js";import{r as yt}from"./index-CYANIyVc.js";import{d as Yn,c as It,u as ce,a as Dt,b as z}from"./createLucideIcon-CPl_Fi5k.js";import{u as X,b as pt,c as De}from"./utils-ClSdSIbF.js";import{b as qn,u as bt,P as Yo,h as qo,a as Jo,R as Zo,F as Qo,D as er}from"./index-DmZd5CDD.js";import{P as U}from"./index-CWPL_hnH.js";import{a as tr,u as nr,C as or}from"./check-IE6dqsU4.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-fUCaa9pg.js";/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const rr=[["path",{d:"m6 9 6 6 6-6",key:"qrunsl"}]],Jn=Yn("chevron-down",rr);/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const sr=[["path",{d:"m18 15-6-6-6 6",key:"153udz"}]],lr=Yn("chevron-up",sr);function Lt(e,[t,n]){return Math.min(n,Math.max(t,e))}function ir(e){const t=e+"CollectionProvider",[n,o]=It(t),[r,l]=n(t,{collectionRef:{current:null},itemMap:new Map}),s=p=>{const{scope:S,children:y}=p,h=Oe.useRef(null),x=Oe.useRef(new Map).current;return i.jsx(r,{scope:S,itemMap:x,collectionRef:h,children:y})};s.displayName=t;const c=e+"CollectionSlot",a=pt(c),d=Oe.forwardRef((p,S)=>{const{scope:y,children:h}=p,x=l(c,y),I=X(S,x.collectionRef);return i.jsx(a,{ref:I,children:h})});d.displayName=c;const u=e+"CollectionItemSlot",f="data-radix-collection-item",w=pt(u),g=Oe.forwardRef((p,S)=>{const{scope:y,children:h,...x}=p,I=Oe.useRef(null),b=X(S,I),P=l(u,y);return Oe.useEffect(()=>(P.itemMap.set(I,{ref:I,...x}),()=>void P.itemMap.delete(I))),i.jsx(w,{[f]:"",ref:b,children:h})});g.displayName=u;function v(p){const S=l(e+"CollectionConsumer",p);return Oe.useCallback(()=>{const h=S.collectionRef.current;if(!h)return[];const x=Array.from(h.querySelectorAll(`[${f}]`));return Array.from(S.itemMap.values()).sort((P,R)=>x.indexOf(P.ref.current)-x.indexOf(R.ref.current))},[S.collectionRef,S.itemMap])}return[{Provider:s,Slot:d,ItemSlot:g},v,o]}var cr=m.createContext(void 0);function ar(e){const t=m.useContext(cr);return e||t||"ltr"}const dr=["top","right","bottom","left"],Ce=Math.min,q=Math.max,Ze=Math.round,qe=Math.floor,ie=e=>({x:e,y:e}),ur={left:"right",right:"left",bottom:"top",top:"bottom"},pr={start:"end",end:"start"};function ft(e,t,n){return q(e,Ce(t,n))}function pe(e,t){return typeof e=="function"?e(t):e}function fe(e){return e.split("-")[0]}function ke(e){return e.split("-")[1]}function Ct(e){return e==="x"?"y":"x"}function At(e){return e==="y"?"height":"width"}const fr=new Set(["top","bottom"]);function le(e){return fr.has(fe(e))?"y":"x"}function Tt(e){return Ct(le(e))}function mr(e,t,n){n===void 0&&(n=!1);const o=ke(e),r=Tt(e),l=At(r);let s=r==="x"?o===(n?"end":"start")?"right":"left":o==="start"?"bottom":"top";return t.reference[l]>t.floating[l]&&(s=Qe(s)),[s,Qe(s)]}function hr(e){const t=Qe(e);return[mt(e),t,mt(t)]}function mt(e){return e.replace(/start|end/g,t=>pr[t])}const kt=["left","right"],Vt=["right","left"],gr=["top","bottom"],Sr=["bottom","top"];function vr(e,t,n){switch(e){case"top":case"bottom":return n?t?Vt:kt:t?kt:Vt;case"left":case"right":return t?gr:Sr;default:return[]}}function xr(e,t,n,o){const r=ke(e);let l=vr(fe(e),n==="start",o);return r&&(l=l.map(s=>s+"-"+r),t&&(l=l.concat(l.map(mt)))),l}function Qe(e){return e.replace(/left|right|bottom|top/g,t=>ur[t])}function wr(e){return{top:0,right:0,bottom:0,left:0,...e}}function Zn(e){return typeof e!="number"?wr(e):{top:e,right:e,bottom:e,left:e}}function et(e){const{x:t,y:n,width:o,height:r}=e;return{width:o,height:r,top:n,left:t,right:t+o,bottom:n+r,x:t,y:n}}function Bt(e,t,n){let{reference:o,floating:r}=e;const l=le(t),s=Tt(t),c=At(s),a=fe(t),d=l==="y",u=o.x+o.width/2-r.width/2,f=o.y+o.height/2-r.height/2,w=o[c]/2-r[c]/2;let g;switch(a){case"top":g={x:u,y:o.y-r.height};break;case"bottom":g={x:u,y:o.y+o.height};break;case"right":g={x:o.x+o.width,y:f};break;case"left":g={x:o.x-r.width,y:f};break;default:g={x:o.x,y:o.y}}switch(ke(t)){case"start":g[s]-=w*(n&&d?-1:1);break;case"end":g[s]+=w*(n&&d?-1:1);break}return g}const yr=async(e,t,n)=>{const{placement:o="bottom",strategy:r="absolute",middleware:l=[],platform:s}=n,c=l.filter(Boolean),a=await(s.isRTL==null?void 0:s.isRTL(t));let d=await s.getElementRects({reference:e,floating:t,strategy:r}),{x:u,y:f}=Bt(d,o,a),w=o,g={},v=0;for(let p=0;p<c.length;p++){const{name:S,fn:y}=c[p],{x:h,y:x,data:I,reset:b}=await y({x:u,y:f,initialPlacement:o,placement:w,strategy:r,middlewareData:g,rects:d,platform:s,elements:{reference:e,floating:t}});u=h??u,f=x??f,g={...g,[S]:{...g[S],...I}},b&&v<=50&&(v++,typeof b=="object"&&(b.placement&&(w=b.placement),b.rects&&(d=b.rects===!0?await s.getElementRects({reference:e,floating:t,strategy:r}):b.rects),{x:u,y:f}=Bt(d,w,a)),p=-1)}return{x:u,y:f,placement:w,strategy:r,middlewareData:g}};async function Ke(e,t){var n;t===void 0&&(t={});const{x:o,y:r,platform:l,rects:s,elements:c,strategy:a}=e,{boundary:d="clippingAncestors",rootBoundary:u="viewport",elementContext:f="floating",altBoundary:w=!1,padding:g=0}=pe(t,e),v=Zn(g),S=c[w?f==="floating"?"reference":"floating":f],y=et(await l.getClippingRect({element:(n=await(l.isElement==null?void 0:l.isElement(S)))==null||n?S:S.contextElement||await(l.getDocumentElement==null?void 0:l.getDocumentElement(c.floating)),boundary:d,rootBoundary:u,strategy:a})),h=f==="floating"?{x:o,y:r,width:s.floating.width,height:s.floating.height}:s.reference,x=await(l.getOffsetParent==null?void 0:l.getOffsetParent(c.floating)),I=await(l.isElement==null?void 0:l.isElement(x))?await(l.getScale==null?void 0:l.getScale(x))||{x:1,y:1}:{x:1,y:1},b=et(l.convertOffsetParentRelativeRectToViewportRelativeRect?await l.convertOffsetParentRelativeRectToViewportRelativeRect({elements:c,rect:h,offsetParent:x,strategy:a}):h);return{top:(y.top-b.top+v.top)/I.y,bottom:(b.bottom-y.bottom+v.bottom)/I.y,left:(y.left-b.left+v.left)/I.x,right:(b.right-y.right+v.right)/I.x}}const Ir=e=>({name:"arrow",options:e,async fn(t){const{x:n,y:o,placement:r,rects:l,platform:s,elements:c,middlewareData:a}=t,{element:d,padding:u=0}=pe(e,t)||{};if(d==null)return{};const f=Zn(u),w={x:n,y:o},g=Tt(r),v=At(g),p=await s.getDimensions(d),S=g==="y",y=S?"top":"left",h=S?"bottom":"right",x=S?"clientHeight":"clientWidth",I=l.reference[v]+l.reference[g]-w[g]-l.floating[v],b=w[g]-l.reference[g],P=await(s.getOffsetParent==null?void 0:s.getOffsetParent(d));let R=P?P[x]:0;(!R||!await(s.isElement==null?void 0:s.isElement(P)))&&(R=c.floating[x]||l.floating[v]);const E=I/2-b/2,W=R/2-p[v]/2-1,L=Ce(f[y],W),V=Ce(f[h],W),B=L,_=R-p[v]-V,N=R/2-p[v]/2+E,$=ft(B,N,_),O=!a.arrow&&ke(r)!=null&&N!==$&&l.reference[v]/2-(N<B?L:V)-p[v]/2<0,j=O?N<B?N-B:N-_:0;return{[g]:w[g]+j,data:{[g]:$,centerOffset:N-$-j,...O&&{alignmentOffset:j}},reset:O}}}),br=function(e){return e===void 0&&(e={}),{name:"flip",options:e,async fn(t){var n,o;const{placement:r,middlewareData:l,rects:s,initialPlacement:c,platform:a,elements:d}=t,{mainAxis:u=!0,crossAxis:f=!0,fallbackPlacements:w,fallbackStrategy:g="bestFit",fallbackAxisSideDirection:v="none",flipAlignment:p=!0,...S}=pe(e,t);if((n=l.arrow)!=null&&n.alignmentOffset)return{};const y=fe(r),h=le(c),x=fe(c)===c,I=await(a.isRTL==null?void 0:a.isRTL(d.floating)),b=w||(x||!p?[Qe(c)]:hr(c)),P=v!=="none";!w&&P&&b.push(...xr(c,p,v,I));const R=[c,...b],E=await Ke(t,S),W=[];let L=((o=l.flip)==null?void 0:o.overflows)||[];if(u&&W.push(E[y]),f){const N=mr(r,s,I);W.push(E[N[0]],E[N[1]])}if(L=[...L,{placement:r,overflows:W}],!W.every(N=>N<=0)){var V,B;const N=(((V=l.flip)==null?void 0:V.index)||0)+1,$=R[N];if($&&(!(f==="alignment"?h!==le($):!1)||L.every(A=>le(A.placement)===h?A.overflows[0]>0:!0)))return{data:{index:N,overflows:L},reset:{placement:$}};let O=(B=L.filter(j=>j.overflows[0]<=0).sort((j,A)=>j.overflows[1]-A.overflows[1])[0])==null?void 0:B.placement;if(!O)switch(g){case"bestFit":{var _;const j=(_=L.filter(A=>{if(P){const F=le(A.placement);return F===h||F==="y"}return!0}).map(A=>[A.placement,A.overflows.filter(F=>F>0).reduce((F,G)=>F+G,0)]).sort((A,F)=>A[1]-F[1])[0])==null?void 0:_[0];j&&(O=j);break}case"initialPlacement":O=c;break}if(r!==O)return{reset:{placement:O}}}return{}}}};function Ft(e,t){return{top:e.top-t.height,right:e.right-t.width,bottom:e.bottom-t.height,left:e.left-t.width}}function Ht(e){return dr.some(t=>e[t]>=0)}const Cr=function(e){return e===void 0&&(e={}),{name:"hide",options:e,async fn(t){const{rects:n}=t,{strategy:o="referenceHidden",...r}=pe(e,t);switch(o){case"referenceHidden":{const l=await Ke(t,{...r,elementContext:"reference"}),s=Ft(l,n.reference);return{data:{referenceHiddenOffsets:s,referenceHidden:Ht(s)}}}case"escaped":{const l=await Ke(t,{...r,altBoundary:!0}),s=Ft(l,n.floating);return{data:{escapedOffsets:s,escaped:Ht(s)}}}default:return{}}}}},Qn=new Set(["left","top"]);async function Ar(e,t){const{placement:n,platform:o,elements:r}=e,l=await(o.isRTL==null?void 0:o.isRTL(r.floating)),s=fe(n),c=ke(n),a=le(n)==="y",d=Qn.has(s)?-1:1,u=l&&a?-1:1,f=pe(t,e);let{mainAxis:w,crossAxis:g,alignmentAxis:v}=typeof f=="number"?{mainAxis:f,crossAxis:0,alignmentAxis:null}:{mainAxis:f.mainAxis||0,crossAxis:f.crossAxis||0,alignmentAxis:f.alignmentAxis};return c&&typeof v=="number"&&(g=c==="end"?v*-1:v),a?{x:g*u,y:w*d}:{x:w*d,y:g*u}}const Tr=function(e){return e===void 0&&(e=0),{name:"offset",options:e,async fn(t){var n,o;const{x:r,y:l,placement:s,middlewareData:c}=t,a=await Ar(t,e);return s===((n=c.offset)==null?void 0:n.placement)&&(o=c.arrow)!=null&&o.alignmentOffset?{}:{x:r+a.x,y:l+a.y,data:{...a,placement:s}}}}},Rr=function(e){return e===void 0&&(e={}),{name:"shift",options:e,async fn(t){const{x:n,y:o,placement:r}=t,{mainAxis:l=!0,crossAxis:s=!1,limiter:c={fn:S=>{let{x:y,y:h}=S;return{x:y,y:h}}},...a}=pe(e,t),d={x:n,y:o},u=await Ke(t,a),f=le(fe(r)),w=Ct(f);let g=d[w],v=d[f];if(l){const S=w==="y"?"top":"left",y=w==="y"?"bottom":"right",h=g+u[S],x=g-u[y];g=ft(h,g,x)}if(s){const S=f==="y"?"top":"left",y=f==="y"?"bottom":"right",h=v+u[S],x=v-u[y];v=ft(h,v,x)}const p=c.fn({...t,[w]:g,[f]:v});return{...p,data:{x:p.x-n,y:p.y-o,enabled:{[w]:l,[f]:s}}}}}},Pr=function(e){return e===void 0&&(e={}),{options:e,fn(t){const{x:n,y:o,placement:r,rects:l,middlewareData:s}=t,{offset:c=0,mainAxis:a=!0,crossAxis:d=!0}=pe(e,t),u={x:n,y:o},f=le(r),w=Ct(f);let g=u[w],v=u[f];const p=pe(c,t),S=typeof p=="number"?{mainAxis:p,crossAxis:0}:{mainAxis:0,crossAxis:0,...p};if(a){const x=w==="y"?"height":"width",I=l.reference[w]-l.floating[x]+S.mainAxis,b=l.reference[w]+l.reference[x]-S.mainAxis;g<I?g=I:g>b&&(g=b)}if(d){var y,h;const x=w==="y"?"width":"height",I=Qn.has(fe(r)),b=l.reference[f]-l.floating[x]+(I&&((y=s.offset)==null?void 0:y[f])||0)+(I?0:S.crossAxis),P=l.reference[f]+l.reference[x]+(I?0:((h=s.offset)==null?void 0:h[f])||0)-(I?S.crossAxis:0);v<b?v=b:v>P&&(v=P)}return{[w]:g,[f]:v}}}},Or=function(e){return e===void 0&&(e={}),{name:"size",options:e,async fn(t){var n,o;const{placement:r,rects:l,platform:s,elements:c}=t,{apply:a=()=>{},...d}=pe(e,t),u=await Ke(t,d),f=fe(r),w=ke(r),g=le(r)==="y",{width:v,height:p}=l.floating;let S,y;f==="top"||f==="bottom"?(S=f,y=w===(await(s.isRTL==null?void 0:s.isRTL(c.floating))?"start":"end")?"left":"right"):(y=f,S=w==="end"?"top":"bottom");const h=p-u.top-u.bottom,x=v-u.left-u.right,I=Ce(p-u[S],h),b=Ce(v-u[y],x),P=!t.middlewareData.shift;let R=I,E=b;if((n=t.middlewareData.shift)!=null&&n.enabled.x&&(E=x),(o=t.middlewareData.shift)!=null&&o.enabled.y&&(R=h),P&&!w){const L=q(u.left,0),V=q(u.right,0),B=q(u.top,0),_=q(u.bottom,0);g?E=v-2*(L!==0||V!==0?L+V:q(u.left,u.right)):R=p-2*(B!==0||_!==0?B+_:q(u.top,u.bottom))}await a({...t,availableWidth:E,availableHeight:R});const W=await s.getDimensions(c.floating);return v!==W.width||p!==W.height?{reset:{rects:!0}}:{}}}};function ot(){return typeof window<"u"}function Ve(e){return eo(e)?(e.nodeName||"").toLowerCase():"#document"}function J(e){var t;return(e==null||(t=e.ownerDocument)==null?void 0:t.defaultView)||window}function de(e){var t;return(t=(eo(e)?e.ownerDocument:e.document)||window.document)==null?void 0:t.documentElement}function eo(e){return ot()?e instanceof Node||e instanceof J(e).Node:!1}function ee(e){return ot()?e instanceof Element||e instanceof J(e).Element:!1}function ae(e){return ot()?e instanceof HTMLElement||e instanceof J(e).HTMLElement:!1}function Wt(e){return!ot()||typeof ShadowRoot>"u"?!1:e instanceof ShadowRoot||e instanceof J(e).ShadowRoot}const Nr=new Set(["inline","contents"]);function Xe(e){const{overflow:t,overflowX:n,overflowY:o,display:r}=te(e);return/auto|scroll|overlay|hidden|clip/.test(t+o+n)&&!Nr.has(r)}const jr=new Set(["table","td","th"]);function Er(e){return jr.has(Ve(e))}const _r=[":popover-open",":modal"];function rt(e){return _r.some(t=>{try{return e.matches(t)}catch{return!1}})}const Mr=["transform","translate","scale","rotate","perspective"],Dr=["transform","translate","scale","rotate","perspective","filter"],Lr=["paint","layout","strict","content"];function Rt(e){const t=Pt(),n=ee(e)?te(e):e;return Mr.some(o=>n[o]?n[o]!=="none":!1)||(n.containerType?n.containerType!=="normal":!1)||!t&&(n.backdropFilter?n.backdropFilter!=="none":!1)||!t&&(n.filter?n.filter!=="none":!1)||Dr.some(o=>(n.willChange||"").includes(o))||Lr.some(o=>(n.contain||"").includes(o))}function kr(e){let t=Ae(e);for(;ae(t)&&!Le(t);){if(Rt(t))return t;if(rt(t))return null;t=Ae(t)}return null}function Pt(){return typeof CSS>"u"||!CSS.supports?!1:CSS.supports("-webkit-backdrop-filter","none")}const Vr=new Set(["html","body","#document"]);function Le(e){return Vr.has(Ve(e))}function te(e){return J(e).getComputedStyle(e)}function st(e){return ee(e)?{scrollLeft:e.scrollLeft,scrollTop:e.scrollTop}:{scrollLeft:e.scrollX,scrollTop:e.scrollY}}function Ae(e){if(Ve(e)==="html")return e;const t=e.assignedSlot||e.parentNode||Wt(e)&&e.host||de(e);return Wt(t)?t.host:t}function to(e){const t=Ae(e);return Le(t)?e.ownerDocument?e.ownerDocument.body:e.body:ae(t)&&Xe(t)?t:to(t)}function Ge(e,t,n){var o;t===void 0&&(t=[]),n===void 0&&(n=!0);const r=to(e),l=r===((o=e.ownerDocument)==null?void 0:o.body),s=J(r);if(l){const c=ht(s);return t.concat(s,s.visualViewport||[],Xe(r)?r:[],c&&n?Ge(c):[])}return t.concat(r,Ge(r,[],n))}function ht(e){return e.parent&&Object.getPrototypeOf(e.parent)?e.frameElement:null}function no(e){const t=te(e);let n=parseFloat(t.width)||0,o=parseFloat(t.height)||0;const r=ae(e),l=r?e.offsetWidth:n,s=r?e.offsetHeight:o,c=Ze(n)!==l||Ze(o)!==s;return c&&(n=l,o=s),{width:n,height:o,$:c}}function Ot(e){return ee(e)?e:e.contextElement}function Me(e){const t=Ot(e);if(!ae(t))return ie(1);const n=t.getBoundingClientRect(),{width:o,height:r,$:l}=no(t);let s=(l?Ze(n.width):n.width)/o,c=(l?Ze(n.height):n.height)/r;return(!s||!Number.isFinite(s))&&(s=1),(!c||!Number.isFinite(c))&&(c=1),{x:s,y:c}}const Br=ie(0);function oo(e){const t=J(e);return!Pt()||!t.visualViewport?Br:{x:t.visualViewport.offsetLeft,y:t.visualViewport.offsetTop}}function Fr(e,t,n){return t===void 0&&(t=!1),!n||t&&n!==J(e)?!1:t}function Ne(e,t,n,o){t===void 0&&(t=!1),n===void 0&&(n=!1);const r=e.getBoundingClientRect(),l=Ot(e);let s=ie(1);t&&(o?ee(o)&&(s=Me(o)):s=Me(e));const c=Fr(l,n,o)?oo(l):ie(0);let a=(r.left+c.x)/s.x,d=(r.top+c.y)/s.y,u=r.width/s.x,f=r.height/s.y;if(l){const w=J(l),g=o&&ee(o)?J(o):o;let v=w,p=ht(v);for(;p&&o&&g!==v;){const S=Me(p),y=p.getBoundingClientRect(),h=te(p),x=y.left+(p.clientLeft+parseFloat(h.paddingLeft))*S.x,I=y.top+(p.clientTop+parseFloat(h.paddingTop))*S.y;a*=S.x,d*=S.y,u*=S.x,f*=S.y,a+=x,d+=I,v=J(p),p=ht(v)}}return et({width:u,height:f,x:a,y:d})}function lt(e,t){const n=st(e).scrollLeft;return t?t.left+n:Ne(de(e)).left+n}function ro(e,t){const n=e.getBoundingClientRect(),o=n.left+t.scrollLeft-lt(e,n),r=n.top+t.scrollTop;return{x:o,y:r}}function Hr(e){let{elements:t,rect:n,offsetParent:o,strategy:r}=e;const l=r==="fixed",s=de(o),c=t?rt(t.floating):!1;if(o===s||c&&l)return n;let a={scrollLeft:0,scrollTop:0},d=ie(1);const u=ie(0),f=ae(o);if((f||!f&&!l)&&((Ve(o)!=="body"||Xe(s))&&(a=st(o)),ae(o))){const g=Ne(o);d=Me(o),u.x=g.x+o.clientLeft,u.y=g.y+o.clientTop}const w=s&&!f&&!l?ro(s,a):ie(0);return{width:n.width*d.x,height:n.height*d.y,x:n.x*d.x-a.scrollLeft*d.x+u.x+w.x,y:n.y*d.y-a.scrollTop*d.y+u.y+w.y}}function Wr(e){return Array.from(e.getClientRects())}function $r(e){const t=de(e),n=st(e),o=e.ownerDocument.body,r=q(t.scrollWidth,t.clientWidth,o.scrollWidth,o.clientWidth),l=q(t.scrollHeight,t.clientHeight,o.scrollHeight,o.clientHeight);let s=-n.scrollLeft+lt(e);const c=-n.scrollTop;return te(o).direction==="rtl"&&(s+=q(t.clientWidth,o.clientWidth)-r),{width:r,height:l,x:s,y:c}}const $t=25;function zr(e,t){const n=J(e),o=de(e),r=n.visualViewport;let l=o.clientWidth,s=o.clientHeight,c=0,a=0;if(r){l=r.width,s=r.height;const u=Pt();(!u||u&&t==="fixed")&&(c=r.offsetLeft,a=r.offsetTop)}const d=lt(o);if(d<=0){const u=o.ownerDocument,f=u.body,w=getComputedStyle(f),g=u.compatMode==="CSS1Compat"&&parseFloat(w.marginLeft)+parseFloat(w.marginRight)||0,v=Math.abs(o.clientWidth-f.clientWidth-g);v<=$t&&(l-=v)}else d<=$t&&(l+=d);return{width:l,height:s,x:c,y:a}}const Ur=new Set(["absolute","fixed"]);function Kr(e,t){const n=Ne(e,!0,t==="fixed"),o=n.top+e.clientTop,r=n.left+e.clientLeft,l=ae(e)?Me(e):ie(1),s=e.clientWidth*l.x,c=e.clientHeight*l.y,a=r*l.x,d=o*l.y;return{width:s,height:c,x:a,y:d}}function zt(e,t,n){let o;if(t==="viewport")o=zr(e,n);else if(t==="document")o=$r(de(e));else if(ee(t))o=Kr(t,n);else{const r=oo(e);o={x:t.x-r.x,y:t.y-r.y,width:t.width,height:t.height}}return et(o)}function so(e,t){const n=Ae(e);return n===t||!ee(n)||Le(n)?!1:te(n).position==="fixed"||so(n,t)}function Gr(e,t){const n=t.get(e);if(n)return n;let o=Ge(e,[],!1).filter(c=>ee(c)&&Ve(c)!=="body"),r=null;const l=te(e).position==="fixed";let s=l?Ae(e):e;for(;ee(s)&&!Le(s);){const c=te(s),a=Rt(s);!a&&c.position==="fixed"&&(r=null),(l?!a&&!r:!a&&c.position==="static"&&!!r&&Ur.has(r.position)||Xe(s)&&!a&&so(e,s))?o=o.filter(u=>u!==s):r=c,s=Ae(s)}return t.set(e,o),o}function Xr(e){let{element:t,boundary:n,rootBoundary:o,strategy:r}=e;const s=[...n==="clippingAncestors"?rt(t)?[]:Gr(t,this._c):[].concat(n),o],c=s[0],a=s.reduce((d,u)=>{const f=zt(t,u,r);return d.top=q(f.top,d.top),d.right=Ce(f.right,d.right),d.bottom=Ce(f.bottom,d.bottom),d.left=q(f.left,d.left),d},zt(t,c,r));return{width:a.right-a.left,height:a.bottom-a.top,x:a.left,y:a.top}}function Yr(e){const{width:t,height:n}=no(e);return{width:t,height:n}}function qr(e,t,n){const o=ae(t),r=de(t),l=n==="fixed",s=Ne(e,!0,l,t);let c={scrollLeft:0,scrollTop:0};const a=ie(0);function d(){a.x=lt(r)}if(o||!o&&!l)if((Ve(t)!=="body"||Xe(r))&&(c=st(t)),o){const g=Ne(t,!0,l,t);a.x=g.x+t.clientLeft,a.y=g.y+t.clientTop}else r&&d();l&&!o&&r&&d();const u=r&&!o&&!l?ro(r,c):ie(0),f=s.left+c.scrollLeft-a.x-u.x,w=s.top+c.scrollTop-a.y-u.y;return{x:f,y:w,width:s.width,height:s.height}}function dt(e){return te(e).position==="static"}function Ut(e,t){if(!ae(e)||te(e).position==="fixed")return null;if(t)return t(e);let n=e.offsetParent;return de(e)===n&&(n=n.ownerDocument.body),n}function lo(e,t){const n=J(e);if(rt(e))return n;if(!ae(e)){let r=Ae(e);for(;r&&!Le(r);){if(ee(r)&&!dt(r))return r;r=Ae(r)}return n}let o=Ut(e,t);for(;o&&Er(o)&&dt(o);)o=Ut(o,t);return o&&Le(o)&&dt(o)&&!Rt(o)?n:o||kr(e)||n}const Jr=async function(e){const t=this.getOffsetParent||lo,n=this.getDimensions,o=await n(e.floating);return{reference:qr(e.reference,await t(e.floating),e.strategy),floating:{x:0,y:0,width:o.width,height:o.height}}};function Zr(e){return te(e).direction==="rtl"}const Qr={convertOffsetParentRelativeRectToViewportRelativeRect:Hr,getDocumentElement:de,getClippingRect:Xr,getOffsetParent:lo,getElementRects:Jr,getClientRects:Wr,getDimensions:Yr,getScale:Me,isElement:ee,isRTL:Zr};function io(e,t){return e.x===t.x&&e.y===t.y&&e.width===t.width&&e.height===t.height}function es(e,t){let n=null,o;const r=de(e);function l(){var c;clearTimeout(o),(c=n)==null||c.disconnect(),n=null}function s(c,a){c===void 0&&(c=!1),a===void 0&&(a=1),l();const d=e.getBoundingClientRect(),{left:u,top:f,width:w,height:g}=d;if(c||t(),!w||!g)return;const v=qe(f),p=qe(r.clientWidth-(u+w)),S=qe(r.clientHeight-(f+g)),y=qe(u),x={rootMargin:-v+"px "+-p+"px "+-S+"px "+-y+"px",threshold:q(0,Ce(1,a))||1};let I=!0;function b(P){const R=P[0].intersectionRatio;if(R!==a){if(!I)return s();R?s(!1,R):o=setTimeout(()=>{s(!1,1e-7)},1e3)}R===1&&!io(d,e.getBoundingClientRect())&&s(),I=!1}try{n=new IntersectionObserver(b,{...x,root:r.ownerDocument})}catch{n=new IntersectionObserver(b,x)}n.observe(e)}return s(!0),l}function ts(e,t,n,o){o===void 0&&(o={});const{ancestorScroll:r=!0,ancestorResize:l=!0,elementResize:s=typeof ResizeObserver=="function",layoutShift:c=typeof IntersectionObserver=="function",animationFrame:a=!1}=o,d=Ot(e),u=r||l?[...d?Ge(d):[],...Ge(t)]:[];u.forEach(y=>{r&&y.addEventListener("scroll",n,{passive:!0}),l&&y.addEventListener("resize",n)});const f=d&&c?es(d,n):null;let w=-1,g=null;s&&(g=new ResizeObserver(y=>{let[h]=y;h&&h.target===d&&g&&(g.unobserve(t),cancelAnimationFrame(w),w=requestAnimationFrame(()=>{var x;(x=g)==null||x.observe(t)})),n()}),d&&!a&&g.observe(d),g.observe(t));let v,p=a?Ne(e):null;a&&S();function S(){const y=Ne(e);p&&!io(p,y)&&n(),p=y,v=requestAnimationFrame(S)}return n(),()=>{var y;u.forEach(h=>{r&&h.removeEventListener("scroll",n),l&&h.removeEventListener("resize",n)}),f==null||f(),(y=g)==null||y.disconnect(),g=null,a&&cancelAnimationFrame(v)}}const ns=Tr,os=Rr,rs=br,ss=Or,ls=Cr,Kt=Ir,is=Pr,cs=(e,t,n)=>{const o=new Map,r={platform:Qr,...n},l={...r.platform,_c:o};return yr(e,t,{...r,platform:l})};var as=typeof document<"u",ds=function(){},Je=as?m.useLayoutEffect:ds;function tt(e,t){if(e===t)return!0;if(typeof e!=typeof t)return!1;if(typeof e=="function"&&e.toString()===t.toString())return!0;let n,o,r;if(e&&t&&typeof e=="object"){if(Array.isArray(e)){if(n=e.length,n!==t.length)return!1;for(o=n;o--!==0;)if(!tt(e[o],t[o]))return!1;return!0}if(r=Object.keys(e),n=r.length,n!==Object.keys(t).length)return!1;for(o=n;o--!==0;)if(!{}.hasOwnProperty.call(t,r[o]))return!1;for(o=n;o--!==0;){const l=r[o];if(!(l==="_owner"&&e.$$typeof)&&!tt(e[l],t[l]))return!1}return!0}return e!==e&&t!==t}function co(e){return typeof window>"u"?1:(e.ownerDocument.defaultView||window).devicePixelRatio||1}function Gt(e,t){const n=co(e);return Math.round(t*n)/n}function ut(e){const t=m.useRef(e);return Je(()=>{t.current=e}),t}function us(e){e===void 0&&(e={});const{placement:t="bottom",strategy:n="absolute",middleware:o=[],platform:r,elements:{reference:l,floating:s}={},transform:c=!0,whileElementsMounted:a,open:d}=e,[u,f]=m.useState({x:0,y:0,strategy:n,placement:t,middlewareData:{},isPositioned:!1}),[w,g]=m.useState(o);tt(w,o)||g(o);const[v,p]=m.useState(null),[S,y]=m.useState(null),h=m.useCallback(A=>{A!==P.current&&(P.current=A,p(A))},[]),x=m.useCallback(A=>{A!==R.current&&(R.current=A,y(A))},[]),I=l||v,b=s||S,P=m.useRef(null),R=m.useRef(null),E=m.useRef(u),W=a!=null,L=ut(a),V=ut(r),B=ut(d),_=m.useCallback(()=>{if(!P.current||!R.current)return;const A={placement:t,strategy:n,middleware:w};V.current&&(A.platform=V.current),cs(P.current,R.current,A).then(F=>{const G={...F,isPositioned:B.current!==!1};N.current&&!tt(E.current,G)&&(E.current=G,yt.flushSync(()=>{f(G)}))})},[w,t,n,V,B]);Je(()=>{d===!1&&E.current.isPositioned&&(E.current.isPositioned=!1,f(A=>({...A,isPositioned:!1})))},[d]);const N=m.useRef(!1);Je(()=>(N.current=!0,()=>{N.current=!1}),[]),Je(()=>{if(I&&(P.current=I),b&&(R.current=b),I&&b){if(L.current)return L.current(I,b,_);_()}},[I,b,_,L,W]);const $=m.useMemo(()=>({reference:P,floating:R,setReference:h,setFloating:x}),[h,x]),O=m.useMemo(()=>({reference:I,floating:b}),[I,b]),j=m.useMemo(()=>{const A={position:n,left:0,top:0};if(!O.floating)return A;const F=Gt(O.floating,u.x),G=Gt(O.floating,u.y);return c?{...A,transform:"translate("+F+"px, "+G+"px)",...co(O.floating)>=1.5&&{willChange:"transform"}}:{position:n,left:F,top:G}},[n,c,O.floating,u.x,u.y]);return m.useMemo(()=>({...u,update:_,refs:$,elements:O,floatingStyles:j}),[u,_,$,O,j])}const ps=e=>{function t(n){return{}.hasOwnProperty.call(n,"current")}return{name:"arrow",options:e,fn(n){const{element:o,padding:r}=typeof e=="function"?e(n):e;return o&&t(o)?o.current!=null?Kt({element:o.current,padding:r}).fn(n):{}:o?Kt({element:o,padding:r}).fn(n):{}}}},fs=(e,t)=>({...ns(e),options:[e,t]}),ms=(e,t)=>({...os(e),options:[e,t]}),hs=(e,t)=>({...is(e),options:[e,t]}),gs=(e,t)=>({...rs(e),options:[e,t]}),Ss=(e,t)=>({...ss(e),options:[e,t]}),vs=(e,t)=>({...ls(e),options:[e,t]}),xs=(e,t)=>({...ps(e),options:[e,t]});var ws="Arrow",ao=m.forwardRef((e,t)=>{const{children:n,width:o=10,height:r=5,...l}=e;return i.jsx(U.svg,{...l,ref:t,width:o,height:r,viewBox:"0 0 30 10",preserveAspectRatio:"none",children:e.asChild?n:i.jsx("polygon",{points:"0,0 30,0 15,10"})})});ao.displayName=ws;var ys=ao,Nt="Popper",[uo,po]=It(Nt),[Is,fo]=uo(Nt),mo=e=>{const{__scopePopper:t,children:n}=e,[o,r]=m.useState(null);return i.jsx(Is,{scope:t,anchor:o,onAnchorChange:r,children:n})};mo.displayName=Nt;var ho="PopperAnchor",go=m.forwardRef((e,t)=>{const{__scopePopper:n,virtualRef:o,...r}=e,l=fo(ho,n),s=m.useRef(null),c=X(t,s),a=m.useRef(null);return m.useEffect(()=>{const d=a.current;a.current=(o==null?void 0:o.current)||s.current,d!==a.current&&l.onAnchorChange(a.current)}),o?null:i.jsx(U.div,{...r,ref:c})});go.displayName=ho;var jt="PopperContent",[bs,Cs]=uo(jt),So=m.forwardRef((e,t)=>{var T,H,K,k,M,D;const{__scopePopper:n,side:o="bottom",sideOffset:r=0,align:l="center",alignOffset:s=0,arrowPadding:c=0,avoidCollisions:a=!0,collisionBoundary:d=[],collisionPadding:u=0,sticky:f="partial",hideWhenDetached:w=!1,updatePositionStrategy:g="optimized",onPlaced:v,...p}=e,S=fo(jt,n),[y,h]=m.useState(null),x=X(t,Y=>h(Y)),[I,b]=m.useState(null),P=tr(I),R=(P==null?void 0:P.width)??0,E=(P==null?void 0:P.height)??0,W=o+(l!=="center"?"-"+l:""),L=typeof u=="number"?u:{top:0,right:0,bottom:0,left:0,...u},V=Array.isArray(d)?d:[d],B=V.length>0,_={padding:L,boundary:V.filter(Ts),altBoundary:B},{refs:N,floatingStyles:$,placement:O,isPositioned:j,middlewareData:A}=us({strategy:"fixed",placement:W,whileElementsMounted:(...Y)=>ts(...Y,{animationFrame:g==="always"}),elements:{reference:S.anchor},middleware:[fs({mainAxis:r+E,alignmentAxis:s}),a&&ms({mainAxis:!0,crossAxis:!1,limiter:f==="partial"?hs():void 0,..._}),a&&gs({..._}),Ss({..._,apply:({elements:Y,rects:se,availableWidth:We,availableHeight:$e})=>{const{width:ze,height:Xo}=se.reference,Ye=Y.floating.style;Ye.setProperty("--radix-popper-available-width",`${We}px`),Ye.setProperty("--radix-popper-available-height",`${$e}px`),Ye.setProperty("--radix-popper-anchor-width",`${ze}px`),Ye.setProperty("--radix-popper-anchor-height",`${Xo}px`)}}),I&&xs({element:I,padding:c}),Rs({arrowWidth:R,arrowHeight:E}),w&&vs({strategy:"referenceHidden",..._})]}),[F,G]=wo(O),ue=qn(v);ce(()=>{j&&(ue==null||ue())},[j,ue]);const Fe=(T=A.arrow)==null?void 0:T.x,He=(H=A.arrow)==null?void 0:H.y,me=((K=A.arrow)==null?void 0:K.centerOffset)!==0,[_e,Pe]=m.useState();return ce(()=>{y&&Pe(window.getComputedStyle(y).zIndex)},[y]),i.jsx("div",{ref:N.setFloating,"data-radix-popper-content-wrapper":"",style:{...$,transform:j?$.transform:"translate(0, -200%)",minWidth:"max-content",zIndex:_e,"--radix-popper-transform-origin":[(k=A.transformOrigin)==null?void 0:k.x,(M=A.transformOrigin)==null?void 0:M.y].join(" "),...((D=A.hide)==null?void 0:D.referenceHidden)&&{visibility:"hidden",pointerEvents:"none"}},dir:e.dir,children:i.jsx(bs,{scope:n,placedSide:F,onArrowChange:b,arrowX:Fe,arrowY:He,shouldHideArrow:me,children:i.jsx(U.div,{"data-side":F,"data-align":G,...p,ref:x,style:{...p.style,animation:j?void 0:"none"}})})})});So.displayName=jt;var vo="PopperArrow",As={top:"bottom",right:"left",bottom:"top",left:"right"},xo=m.forwardRef(function(t,n){const{__scopePopper:o,...r}=t,l=Cs(vo,o),s=As[l.placedSide];return i.jsx("span",{ref:l.onArrowChange,style:{position:"absolute",left:l.arrowX,top:l.arrowY,[s]:0,transformOrigin:{top:"",right:"0 0",bottom:"center 0",left:"100% 0"}[l.placedSide],transform:{top:"translateY(100%)",right:"translateY(50%) rotate(90deg) translateX(-50%)",bottom:"rotate(180deg)",left:"translateY(50%) rotate(-90deg) translateX(50%)"}[l.placedSide],visibility:l.shouldHideArrow?"hidden":void 0},children:i.jsx(ys,{...r,ref:n,style:{...r.style,display:"block"}})})});xo.displayName=vo;function Ts(e){return e!==null}var Rs=e=>({name:"transformOrigin",options:e,fn(t){var S,y,h;const{placement:n,rects:o,middlewareData:r}=t,s=((S=r.arrow)==null?void 0:S.centerOffset)!==0,c=s?0:e.arrowWidth,a=s?0:e.arrowHeight,[d,u]=wo(n),f={start:"0%",center:"50%",end:"100%"}[u],w=(((y=r.arrow)==null?void 0:y.x)??0)+c/2,g=(((h=r.arrow)==null?void 0:h.y)??0)+a/2;let v="",p="";return d==="bottom"?(v=s?f:`${w}px`,p=`${-a}px`):d==="top"?(v=s?f:`${w}px`,p=`${o.floating.height+a}px`):d==="right"?(v=`${-a}px`,p=s?f:`${g}px`):d==="left"&&(v=`${o.floating.width+a}px`,p=s?f:`${g}px`),{data:{x:v,y:p}}}});function wo(e){const[t,n="center"]=e.split("-");return[t,n]}var Ps=mo,Os=go,Ns=So,js=xo,yo=Object.freeze({position:"absolute",border:0,width:1,height:1,padding:0,margin:-1,overflow:"hidden",clip:"rect(0, 0, 0, 0)",whiteSpace:"nowrap",wordWrap:"normal"}),Es="VisuallyHidden",_s=m.forwardRef((e,t)=>i.jsx(U.span,{...e,ref:t,style:{...yo,...e.style}}));_s.displayName=Es;var Ms=[" ","Enter","ArrowUp","ArrowDown"],Ds=[" ","Enter"],je="Select",[it,ct,Ls]=ir(je),[Be]=It(je,[Ls,po]),at=po(),[ks,Te]=Be(je),[Vs,Bs]=Be(je),Io=e=>{const{__scopeSelect:t,children:n,open:o,defaultOpen:r,onOpenChange:l,value:s,defaultValue:c,onValueChange:a,dir:d,name:u,autoComplete:f,disabled:w,required:g,form:v}=e,p=at(t),[S,y]=m.useState(null),[h,x]=m.useState(null),[I,b]=m.useState(!1),P=ar(d),[R,E]=Dt({prop:o,defaultProp:r??!1,onChange:l,caller:je}),[W,L]=Dt({prop:s,defaultProp:c,onChange:a,caller:je}),V=m.useRef(null),B=S?v||!!S.closest("form"):!0,[_,N]=m.useState(new Set),$=Array.from(_).map(O=>O.props.value).join(";");return i.jsx(Ps,{...p,children:i.jsxs(ks,{required:g,scope:t,trigger:S,onTriggerChange:y,valueNode:h,onValueNodeChange:x,valueNodeHasChildren:I,onValueNodeHasChildrenChange:b,contentId:bt(),value:W,onValueChange:L,open:R,onOpenChange:E,dir:P,triggerPointerDownPosRef:V,disabled:w,children:[i.jsx(it.Provider,{scope:t,children:i.jsx(Vs,{scope:e.__scopeSelect,onNativeOptionAdd:m.useCallback(O=>{N(j=>new Set(j).add(O))},[]),onNativeOptionRemove:m.useCallback(O=>{N(j=>{const A=new Set(j);return A.delete(O),A})},[]),children:n})}),B?i.jsxs(zo,{"aria-hidden":!0,required:g,tabIndex:-1,name:u,autoComplete:f,value:W,onChange:O=>L(O.target.value),disabled:w,form:v,children:[W===void 0?i.jsx("option",{value:""}):null,Array.from(_)]},$):null]})})};Io.displayName=je;var bo="SelectTrigger",Co=m.forwardRef((e,t)=>{const{__scopeSelect:n,disabled:o=!1,...r}=e,l=at(n),s=Te(bo,n),c=s.disabled||o,a=X(t,s.onTriggerChange),d=ct(n),u=m.useRef("touch"),[f,w,g]=Ko(p=>{const S=d().filter(x=>!x.disabled),y=S.find(x=>x.value===s.value),h=Go(S,p,y);h!==void 0&&s.onValueChange(h.value)}),v=p=>{c||(s.onOpenChange(!0),g()),p&&(s.triggerPointerDownPosRef.current={x:Math.round(p.pageX),y:Math.round(p.pageY)})};return i.jsx(Os,{asChild:!0,...l,children:i.jsx(U.button,{type:"button",role:"combobox","aria-controls":s.contentId,"aria-expanded":s.open,"aria-required":s.required,"aria-autocomplete":"none",dir:s.dir,"data-state":s.open?"open":"closed",disabled:c,"data-disabled":c?"":void 0,"data-placeholder":Uo(s.value)?"":void 0,...r,ref:a,onClick:z(r.onClick,p=>{p.currentTarget.focus(),u.current!=="mouse"&&v(p)}),onPointerDown:z(r.onPointerDown,p=>{u.current=p.pointerType;const S=p.target;S.hasPointerCapture(p.pointerId)&&S.releasePointerCapture(p.pointerId),p.button===0&&p.ctrlKey===!1&&p.pointerType==="mouse"&&(v(p),p.preventDefault())}),onKeyDown:z(r.onKeyDown,p=>{const S=f.current!=="";!(p.ctrlKey||p.altKey||p.metaKey)&&p.key.length===1&&w(p.key),!(S&&p.key===" ")&&Ms.includes(p.key)&&(v(),p.preventDefault())})})})});Co.displayName=bo;var Ao="SelectValue",To=m.forwardRef((e,t)=>{const{__scopeSelect:n,className:o,style:r,children:l,placeholder:s="",...c}=e,a=Te(Ao,n),{onValueNodeHasChildrenChange:d}=a,u=l!==void 0,f=X(t,a.onValueNodeChange);return ce(()=>{d(u)},[d,u]),i.jsx(U.span,{...c,ref:f,style:{pointerEvents:"none"},children:Uo(a.value)?i.jsx(i.Fragment,{children:s}):l})});To.displayName=Ao;var Fs="SelectIcon",Ro=m.forwardRef((e,t)=>{const{__scopeSelect:n,children:o,...r}=e;return i.jsx(U.span,{"aria-hidden":!0,...r,ref:t,children:o||"▼"})});Ro.displayName=Fs;var Hs="SelectPortal",Po=e=>i.jsx(Yo,{asChild:!0,...e});Po.displayName=Hs;var Ee="SelectContent",Oo=m.forwardRef((e,t)=>{const n=Te(Ee,e.__scopeSelect),[o,r]=m.useState();if(ce(()=>{r(new DocumentFragment)},[]),!n.open){const l=o;return l?yt.createPortal(i.jsx(No,{scope:e.__scopeSelect,children:i.jsx(it.Slot,{scope:e.__scopeSelect,children:i.jsx("div",{children:e.children})})}),l):null}return i.jsx(jo,{...e,ref:t})});Oo.displayName=Ee;var Q=10,[No,Re]=Be(Ee),Ws="SelectContentImpl",$s=pt("SelectContent.RemoveScroll"),jo=m.forwardRef((e,t)=>{const{__scopeSelect:n,position:o="item-aligned",onCloseAutoFocus:r,onEscapeKeyDown:l,onPointerDownOutside:s,side:c,sideOffset:a,align:d,alignOffset:u,arrowPadding:f,collisionBoundary:w,collisionPadding:g,sticky:v,hideWhenDetached:p,avoidCollisions:S,...y}=e,h=Te(Ee,n),[x,I]=m.useState(null),[b,P]=m.useState(null),R=X(t,T=>I(T)),[E,W]=m.useState(null),[L,V]=m.useState(null),B=ct(n),[_,N]=m.useState(!1),$=m.useRef(!1);m.useEffect(()=>{if(x)return qo(x)},[x]),Jo();const O=m.useCallback(T=>{const[H,...K]=B().map(D=>D.ref.current),[k]=K.slice(-1),M=document.activeElement;for(const D of T)if(D===M||(D==null||D.scrollIntoView({block:"nearest"}),D===H&&b&&(b.scrollTop=0),D===k&&b&&(b.scrollTop=b.scrollHeight),D==null||D.focus(),document.activeElement!==M))return},[B,b]),j=m.useCallback(()=>O([E,x]),[O,E,x]);m.useEffect(()=>{_&&j()},[_,j]);const{onOpenChange:A,triggerPointerDownPosRef:F}=h;m.useEffect(()=>{if(x){let T={x:0,y:0};const H=k=>{var M,D;T={x:Math.abs(Math.round(k.pageX)-(((M=F.current)==null?void 0:M.x)??0)),y:Math.abs(Math.round(k.pageY)-(((D=F.current)==null?void 0:D.y)??0))}},K=k=>{T.x<=10&&T.y<=10?k.preventDefault():x.contains(k.target)||A(!1),document.removeEventListener("pointermove",H),F.current=null};return F.current!==null&&(document.addEventListener("pointermove",H),document.addEventListener("pointerup",K,{capture:!0,once:!0})),()=>{document.removeEventListener("pointermove",H),document.removeEventListener("pointerup",K,{capture:!0})}}},[x,A,F]),m.useEffect(()=>{const T=()=>A(!1);return window.addEventListener("blur",T),window.addEventListener("resize",T),()=>{window.removeEventListener("blur",T),window.removeEventListener("resize",T)}},[A]);const[G,ue]=Ko(T=>{const H=B().filter(M=>!M.disabled),K=H.find(M=>M.ref.current===document.activeElement),k=Go(H,T,K);k&&setTimeout(()=>k.ref.current.focus())}),Fe=m.useCallback((T,H,K)=>{const k=!$.current&&!K;(h.value!==void 0&&h.value===H||k)&&(W(T),k&&($.current=!0))},[h.value]),He=m.useCallback(()=>x==null?void 0:x.focus(),[x]),me=m.useCallback((T,H,K)=>{const k=!$.current&&!K;(h.value!==void 0&&h.value===H||k)&&V(T)},[h.value]),_e=o==="popper"?gt:Eo,Pe=_e===gt?{side:c,sideOffset:a,align:d,alignOffset:u,arrowPadding:f,collisionBoundary:w,collisionPadding:g,sticky:v,hideWhenDetached:p,avoidCollisions:S}:{};return i.jsx(No,{scope:n,content:x,viewport:b,onViewportChange:P,itemRefCallback:Fe,selectedItem:E,onItemLeave:He,itemTextRefCallback:me,focusSelectedItem:j,selectedItemText:L,position:o,isPositioned:_,searchRef:G,children:i.jsx(Zo,{as:$s,allowPinchZoom:!0,children:i.jsx(Qo,{asChild:!0,trapped:h.open,onMountAutoFocus:T=>{T.preventDefault()},onUnmountAutoFocus:z(r,T=>{var H;(H=h.trigger)==null||H.focus({preventScroll:!0}),T.preventDefault()}),children:i.jsx(er,{asChild:!0,disableOutsidePointerEvents:!0,onEscapeKeyDown:l,onPointerDownOutside:s,onFocusOutside:T=>T.preventDefault(),onDismiss:()=>h.onOpenChange(!1),children:i.jsx(_e,{role:"listbox",id:h.contentId,"data-state":h.open?"open":"closed",dir:h.dir,onContextMenu:T=>T.preventDefault(),...y,...Pe,onPlaced:()=>N(!0),ref:R,style:{display:"flex",flexDirection:"column",outline:"none",...y.style},onKeyDown:z(y.onKeyDown,T=>{const H=T.ctrlKey||T.altKey||T.metaKey;if(T.key==="Tab"&&T.preventDefault(),!H&&T.key.length===1&&ue(T.key),["ArrowUp","ArrowDown","Home","End"].includes(T.key)){let k=B().filter(M=>!M.disabled).map(M=>M.ref.current);if(["ArrowUp","End"].includes(T.key)&&(k=k.slice().reverse()),["ArrowUp","ArrowDown"].includes(T.key)){const M=T.target,D=k.indexOf(M);k=k.slice(D+1)}setTimeout(()=>O(k)),T.preventDefault()}})})})})})})});jo.displayName=Ws;var zs="SelectItemAlignedPosition",Eo=m.forwardRef((e,t)=>{const{__scopeSelect:n,onPlaced:o,...r}=e,l=Te(Ee,n),s=Re(Ee,n),[c,a]=m.useState(null),[d,u]=m.useState(null),f=X(t,R=>u(R)),w=ct(n),g=m.useRef(!1),v=m.useRef(!0),{viewport:p,selectedItem:S,selectedItemText:y,focusSelectedItem:h}=s,x=m.useCallback(()=>{if(l.trigger&&l.valueNode&&c&&d&&p&&S&&y){const R=l.trigger.getBoundingClientRect(),E=d.getBoundingClientRect(),W=l.valueNode.getBoundingClientRect(),L=y.getBoundingClientRect();if(l.dir!=="rtl"){const M=L.left-E.left,D=W.left-M,Y=R.left-D,se=R.width+Y,We=Math.max(se,E.width),$e=window.innerWidth-Q,ze=Lt(D,[Q,Math.max(Q,$e-We)]);c.style.minWidth=se+"px",c.style.left=ze+"px"}else{const M=E.right-L.right,D=window.innerWidth-W.right-M,Y=window.innerWidth-R.right-D,se=R.width+Y,We=Math.max(se,E.width),$e=window.innerWidth-Q,ze=Lt(D,[Q,Math.max(Q,$e-We)]);c.style.minWidth=se+"px",c.style.right=ze+"px"}const V=w(),B=window.innerHeight-Q*2,_=p.scrollHeight,N=window.getComputedStyle(d),$=parseInt(N.borderTopWidth,10),O=parseInt(N.paddingTop,10),j=parseInt(N.borderBottomWidth,10),A=parseInt(N.paddingBottom,10),F=$+O+_+A+j,G=Math.min(S.offsetHeight*5,F),ue=window.getComputedStyle(p),Fe=parseInt(ue.paddingTop,10),He=parseInt(ue.paddingBottom,10),me=R.top+R.height/2-Q,_e=B-me,Pe=S.offsetHeight/2,T=S.offsetTop+Pe,H=$+O+T,K=F-H;if(H<=me){const M=V.length>0&&S===V[V.length-1].ref.current;c.style.bottom="0px";const D=d.clientHeight-p.offsetTop-p.offsetHeight,Y=Math.max(_e,Pe+(M?He:0)+D+j),se=H+Y;c.style.height=se+"px"}else{const M=V.length>0&&S===V[0].ref.current;c.style.top="0px";const Y=Math.max(me,$+p.offsetTop+(M?Fe:0)+Pe)+K;c.style.height=Y+"px",p.scrollTop=H-me+p.offsetTop}c.style.margin=`${Q}px 0`,c.style.minHeight=G+"px",c.style.maxHeight=B+"px",o==null||o(),requestAnimationFrame(()=>g.current=!0)}},[w,l.trigger,l.valueNode,c,d,p,S,y,l.dir,o]);ce(()=>x(),[x]);const[I,b]=m.useState();ce(()=>{d&&b(window.getComputedStyle(d).zIndex)},[d]);const P=m.useCallback(R=>{R&&v.current===!0&&(x(),h==null||h(),v.current=!1)},[x,h]);return i.jsx(Ks,{scope:n,contentWrapper:c,shouldExpandOnScrollRef:g,onScrollButtonChange:P,children:i.jsx("div",{ref:a,style:{display:"flex",flexDirection:"column",position:"fixed",zIndex:I},children:i.jsx(U.div,{...r,ref:f,style:{boxSizing:"border-box",maxHeight:"100%",...r.style}})})})});Eo.displayName=zs;var Us="SelectPopperPosition",gt=m.forwardRef((e,t)=>{const{__scopeSelect:n,align:o="start",collisionPadding:r=Q,...l}=e,s=at(n);return i.jsx(Ns,{...s,...l,ref:t,align:o,collisionPadding:r,style:{boxSizing:"border-box",...l.style,"--radix-select-content-transform-origin":"var(--radix-popper-transform-origin)","--radix-select-content-available-width":"var(--radix-popper-available-width)","--radix-select-content-available-height":"var(--radix-popper-available-height)","--radix-select-trigger-width":"var(--radix-popper-anchor-width)","--radix-select-trigger-height":"var(--radix-popper-anchor-height)"}})});gt.displayName=Us;var[Ks,Et]=Be(Ee,{}),St="SelectViewport",_o=m.forwardRef((e,t)=>{const{__scopeSelect:n,nonce:o,...r}=e,l=Re(St,n),s=Et(St,n),c=X(t,l.onViewportChange),a=m.useRef(0);return i.jsxs(i.Fragment,{children:[i.jsx("style",{dangerouslySetInnerHTML:{__html:"[data-radix-select-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-select-viewport]::-webkit-scrollbar{display:none}"},nonce:o}),i.jsx(it.Slot,{scope:n,children:i.jsx(U.div,{"data-radix-select-viewport":"",role:"presentation",...r,ref:c,style:{position:"relative",flex:1,overflow:"hidden auto",...r.style},onScroll:z(r.onScroll,d=>{const u=d.currentTarget,{contentWrapper:f,shouldExpandOnScrollRef:w}=s;if(w!=null&&w.current&&f){const g=Math.abs(a.current-u.scrollTop);if(g>0){const v=window.innerHeight-Q*2,p=parseFloat(f.style.minHeight),S=parseFloat(f.style.height),y=Math.max(p,S);if(y<v){const h=y+g,x=Math.min(v,h),I=h-x;f.style.height=x+"px",f.style.bottom==="0px"&&(u.scrollTop=I>0?I:0,f.style.justifyContent="flex-end")}}}a.current=u.scrollTop})})})]})});_o.displayName=St;var Mo="SelectGroup",[Gs,Xs]=Be(Mo),Ys=m.forwardRef((e,t)=>{const{__scopeSelect:n,...o}=e,r=bt();return i.jsx(Gs,{scope:n,id:r,children:i.jsx(U.div,{role:"group","aria-labelledby":r,...o,ref:t})})});Ys.displayName=Mo;var Do="SelectLabel",qs=m.forwardRef((e,t)=>{const{__scopeSelect:n,...o}=e,r=Xs(Do,n);return i.jsx(U.div,{id:r.id,...o,ref:t})});qs.displayName=Do;var nt="SelectItem",[Js,Lo]=Be(nt),ko=m.forwardRef((e,t)=>{const{__scopeSelect:n,value:o,disabled:r=!1,textValue:l,...s}=e,c=Te(nt,n),a=Re(nt,n),d=c.value===o,[u,f]=m.useState(l??""),[w,g]=m.useState(!1),v=X(t,h=>{var x;return(x=a.itemRefCallback)==null?void 0:x.call(a,h,o,r)}),p=bt(),S=m.useRef("touch"),y=()=>{r||(c.onValueChange(o),c.onOpenChange(!1))};if(o==="")throw new Error("A <Select.Item /> must have a value prop that is not an empty string. This is because the Select value can be set to an empty string to clear the selection and show the placeholder.");return i.jsx(Js,{scope:n,value:o,disabled:r,textId:p,isSelected:d,onItemTextChange:m.useCallback(h=>{f(x=>x||((h==null?void 0:h.textContent)??"").trim())},[]),children:i.jsx(it.ItemSlot,{scope:n,value:o,disabled:r,textValue:u,children:i.jsx(U.div,{role:"option","aria-labelledby":p,"data-highlighted":w?"":void 0,"aria-selected":d&&w,"data-state":d?"checked":"unchecked","aria-disabled":r||void 0,"data-disabled":r?"":void 0,tabIndex:r?void 0:-1,...s,ref:v,onFocus:z(s.onFocus,()=>g(!0)),onBlur:z(s.onBlur,()=>g(!1)),onClick:z(s.onClick,()=>{S.current!=="mouse"&&y()}),onPointerUp:z(s.onPointerUp,()=>{S.current==="mouse"&&y()}),onPointerDown:z(s.onPointerDown,h=>{S.current=h.pointerType}),onPointerMove:z(s.onPointerMove,h=>{var x;S.current=h.pointerType,r?(x=a.onItemLeave)==null||x.call(a):S.current==="mouse"&&h.currentTarget.focus({preventScroll:!0})}),onPointerLeave:z(s.onPointerLeave,h=>{var x;h.currentTarget===document.activeElement&&((x=a.onItemLeave)==null||x.call(a))}),onKeyDown:z(s.onKeyDown,h=>{var I;((I=a.searchRef)==null?void 0:I.current)!==""&&h.key===" "||(Ds.includes(h.key)&&y(),h.key===" "&&h.preventDefault())})})})})});ko.displayName=nt;var Ue="SelectItemText",Vo=m.forwardRef((e,t)=>{const{__scopeSelect:n,className:o,style:r,...l}=e,s=Te(Ue,n),c=Re(Ue,n),a=Lo(Ue,n),d=Bs(Ue,n),[u,f]=m.useState(null),w=X(t,y=>f(y),a.onItemTextChange,y=>{var h;return(h=c.itemTextRefCallback)==null?void 0:h.call(c,y,a.value,a.disabled)}),g=u==null?void 0:u.textContent,v=m.useMemo(()=>i.jsx("option",{value:a.value,disabled:a.disabled,children:g},a.value),[a.disabled,a.value,g]),{onNativeOptionAdd:p,onNativeOptionRemove:S}=d;return ce(()=>(p(v),()=>S(v)),[p,S,v]),i.jsxs(i.Fragment,{children:[i.jsx(U.span,{id:a.textId,...l,ref:w}),a.isSelected&&s.valueNode&&!s.valueNodeHasChildren?yt.createPortal(l.children,s.valueNode):null]})});Vo.displayName=Ue;var Bo="SelectItemIndicator",Fo=m.forwardRef((e,t)=>{const{__scopeSelect:n,...o}=e;return Lo(Bo,n).isSelected?i.jsx(U.span,{"aria-hidden":!0,...o,ref:t}):null});Fo.displayName=Bo;var vt="SelectScrollUpButton",Ho=m.forwardRef((e,t)=>{const n=Re(vt,e.__scopeSelect),o=Et(vt,e.__scopeSelect),[r,l]=m.useState(!1),s=X(t,o.onScrollButtonChange);return ce(()=>{if(n.viewport&&n.isPositioned){let c=function(){const d=a.scrollTop>0;l(d)};const a=n.viewport;return c(),a.addEventListener("scroll",c),()=>a.removeEventListener("scroll",c)}},[n.viewport,n.isPositioned]),r?i.jsx($o,{...e,ref:s,onAutoScroll:()=>{const{viewport:c,selectedItem:a}=n;c&&a&&(c.scrollTop=c.scrollTop-a.offsetHeight)}}):null});Ho.displayName=vt;var xt="SelectScrollDownButton",Wo=m.forwardRef((e,t)=>{const n=Re(xt,e.__scopeSelect),o=Et(xt,e.__scopeSelect),[r,l]=m.useState(!1),s=X(t,o.onScrollButtonChange);return ce(()=>{if(n.viewport&&n.isPositioned){let c=function(){const d=a.scrollHeight-a.clientHeight,u=Math.ceil(a.scrollTop)<d;l(u)};const a=n.viewport;return c(),a.addEventListener("scroll",c),()=>a.removeEventListener("scroll",c)}},[n.viewport,n.isPositioned]),r?i.jsx($o,{...e,ref:s,onAutoScroll:()=>{const{viewport:c,selectedItem:a}=n;c&&a&&(c.scrollTop=c.scrollTop+a.offsetHeight)}}):null});Wo.displayName=xt;var $o=m.forwardRef((e,t)=>{const{__scopeSelect:n,onAutoScroll:o,...r}=e,l=Re("SelectScrollButton",n),s=m.useRef(null),c=ct(n),a=m.useCallback(()=>{s.current!==null&&(window.clearInterval(s.current),s.current=null)},[]);return m.useEffect(()=>()=>a(),[a]),ce(()=>{var u;const d=c().find(f=>f.ref.current===document.activeElement);(u=d==null?void 0:d.ref.current)==null||u.scrollIntoView({block:"nearest"})},[c]),i.jsx(U.div,{"aria-hidden":!0,...r,ref:t,style:{flexShrink:0,...r.style},onPointerDown:z(r.onPointerDown,()=>{s.current===null&&(s.current=window.setInterval(o,50))}),onPointerMove:z(r.onPointerMove,()=>{var d;(d=l.onItemLeave)==null||d.call(l),s.current===null&&(s.current=window.setInterval(o,50))}),onPointerLeave:z(r.onPointerLeave,()=>{a()})})}),Zs="SelectSeparator",Qs=m.forwardRef((e,t)=>{const{__scopeSelect:n,...o}=e;return i.jsx(U.div,{"aria-hidden":!0,...o,ref:t})});Qs.displayName=Zs;var wt="SelectArrow",el=m.forwardRef((e,t)=>{const{__scopeSelect:n,...o}=e,r=at(n),l=Te(wt,n),s=Re(wt,n);return l.open&&s.position==="popper"?i.jsx(js,{...r,...o,ref:t}):null});el.displayName=wt;var tl="SelectBubbleInput",zo=m.forwardRef(({__scopeSelect:e,value:t,...n},o)=>{const r=m.useRef(null),l=X(o,r),s=nr(t);return m.useEffect(()=>{const c=r.current;if(!c)return;const a=window.HTMLSelectElement.prototype,u=Object.getOwnPropertyDescriptor(a,"value").set;if(s!==t&&u){const f=new Event("change",{bubbles:!0});u.call(c,t),c.dispatchEvent(f)}},[s,t]),i.jsx(U.select,{...n,style:{...yo,...n.style},ref:l,defaultValue:t})});zo.displayName=tl;function Uo(e){return e===""||e===void 0}function Ko(e){const t=qn(e),n=m.useRef(""),o=m.useRef(0),r=m.useCallback(s=>{const c=n.current+s;t(c),(function a(d){n.current=d,window.clearTimeout(o.current),d!==""&&(o.current=window.setTimeout(()=>a(""),1e3))})(c)},[t]),l=m.useCallback(()=>{n.current="",window.clearTimeout(o.current)},[]);return m.useEffect(()=>()=>window.clearTimeout(o.current),[]),[n,r,l]}function Go(e,t,n){const r=t.length>1&&Array.from(t).every(d=>d===t[0])?t[0]:t,l=n?e.indexOf(n):-1;let s=nl(e,Math.max(l,0));r.length===1&&(s=s.filter(d=>d!==n));const a=s.find(d=>d.textValue.toLowerCase().startsWith(r.toLowerCase()));return a!==n?a:void 0}function nl(e,t){return e.map((n,o)=>e[(t+o)%e.length])}var ol=Io,rl=Co,sl=To,ll=Ro,il=Po,cl=Oo,al=_o,dl=ko,ul=Vo,pl=Fo,fl=Ho,ml=Wo;function Z({...e}){return i.jsx(ol,{"data-slot":"select",...e})}function ne({...e}){return i.jsx(sl,{"data-slot":"select-value",...e})}function oe({className:e,size:t="default",children:n,...o}){return i.jsxs(rl,{"data-slot":"select-trigger","data-size":t,className:De("border-input data-[placeholder]:text-muted-foreground [&_svg:not([class*='text-'])]:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 dark:hover:bg-input/50 flex w-fit items-center justify-between gap-2 rounded-md border bg-transparent px-3 py-2 text-sm whitespace-nowrap shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 data-[size=default]:h-9 data-[size=sm]:h-8 *:data-[slot=select-value]:line-clamp-1 *:data-[slot=select-value]:flex *:data-[slot=select-value]:items-center *:data-[slot=select-value]:gap-2 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",e),...o,children:[n,i.jsx(ll,{asChild:!0,children:i.jsx(Jn,{className:"size-4 opacity-50"})})]})}function re({className:e,children:t,position:n="popper",...o}){return i.jsx(il,{children:i.jsxs(cl,{"data-slot":"select-content",className:De("bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 relative z-50 max-h-(--radix-select-content-available-height) min-w-[8rem] origin-(--radix-select-content-transform-origin) overflow-x-hidden overflow-y-auto rounded-md border shadow-md",n==="popper"&&"data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1",e),position:n,...o,children:[i.jsx(_t,{}),i.jsx(al,{className:De("p-1",n==="popper"&&"h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)] scroll-my-1"),children:t}),i.jsx(Mt,{})]})})}function C({className:e,children:t,...n}){return i.jsxs(dl,{"data-slot":"select-item",className:De("focus:bg-accent focus:text-accent-foreground [&_svg:not([class*='text-'])]:text-muted-foreground relative flex w-full cursor-default items-center gap-2 rounded-sm py-1.5 pr-8 pl-2 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4 *:[span]:last:flex *:[span]:last:items-center *:[span]:last:gap-2",e),...n,children:[i.jsx("span",{className:"absolute right-2 flex size-3.5 items-center justify-center",children:i.jsx(pl,{children:i.jsx(or,{className:"size-4"})})}),i.jsx(ul,{children:t})]})}function _t({className:e,...t}){return i.jsx(fl,{"data-slot":"select-scroll-up-button",className:De("flex cursor-default items-center justify-center py-1",e),...t,children:i.jsx(lr,{className:"size-4"})})}function Mt({className:e,...t}){return i.jsx(ml,{"data-slot":"select-scroll-down-button",className:De("flex cursor-default items-center justify-center py-1",e),...t,children:i.jsx(Jn,{className:"size-4"})})}Z.__docgenInfo={description:"",methods:[],displayName:"Select"};re.__docgenInfo={description:"",methods:[],displayName:"SelectContent",props:{position:{defaultValue:{value:'"popper"',computed:!1},required:!1}}};C.__docgenInfo={description:"",methods:[],displayName:"SelectItem"};Mt.__docgenInfo={description:"",methods:[],displayName:"SelectScrollDownButton"};_t.__docgenInfo={description:"",methods:[],displayName:"SelectScrollUpButton"};oe.__docgenInfo={description:"",methods:[],displayName:"SelectTrigger",props:{size:{defaultValue:{value:'"default"',computed:!1},required:!1}}};ne.__docgenInfo={description:"",methods:[],displayName:"SelectValue"};Z.__docgenInfo={description:"",methods:[],displayName:"Select"};re.__docgenInfo={description:"",methods:[],displayName:"SelectContent",props:{position:{defaultValue:{value:'"popper"',computed:!1},required:!1}}};C.__docgenInfo={description:"",methods:[],displayName:"SelectItem"};Mt.__docgenInfo={description:"",methods:[],displayName:"SelectScrollDownButton"};_t.__docgenInfo={description:"",methods:[],displayName:"SelectScrollUpButton"};oe.__docgenInfo={description:"",methods:[],displayName:"SelectTrigger",props:{size:{defaultValue:{value:'"default"',computed:!1},required:!1}}};ne.__docgenInfo={description:"",methods:[],displayName:"SelectValue"};const Al={title:"UI/Select",component:Z,parameters:{layout:"centered",docs:{description:{component:`
The Select component is a dropdown menu that allows users to choose from a list of options. It's built on top of Radix UI's Select primitive for maximum accessibility.

### Usage Guidelines
- Use for lists of 5+ options where space is limited
- Provide clear, descriptive option labels
- Use placeholder text to indicate the expected selection
- Group related options when dealing with many choices
- Consider using radio buttons for 2-4 options instead

### Accessibility
- Full keyboard navigation (Arrow keys, Enter, Escape)
- Screen reader support with proper ARIA attributes
- Focus management and visual indicators
- Supports disabled state for individual options
        `}}},tags:["autodocs"],argTypes:{disabled:{control:"boolean",description:"Whether the select is disabled",table:{type:{summary:"boolean"},defaultValue:{summary:"false"}}},defaultValue:{control:"text",description:"Default selected value",table:{type:{summary:"string"}}},onValueChange:{action:"valueChanged",description:"Function called when selection changes",table:{type:{summary:"(value: string) => void"}}}}},he={render:()=>i.jsxs(Z,{children:[i.jsx(oe,{className:"w-[180px]",children:i.jsx(ne,{placeholder:"Select a fruit"})}),i.jsxs(re,{children:[i.jsx(C,{value:"apple",children:"Apple"}),i.jsx(C,{value:"banana",children:"Banana"}),i.jsx(C,{value:"orange",children:"Orange"}),i.jsx(C,{value:"grape",children:"Grape"}),i.jsx(C,{value:"pineapple",children:"Pineapple"})]})]})},ge={render:()=>i.jsxs(Z,{defaultValue:"banana",children:[i.jsx(oe,{className:"w-[180px]",children:i.jsx(ne,{placeholder:"Select a fruit"})}),i.jsxs(re,{children:[i.jsx(C,{value:"apple",children:"Apple"}),i.jsx(C,{value:"banana",children:"Banana"}),i.jsx(C,{value:"orange",children:"Orange"}),i.jsx(C,{value:"grape",children:"Grape"}),i.jsx(C,{value:"pineapple",children:"Pineapple"})]})]}),parameters:{docs:{description:{story:"Select with a pre-selected default value."}}}},Se={render:()=>i.jsxs(Z,{disabled:!0,children:[i.jsx(oe,{className:"w-[180px]",children:i.jsx(ne,{placeholder:"Select a fruit"})}),i.jsxs(re,{children:[i.jsx(C,{value:"apple",children:"Apple"}),i.jsx(C,{value:"banana",children:"Banana"}),i.jsx(C,{value:"orange",children:"Orange"})]})]}),parameters:{docs:{description:{story:"Select in disabled state - user cannot interact with it."}}}},ve={render:()=>i.jsxs(Z,{children:[i.jsx(oe,{className:"w-[250px]",children:i.jsx(ne,{placeholder:"Select a programming language"})}),i.jsxs(re,{children:[i.jsx(C,{value:"javascript",children:"JavaScript - The versatile web language"}),i.jsx(C,{value:"typescript",children:"TypeScript - JavaScript with static typing"}),i.jsx(C,{value:"python",children:"Python - Simple and powerful programming"}),i.jsx(C,{value:"rust",children:"Rust - Systems programming with memory safety"}),i.jsx(C,{value:"go",children:"Go - Fast and simple backend development"})]})]}),parameters:{docs:{description:{story:"Select with long option text to test text wrapping and layout."}}}},xe={render:()=>i.jsxs(Z,{children:[i.jsx(oe,{className:"w-[200px]",children:i.jsx(ne,{placeholder:"Select a country"})}),i.jsxs(re,{children:[i.jsx(C,{value:"us",children:"United States"}),i.jsx(C,{value:"ca",children:"Canada"}),i.jsx(C,{value:"mx",children:"Mexico"}),i.jsx(C,{value:"uk",children:"United Kingdom"}),i.jsx(C,{value:"fr",children:"France"}),i.jsx(C,{value:"de",children:"Germany"}),i.jsx(C,{value:"it",children:"Italy"}),i.jsx(C,{value:"es",children:"Spain"}),i.jsx(C,{value:"jp",children:"Japan"}),i.jsx(C,{value:"kr",children:"South Korea"}),i.jsx(C,{value:"cn",children:"China"}),i.jsx(C,{value:"in",children:"India"}),i.jsx(C,{value:"au",children:"Australia"}),i.jsx(C,{value:"br",children:"Brazil"}),i.jsx(C,{value:"ar",children:"Argentina"})]})]}),parameters:{docs:{description:{story:"Select with many options to test scrolling behavior."}}}},we={render:()=>i.jsxs(Z,{children:[i.jsx(oe,{className:"w-[100px]",children:i.jsx(ne,{placeholder:"Size"})}),i.jsxs(re,{children:[i.jsx(C,{value:"xs",children:"XS"}),i.jsx(C,{value:"s",children:"S"}),i.jsx(C,{value:"m",children:"M"}),i.jsx(C,{value:"l",children:"L"}),i.jsx(C,{value:"xl",children:"XL"})]})]}),parameters:{docs:{description:{story:"Select with minimal width to test compact layouts."}}}},ye={render:()=>i.jsxs(Z,{children:[i.jsx(oe,{className:"w-[180px]",children:i.jsx(ne,{placeholder:"Select an option"})}),i.jsxs(re,{children:[i.jsx(C,{value:"",children:"None"}),i.jsx(C,{value:"option1",children:"Option 1"}),i.jsx(C,{value:"option2",children:"Option 2"}),i.jsx(C,{value:"option3",children:"Option 3"})]})]}),parameters:{docs:{description:{story:"Select with an empty/none option for clearing selection."}}}},Ie={render:()=>i.jsxs(Z,{children:[i.jsx(oe,{className:"w-[200px]",children:i.jsx(ne,{placeholder:"Select a status"})}),i.jsxs(re,{children:[i.jsx(C,{value:"active",children:"✅ Active"}),i.jsx(C,{value:"pending",children:"⏳ Pending"}),i.jsx(C,{value:"inactive",children:"❌ Inactive"}),i.jsx(C,{value:"archived",children:"📦 Archived"})]})]}),parameters:{docs:{description:{story:"Select options with icons for better visual identification."}}}},be={render:()=>i.jsxs(Z,{onValueChange:e=>console.log("Selected:",e),children:[i.jsx(oe,{className:"w-[180px]",children:i.jsx(ne,{placeholder:"Make a selection"})}),i.jsxs(re,{children:[i.jsx(C,{value:"option1",children:"Option 1"}),i.jsx(C,{value:"option2",children:"Option 2"}),i.jsx(C,{value:"option3",children:"Option 3"})]})]}),parameters:{docs:{description:{story:"Interactive select that logs selection changes to console."}}}};var Xt,Yt,qt;he.parameters={...he.parameters,docs:{...(Xt=he.parameters)==null?void 0:Xt.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a fruit" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="apple">Apple</SelectItem>
        <SelectItem value="banana">Banana</SelectItem>
        <SelectItem value="orange">Orange</SelectItem>
        <SelectItem value="grape">Grape</SelectItem>
        <SelectItem value="pineapple">Pineapple</SelectItem>
      </SelectContent>
    </Select>
}`,...(qt=(Yt=he.parameters)==null?void 0:Yt.docs)==null?void 0:qt.source}}};var Jt,Zt,Qt;ge.parameters={...ge.parameters,docs:{...(Jt=ge.parameters)==null?void 0:Jt.docs,source:{originalSource:`{
  render: () => <Select defaultValue="banana">
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a fruit" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="apple">Apple</SelectItem>
        <SelectItem value="banana">Banana</SelectItem>
        <SelectItem value="orange">Orange</SelectItem>
        <SelectItem value="grape">Grape</SelectItem>
        <SelectItem value="pineapple">Pineapple</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select with a pre-selected default value.'
      }
    }
  }
}`,...(Qt=(Zt=ge.parameters)==null?void 0:Zt.docs)==null?void 0:Qt.source}}};var en,tn,nn;Se.parameters={...Se.parameters,docs:{...(en=Se.parameters)==null?void 0:en.docs,source:{originalSource:`{
  render: () => <Select disabled>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a fruit" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="apple">Apple</SelectItem>
        <SelectItem value="banana">Banana</SelectItem>
        <SelectItem value="orange">Orange</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select in disabled state - user cannot interact with it.'
      }
    }
  }
}`,...(nn=(tn=Se.parameters)==null?void 0:tn.docs)==null?void 0:nn.source}}};var on,rn,sn;ve.parameters={...ve.parameters,docs:{...(on=ve.parameters)==null?void 0:on.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[250px]">
        <SelectValue placeholder="Select a programming language" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="javascript">JavaScript - The versatile web language</SelectItem>
        <SelectItem value="typescript">TypeScript - JavaScript with static typing</SelectItem>
        <SelectItem value="python">Python - Simple and powerful programming</SelectItem>
        <SelectItem value="rust">Rust - Systems programming with memory safety</SelectItem>
        <SelectItem value="go">Go - Fast and simple backend development</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select with long option text to test text wrapping and layout.'
      }
    }
  }
}`,...(sn=(rn=ve.parameters)==null?void 0:rn.docs)==null?void 0:sn.source}}};var ln,cn,an;xe.parameters={...xe.parameters,docs:{...(ln=xe.parameters)==null?void 0:ln.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select a country" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="us">United States</SelectItem>
        <SelectItem value="ca">Canada</SelectItem>
        <SelectItem value="mx">Mexico</SelectItem>
        <SelectItem value="uk">United Kingdom</SelectItem>
        <SelectItem value="fr">France</SelectItem>
        <SelectItem value="de">Germany</SelectItem>
        <SelectItem value="it">Italy</SelectItem>
        <SelectItem value="es">Spain</SelectItem>
        <SelectItem value="jp">Japan</SelectItem>
        <SelectItem value="kr">South Korea</SelectItem>
        <SelectItem value="cn">China</SelectItem>
        <SelectItem value="in">India</SelectItem>
        <SelectItem value="au">Australia</SelectItem>
        <SelectItem value="br">Brazil</SelectItem>
        <SelectItem value="ar">Argentina</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select with many options to test scrolling behavior.'
      }
    }
  }
}`,...(an=(cn=xe.parameters)==null?void 0:cn.docs)==null?void 0:an.source}}};var dn,un,pn;we.parameters={...we.parameters,docs:{...(dn=we.parameters)==null?void 0:dn.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[100px]">
        <SelectValue placeholder="Size" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="xs">XS</SelectItem>
        <SelectItem value="s">S</SelectItem>
        <SelectItem value="m">M</SelectItem>
        <SelectItem value="l">L</SelectItem>
        <SelectItem value="xl">XL</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select with minimal width to test compact layouts.'
      }
    }
  }
}`,...(pn=(un=we.parameters)==null?void 0:un.docs)==null?void 0:pn.source}}};var fn,mn,hn;ye.parameters={...ye.parameters,docs:{...(fn=ye.parameters)==null?void 0:fn.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select an option" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="">None</SelectItem>
        <SelectItem value="option1">Option 1</SelectItem>
        <SelectItem value="option2">Option 2</SelectItem>
        <SelectItem value="option3">Option 3</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select with an empty/none option for clearing selection.'
      }
    }
  }
}`,...(hn=(mn=ye.parameters)==null?void 0:mn.docs)==null?void 0:hn.source}}};var gn,Sn,vn;Ie.parameters={...Ie.parameters,docs:{...(gn=Ie.parameters)==null?void 0:gn.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select a status" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="active">✅ Active</SelectItem>
        <SelectItem value="pending">⏳ Pending</SelectItem>
        <SelectItem value="inactive">❌ Inactive</SelectItem>
        <SelectItem value="archived">📦 Archived</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select options with icons for better visual identification.'
      }
    }
  }
}`,...(vn=(Sn=Ie.parameters)==null?void 0:Sn.docs)==null?void 0:vn.source}}};var xn,wn,yn;be.parameters={...be.parameters,docs:{...(xn=be.parameters)==null?void 0:xn.docs,source:{originalSource:`{
  render: () => <Select onValueChange={value => console.log('Selected:', value)}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Make a selection" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="option1">Option 1</SelectItem>
        <SelectItem value="option2">Option 2</SelectItem>
        <SelectItem value="option3">Option 3</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Interactive select that logs selection changes to console.'
      }
    }
  }
}`,...(yn=(wn=be.parameters)==null?void 0:wn.docs)==null?void 0:yn.source}}};var In,bn,Cn;he.parameters={...he.parameters,docs:{...(In=he.parameters)==null?void 0:In.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a fruit" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="apple">Apple</SelectItem>
        <SelectItem value="banana">Banana</SelectItem>
        <SelectItem value="orange">Orange</SelectItem>
        <SelectItem value="grape">Grape</SelectItem>
        <SelectItem value="pineapple">Pineapple</SelectItem>
      </SelectContent>
    </Select>
}`,...(Cn=(bn=he.parameters)==null?void 0:bn.docs)==null?void 0:Cn.source}}};var An,Tn,Rn;ge.parameters={...ge.parameters,docs:{...(An=ge.parameters)==null?void 0:An.docs,source:{originalSource:`{
  render: () => <Select defaultValue="banana">
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a fruit" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="apple">Apple</SelectItem>
        <SelectItem value="banana">Banana</SelectItem>
        <SelectItem value="orange">Orange</SelectItem>
        <SelectItem value="grape">Grape</SelectItem>
        <SelectItem value="pineapple">Pineapple</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select with a pre-selected default value.'
      }
    }
  }
}`,...(Rn=(Tn=ge.parameters)==null?void 0:Tn.docs)==null?void 0:Rn.source}}};var Pn,On,Nn;Se.parameters={...Se.parameters,docs:{...(Pn=Se.parameters)==null?void 0:Pn.docs,source:{originalSource:`{
  render: () => <Select disabled>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a fruit" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="apple">Apple</SelectItem>
        <SelectItem value="banana">Banana</SelectItem>
        <SelectItem value="orange">Orange</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select in disabled state - user cannot interact with it.'
      }
    }
  }
}`,...(Nn=(On=Se.parameters)==null?void 0:On.docs)==null?void 0:Nn.source}}};var jn,En,_n;ve.parameters={...ve.parameters,docs:{...(jn=ve.parameters)==null?void 0:jn.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[250px]">
        <SelectValue placeholder="Select a programming language" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="javascript">JavaScript - The versatile web language</SelectItem>
        <SelectItem value="typescript">TypeScript - JavaScript with static typing</SelectItem>
        <SelectItem value="python">Python - Simple and powerful programming</SelectItem>
        <SelectItem value="rust">Rust - Systems programming with memory safety</SelectItem>
        <SelectItem value="go">Go - Fast and simple backend development</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select with long option text to test text wrapping and layout.'
      }
    }
  }
}`,...(_n=(En=ve.parameters)==null?void 0:En.docs)==null?void 0:_n.source}}};var Mn,Dn,Ln;xe.parameters={...xe.parameters,docs:{...(Mn=xe.parameters)==null?void 0:Mn.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select a country" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="us">United States</SelectItem>
        <SelectItem value="ca">Canada</SelectItem>
        <SelectItem value="mx">Mexico</SelectItem>
        <SelectItem value="uk">United Kingdom</SelectItem>
        <SelectItem value="fr">France</SelectItem>
        <SelectItem value="de">Germany</SelectItem>
        <SelectItem value="it">Italy</SelectItem>
        <SelectItem value="es">Spain</SelectItem>
        <SelectItem value="jp">Japan</SelectItem>
        <SelectItem value="kr">South Korea</SelectItem>
        <SelectItem value="cn">China</SelectItem>
        <SelectItem value="in">India</SelectItem>
        <SelectItem value="au">Australia</SelectItem>
        <SelectItem value="br">Brazil</SelectItem>
        <SelectItem value="ar">Argentina</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select with many options to test scrolling behavior.'
      }
    }
  }
}`,...(Ln=(Dn=xe.parameters)==null?void 0:Dn.docs)==null?void 0:Ln.source}}};var kn,Vn,Bn;we.parameters={...we.parameters,docs:{...(kn=we.parameters)==null?void 0:kn.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[100px]">
        <SelectValue placeholder="Size" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="xs">XS</SelectItem>
        <SelectItem value="s">S</SelectItem>
        <SelectItem value="m">M</SelectItem>
        <SelectItem value="l">L</SelectItem>
        <SelectItem value="xl">XL</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select with minimal width to test compact layouts.'
      }
    }
  }
}`,...(Bn=(Vn=we.parameters)==null?void 0:Vn.docs)==null?void 0:Bn.source}}};var Fn,Hn,Wn;ye.parameters={...ye.parameters,docs:{...(Fn=ye.parameters)==null?void 0:Fn.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select an option" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="">None</SelectItem>
        <SelectItem value="option1">Option 1</SelectItem>
        <SelectItem value="option2">Option 2</SelectItem>
        <SelectItem value="option3">Option 3</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select with an empty/none option for clearing selection.'
      }
    }
  }
}`,...(Wn=(Hn=ye.parameters)==null?void 0:Hn.docs)==null?void 0:Wn.source}}};var $n,zn,Un;Ie.parameters={...Ie.parameters,docs:{...($n=Ie.parameters)==null?void 0:$n.docs,source:{originalSource:`{
  render: () => <Select>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select a status" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="active">✅ Active</SelectItem>
        <SelectItem value="pending">⏳ Pending</SelectItem>
        <SelectItem value="inactive">❌ Inactive</SelectItem>
        <SelectItem value="archived">📦 Archived</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Select options with icons for better visual identification.'
      }
    }
  }
}`,...(Un=(zn=Ie.parameters)==null?void 0:zn.docs)==null?void 0:Un.source}}};var Kn,Gn,Xn;be.parameters={...be.parameters,docs:{...(Kn=be.parameters)==null?void 0:Kn.docs,source:{originalSource:`{
  render: () => <Select onValueChange={value => console.log('Selected:', value)}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Make a selection" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="option1">Option 1</SelectItem>
        <SelectItem value="option2">Option 2</SelectItem>
        <SelectItem value="option3">Option 3</SelectItem>
      </SelectContent>
    </Select>,
  parameters: {
    docs: {
      description: {
        story: 'Interactive select that logs selection changes to console.'
      }
    }
  }
}`,...(Xn=(Gn=be.parameters)==null?void 0:Gn.docs)==null?void 0:Xn.source}}};const Tl=["Default","WithDefaultValue","Disabled","LongOptions","ManyOptions","SmallWidth","WithEmptyOption","WithIcons","Interactive"];export{he as Default,Se as Disabled,be as Interactive,ve as LongOptions,xe as ManyOptions,we as SmallWidth,ge as WithDefaultValue,ye as WithEmptyOption,Ie as WithIcons,Tl as __namedExportsOrder,Al as default};
