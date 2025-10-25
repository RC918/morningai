import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r}from"./index-Dz3UJJSw.js";import{r as Wt}from"./index-CYANIyVc.js";import{u as He,c as _}from"./index-Bo7lbUv-.js";import{u as xo,c as Io}from"./index-M8eZJUAT.js";import{u as F,c as wo}from"./index-DRuEWG1E.js";import{c as yo,u as ne}from"./index-DiKooijE.js";import{P as Co,D as bo}from"./index-CevHeI5L.js";import{h as To,u as jo,R as No,F as _o}from"./index-DTuDuRIS.js";import{u as ke}from"./index-HmPO_Abe.js";import{c as zt,R as Po,V as Eo,A as Ro,C as Oo,a as Ao}from"./index-DxHjUX3g.js";import{P as O}from"./index-C7eB__Z-.js";import{u as Mo}from"./index-BwP8QHTI.js";import{u as Vo}from"./index-D8y_WRrw.js";import{c as he}from"./utils-D-KgF5mV.js";import{C as Kt}from"./chevron-down-DSMCphj4.js";import{C as Do}from"./check-rI9F-S9H.js";import{c as ko}from"./createLucideIcon-ClV4rtrr.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-fUCaa9pg.js";import"./index-DW9D76JB.js";/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bo=[["path",{d:"m18 15-6-6-6 6",key:"153udz"}]],Lo=ko("chevron-up",Bo);function Fe(o,[l,t]){return Math.min(t,Math.max(l,o))}var Uo=[" ","Enter","ArrowUp","ArrowDown"],Ho=[" ","Enter"],ue="Select",[Ce,be,Fo]=Io(ue),[ge]=yo(ue,[Fo,zt]),Te=zt(),[Wo,ce]=ge(ue),[zo,Ko]=ge(ue),Gt=o=>{const{__scopeSelect:l,children:t,open:s,defaultOpen:i,onOpenChange:m,value:n,defaultValue:c,onValueChange:a,dir:S,name:f,autoComplete:w,disabled:j,required:N,form:T}=o,p=Te(l),[v,y]=r.useState(null),[u,g]=r.useState(null),[M,V]=r.useState(!1),ve=xo(S),[P,U]=He({prop:s,defaultProp:i??!1,onChange:m,caller:ue}),[J,ie]=He({prop:n,defaultProp:c,onChange:a,caller:ue}),W=r.useRef(null),z=v?T||!!v.closest("form"):!0,[X,K]=r.useState(new Set),G=Array.from(X).map(E=>E.props.value).join(";");return e.jsx(Po,{...p,children:e.jsxs(Wo,{required:N,scope:l,trigger:v,onTriggerChange:y,valueNode:u,onValueNodeChange:g,valueNodeHasChildren:M,onValueNodeHasChildrenChange:V,contentId:ke(),value:J,onValueChange:ie,open:P,onOpenChange:U,dir:ve,triggerPointerDownPosRef:W,disabled:j,children:[e.jsx(Ce.Provider,{scope:l,children:e.jsx(zo,{scope:o.__scopeSelect,onNativeOptionAdd:r.useCallback(E=>{K(H=>new Set(H).add(E))},[]),onNativeOptionRemove:r.useCallback(E=>{K(H=>{const $=new Set(H);return $.delete(E),$})},[]),children:t})}),z?e.jsxs(ho,{"aria-hidden":!0,required:N,tabIndex:-1,name:f,autoComplete:w,value:J,onChange:E=>ie(E.target.value),disabled:j,form:T,children:[J===void 0?e.jsx("option",{value:""}):null,Array.from(X)]},G):null]})})};Gt.displayName=ue;var $t="SelectTrigger",Jt=r.forwardRef((o,l)=>{const{__scopeSelect:t,disabled:s=!1,...i}=o,m=Te(t),n=ce($t,t),c=n.disabled||s,a=F(l,n.onTriggerChange),S=be(t),f=r.useRef("touch"),[w,j,N]=vo(p=>{const v=S().filter(g=>!g.disabled),y=v.find(g=>g.value===n.value),u=fo(v,p,y);u!==void 0&&n.onValueChange(u.value)}),T=p=>{c||(n.onOpenChange(!0),N()),p&&(n.triggerPointerDownPosRef.current={x:Math.round(p.pageX),y:Math.round(p.pageY)})};return e.jsx(Ro,{asChild:!0,...m,children:e.jsx(O.button,{type:"button",role:"combobox","aria-controls":n.contentId,"aria-expanded":n.open,"aria-required":n.required,"aria-autocomplete":"none",dir:n.dir,"data-state":n.open?"open":"closed",disabled:c,"data-disabled":c?"":void 0,"data-placeholder":go(n.value)?"":void 0,...i,ref:a,onClick:_(i.onClick,p=>{p.currentTarget.focus(),f.current!=="mouse"&&T(p)}),onPointerDown:_(i.onPointerDown,p=>{f.current=p.pointerType;const v=p.target;v.hasPointerCapture(p.pointerId)&&v.releasePointerCapture(p.pointerId),p.button===0&&p.ctrlKey===!1&&p.pointerType==="mouse"&&(T(p),p.preventDefault())}),onKeyDown:_(i.onKeyDown,p=>{const v=w.current!=="";!(p.ctrlKey||p.altKey||p.metaKey)&&p.key.length===1&&j(p.key),!(v&&p.key===" ")&&Uo.includes(p.key)&&(T(),p.preventDefault())})})})});Jt.displayName=$t;var Xt="SelectValue",qt=r.forwardRef((o,l)=>{const{__scopeSelect:t,className:s,style:i,children:m,placeholder:n="",...c}=o,a=ce(Xt,t),{onValueNodeHasChildrenChange:S}=a,f=m!==void 0,w=F(l,a.onValueNodeChange);return ne(()=>{S(f)},[S,f]),e.jsx(O.span,{...c,ref:w,style:{pointerEvents:"none"},children:go(a.value)?e.jsx(e.Fragment,{children:n}):m})});qt.displayName=Xt;var Go="SelectIcon",Yt=r.forwardRef((o,l)=>{const{__scopeSelect:t,children:s,...i}=o;return e.jsx(O.span,{"aria-hidden":!0,...i,ref:l,children:s||"▼"})});Yt.displayName=Go;var $o="SelectPortal",Zt=o=>e.jsx(Co,{asChild:!0,...o});Zt.displayName=$o;var me="SelectContent",Qt=r.forwardRef((o,l)=>{const t=ce(me,o.__scopeSelect),[s,i]=r.useState();if(ne(()=>{i(new DocumentFragment)},[]),!t.open){const m=s;return m?Wt.createPortal(e.jsx(eo,{scope:o.__scopeSelect,children:e.jsx(Ce.Slot,{scope:o.__scopeSelect,children:e.jsx("div",{children:o.children})})}),m):null}return e.jsx(to,{...o,ref:l})});Qt.displayName=me;var D=10,[eo,se]=ge(me),Jo="SelectContentImpl",Xo=wo("SelectContent.RemoveScroll"),to=r.forwardRef((o,l)=>{const{__scopeSelect:t,position:s="item-aligned",onCloseAutoFocus:i,onEscapeKeyDown:m,onPointerDownOutside:n,side:c,sideOffset:a,align:S,alignOffset:f,arrowPadding:w,collisionBoundary:j,collisionPadding:N,sticky:T,hideWhenDetached:p,avoidCollisions:v,...y}=o,u=ce(me,t),[g,M]=r.useState(null),[V,ve]=r.useState(null),P=F(l,h=>M(h)),[U,J]=r.useState(null),[ie,W]=r.useState(null),z=be(t),[X,K]=r.useState(!1),G=r.useRef(!1);r.useEffect(()=>{if(g)return To(g)},[g]),jo();const E=r.useCallback(h=>{const[b,...R]=z().map(I=>I.ref.current),[C]=R.slice(-1),x=document.activeElement;for(const I of h)if(I===x||(I==null||I.scrollIntoView({block:"nearest"}),I===b&&V&&(V.scrollTop=0),I===C&&V&&(V.scrollTop=V.scrollHeight),I==null||I.focus(),document.activeElement!==x))return},[z,V]),H=r.useCallback(()=>E([U,g]),[E,U,g]);r.useEffect(()=>{X&&H()},[X,H]);const{onOpenChange:$,triggerPointerDownPosRef:q}=u;r.useEffect(()=>{if(g){let h={x:0,y:0};const b=C=>{var x,I;h={x:Math.abs(Math.round(C.pageX)-(((x=q.current)==null?void 0:x.x)??0)),y:Math.abs(Math.round(C.pageY)-(((I=q.current)==null?void 0:I.y)??0))}},R=C=>{h.x<=10&&h.y<=10?C.preventDefault():g.contains(C.target)||$(!1),document.removeEventListener("pointermove",b),q.current=null};return q.current!==null&&(document.addEventListener("pointermove",b),document.addEventListener("pointerup",R,{capture:!0,once:!0})),()=>{document.removeEventListener("pointermove",b),document.removeEventListener("pointerup",R,{capture:!0})}}},[g,$,q]),r.useEffect(()=>{const h=()=>$(!1);return window.addEventListener("blur",h),window.addEventListener("resize",h),()=>{window.removeEventListener("blur",h),window.removeEventListener("resize",h)}},[$]);const[je,Ie]=vo(h=>{const b=z().filter(x=>!x.disabled),R=b.find(x=>x.ref.current===document.activeElement),C=fo(b,h,R);C&&setTimeout(()=>C.ref.current.focus())}),Ne=r.useCallback((h,b,R)=>{const C=!G.current&&!R;(u.value!==void 0&&u.value===b||C)&&(J(h),C&&(G.current=!0))},[u.value]),_e=r.useCallback(()=>g==null?void 0:g.focus(),[g]),Se=r.useCallback((h,b,R)=>{const C=!G.current&&!R;(u.value!==void 0&&u.value===b||C)&&W(h)},[u.value]),we=s==="popper"?Oe:oo,fe=we===Oe?{side:c,sideOffset:a,align:S,alignOffset:f,arrowPadding:w,collisionBoundary:j,collisionPadding:N,sticky:T,hideWhenDetached:p,avoidCollisions:v}:{};return e.jsx(eo,{scope:t,content:g,viewport:V,onViewportChange:ve,itemRefCallback:Ne,selectedItem:U,onItemLeave:_e,itemTextRefCallback:Se,focusSelectedItem:H,selectedItemText:ie,position:s,isPositioned:X,searchRef:je,children:e.jsx(No,{as:Xo,allowPinchZoom:!0,children:e.jsx(_o,{asChild:!0,trapped:u.open,onMountAutoFocus:h=>{h.preventDefault()},onUnmountAutoFocus:_(i,h=>{var b;(b=u.trigger)==null||b.focus({preventScroll:!0}),h.preventDefault()}),children:e.jsx(bo,{asChild:!0,disableOutsidePointerEvents:!0,onEscapeKeyDown:m,onPointerDownOutside:n,onFocusOutside:h=>h.preventDefault(),onDismiss:()=>u.onOpenChange(!1),children:e.jsx(we,{role:"listbox",id:u.contentId,"data-state":u.open?"open":"closed",dir:u.dir,onContextMenu:h=>h.preventDefault(),...y,...fe,onPlaced:()=>K(!0),ref:P,style:{display:"flex",flexDirection:"column",outline:"none",...y.style},onKeyDown:_(y.onKeyDown,h=>{const b=h.ctrlKey||h.altKey||h.metaKey;if(h.key==="Tab"&&h.preventDefault(),!b&&h.key.length===1&&Ie(h.key),["ArrowUp","ArrowDown","Home","End"].includes(h.key)){let C=z().filter(x=>!x.disabled).map(x=>x.ref.current);if(["ArrowUp","End"].includes(h.key)&&(C=C.slice().reverse()),["ArrowUp","ArrowDown"].includes(h.key)){const x=h.target,I=C.indexOf(x);C=C.slice(I+1)}setTimeout(()=>E(C)),h.preventDefault()}})})})})})})});to.displayName=Jo;var qo="SelectItemAlignedPosition",oo=r.forwardRef((o,l)=>{const{__scopeSelect:t,onPlaced:s,...i}=o,m=ce(me,t),n=se(me,t),[c,a]=r.useState(null),[S,f]=r.useState(null),w=F(l,P=>f(P)),j=be(t),N=r.useRef(!1),T=r.useRef(!0),{viewport:p,selectedItem:v,selectedItemText:y,focusSelectedItem:u}=n,g=r.useCallback(()=>{if(m.trigger&&m.valueNode&&c&&S&&p&&v&&y){const P=m.trigger.getBoundingClientRect(),U=S.getBoundingClientRect(),J=m.valueNode.getBoundingClientRect(),ie=y.getBoundingClientRect();if(m.dir!=="rtl"){const x=ie.left-U.left,I=J.left-x,de=P.left-I,pe=P.width+de,Pe=Math.max(pe,U.width),Ee=window.innerWidth-D,Re=Fe(I,[D,Math.max(D,Ee-Pe)]);c.style.minWidth=pe+"px",c.style.left=Re+"px"}else{const x=U.right-ie.right,I=window.innerWidth-J.right-x,de=window.innerWidth-P.right-I,pe=P.width+de,Pe=Math.max(pe,U.width),Ee=window.innerWidth-D,Re=Fe(I,[D,Math.max(D,Ee-Pe)]);c.style.minWidth=pe+"px",c.style.right=Re+"px"}const W=j(),z=window.innerHeight-D*2,X=p.scrollHeight,K=window.getComputedStyle(S),G=parseInt(K.borderTopWidth,10),E=parseInt(K.paddingTop,10),H=parseInt(K.borderBottomWidth,10),$=parseInt(K.paddingBottom,10),q=G+E+X+$+H,je=Math.min(v.offsetHeight*5,q),Ie=window.getComputedStyle(p),Ne=parseInt(Ie.paddingTop,10),_e=parseInt(Ie.paddingBottom,10),Se=P.top+P.height/2-D,we=z-Se,fe=v.offsetHeight/2,h=v.offsetTop+fe,b=G+E+h,R=q-b;if(b<=Se){const x=W.length>0&&v===W[W.length-1].ref.current;c.style.bottom="0px";const I=S.clientHeight-p.offsetTop-p.offsetHeight,de=Math.max(we,fe+(x?_e:0)+I+H),pe=b+de;c.style.height=pe+"px"}else{const x=W.length>0&&v===W[0].ref.current;c.style.top="0px";const de=Math.max(Se,G+p.offsetTop+(x?Ne:0)+fe)+R;c.style.height=de+"px",p.scrollTop=b-Se+p.offsetTop}c.style.margin=`${D}px 0`,c.style.minHeight=je+"px",c.style.maxHeight=z+"px",s==null||s(),requestAnimationFrame(()=>N.current=!0)}},[j,m.trigger,m.valueNode,c,S,p,v,y,m.dir,s]);ne(()=>g(),[g]);const[M,V]=r.useState();ne(()=>{S&&V(window.getComputedStyle(S).zIndex)},[S]);const ve=r.useCallback(P=>{P&&T.current===!0&&(g(),u==null||u(),T.current=!1)},[g,u]);return e.jsx(Zo,{scope:t,contentWrapper:c,shouldExpandOnScrollRef:N,onScrollButtonChange:ve,children:e.jsx("div",{ref:a,style:{display:"flex",flexDirection:"column",position:"fixed",zIndex:M},children:e.jsx(O.div,{...i,ref:w,style:{boxSizing:"border-box",maxHeight:"100%",...i.style}})})})});oo.displayName=qo;var Yo="SelectPopperPosition",Oe=r.forwardRef((o,l)=>{const{__scopeSelect:t,align:s="start",collisionPadding:i=D,...m}=o,n=Te(t);return e.jsx(Oo,{...n,...m,ref:l,align:s,collisionPadding:i,style:{boxSizing:"border-box",...m.style,"--radix-select-content-transform-origin":"var(--radix-popper-transform-origin)","--radix-select-content-available-width":"var(--radix-popper-available-width)","--radix-select-content-available-height":"var(--radix-popper-available-height)","--radix-select-trigger-width":"var(--radix-popper-anchor-width)","--radix-select-trigger-height":"var(--radix-popper-anchor-height)"}})});Oe.displayName=Yo;var[Zo,Be]=ge(me,{}),Ae="SelectViewport",ro=r.forwardRef((o,l)=>{const{__scopeSelect:t,nonce:s,...i}=o,m=se(Ae,t),n=Be(Ae,t),c=F(l,m.onViewportChange),a=r.useRef(0);return e.jsxs(e.Fragment,{children:[e.jsx("style",{dangerouslySetInnerHTML:{__html:"[data-radix-select-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-select-viewport]::-webkit-scrollbar{display:none}"},nonce:s}),e.jsx(Ce.Slot,{scope:t,children:e.jsx(O.div,{"data-radix-select-viewport":"",role:"presentation",...i,ref:c,style:{position:"relative",flex:1,overflow:"hidden auto",...i.style},onScroll:_(i.onScroll,S=>{const f=S.currentTarget,{contentWrapper:w,shouldExpandOnScrollRef:j}=n;if(j!=null&&j.current&&w){const N=Math.abs(a.current-f.scrollTop);if(N>0){const T=window.innerHeight-D*2,p=parseFloat(w.style.minHeight),v=parseFloat(w.style.height),y=Math.max(p,v);if(y<T){const u=y+N,g=Math.min(T,u),M=u-g;w.style.height=g+"px",w.style.bottom==="0px"&&(f.scrollTop=M>0?M:0,w.style.justifyContent="flex-end")}}}a.current=f.scrollTop})})})]})});ro.displayName=Ae;var lo="SelectGroup",[Qo,er]=ge(lo),tr=r.forwardRef((o,l)=>{const{__scopeSelect:t,...s}=o,i=ke();return e.jsx(Qo,{scope:t,id:i,children:e.jsx(O.div,{role:"group","aria-labelledby":i,...s,ref:l})})});tr.displayName=lo;var ao="SelectLabel",or=r.forwardRef((o,l)=>{const{__scopeSelect:t,...s}=o,i=er(ao,t);return e.jsx(O.div,{id:i.id,...s,ref:l})});or.displayName=ao;var ye="SelectItem",[rr,no]=ge(ye),co=r.forwardRef((o,l)=>{const{__scopeSelect:t,value:s,disabled:i=!1,textValue:m,...n}=o,c=ce(ye,t),a=se(ye,t),S=c.value===s,[f,w]=r.useState(m??""),[j,N]=r.useState(!1),T=F(l,u=>{var g;return(g=a.itemRefCallback)==null?void 0:g.call(a,u,s,i)}),p=ke(),v=r.useRef("touch"),y=()=>{i||(c.onValueChange(s),c.onOpenChange(!1))};if(s==="")throw new Error("A <Select.Item /> must have a value prop that is not an empty string. This is because the Select value can be set to an empty string to clear the selection and show the placeholder.");return e.jsx(rr,{scope:t,value:s,disabled:i,textId:p,isSelected:S,onItemTextChange:r.useCallback(u=>{w(g=>g||((u==null?void 0:u.textContent)??"").trim())},[]),children:e.jsx(Ce.ItemSlot,{scope:t,value:s,disabled:i,textValue:f,children:e.jsx(O.div,{role:"option","aria-labelledby":p,"data-highlighted":j?"":void 0,"aria-selected":S&&j,"data-state":S?"checked":"unchecked","aria-disabled":i||void 0,"data-disabled":i?"":void 0,tabIndex:i?void 0:-1,...n,ref:T,onFocus:_(n.onFocus,()=>N(!0)),onBlur:_(n.onBlur,()=>N(!1)),onClick:_(n.onClick,()=>{v.current!=="mouse"&&y()}),onPointerUp:_(n.onPointerUp,()=>{v.current==="mouse"&&y()}),onPointerDown:_(n.onPointerDown,u=>{v.current=u.pointerType}),onPointerMove:_(n.onPointerMove,u=>{var g;v.current=u.pointerType,i?(g=a.onItemLeave)==null||g.call(a):v.current==="mouse"&&u.currentTarget.focus({preventScroll:!0})}),onPointerLeave:_(n.onPointerLeave,u=>{var g;u.currentTarget===document.activeElement&&((g=a.onItemLeave)==null||g.call(a))}),onKeyDown:_(n.onKeyDown,u=>{var M;((M=a.searchRef)==null?void 0:M.current)!==""&&u.key===" "||(Ho.includes(u.key)&&y(),u.key===" "&&u.preventDefault())})})})})});co.displayName=ye;var xe="SelectItemText",so=r.forwardRef((o,l)=>{const{__scopeSelect:t,className:s,style:i,...m}=o,n=ce(xe,t),c=se(xe,t),a=no(xe,t),S=Ko(xe,t),[f,w]=r.useState(null),j=F(l,y=>w(y),a.onItemTextChange,y=>{var u;return(u=c.itemTextRefCallback)==null?void 0:u.call(c,y,a.value,a.disabled)}),N=f==null?void 0:f.textContent,T=r.useMemo(()=>e.jsx("option",{value:a.value,disabled:a.disabled,children:N},a.value),[a.disabled,a.value,N]),{onNativeOptionAdd:p,onNativeOptionRemove:v}=S;return ne(()=>(p(T),()=>v(T)),[p,v,T]),e.jsxs(e.Fragment,{children:[e.jsx(O.span,{id:a.textId,...m,ref:j}),a.isSelected&&n.valueNode&&!n.valueNodeHasChildren?Wt.createPortal(m.children,n.valueNode):null]})});so.displayName=xe;var io="SelectItemIndicator",po=r.forwardRef((o,l)=>{const{__scopeSelect:t,...s}=o;return no(io,t).isSelected?e.jsx(O.span,{"aria-hidden":!0,...s,ref:l}):null});po.displayName=io;var Me="SelectScrollUpButton",uo=r.forwardRef((o,l)=>{const t=se(Me,o.__scopeSelect),s=Be(Me,o.__scopeSelect),[i,m]=r.useState(!1),n=F(l,s.onScrollButtonChange);return ne(()=>{if(t.viewport&&t.isPositioned){let c=function(){const S=a.scrollTop>0;m(S)};const a=t.viewport;return c(),a.addEventListener("scroll",c),()=>a.removeEventListener("scroll",c)}},[t.viewport,t.isPositioned]),i?e.jsx(So,{...o,ref:n,onAutoScroll:()=>{const{viewport:c,selectedItem:a}=t;c&&a&&(c.scrollTop=c.scrollTop-a.offsetHeight)}}):null});uo.displayName=Me;var Ve="SelectScrollDownButton",mo=r.forwardRef((o,l)=>{const t=se(Ve,o.__scopeSelect),s=Be(Ve,o.__scopeSelect),[i,m]=r.useState(!1),n=F(l,s.onScrollButtonChange);return ne(()=>{if(t.viewport&&t.isPositioned){let c=function(){const S=a.scrollHeight-a.clientHeight,f=Math.ceil(a.scrollTop)<S;m(f)};const a=t.viewport;return c(),a.addEventListener("scroll",c),()=>a.removeEventListener("scroll",c)}},[t.viewport,t.isPositioned]),i?e.jsx(So,{...o,ref:n,onAutoScroll:()=>{const{viewport:c,selectedItem:a}=t;c&&a&&(c.scrollTop=c.scrollTop+a.offsetHeight)}}):null});mo.displayName=Ve;var So=r.forwardRef((o,l)=>{const{__scopeSelect:t,onAutoScroll:s,...i}=o,m=se("SelectScrollButton",t),n=r.useRef(null),c=be(t),a=r.useCallback(()=>{n.current!==null&&(window.clearInterval(n.current),n.current=null)},[]);return r.useEffect(()=>()=>a(),[a]),ne(()=>{var f;const S=c().find(w=>w.ref.current===document.activeElement);(f=S==null?void 0:S.ref.current)==null||f.scrollIntoView({block:"nearest"})},[c]),e.jsx(O.div,{"aria-hidden":!0,...i,ref:l,style:{flexShrink:0,...i.style},onPointerDown:_(i.onPointerDown,()=>{n.current===null&&(n.current=window.setInterval(s,50))}),onPointerMove:_(i.onPointerMove,()=>{var S;(S=m.onItemLeave)==null||S.call(m),n.current===null&&(n.current=window.setInterval(s,50))}),onPointerLeave:_(i.onPointerLeave,()=>{a()})})}),lr="SelectSeparator",ar=r.forwardRef((o,l)=>{const{__scopeSelect:t,...s}=o;return e.jsx(O.div,{"aria-hidden":!0,...s,ref:l})});ar.displayName=lr;var De="SelectArrow",nr=r.forwardRef((o,l)=>{const{__scopeSelect:t,...s}=o,i=Te(t),m=ce(De,t),n=se(De,t);return m.open&&n.position==="popper"?e.jsx(Ao,{...i,...s,ref:l}):null});nr.displayName=De;var cr="SelectBubbleInput",ho=r.forwardRef(({__scopeSelect:o,value:l,...t},s)=>{const i=r.useRef(null),m=F(s,i),n=Vo(l);return r.useEffect(()=>{const c=i.current;if(!c)return;const a=window.HTMLSelectElement.prototype,f=Object.getOwnPropertyDescriptor(a,"value").set;if(n!==l&&f){const w=new Event("change",{bubbles:!0});f.call(c,l),c.dispatchEvent(w)}},[n,l]),e.jsx(O.select,{...t,style:{...Eo,...t.style},ref:m,defaultValue:l})});ho.displayName=cr;function go(o){return o===""||o===void 0}function vo(o){const l=Mo(o),t=r.useRef(""),s=r.useRef(0),i=r.useCallback(n=>{const c=t.current+n;l(c),(function a(S){t.current=S,window.clearTimeout(s.current),S!==""&&(s.current=window.setTimeout(()=>a(""),1e3))})(c)},[l]),m=r.useCallback(()=>{t.current="",window.clearTimeout(s.current)},[]);return r.useEffect(()=>()=>window.clearTimeout(s.current),[]),[t,i,m]}function fo(o,l,t){const i=l.length>1&&Array.from(l).every(S=>S===l[0])?l[0]:l,m=t?o.indexOf(t):-1;let n=sr(o,Math.max(m,0));i.length===1&&(n=n.filter(S=>S!==t));const a=n.find(S=>S.textValue.toLowerCase().startsWith(i.toLowerCase()));return a!==t?a:void 0}function sr(o,l){return o.map((t,s)=>o[(l+s)%o.length])}var ir=Gt,dr=Jt,pr=qt,ur=Yt,mr=Zt,Sr=Qt,hr=ro,gr=co,vr=so,fr=po,xr=uo,Ir=mo;function A({...o}){return e.jsx(ir,{"data-slot":"select",...o})}function k({...o}){return e.jsx(pr,{"data-slot":"select-value",...o})}function B({className:o,size:l="default",children:t,...s}){return e.jsxs(dr,{"data-slot":"select-trigger","data-size":l,className:he("border-input data-[placeholder]:text-muted-foreground [&_svg:not([class*='text-'])]:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 dark:hover:bg-input/50 flex w-fit items-center justify-between gap-2 rounded-md border bg-transparent px-3 py-2 text-sm whitespace-nowrap shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 data-[size=default]:h-9 data-[size=sm]:h-8 *:data-[slot=select-value]:line-clamp-1 *:data-[slot=select-value]:flex *:data-[slot=select-value]:items-center *:data-[slot=select-value]:gap-2 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",o),...s,children:[t,e.jsx(ur,{asChild:!0,children:e.jsx(Kt,{className:"size-4 opacity-50"})})]})}function L({className:o,children:l,position:t="popper",...s}){return e.jsx(mr,{children:e.jsxs(Sr,{"data-slot":"select-content",className:he("bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 relative z-50 max-h-(--radix-select-content-available-height) min-w-[8rem] origin-(--radix-select-content-transform-origin) overflow-x-hidden overflow-y-auto rounded-md border shadow-md",t==="popper"&&"data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1",o),position:t,...s,children:[e.jsx(Le,{}),e.jsx(hr,{className:he("p-1",t==="popper"&&"h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)] scroll-my-1"),children:l}),e.jsx(Ue,{})]})})}function d({className:o,children:l,...t}){return e.jsxs(gr,{"data-slot":"select-item",className:he("focus:bg-accent focus:text-accent-foreground [&_svg:not([class*='text-'])]:text-muted-foreground relative flex w-full cursor-default items-center gap-2 rounded-sm py-1.5 pr-8 pl-2 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4 *:[span]:last:flex *:[span]:last:items-center *:[span]:last:gap-2",o),...t,children:[e.jsx("span",{className:"absolute right-2 flex size-3.5 items-center justify-center",children:e.jsx(fr,{children:e.jsx(Do,{className:"size-4"})})}),e.jsx(vr,{children:l})]})}function Le({className:o,...l}){return e.jsx(xr,{"data-slot":"select-scroll-up-button",className:he("flex cursor-default items-center justify-center py-1",o),...l,children:e.jsx(Lo,{className:"size-4"})})}function Ue({className:o,...l}){return e.jsx(Ir,{"data-slot":"select-scroll-down-button",className:he("flex cursor-default items-center justify-center py-1",o),...l,children:e.jsx(Kt,{className:"size-4"})})}A.__docgenInfo={description:"",methods:[],displayName:"Select"};L.__docgenInfo={description:"",methods:[],displayName:"SelectContent",props:{position:{defaultValue:{value:'"popper"',computed:!1},required:!1}}};d.__docgenInfo={description:"",methods:[],displayName:"SelectItem"};Ue.__docgenInfo={description:"",methods:[],displayName:"SelectScrollDownButton"};Le.__docgenInfo={description:"",methods:[],displayName:"SelectScrollUpButton"};B.__docgenInfo={description:"",methods:[],displayName:"SelectTrigger",props:{size:{defaultValue:{value:'"default"',computed:!1},required:!1}}};k.__docgenInfo={description:"",methods:[],displayName:"SelectValue"};A.__docgenInfo={description:"",methods:[],displayName:"Select"};L.__docgenInfo={description:"",methods:[],displayName:"SelectContent",props:{position:{defaultValue:{value:'"popper"',computed:!1},required:!1}}};d.__docgenInfo={description:"",methods:[],displayName:"SelectItem"};Ue.__docgenInfo={description:"",methods:[],displayName:"SelectScrollDownButton"};Le.__docgenInfo={description:"",methods:[],displayName:"SelectScrollUpButton"};B.__docgenInfo={description:"",methods:[],displayName:"SelectTrigger",props:{size:{defaultValue:{value:'"default"',computed:!1},required:!1}}};k.__docgenInfo={description:"",methods:[],displayName:"SelectValue"};const Fr={title:"UI/Select",component:A,parameters:{layout:"centered",docs:{description:{component:`
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
        `}}},tags:["autodocs"],argTypes:{disabled:{control:"boolean",description:"Whether the select is disabled",table:{type:{summary:"boolean"},defaultValue:{summary:"false"}}},defaultValue:{control:"text",description:"Default selected value",table:{type:{summary:"string"}}},onValueChange:{action:"valueChanged",description:"Function called when selection changes",table:{type:{summary:"(value: string) => void"}}}}},Y={render:()=>e.jsxs(A,{children:[e.jsx(B,{className:"w-[180px]",children:e.jsx(k,{placeholder:"Select a fruit"})}),e.jsxs(L,{children:[e.jsx(d,{value:"apple",children:"Apple"}),e.jsx(d,{value:"banana",children:"Banana"}),e.jsx(d,{value:"orange",children:"Orange"}),e.jsx(d,{value:"grape",children:"Grape"}),e.jsx(d,{value:"pineapple",children:"Pineapple"})]})]})},Z={render:()=>e.jsxs(A,{defaultValue:"banana",children:[e.jsx(B,{className:"w-[180px]",children:e.jsx(k,{placeholder:"Select a fruit"})}),e.jsxs(L,{children:[e.jsx(d,{value:"apple",children:"Apple"}),e.jsx(d,{value:"banana",children:"Banana"}),e.jsx(d,{value:"orange",children:"Orange"}),e.jsx(d,{value:"grape",children:"Grape"}),e.jsx(d,{value:"pineapple",children:"Pineapple"})]})]}),parameters:{docs:{description:{story:"Select with a pre-selected default value."}}}},Q={render:()=>e.jsxs(A,{disabled:!0,children:[e.jsx(B,{className:"w-[180px]",children:e.jsx(k,{placeholder:"Select a fruit"})}),e.jsxs(L,{children:[e.jsx(d,{value:"apple",children:"Apple"}),e.jsx(d,{value:"banana",children:"Banana"}),e.jsx(d,{value:"orange",children:"Orange"})]})]}),parameters:{docs:{description:{story:"Select in disabled state - user cannot interact with it."}}}},ee={render:()=>e.jsxs(A,{children:[e.jsx(B,{className:"w-[250px]",children:e.jsx(k,{placeholder:"Select a programming language"})}),e.jsxs(L,{children:[e.jsx(d,{value:"javascript",children:"JavaScript - The versatile web language"}),e.jsx(d,{value:"typescript",children:"TypeScript - JavaScript with static typing"}),e.jsx(d,{value:"python",children:"Python - Simple and powerful programming"}),e.jsx(d,{value:"rust",children:"Rust - Systems programming with memory safety"}),e.jsx(d,{value:"go",children:"Go - Fast and simple backend development"})]})]}),parameters:{docs:{description:{story:"Select with long option text to test text wrapping and layout."}}}},te={render:()=>e.jsxs(A,{children:[e.jsx(B,{className:"w-[200px]",children:e.jsx(k,{placeholder:"Select a country"})}),e.jsxs(L,{children:[e.jsx(d,{value:"us",children:"United States"}),e.jsx(d,{value:"ca",children:"Canada"}),e.jsx(d,{value:"mx",children:"Mexico"}),e.jsx(d,{value:"uk",children:"United Kingdom"}),e.jsx(d,{value:"fr",children:"France"}),e.jsx(d,{value:"de",children:"Germany"}),e.jsx(d,{value:"it",children:"Italy"}),e.jsx(d,{value:"es",children:"Spain"}),e.jsx(d,{value:"jp",children:"Japan"}),e.jsx(d,{value:"kr",children:"South Korea"}),e.jsx(d,{value:"cn",children:"China"}),e.jsx(d,{value:"in",children:"India"}),e.jsx(d,{value:"au",children:"Australia"}),e.jsx(d,{value:"br",children:"Brazil"}),e.jsx(d,{value:"ar",children:"Argentina"})]})]}),parameters:{docs:{description:{story:"Select with many options to test scrolling behavior."}}}},oe={render:()=>e.jsxs(A,{children:[e.jsx(B,{className:"w-[100px]",children:e.jsx(k,{placeholder:"Size"})}),e.jsxs(L,{children:[e.jsx(d,{value:"xs",children:"XS"}),e.jsx(d,{value:"s",children:"S"}),e.jsx(d,{value:"m",children:"M"}),e.jsx(d,{value:"l",children:"L"}),e.jsx(d,{value:"xl",children:"XL"})]})]}),parameters:{docs:{description:{story:"Select with minimal width to test compact layouts."}}}},re={render:()=>e.jsxs(A,{children:[e.jsx(B,{className:"w-[180px]",children:e.jsx(k,{placeholder:"Select an option"})}),e.jsxs(L,{children:[e.jsx(d,{value:"",children:"None"}),e.jsx(d,{value:"option1",children:"Option 1"}),e.jsx(d,{value:"option2",children:"Option 2"}),e.jsx(d,{value:"option3",children:"Option 3"})]})]}),parameters:{docs:{description:{story:"Select with an empty/none option for clearing selection."}}}},le={render:()=>e.jsxs(A,{children:[e.jsx(B,{className:"w-[200px]",children:e.jsx(k,{placeholder:"Select a status"})}),e.jsxs(L,{children:[e.jsx(d,{value:"active",children:"✅ Active"}),e.jsx(d,{value:"pending",children:"⏳ Pending"}),e.jsx(d,{value:"inactive",children:"❌ Inactive"}),e.jsx(d,{value:"archived",children:"📦 Archived"})]})]}),parameters:{docs:{description:{story:"Select options with icons for better visual identification."}}}},ae={render:()=>e.jsxs(A,{onValueChange:o=>console.log("Selected:",o),children:[e.jsx(B,{className:"w-[180px]",children:e.jsx(k,{placeholder:"Make a selection"})}),e.jsxs(L,{children:[e.jsx(d,{value:"option1",children:"Option 1"}),e.jsx(d,{value:"option2",children:"Option 2"}),e.jsx(d,{value:"option3",children:"Option 3"})]})]}),parameters:{docs:{description:{story:"Interactive select that logs selection changes to console."}}}};var We,ze,Ke;Y.parameters={...Y.parameters,docs:{...(We=Y.parameters)==null?void 0:We.docs,source:{originalSource:`{
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
}`,...(Ke=(ze=Y.parameters)==null?void 0:ze.docs)==null?void 0:Ke.source}}};var Ge,$e,Je;Z.parameters={...Z.parameters,docs:{...(Ge=Z.parameters)==null?void 0:Ge.docs,source:{originalSource:`{
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
}`,...(Je=($e=Z.parameters)==null?void 0:$e.docs)==null?void 0:Je.source}}};var Xe,qe,Ye;Q.parameters={...Q.parameters,docs:{...(Xe=Q.parameters)==null?void 0:Xe.docs,source:{originalSource:`{
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
}`,...(Ye=(qe=Q.parameters)==null?void 0:qe.docs)==null?void 0:Ye.source}}};var Ze,Qe,et;ee.parameters={...ee.parameters,docs:{...(Ze=ee.parameters)==null?void 0:Ze.docs,source:{originalSource:`{
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
}`,...(et=(Qe=ee.parameters)==null?void 0:Qe.docs)==null?void 0:et.source}}};var tt,ot,rt;te.parameters={...te.parameters,docs:{...(tt=te.parameters)==null?void 0:tt.docs,source:{originalSource:`{
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
}`,...(rt=(ot=te.parameters)==null?void 0:ot.docs)==null?void 0:rt.source}}};var lt,at,nt;oe.parameters={...oe.parameters,docs:{...(lt=oe.parameters)==null?void 0:lt.docs,source:{originalSource:`{
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
}`,...(nt=(at=oe.parameters)==null?void 0:at.docs)==null?void 0:nt.source}}};var ct,st,it;re.parameters={...re.parameters,docs:{...(ct=re.parameters)==null?void 0:ct.docs,source:{originalSource:`{
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
}`,...(it=(st=re.parameters)==null?void 0:st.docs)==null?void 0:it.source}}};var dt,pt,ut;le.parameters={...le.parameters,docs:{...(dt=le.parameters)==null?void 0:dt.docs,source:{originalSource:`{
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
}`,...(ut=(pt=le.parameters)==null?void 0:pt.docs)==null?void 0:ut.source}}};var mt,St,ht;ae.parameters={...ae.parameters,docs:{...(mt=ae.parameters)==null?void 0:mt.docs,source:{originalSource:`{
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
}`,...(ht=(St=ae.parameters)==null?void 0:St.docs)==null?void 0:ht.source}}};var gt,vt,ft;Y.parameters={...Y.parameters,docs:{...(gt=Y.parameters)==null?void 0:gt.docs,source:{originalSource:`{
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
}`,...(ft=(vt=Y.parameters)==null?void 0:vt.docs)==null?void 0:ft.source}}};var xt,It,wt;Z.parameters={...Z.parameters,docs:{...(xt=Z.parameters)==null?void 0:xt.docs,source:{originalSource:`{
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
}`,...(wt=(It=Z.parameters)==null?void 0:It.docs)==null?void 0:wt.source}}};var yt,Ct,bt;Q.parameters={...Q.parameters,docs:{...(yt=Q.parameters)==null?void 0:yt.docs,source:{originalSource:`{
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
}`,...(bt=(Ct=Q.parameters)==null?void 0:Ct.docs)==null?void 0:bt.source}}};var Tt,jt,Nt;ee.parameters={...ee.parameters,docs:{...(Tt=ee.parameters)==null?void 0:Tt.docs,source:{originalSource:`{
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
}`,...(Nt=(jt=ee.parameters)==null?void 0:jt.docs)==null?void 0:Nt.source}}};var _t,Pt,Et;te.parameters={...te.parameters,docs:{...(_t=te.parameters)==null?void 0:_t.docs,source:{originalSource:`{
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
}`,...(Et=(Pt=te.parameters)==null?void 0:Pt.docs)==null?void 0:Et.source}}};var Rt,Ot,At;oe.parameters={...oe.parameters,docs:{...(Rt=oe.parameters)==null?void 0:Rt.docs,source:{originalSource:`{
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
}`,...(At=(Ot=oe.parameters)==null?void 0:Ot.docs)==null?void 0:At.source}}};var Mt,Vt,Dt;re.parameters={...re.parameters,docs:{...(Mt=re.parameters)==null?void 0:Mt.docs,source:{originalSource:`{
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
}`,...(Dt=(Vt=re.parameters)==null?void 0:Vt.docs)==null?void 0:Dt.source}}};var kt,Bt,Lt;le.parameters={...le.parameters,docs:{...(kt=le.parameters)==null?void 0:kt.docs,source:{originalSource:`{
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
}`,...(Lt=(Bt=le.parameters)==null?void 0:Bt.docs)==null?void 0:Lt.source}}};var Ut,Ht,Ft;ae.parameters={...ae.parameters,docs:{...(Ut=ae.parameters)==null?void 0:Ut.docs,source:{originalSource:`{
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
}`,...(Ft=(Ht=ae.parameters)==null?void 0:Ht.docs)==null?void 0:Ft.source}}};const Wr=["Default","WithDefaultValue","Disabled","LongOptions","ManyOptions","SmallWidth","WithEmptyOption","WithIcons","Interactive"];export{Y as Default,Q as Disabled,ae as Interactive,ee as LongOptions,te as ManyOptions,oe as SmallWidth,Z as WithDefaultValue,re as WithEmptyOption,le as WithIcons,Wr as __namedExportsOrder,Fr as default};
