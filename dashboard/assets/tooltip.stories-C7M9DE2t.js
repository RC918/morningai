import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as s}from"./index-Dz3UJJSw.js";import{u as Ke,c as I}from"./index-Bo7lbUv-.js";import{u as Le,a as Je}from"./index-DRuEWG1E.js";import{c as Qe}from"./index-DiKooijE.js";import{P as Ze,D as et}from"./index-CevHeI5L.js";import{u as tt}from"./index-HmPO_Abe.js";import{c as Ae,R as ot,A as rt,a as nt,C as it,b as st}from"./index-DxHjUX3g.js";import{P as Me}from"./index-B6CVSQiA.js";import{P as at}from"./index-C7eB__Z-.js";import{c as lt}from"./utils-D-KgF5mV.js";import{B as j}from"./button-6x4QkhmZ.js";import{I as He}from"./info-Dd4rymu9.js";import{c as ze}from"./createLucideIcon-ClV4rtrr.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-BwP8QHTI.js";import"./index-CYANIyVc.js";import"./index-fUCaa9pg.js";import"./index-DW9D76JB.js";import"./index-CGrAONsN.js";/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ct=[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["path",{d:"M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3",key:"1u773s"}],["path",{d:"M12 17h.01",key:"p32p05"}]],pt=ze("circle-help",ct);/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const dt=[["path",{d:"M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z",key:"1qme2f"}],["circle",{cx:"12",cy:"12",r:"3",key:"1v7zrd"}]],ut=ze("settings",dt);var[H]=Qe("Tooltip",[Ae]),z=Ae(),Ve="TooltipProvider",Tt=700,V="tooltip.open",[mt,q]=H(Ve),Ge=t=>{const{__scopeTooltip:r,delayDuration:o=Tt,skipDelayDuration:n=300,disableHoverableContent:i=!1,children:l}=t,c=s.useRef(!0),m=s.useRef(!1),a=s.useRef(0);return s.useEffect(()=>{const u=a.current;return()=>window.clearTimeout(u)},[]),e.jsx(mt,{scope:r,isOpenDelayedRef:c,delayDuration:o,onOpen:s.useCallback(()=>{window.clearTimeout(a.current),c.current=!1},[]),onClose:s.useCallback(()=>{window.clearTimeout(a.current),a.current=window.setTimeout(()=>c.current=!0,n)},[n]),isPointerInTransitRef:m,onPointerInTransitChange:s.useCallback(u=>{m.current=u},[]),disableHoverableContent:i,children:l})};Ge.displayName=Ve;var A="Tooltip",[ht,M]=H(A),qe=t=>{const{__scopeTooltip:r,children:o,open:n,defaultOpen:i,onOpenChange:l,disableHoverableContent:c,delayDuration:m}=t,a=q(A,t.__scopeTooltip),u=z(r),[p,T]=s.useState(null),h=tt(),d=s.useRef(0),C=c??a.disableHoverableContent,y=m??a.delayDuration,v=s.useRef(!1),[b,w]=Ke({prop:n,defaultProp:i??!1,onChange:W=>{W?(a.onOpen(),document.dispatchEvent(new CustomEvent(V))):a.onClose(),l==null||l(W)},caller:A}),k=s.useMemo(()=>b?v.current?"delayed-open":"instant-open":"closed",[b]),D=s.useCallback(()=>{window.clearTimeout(d.current),d.current=0,v.current=!1,w(!0)},[w]),L=s.useCallback(()=>{window.clearTimeout(d.current),d.current=0,w(!1)},[w]),U=s.useCallback(()=>{window.clearTimeout(d.current),d.current=window.setTimeout(()=>{v.current=!0,w(!0),d.current=0},y)},[y,w]);return s.useEffect(()=>()=>{d.current&&(window.clearTimeout(d.current),d.current=0)},[]),e.jsx(ot,{...u,children:e.jsx(ht,{scope:r,contentId:h,open:b,stateAttribute:k,trigger:p,onTriggerChange:T,onTriggerEnter:s.useCallback(()=>{a.isOpenDelayedRef.current?U():D()},[a.isOpenDelayedRef,U,D]),onTriggerLeave:s.useCallback(()=>{C?L():(window.clearTimeout(d.current),d.current=0)},[L,C]),onOpen:D,onClose:L,disableHoverableContent:C,children:o})})};qe.displayName=A;var G="TooltipTrigger",Fe=s.forwardRef((t,r)=>{const{__scopeTooltip:o,...n}=t,i=M(G,o),l=q(G,o),c=z(o),m=s.useRef(null),a=Le(r,m,i.onTriggerChange),u=s.useRef(!1),p=s.useRef(!1),T=s.useCallback(()=>u.current=!1,[]);return s.useEffect(()=>()=>document.removeEventListener("pointerup",T),[T]),e.jsx(rt,{asChild:!0,...c,children:e.jsx(at.button,{"aria-describedby":i.open?i.contentId:void 0,"data-state":i.stateAttribute,...n,ref:a,onPointerMove:I(t.onPointerMove,h=>{h.pointerType!=="touch"&&!p.current&&!l.isPointerInTransitRef.current&&(i.onTriggerEnter(),p.current=!0)}),onPointerLeave:I(t.onPointerLeave,()=>{i.onTriggerLeave(),p.current=!1}),onPointerDown:I(t.onPointerDown,()=>{i.open&&i.onClose(),u.current=!0,document.addEventListener("pointerup",T,{once:!0})}),onFocus:I(t.onFocus,()=>{u.current||i.onOpen()}),onBlur:I(t.onBlur,i.onClose),onClick:I(t.onClick,i.onClose)})})});Fe.displayName=G;var F="TooltipPortal",[ft,gt]=H(F,{forceMount:void 0}),$e=t=>{const{__scopeTooltip:r,forceMount:o,children:n,container:i}=t,l=M(F,r);return e.jsx(ft,{scope:r,forceMount:o,children:e.jsx(Me,{present:o||l.open,children:e.jsx(Ze,{asChild:!0,container:i,children:n})})})};$e.displayName=F;var S="TooltipContent",Ue=s.forwardRef((t,r)=>{const o=gt(S,t.__scopeTooltip),{forceMount:n=o.forceMount,side:i="top",...l}=t,c=M(S,t.__scopeTooltip);return e.jsx(Me,{present:n||c.open,children:c.disableHoverableContent?e.jsx(We,{side:i,...l,ref:r}):e.jsx(xt,{side:i,...l,ref:r})})}),xt=s.forwardRef((t,r)=>{const o=M(S,t.__scopeTooltip),n=q(S,t.__scopeTooltip),i=s.useRef(null),l=Le(r,i),[c,m]=s.useState(null),{trigger:a,onClose:u}=o,p=i.current,{onPointerInTransitChange:T}=n,h=s.useCallback(()=>{m(null),T(!1)},[T]),d=s.useCallback((C,y)=>{const v=C.currentTarget,b={x:C.clientX,y:C.clientY},w=jt(b,v.getBoundingClientRect()),k=wt(b,w),D=bt(y.getBoundingClientRect()),L=Pt([...k,...D]);m(L),T(!0)},[T]);return s.useEffect(()=>()=>h(),[h]),s.useEffect(()=>{if(a&&p){const C=v=>d(v,p),y=v=>d(v,a);return a.addEventListener("pointerleave",C),p.addEventListener("pointerleave",y),()=>{a.removeEventListener("pointerleave",C),p.removeEventListener("pointerleave",y)}}},[a,p,d,h]),s.useEffect(()=>{if(c){const C=y=>{const v=y.target,b={x:y.clientX,y:y.clientY},w=(a==null?void 0:a.contains(v))||(p==null?void 0:p.contains(v)),k=!Nt(b,c);w?h():k&&(h(),u())};return document.addEventListener("pointermove",C),()=>document.removeEventListener("pointermove",C)}},[a,p,c,u,h]),e.jsx(We,{...t,ref:l})}),[Ct,vt]=H(A,{isInside:!1}),yt=Je("TooltipContent"),We=s.forwardRef((t,r)=>{const{__scopeTooltip:o,children:n,"aria-label":i,onEscapeKeyDown:l,onPointerDownOutside:c,...m}=t,a=M(S,o),u=z(o),{onClose:p}=a;return s.useEffect(()=>(document.addEventListener(V,p),()=>document.removeEventListener(V,p)),[p]),s.useEffect(()=>{if(a.trigger){const T=h=>{const d=h.target;d!=null&&d.contains(a.trigger)&&p()};return window.addEventListener("scroll",T,{capture:!0}),()=>window.removeEventListener("scroll",T,{capture:!0})}},[a.trigger,p]),e.jsx(et,{asChild:!0,disableOutsidePointerEvents:!1,onEscapeKeyDown:l,onPointerDownOutside:c,onFocusOutside:T=>T.preventDefault(),onDismiss:p,children:e.jsxs(it,{"data-state":a.stateAttribute,...u,...m,ref:r,style:{...m.style,"--radix-tooltip-content-transform-origin":"var(--radix-popper-transform-origin)","--radix-tooltip-content-available-width":"var(--radix-popper-available-width)","--radix-tooltip-content-available-height":"var(--radix-popper-available-height)","--radix-tooltip-trigger-width":"var(--radix-popper-anchor-width)","--radix-tooltip-trigger-height":"var(--radix-popper-anchor-height)"},children:[e.jsx(yt,{children:n}),e.jsx(Ct,{scope:o,isInside:!0,children:e.jsx(st,{id:a.contentId,role:"tooltip",children:i||n})})]})})});Ue.displayName=S;var Ye="TooltipArrow",Xe=s.forwardRef((t,r)=>{const{__scopeTooltip:o,...n}=t,i=z(o);return vt(Ye,o).isInside?null:e.jsx(nt,{...i,...n,ref:r})});Xe.displayName=Ye;function jt(t,r){const o=Math.abs(r.top-t.y),n=Math.abs(r.bottom-t.y),i=Math.abs(r.right-t.x),l=Math.abs(r.left-t.x);switch(Math.min(o,n,i,l)){case l:return"left";case i:return"right";case o:return"top";case n:return"bottom";default:throw new Error("unreachable")}}function wt(t,r,o=5){const n=[];switch(r){case"top":n.push({x:t.x-o,y:t.y+o},{x:t.x+o,y:t.y+o});break;case"bottom":n.push({x:t.x-o,y:t.y-o},{x:t.x+o,y:t.y-o});break;case"left":n.push({x:t.x+o,y:t.y-o},{x:t.x+o,y:t.y+o});break;case"right":n.push({x:t.x-o,y:t.y-o},{x:t.x-o,y:t.y+o});break}return n}function bt(t){const{top:r,right:o,bottom:n,left:i}=t;return[{x:i,y:r},{x:o,y:r},{x:o,y:n},{x:i,y:n}]}function Nt(t,r){const{x:o,y:n}=t;let i=!1;for(let l=0,c=r.length-1;l<r.length;c=l++){const m=r[l],a=r[c],u=m.x,p=m.y,T=a.x,h=a.y;p>n!=h>n&&o<(T-u)*(n-p)/(h-p)+u&&(i=!i)}return i}function Pt(t){const r=t.slice();return r.sort((o,n)=>o.x<n.x?-1:o.x>n.x?1:o.y<n.y?-1:o.y>n.y?1:0),_t(r)}function _t(t){if(t.length<=1)return t.slice();const r=[];for(let n=0;n<t.length;n++){const i=t[n];for(;r.length>=2;){const l=r[r.length-1],c=r[r.length-2];if((l.x-c.x)*(i.y-c.y)>=(l.y-c.y)*(i.x-c.x))r.pop();else break}r.push(i)}r.pop();const o=[];for(let n=t.length-1;n>=0;n--){const i=t[n];for(;o.length>=2;){const l=o[o.length-1],c=o[o.length-2];if((l.x-c.x)*(i.y-c.y)>=(l.y-c.y)*(i.x-c.x))o.pop();else break}o.push(i)}return o.pop(),r.length===1&&o.length===1&&r[0].x===o[0].x&&r[0].y===o[0].y?r:r.concat(o)}var Bt=Ge,Et=qe,Rt=Fe,Ot=$e,It=Ue,St=Xe;function $({delayDuration:t=0,...r}){return e.jsx(Bt,{"data-slot":"tooltip-provider",delayDuration:t,...r})}function f({...t}){return e.jsx($,{children:e.jsx(Et,{"data-slot":"tooltip",...t})})}function g({...t}){return e.jsx(Rt,{"data-slot":"tooltip-trigger",...t})}function x({className:t,sideOffset:r=0,children:o,...n}){return e.jsx(Ot,{children:e.jsxs(It,{"data-slot":"tooltip-content",sideOffset:r,className:lt("bg-primary text-primary-foreground animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 w-fit origin-(--radix-tooltip-content-transform-origin) rounded-md px-3 py-1.5 text-xs text-balance",t),...n,children:[o,e.jsx(St,{className:"bg-primary fill-primary z-50 size-2.5 translate-y-[calc(-50%_-_2px)] rotate-45 rounded-[2px]"})]})})}f.__docgenInfo={description:"",methods:[],displayName:"Tooltip"};g.__docgenInfo={description:"",methods:[],displayName:"TooltipTrigger"};x.__docgenInfo={description:"",methods:[],displayName:"TooltipContent",props:{sideOffset:{defaultValue:{value:"0",computed:!1},required:!1}}};$.__docgenInfo={description:"",methods:[],displayName:"TooltipProvider",props:{delayDuration:{defaultValue:{value:"0",computed:!1},required:!1}}};f.__docgenInfo={description:"",methods:[],displayName:"Tooltip"};g.__docgenInfo={description:"",methods:[],displayName:"TooltipTrigger"};x.__docgenInfo={description:"",methods:[],displayName:"TooltipContent",props:{sideOffset:{defaultValue:{value:"0",computed:!1},required:!1}}};$.__docgenInfo={description:"",methods:[],displayName:"TooltipProvider",props:{delayDuration:{defaultValue:{value:"0",computed:!1},required:!1}}};const eo={title:"UI/Tooltip",component:f,parameters:{layout:"centered"},tags:["autodocs"]},N={render:()=>e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Hover me"})}),e.jsx(x,{children:e.jsx("p",{children:"This is a tooltip"})})]})},P={render:()=>e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"ghost",size:"icon",children:e.jsx(He,{className:"h-4 w-4"})})}),e.jsx(x,{children:e.jsx("p",{children:"Click for more information"})})]}),parameters:{docs:{description:{story:"Tooltip on an icon button."}}}},_={render:()=>e.jsxs("div",{className:"flex flex-col items-center gap-16",children:[e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Top"})}),e.jsx(x,{side:"top",children:e.jsx("p",{children:"Tooltip on top"})})]}),e.jsxs("div",{className:"flex gap-16",children:[e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Left"})}),e.jsx(x,{side:"left",children:e.jsx("p",{children:"Tooltip on left"})})]}),e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Right"})}),e.jsx(x,{side:"right",children:e.jsx("p",{children:"Tooltip on right"})})]})]}),e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Bottom"})}),e.jsx(x,{side:"bottom",children:e.jsx("p",{children:"Tooltip on bottom"})})]})]}),parameters:{docs:{description:{story:"Tooltips can be positioned on all four sides."}}}},B={render:()=>e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Hover for details"})}),e.jsx(x,{className:"max-w-xs",children:e.jsx("p",{children:"This tooltip contains longer content that wraps to multiple lines. The max-width ensures it doesn't become too wide and remains readable."})})]}),parameters:{docs:{description:{story:"Tooltip with longer content that wraps to multiple lines."}}}},E={render:()=>e.jsxs("p",{className:"text-sm",children:["This is some text with a"," ",e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx("span",{className:"underline decoration-dotted cursor-help",children:"technical term"})}),e.jsx(x,{children:e.jsx("p",{children:"A detailed explanation of the technical term"})})]})," ","that needs explanation."]}),parameters:{docs:{description:{story:"Tooltip on inline text with dotted underline."}}}},R={render:()=>e.jsxs("div",{className:"flex gap-4",children:[e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"ghost",size:"icon",children:e.jsx(pt,{className:"h-4 w-4"})})}),e.jsx(x,{children:e.jsx("p",{children:"Get help"})})]}),e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"ghost",size:"icon",children:e.jsx(ut,{className:"h-4 w-4"})})}),e.jsx(x,{children:e.jsx("p",{children:"Open settings"})})]}),e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"ghost",size:"icon",children:e.jsx(He,{className:"h-4 w-4"})})}),e.jsx(x,{children:e.jsx("p",{children:"View information"})})]})]}),parameters:{docs:{description:{story:"Multiple tooltips on different elements."}}}},O={render:()=>e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Custom offset"})}),e.jsx(x,{sideOffset:10,children:e.jsx("p",{children:"This tooltip has a custom offset of 10px"})})]}),parameters:{docs:{description:{story:"Tooltip with custom sideOffset to control distance from trigger."}}}};var Y,X,K;N.parameters={...N.parameters,docs:{...(Y=N.parameters)==null?void 0:Y.docs,source:{originalSource:`{
  render: () => <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Hover me</Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>This is a tooltip</p>
      </TooltipContent>
    </Tooltip>
}`,...(K=(X=N.parameters)==null?void 0:X.docs)==null?void 0:K.source}}};var J,Q,Z;P.parameters={...P.parameters,docs:{...(J=P.parameters)==null?void 0:J.docs,source:{originalSource:`{
  render: () => <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost" size="icon">
          <Info className="h-4 w-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Click for more information</p>
      </TooltipContent>
    </Tooltip>,
  parameters: {
    docs: {
      description: {
        story: 'Tooltip on an icon button.'
      }
    }
  }
}`,...(Z=(Q=P.parameters)==null?void 0:Q.docs)==null?void 0:Z.source}}};var ee,te,oe;_.parameters={..._.parameters,docs:{...(ee=_.parameters)==null?void 0:ee.docs,source:{originalSource:`{
  render: () => <div className="flex flex-col items-center gap-16">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Top</Button>
        </TooltipTrigger>
        <TooltipContent side="top">
          <p>Tooltip on top</p>
        </TooltipContent>
      </Tooltip>
      
      <div className="flex gap-16">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline">Left</Button>
          </TooltipTrigger>
          <TooltipContent side="left">
            <p>Tooltip on left</p>
          </TooltipContent>
        </Tooltip>
        
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline">Right</Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>Tooltip on right</p>
          </TooltipContent>
        </Tooltip>
      </div>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Bottom</Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>Tooltip on bottom</p>
        </TooltipContent>
      </Tooltip>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Tooltips can be positioned on all four sides.'
      }
    }
  }
}`,...(oe=(te=_.parameters)==null?void 0:te.docs)==null?void 0:oe.source}}};var re,ne,ie;B.parameters={...B.parameters,docs:{...(re=B.parameters)==null?void 0:re.docs,source:{originalSource:`{
  render: () => <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Hover for details</Button>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs">
        <p>
          This tooltip contains longer content that wraps to multiple lines. 
          The max-width ensures it doesn't become too wide and remains readable.
        </p>
      </TooltipContent>
    </Tooltip>,
  parameters: {
    docs: {
      description: {
        story: 'Tooltip with longer content that wraps to multiple lines.'
      }
    }
  }
}`,...(ie=(ne=B.parameters)==null?void 0:ne.docs)==null?void 0:ie.source}}};var se,ae,le;E.parameters={...E.parameters,docs:{...(se=E.parameters)==null?void 0:se.docs,source:{originalSource:`{
  render: () => <p className="text-sm">
      This is some text with a{' '}
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="underline decoration-dotted cursor-help">technical term</span>
        </TooltipTrigger>
        <TooltipContent>
          <p>A detailed explanation of the technical term</p>
        </TooltipContent>
      </Tooltip>
      {' '}that needs explanation.
    </p>,
  parameters: {
    docs: {
      description: {
        story: 'Tooltip on inline text with dotted underline.'
      }
    }
  }
}`,...(le=(ae=E.parameters)==null?void 0:ae.docs)==null?void 0:le.source}}};var ce,pe,de;R.parameters={...R.parameters,docs:{...(ce=R.parameters)==null?void 0:ce.docs,source:{originalSource:`{
  render: () => <div className="flex gap-4">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon">
            <HelpCircle className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>Get help</p>
        </TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>Open settings</p>
        </TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon">
            <Info className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>View information</p>
        </TooltipContent>
      </Tooltip>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple tooltips on different elements.'
      }
    }
  }
}`,...(de=(pe=R.parameters)==null?void 0:pe.docs)==null?void 0:de.source}}};var ue,Te,me;O.parameters={...O.parameters,docs:{...(ue=O.parameters)==null?void 0:ue.docs,source:{originalSource:`{
  render: () => <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Custom offset</Button>
      </TooltipTrigger>
      <TooltipContent sideOffset={10}>
        <p>This tooltip has a custom offset of 10px</p>
      </TooltipContent>
    </Tooltip>,
  parameters: {
    docs: {
      description: {
        story: 'Tooltip with custom sideOffset to control distance from trigger.'
      }
    }
  }
}`,...(me=(Te=O.parameters)==null?void 0:Te.docs)==null?void 0:me.source}}};var he,fe,ge;N.parameters={...N.parameters,docs:{...(he=N.parameters)==null?void 0:he.docs,source:{originalSource:`{
  render: () => <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Hover me</Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>This is a tooltip</p>
      </TooltipContent>
    </Tooltip>
}`,...(ge=(fe=N.parameters)==null?void 0:fe.docs)==null?void 0:ge.source}}};var xe,Ce,ve;P.parameters={...P.parameters,docs:{...(xe=P.parameters)==null?void 0:xe.docs,source:{originalSource:`{
  render: () => <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost" size="icon">
          <Info className="h-4 w-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Click for more information</p>
      </TooltipContent>
    </Tooltip>,
  parameters: {
    docs: {
      description: {
        story: 'Tooltip on an icon button.'
      }
    }
  }
}`,...(ve=(Ce=P.parameters)==null?void 0:Ce.docs)==null?void 0:ve.source}}};var ye,je,we;_.parameters={..._.parameters,docs:{...(ye=_.parameters)==null?void 0:ye.docs,source:{originalSource:`{
  render: () => <div className="flex flex-col items-center gap-16">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Top</Button>
        </TooltipTrigger>
        <TooltipContent side="top">
          <p>Tooltip on top</p>
        </TooltipContent>
      </Tooltip>
      
      <div className="flex gap-16">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline">Left</Button>
          </TooltipTrigger>
          <TooltipContent side="left">
            <p>Tooltip on left</p>
          </TooltipContent>
        </Tooltip>
        
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline">Right</Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>Tooltip on right</p>
          </TooltipContent>
        </Tooltip>
      </div>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Bottom</Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>Tooltip on bottom</p>
        </TooltipContent>
      </Tooltip>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Tooltips can be positioned on all four sides.'
      }
    }
  }
}`,...(we=(je=_.parameters)==null?void 0:je.docs)==null?void 0:we.source}}};var be,Ne,Pe;B.parameters={...B.parameters,docs:{...(be=B.parameters)==null?void 0:be.docs,source:{originalSource:`{
  render: () => <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Hover for details</Button>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs">
        <p>
          This tooltip contains longer content that wraps to multiple lines. 
          The max-width ensures it doesn't become too wide and remains readable.
        </p>
      </TooltipContent>
    </Tooltip>,
  parameters: {
    docs: {
      description: {
        story: 'Tooltip with longer content that wraps to multiple lines.'
      }
    }
  }
}`,...(Pe=(Ne=B.parameters)==null?void 0:Ne.docs)==null?void 0:Pe.source}}};var _e,Be,Ee;E.parameters={...E.parameters,docs:{...(_e=E.parameters)==null?void 0:_e.docs,source:{originalSource:`{
  render: () => <p className="text-sm">
      This is some text with a{' '}
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="underline decoration-dotted cursor-help">technical term</span>
        </TooltipTrigger>
        <TooltipContent>
          <p>A detailed explanation of the technical term</p>
        </TooltipContent>
      </Tooltip>
      {' '}that needs explanation.
    </p>,
  parameters: {
    docs: {
      description: {
        story: 'Tooltip on inline text with dotted underline.'
      }
    }
  }
}`,...(Ee=(Be=E.parameters)==null?void 0:Be.docs)==null?void 0:Ee.source}}};var Re,Oe,Ie;R.parameters={...R.parameters,docs:{...(Re=R.parameters)==null?void 0:Re.docs,source:{originalSource:`{
  render: () => <div className="flex gap-4">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon">
            <HelpCircle className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>Get help</p>
        </TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>Open settings</p>
        </TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon">
            <Info className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>View information</p>
        </TooltipContent>
      </Tooltip>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple tooltips on different elements.'
      }
    }
  }
}`,...(Ie=(Oe=R.parameters)==null?void 0:Oe.docs)==null?void 0:Ie.source}}};var Se,ke,De;O.parameters={...O.parameters,docs:{...(Se=O.parameters)==null?void 0:Se.docs,source:{originalSource:`{
  render: () => <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Custom offset</Button>
      </TooltipTrigger>
      <TooltipContent sideOffset={10}>
        <p>This tooltip has a custom offset of 10px</p>
      </TooltipContent>
    </Tooltip>,
  parameters: {
    docs: {
      description: {
        story: 'Tooltip with custom sideOffset to control distance from trigger.'
      }
    }
  }
}`,...(De=(ke=O.parameters)==null?void 0:ke.docs)==null?void 0:De.source}}};const to=["Default","WithIcon","Positions","LongContent","OnText","MultipleTooltips","CustomOffset"];export{O as CustomOffset,N as Default,B as LongContent,R as MultipleTooltips,E as OnText,_ as Positions,P as WithIcon,to as __namedExportsOrder,eo as default};
