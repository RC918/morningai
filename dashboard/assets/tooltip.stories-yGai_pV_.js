import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as s}from"./index-Dz3UJJSw.js";import{u as Xe,c as I}from"./index-Bo7lbUv-.js";import{u as ke,a as Ke}from"./index-DRuEWG1E.js";import{c as Je}from"./index-DiKooijE.js";import{P as Qe,D as Ze}from"./index-CevHeI5L.js";import{u as et}from"./index-HmPO_Abe.js";import{c as Ae,R as tt,A as ot,a as rt,C as it,b as nt}from"./index-DxHjUX3g.js";import{P as Me}from"./index-B6CVSQiA.js";import{P as st}from"./index-C7eB__Z-.js";import{c as at}from"./utils-D-KgF5mV.js";import{B as j}from"./button-6x4QkhmZ.js";import{I as He}from"./info-Dd4rymu9.js";import{c as lt}from"./createLucideIcon-ClV4rtrr.js";import{S as pt}from"./settings-BgPMZKHw.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-BwP8QHTI.js";import"./index-CYANIyVc.js";import"./index-fUCaa9pg.js";import"./index-DW9D76JB.js";import"./index-CGrAONsN.js";/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ct=[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["path",{d:"M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3",key:"1u773s"}],["path",{d:"M12 17h.01",key:"p32p05"}]],dt=lt("circle-help",ct);var[H]=Je("Tooltip",[Ae]),z=Ae(),ze="TooltipProvider",ut=700,G="tooltip.open",[Tt,q]=H(ze),Ge=t=>{const{__scopeTooltip:r,delayDuration:o=ut,skipDelayDuration:i=300,disableHoverableContent:n=!1,children:l}=t,p=s.useRef(!0),m=s.useRef(!1),a=s.useRef(0);return s.useEffect(()=>{const u=a.current;return()=>window.clearTimeout(u)},[]),e.jsx(Tt,{scope:r,isOpenDelayedRef:p,delayDuration:o,onOpen:s.useCallback(()=>{window.clearTimeout(a.current),p.current=!1},[]),onClose:s.useCallback(()=>{window.clearTimeout(a.current),a.current=window.setTimeout(()=>p.current=!0,i)},[i]),isPointerInTransitRef:m,onPointerInTransitChange:s.useCallback(u=>{m.current=u},[]),disableHoverableContent:n,children:l})};Ge.displayName=ze;var A="Tooltip",[mt,M]=H(A),Ve=t=>{const{__scopeTooltip:r,children:o,open:i,defaultOpen:n,onOpenChange:l,disableHoverableContent:p,delayDuration:m}=t,a=q(A,t.__scopeTooltip),u=z(r),[c,T]=s.useState(null),h=et(),d=s.useRef(0),C=p??a.disableHoverableContent,y=m??a.delayDuration,v=s.useRef(!1),[b,w]=Xe({prop:i,defaultProp:n??!1,onChange:W=>{W?(a.onOpen(),document.dispatchEvent(new CustomEvent(G))):a.onClose(),l==null||l(W)},caller:A}),D=s.useMemo(()=>b?v.current?"delayed-open":"instant-open":"closed",[b]),L=s.useCallback(()=>{window.clearTimeout(d.current),d.current=0,v.current=!1,w(!0)},[w]),k=s.useCallback(()=>{window.clearTimeout(d.current),d.current=0,w(!1)},[w]),U=s.useCallback(()=>{window.clearTimeout(d.current),d.current=window.setTimeout(()=>{v.current=!0,w(!0),d.current=0},y)},[y,w]);return s.useEffect(()=>()=>{d.current&&(window.clearTimeout(d.current),d.current=0)},[]),e.jsx(tt,{...u,children:e.jsx(mt,{scope:r,contentId:h,open:b,stateAttribute:D,trigger:c,onTriggerChange:T,onTriggerEnter:s.useCallback(()=>{a.isOpenDelayedRef.current?U():L()},[a.isOpenDelayedRef,U,L]),onTriggerLeave:s.useCallback(()=>{C?k():(window.clearTimeout(d.current),d.current=0)},[k,C]),onOpen:L,onClose:k,disableHoverableContent:C,children:o})})};Ve.displayName=A;var V="TooltipTrigger",qe=s.forwardRef((t,r)=>{const{__scopeTooltip:o,...i}=t,n=M(V,o),l=q(V,o),p=z(o),m=s.useRef(null),a=ke(r,m,n.onTriggerChange),u=s.useRef(!1),c=s.useRef(!1),T=s.useCallback(()=>u.current=!1,[]);return s.useEffect(()=>()=>document.removeEventListener("pointerup",T),[T]),e.jsx(ot,{asChild:!0,...p,children:e.jsx(st.button,{"aria-describedby":n.open?n.contentId:void 0,"data-state":n.stateAttribute,...i,ref:a,onPointerMove:I(t.onPointerMove,h=>{h.pointerType!=="touch"&&!c.current&&!l.isPointerInTransitRef.current&&(n.onTriggerEnter(),c.current=!0)}),onPointerLeave:I(t.onPointerLeave,()=>{n.onTriggerLeave(),c.current=!1}),onPointerDown:I(t.onPointerDown,()=>{n.open&&n.onClose(),u.current=!0,document.addEventListener("pointerup",T,{once:!0})}),onFocus:I(t.onFocus,()=>{u.current||n.onOpen()}),onBlur:I(t.onBlur,n.onClose),onClick:I(t.onClick,n.onClose)})})});qe.displayName=V;var F="TooltipPortal",[ht,ft]=H(F,{forceMount:void 0}),Fe=t=>{const{__scopeTooltip:r,forceMount:o,children:i,container:n}=t,l=M(F,r);return e.jsx(ht,{scope:r,forceMount:o,children:e.jsx(Me,{present:o||l.open,children:e.jsx(Qe,{asChild:!0,container:n,children:i})})})};Fe.displayName=F;var S="TooltipContent",$e=s.forwardRef((t,r)=>{const o=ft(S,t.__scopeTooltip),{forceMount:i=o.forceMount,side:n="top",...l}=t,p=M(S,t.__scopeTooltip);return e.jsx(Me,{present:i||p.open,children:p.disableHoverableContent?e.jsx(Ue,{side:n,...l,ref:r}):e.jsx(gt,{side:n,...l,ref:r})})}),gt=s.forwardRef((t,r)=>{const o=M(S,t.__scopeTooltip),i=q(S,t.__scopeTooltip),n=s.useRef(null),l=ke(r,n),[p,m]=s.useState(null),{trigger:a,onClose:u}=o,c=n.current,{onPointerInTransitChange:T}=i,h=s.useCallback(()=>{m(null),T(!1)},[T]),d=s.useCallback((C,y)=>{const v=C.currentTarget,b={x:C.clientX,y:C.clientY},w=yt(b,v.getBoundingClientRect()),D=jt(b,w),L=wt(y.getBoundingClientRect()),k=Nt([...D,...L]);m(k),T(!0)},[T]);return s.useEffect(()=>()=>h(),[h]),s.useEffect(()=>{if(a&&c){const C=v=>d(v,c),y=v=>d(v,a);return a.addEventListener("pointerleave",C),c.addEventListener("pointerleave",y),()=>{a.removeEventListener("pointerleave",C),c.removeEventListener("pointerleave",y)}}},[a,c,d,h]),s.useEffect(()=>{if(p){const C=y=>{const v=y.target,b={x:y.clientX,y:y.clientY},w=(a==null?void 0:a.contains(v))||(c==null?void 0:c.contains(v)),D=!bt(b,p);w?h():D&&(h(),u())};return document.addEventListener("pointermove",C),()=>document.removeEventListener("pointermove",C)}},[a,c,p,u,h]),e.jsx(Ue,{...t,ref:l})}),[xt,Ct]=H(A,{isInside:!1}),vt=Ke("TooltipContent"),Ue=s.forwardRef((t,r)=>{const{__scopeTooltip:o,children:i,"aria-label":n,onEscapeKeyDown:l,onPointerDownOutside:p,...m}=t,a=M(S,o),u=z(o),{onClose:c}=a;return s.useEffect(()=>(document.addEventListener(G,c),()=>document.removeEventListener(G,c)),[c]),s.useEffect(()=>{if(a.trigger){const T=h=>{const d=h.target;d!=null&&d.contains(a.trigger)&&c()};return window.addEventListener("scroll",T,{capture:!0}),()=>window.removeEventListener("scroll",T,{capture:!0})}},[a.trigger,c]),e.jsx(Ze,{asChild:!0,disableOutsidePointerEvents:!1,onEscapeKeyDown:l,onPointerDownOutside:p,onFocusOutside:T=>T.preventDefault(),onDismiss:c,children:e.jsxs(it,{"data-state":a.stateAttribute,...u,...m,ref:r,style:{...m.style,"--radix-tooltip-content-transform-origin":"var(--radix-popper-transform-origin)","--radix-tooltip-content-available-width":"var(--radix-popper-available-width)","--radix-tooltip-content-available-height":"var(--radix-popper-available-height)","--radix-tooltip-trigger-width":"var(--radix-popper-anchor-width)","--radix-tooltip-trigger-height":"var(--radix-popper-anchor-height)"},children:[e.jsx(vt,{children:i}),e.jsx(xt,{scope:o,isInside:!0,children:e.jsx(nt,{id:a.contentId,role:"tooltip",children:n||i})})]})})});$e.displayName=S;var We="TooltipArrow",Ye=s.forwardRef((t,r)=>{const{__scopeTooltip:o,...i}=t,n=z(o);return Ct(We,o).isInside?null:e.jsx(rt,{...n,...i,ref:r})});Ye.displayName=We;function yt(t,r){const o=Math.abs(r.top-t.y),i=Math.abs(r.bottom-t.y),n=Math.abs(r.right-t.x),l=Math.abs(r.left-t.x);switch(Math.min(o,i,n,l)){case l:return"left";case n:return"right";case o:return"top";case i:return"bottom";default:throw new Error("unreachable")}}function jt(t,r,o=5){const i=[];switch(r){case"top":i.push({x:t.x-o,y:t.y+o},{x:t.x+o,y:t.y+o});break;case"bottom":i.push({x:t.x-o,y:t.y-o},{x:t.x+o,y:t.y-o});break;case"left":i.push({x:t.x+o,y:t.y-o},{x:t.x+o,y:t.y+o});break;case"right":i.push({x:t.x-o,y:t.y-o},{x:t.x-o,y:t.y+o});break}return i}function wt(t){const{top:r,right:o,bottom:i,left:n}=t;return[{x:n,y:r},{x:o,y:r},{x:o,y:i},{x:n,y:i}]}function bt(t,r){const{x:o,y:i}=t;let n=!1;for(let l=0,p=r.length-1;l<r.length;p=l++){const m=r[l],a=r[p],u=m.x,c=m.y,T=a.x,h=a.y;c>i!=h>i&&o<(T-u)*(i-c)/(h-c)+u&&(n=!n)}return n}function Nt(t){const r=t.slice();return r.sort((o,i)=>o.x<i.x?-1:o.x>i.x?1:o.y<i.y?-1:o.y>i.y?1:0),Pt(r)}function Pt(t){if(t.length<=1)return t.slice();const r=[];for(let i=0;i<t.length;i++){const n=t[i];for(;r.length>=2;){const l=r[r.length-1],p=r[r.length-2];if((l.x-p.x)*(n.y-p.y)>=(l.y-p.y)*(n.x-p.x))r.pop();else break}r.push(n)}r.pop();const o=[];for(let i=t.length-1;i>=0;i--){const n=t[i];for(;o.length>=2;){const l=o[o.length-1],p=o[o.length-2];if((l.x-p.x)*(n.y-p.y)>=(l.y-p.y)*(n.x-p.x))o.pop();else break}o.push(n)}return o.pop(),r.length===1&&o.length===1&&r[0].x===o[0].x&&r[0].y===o[0].y?r:r.concat(o)}var Bt=Ge,_t=Ve,Et=qe,Rt=Fe,Ot=$e,It=Ye;function $({delayDuration:t=0,...r}){return e.jsx(Bt,{"data-slot":"tooltip-provider",delayDuration:t,...r})}function f({...t}){return e.jsx($,{children:e.jsx(_t,{"data-slot":"tooltip",...t})})}function g({...t}){return e.jsx(Et,{"data-slot":"tooltip-trigger",...t})}function x({className:t,sideOffset:r=0,children:o,...i}){return e.jsx(Rt,{children:e.jsxs(Ot,{"data-slot":"tooltip-content",sideOffset:r,className:at("bg-primary text-primary-foreground animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 w-fit origin-(--radix-tooltip-content-transform-origin) rounded-md px-3 py-1.5 text-xs text-balance",t),...i,children:[o,e.jsx(It,{className:"bg-primary fill-primary z-50 size-2.5 translate-y-[calc(-50%_-_2px)] rotate-45 rounded-[2px]"})]})})}f.__docgenInfo={description:"",methods:[],displayName:"Tooltip"};g.__docgenInfo={description:"",methods:[],displayName:"TooltipTrigger"};x.__docgenInfo={description:"",methods:[],displayName:"TooltipContent",props:{sideOffset:{defaultValue:{value:"0",computed:!1},required:!1}}};$.__docgenInfo={description:"",methods:[],displayName:"TooltipProvider",props:{delayDuration:{defaultValue:{value:"0",computed:!1},required:!1}}};f.__docgenInfo={description:"",methods:[],displayName:"Tooltip"};g.__docgenInfo={description:"",methods:[],displayName:"TooltipTrigger"};x.__docgenInfo={description:"",methods:[],displayName:"TooltipContent",props:{sideOffset:{defaultValue:{value:"0",computed:!1},required:!1}}};$.__docgenInfo={description:"",methods:[],displayName:"TooltipProvider",props:{delayDuration:{defaultValue:{value:"0",computed:!1},required:!1}}};const eo={title:"UI/Tooltip",component:f,parameters:{layout:"centered"},tags:["autodocs"]},N={render:()=>e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Hover me"})}),e.jsx(x,{children:e.jsx("p",{children:"This is a tooltip"})})]})},P={render:()=>e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"ghost",size:"icon",children:e.jsx(He,{className:"h-4 w-4"})})}),e.jsx(x,{children:e.jsx("p",{children:"Click for more information"})})]}),parameters:{docs:{description:{story:"Tooltip on an icon button."}}}},B={render:()=>e.jsxs("div",{className:"flex flex-col items-center gap-16",children:[e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Top"})}),e.jsx(x,{side:"top",children:e.jsx("p",{children:"Tooltip on top"})})]}),e.jsxs("div",{className:"flex gap-16",children:[e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Left"})}),e.jsx(x,{side:"left",children:e.jsx("p",{children:"Tooltip on left"})})]}),e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Right"})}),e.jsx(x,{side:"right",children:e.jsx("p",{children:"Tooltip on right"})})]})]}),e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Bottom"})}),e.jsx(x,{side:"bottom",children:e.jsx("p",{children:"Tooltip on bottom"})})]})]}),parameters:{docs:{description:{story:"Tooltips can be positioned on all four sides."}}}},_={render:()=>e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Hover for details"})}),e.jsx(x,{className:"max-w-xs",children:e.jsx("p",{children:"This tooltip contains longer content that wraps to multiple lines. The max-width ensures it doesn't become too wide and remains readable."})})]}),parameters:{docs:{description:{story:"Tooltip with longer content that wraps to multiple lines."}}}},E={render:()=>e.jsxs("p",{className:"text-sm",children:["This is some text with a"," ",e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx("span",{className:"underline decoration-dotted cursor-help",children:"technical term"})}),e.jsx(x,{children:e.jsx("p",{children:"A detailed explanation of the technical term"})})]})," ","that needs explanation."]}),parameters:{docs:{description:{story:"Tooltip on inline text with dotted underline."}}}},R={render:()=>e.jsxs("div",{className:"flex gap-4",children:[e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"ghost",size:"icon",children:e.jsx(dt,{className:"h-4 w-4"})})}),e.jsx(x,{children:e.jsx("p",{children:"Get help"})})]}),e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"ghost",size:"icon",children:e.jsx(pt,{className:"h-4 w-4"})})}),e.jsx(x,{children:e.jsx("p",{children:"Open settings"})})]}),e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"ghost",size:"icon",children:e.jsx(He,{className:"h-4 w-4"})})}),e.jsx(x,{children:e.jsx("p",{children:"View information"})})]})]}),parameters:{docs:{description:{story:"Multiple tooltips on different elements."}}}},O={render:()=>e.jsxs(f,{children:[e.jsx(g,{asChild:!0,children:e.jsx(j,{variant:"outline",children:"Custom offset"})}),e.jsx(x,{sideOffset:10,children:e.jsx("p",{children:"This tooltip has a custom offset of 10px"})})]}),parameters:{docs:{description:{story:"Tooltip with custom sideOffset to control distance from trigger."}}}};var Y,X,K;N.parameters={...N.parameters,docs:{...(Y=N.parameters)==null?void 0:Y.docs,source:{originalSource:`{
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
}`,...(Z=(Q=P.parameters)==null?void 0:Q.docs)==null?void 0:Z.source}}};var ee,te,oe;B.parameters={...B.parameters,docs:{...(ee=B.parameters)==null?void 0:ee.docs,source:{originalSource:`{
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
}`,...(oe=(te=B.parameters)==null?void 0:te.docs)==null?void 0:oe.source}}};var re,ie,ne;_.parameters={..._.parameters,docs:{...(re=_.parameters)==null?void 0:re.docs,source:{originalSource:`{
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
}`,...(ne=(ie=_.parameters)==null?void 0:ie.docs)==null?void 0:ne.source}}};var se,ae,le;E.parameters={...E.parameters,docs:{...(se=E.parameters)==null?void 0:se.docs,source:{originalSource:`{
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
}`,...(le=(ae=E.parameters)==null?void 0:ae.docs)==null?void 0:le.source}}};var pe,ce,de;R.parameters={...R.parameters,docs:{...(pe=R.parameters)==null?void 0:pe.docs,source:{originalSource:`{
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
}`,...(de=(ce=R.parameters)==null?void 0:ce.docs)==null?void 0:de.source}}};var ue,Te,me;O.parameters={...O.parameters,docs:{...(ue=O.parameters)==null?void 0:ue.docs,source:{originalSource:`{
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
}`,...(ve=(Ce=P.parameters)==null?void 0:Ce.docs)==null?void 0:ve.source}}};var ye,je,we;B.parameters={...B.parameters,docs:{...(ye=B.parameters)==null?void 0:ye.docs,source:{originalSource:`{
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
}`,...(we=(je=B.parameters)==null?void 0:je.docs)==null?void 0:we.source}}};var be,Ne,Pe;_.parameters={..._.parameters,docs:{...(be=_.parameters)==null?void 0:be.docs,source:{originalSource:`{
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
}`,...(Pe=(Ne=_.parameters)==null?void 0:Ne.docs)==null?void 0:Pe.source}}};var Be,_e,Ee;E.parameters={...E.parameters,docs:{...(Be=E.parameters)==null?void 0:Be.docs,source:{originalSource:`{
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
}`,...(Ee=(_e=E.parameters)==null?void 0:_e.docs)==null?void 0:Ee.source}}};var Re,Oe,Ie;R.parameters={...R.parameters,docs:{...(Re=R.parameters)==null?void 0:Re.docs,source:{originalSource:`{
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
}`,...(Ie=(Oe=R.parameters)==null?void 0:Oe.docs)==null?void 0:Ie.source}}};var Se,De,Le;O.parameters={...O.parameters,docs:{...(Se=O.parameters)==null?void 0:Se.docs,source:{originalSource:`{
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
}`,...(Le=(De=O.parameters)==null?void 0:De.docs)==null?void 0:Le.source}}};const to=["Default","WithIcon","Positions","LongContent","OnText","MultipleTooltips","CustomOffset"];export{O as CustomOffset,N as Default,_ as LongContent,R as MultipleTooltips,E as OnText,B as Positions,P as WithIcon,to as __namedExportsOrder,eo as default};
