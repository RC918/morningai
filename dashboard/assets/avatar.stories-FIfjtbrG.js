import{j as a}from"./jsx-runtime-D_zvdyIk.js";import{r as y}from"./storybook-vendor-CPzy2iGn.js";import{c as Ea,u as C}from"./index-CfloHgh8.js";import{u as Ua}from"./index-DCVD7z6x.js";import{P as E}from"./index-DRUeUdNs.js";import{r as _a}from"./react-vendor-Bzgz95E1.js";import{c as U}from"./utils-D-KgF5mV.js";import"./index-CAPShSkS.js";import"./index-CXs_xfTS.js";var R={exports:{}},L={};/**
 * @license React
 * use-sync-external-store-shim.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var z;function za(){if(z)return L;z=1;var e=_a();function r(o,n){return o===n&&(o!==0||1/o===1/n)||o!==o&&n!==n}var d=typeof Object.is=="function"?Object.is:r,i=e.useState,v=e.useEffect,t=e.useLayoutEffect,F=e.useDebugValue;function m(o,n){var S=n(),w=i({inst:{value:S,getSnapshot:n}}),u=w[0].inst,I=w[1];return t(function(){u.value=S,u.getSnapshot=n,p(u)&&I({inst:u})},[o,S,n]),v(function(){return p(u)&&I({inst:u}),o(function(){p(u)&&I({inst:u})})},[o]),F(S),S}function p(o){var n=o.getSnapshot;o=o.value;try{var S=n();return!d(o,S)}catch{return!0}}function N(o,n){return n()}var j=typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"?N:m;return L.useSyncExternalStore=e.useSyncExternalStore!==void 0?e.useSyncExternalStore:j,L}var M;function Ma(){return M||(M=1,R.exports=za()),R.exports}var Da=Ma();function Ga(){return Da.useSyncExternalStore(Pa,()=>!0,()=>!1)}function Pa(){return()=>{}}var _="Avatar",[Ta]=Ea(_),[Wa,ja]=Ta(_),wa=y.forwardRef((e,r)=>{const{__scopeAvatar:d,...i}=e,[v,t]=y.useState("idle");return a.jsx(Wa,{scope:d,imageLoadingStatus:v,onImageLoadingStatusChange:t,children:a.jsx(E.span,{...i,ref:r})})});wa.displayName=_;var Ia="AvatarImage",Ra=y.forwardRef((e,r)=>{const{__scopeAvatar:d,src:i,onLoadingStatusChange:v=()=>{},...t}=e,F=ja(Ia,d),m=Ba(i,t),p=Ua(N=>{v(N),F.onImageLoadingStatusChange(N)});return C(()=>{m!=="idle"&&p(m)},[m,p]),m==="loaded"?a.jsx(E.img,{...t,ref:r,src:i}):null});Ra.displayName=Ia;var La="AvatarFallback",Ca=y.forwardRef((e,r)=>{const{__scopeAvatar:d,delayMs:i,...v}=e,t=ja(La,d),[F,m]=y.useState(i===void 0);return y.useEffect(()=>{if(i!==void 0){const p=window.setTimeout(()=>m(!0),i);return()=>window.clearTimeout(p)}},[i]),F&&t.imageLoadingStatus!=="loaded"?a.jsx(E.span,{...v,ref:r}):null});Ca.displayName=La;function D(e,r){return e?r?(e.src!==r&&(e.src=r),e.complete&&e.naturalWidth>0?"loaded":"loading"):"error":"idle"}function Ba(e,{referrerPolicy:r,crossOrigin:d}){const i=Ga(),v=y.useRef(null),t=i?(v.current||(v.current=new window.Image),v.current):null,[F,m]=y.useState(()=>D(t,e));return C(()=>{m(D(t,e))},[t,e]),C(()=>{const p=o=>()=>{m(o)};if(!t)return;const N=p("loaded"),j=p("error");return t.addEventListener("load",N),t.addEventListener("error",j),r&&(t.referrerPolicy=r),typeof d=="string"&&(t.crossOrigin=d),()=>{t.removeEventListener("load",N),t.removeEventListener("error",j)}},[t,d,r]),F}var qa=wa,Xa=Ra,$a=Ca;function s({className:e,...r}){return a.jsx(qa,{"data-slot":"avatar",className:U("relative flex size-8 shrink-0 overflow-hidden rounded-full",e),...r})}function l({className:e,...r}){return a.jsx(Xa,{"data-slot":"avatar-image",className:U("aspect-square size-full",e),...r})}function c({className:e,...r}){return a.jsx($a,{"data-slot":"avatar-fallback",className:U("bg-muted flex size-full items-center justify-center rounded-full",e),...r})}s.__docgenInfo={description:"",methods:[],displayName:"Avatar"};l.__docgenInfo={description:"",methods:[],displayName:"AvatarImage"};c.__docgenInfo={description:"",methods:[],displayName:"AvatarFallback"};s.__docgenInfo={description:"",methods:[],displayName:"Avatar"};l.__docgenInfo={description:"",methods:[],displayName:"AvatarImage"};c.__docgenInfo={description:"",methods:[],displayName:"AvatarFallback"};const ee={title:"UI/Avatar",component:s,parameters:{layout:"centered"},tags:["autodocs"]},A={render:()=>a.jsxs(s,{children:[a.jsx(l,{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan",alt:"Ryan Chen"}),a.jsx(c,{children:"RC"})]})},g={render:()=>a.jsxs(s,{children:[a.jsx(l,{src:"/invalid-image.jpg",alt:"User"}),a.jsx(c,{children:"JD"})]}),parameters:{docs:{description:{story:"When the image fails to load, the fallback text is displayed."}}}},b={render:()=>a.jsx(s,{children:a.jsx(c,{children:"AB"})}),parameters:{docs:{description:{story:"Avatar with only fallback text, no image source."}}}},x={render:()=>a.jsxs("div",{className:"flex items-center gap-4",children:[a.jsxs(s,{className:"size-8",children:[a.jsx(l,{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=Small"}),a.jsx(c,{children:"SM"})]}),a.jsxs(s,{className:"size-12",children:[a.jsx(l,{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=Medium"}),a.jsx(c,{children:"MD"})]}),a.jsxs(s,{className:"size-16",children:[a.jsx(l,{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=Large"}),a.jsx(c,{children:"LG"})]}),a.jsxs(s,{className:"size-24",children:[a.jsx(l,{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=XLarge"}),a.jsx(c,{children:"XL"})]})]}),parameters:{docs:{description:{story:"Avatars in different sizes using Tailwind size utilities."}}}},h={render:()=>a.jsxs("div",{className:"flex items-center gap-4",children:[a.jsx(s,{children:a.jsx(c,{className:"bg-blue-100 text-blue-600",children:"BL"})}),a.jsx(s,{children:a.jsx(c,{className:"bg-green-100 text-green-600",children:"GR"})}),a.jsx(s,{children:a.jsx(c,{className:"bg-purple-100 text-purple-600",children:"PU"})}),a.jsx(s,{children:a.jsx(c,{className:"bg-red-100 text-red-600",children:"RD"})})]}),parameters:{docs:{description:{story:"Avatars with custom background and text colors."}}}},f={render:()=>a.jsxs("div",{className:"flex -space-x-4",children:[a.jsxs(s,{className:"border-2 border-white",children:[a.jsx(l,{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=User1"}),a.jsx(c,{children:"U1"})]}),a.jsxs(s,{className:"border-2 border-white",children:[a.jsx(l,{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=User2"}),a.jsx(c,{children:"U2"})]}),a.jsxs(s,{className:"border-2 border-white",children:[a.jsx(l,{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=User3"}),a.jsx(c,{children:"U3"})]}),a.jsx(s,{className:"border-2 border-white",children:a.jsx(c,{className:"bg-gray-200 text-gray-600",children:"+5"})})]}),parameters:{docs:{description:{story:"Multiple avatars overlapping to show a group of users."}}}},k={render:()=>a.jsxs("div",{className:"flex items-center gap-3",children:[a.jsxs(s,{children:[a.jsx(l,{src:"https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan"}),a.jsx(c,{children:"RC"})]}),a.jsxs("div",{children:[a.jsx("p",{className:"text-sm font-medium",children:"Ryan Chen"}),a.jsx("p",{className:"text-xs text-muted-foreground",children:"ryan@morningai.com"})]})]}),parameters:{docs:{description:{story:"Avatar combined with user information text."}}}};var G,P,T;A.parameters={...A.parameters,docs:{...(G=A.parameters)==null?void 0:G.docs,source:{originalSource:`{
  render: () => <Avatar>
      <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan" alt="Ryan Chen" />
      <AvatarFallback>RC</AvatarFallback>
    </Avatar>
}`,...(T=(P=A.parameters)==null?void 0:P.docs)==null?void 0:T.source}}};var W,B,q;g.parameters={...g.parameters,docs:{...(W=g.parameters)==null?void 0:W.docs,source:{originalSource:`{
  render: () => <Avatar>
      <AvatarImage src="/invalid-image.jpg" alt="User" />
      <AvatarFallback>JD</AvatarFallback>
    </Avatar>,
  parameters: {
    docs: {
      description: {
        story: 'When the image fails to load, the fallback text is displayed.'
      }
    }
  }
}`,...(q=(B=g.parameters)==null?void 0:B.docs)==null?void 0:q.source}}};var X,$,O;b.parameters={...b.parameters,docs:{...(X=b.parameters)==null?void 0:X.docs,source:{originalSource:`{
  render: () => <Avatar>
      <AvatarFallback>AB</AvatarFallback>
    </Avatar>,
  parameters: {
    docs: {
      description: {
        story: 'Avatar with only fallback text, no image source.'
      }
    }
  }
}`,...(O=($=b.parameters)==null?void 0:$.docs)==null?void 0:O.source}}};var J,V,H;x.parameters={...x.parameters,docs:{...(J=x.parameters)==null?void 0:J.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-4">
      <Avatar className="size-8">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Small" />
        <AvatarFallback>SM</AvatarFallback>
      </Avatar>
      <Avatar className="size-12">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Medium" />
        <AvatarFallback>MD</AvatarFallback>
      </Avatar>
      <Avatar className="size-16">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Large" />
        <AvatarFallback>LG</AvatarFallback>
      </Avatar>
      <Avatar className="size-24">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=XLarge" />
        <AvatarFallback>XL</AvatarFallback>
      </Avatar>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Avatars in different sizes using Tailwind size utilities.'
      }
    }
  }
}`,...(H=(V=x.parameters)==null?void 0:V.docs)==null?void 0:H.source}}};var K,Q,Y;h.parameters={...h.parameters,docs:{...(K=h.parameters)==null?void 0:K.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-4">
      <Avatar>
        <AvatarFallback className="bg-blue-100 text-blue-600">BL</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarFallback className="bg-green-100 text-green-600">GR</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarFallback className="bg-purple-100 text-purple-600">PU</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarFallback className="bg-red-100 text-red-600">RD</AvatarFallback>
      </Avatar>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Avatars with custom background and text colors.'
      }
    }
  }
}`,...(Y=(Q=h.parameters)==null?void 0:Q.docs)==null?void 0:Y.source}}};var Z,aa,ea;f.parameters={...f.parameters,docs:{...(Z=f.parameters)==null?void 0:Z.docs,source:{originalSource:`{
  render: () => <div className="flex -space-x-4">
      <Avatar className="border-2 border-white">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=User1" />
        <AvatarFallback>U1</AvatarFallback>
      </Avatar>
      <Avatar className="border-2 border-white">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=User2" />
        <AvatarFallback>U2</AvatarFallback>
      </Avatar>
      <Avatar className="border-2 border-white">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=User3" />
        <AvatarFallback>U3</AvatarFallback>
      </Avatar>
      <Avatar className="border-2 border-white">
        <AvatarFallback className="bg-gray-200 text-gray-600">+5</AvatarFallback>
      </Avatar>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple avatars overlapping to show a group of users.'
      }
    }
  }
}`,...(ea=(aa=f.parameters)==null?void 0:aa.docs)==null?void 0:ea.source}}};var ra,ta,sa;k.parameters={...k.parameters,docs:{...(ra=k.parameters)==null?void 0:ra.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-3">
      <Avatar>
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan" />
        <AvatarFallback>RC</AvatarFallback>
      </Avatar>
      <div>
        <p className="text-sm font-medium">Ryan Chen</p>
        <p className="text-xs text-muted-foreground">ryan@morningai.com</p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Avatar combined with user information text.'
      }
    }
  }
}`,...(sa=(ta=k.parameters)==null?void 0:ta.docs)==null?void 0:sa.source}}};var ca,oa,ia;A.parameters={...A.parameters,docs:{...(ca=A.parameters)==null?void 0:ca.docs,source:{originalSource:`{
  render: () => <Avatar>
      <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan" alt="Ryan Chen" />
      <AvatarFallback>RC</AvatarFallback>
    </Avatar>
}`,...(ia=(oa=A.parameters)==null?void 0:oa.docs)==null?void 0:ia.source}}};var na,la,da;g.parameters={...g.parameters,docs:{...(na=g.parameters)==null?void 0:na.docs,source:{originalSource:`{
  render: () => <Avatar>
      <AvatarImage src="/invalid-image.jpg" alt="User" />
      <AvatarFallback>JD</AvatarFallback>
    </Avatar>,
  parameters: {
    docs: {
      description: {
        story: 'When the image fails to load, the fallback text is displayed.'
      }
    }
  }
}`,...(da=(la=g.parameters)==null?void 0:la.docs)==null?void 0:da.source}}};var va,ma,pa;b.parameters={...b.parameters,docs:{...(va=b.parameters)==null?void 0:va.docs,source:{originalSource:`{
  render: () => <Avatar>
      <AvatarFallback>AB</AvatarFallback>
    </Avatar>,
  parameters: {
    docs: {
      description: {
        story: 'Avatar with only fallback text, no image source.'
      }
    }
  }
}`,...(pa=(ma=b.parameters)==null?void 0:ma.docs)==null?void 0:pa.source}}};var ua,Aa,ga;x.parameters={...x.parameters,docs:{...(ua=x.parameters)==null?void 0:ua.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-4">
      <Avatar className="size-8">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Small" />
        <AvatarFallback>SM</AvatarFallback>
      </Avatar>
      <Avatar className="size-12">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Medium" />
        <AvatarFallback>MD</AvatarFallback>
      </Avatar>
      <Avatar className="size-16">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Large" />
        <AvatarFallback>LG</AvatarFallback>
      </Avatar>
      <Avatar className="size-24">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=XLarge" />
        <AvatarFallback>XL</AvatarFallback>
      </Avatar>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Avatars in different sizes using Tailwind size utilities.'
      }
    }
  }
}`,...(ga=(Aa=x.parameters)==null?void 0:Aa.docs)==null?void 0:ga.source}}};var ba,xa,ha;h.parameters={...h.parameters,docs:{...(ba=h.parameters)==null?void 0:ba.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-4">
      <Avatar>
        <AvatarFallback className="bg-blue-100 text-blue-600">BL</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarFallback className="bg-green-100 text-green-600">GR</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarFallback className="bg-purple-100 text-purple-600">PU</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarFallback className="bg-red-100 text-red-600">RD</AvatarFallback>
      </Avatar>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Avatars with custom background and text colors.'
      }
    }
  }
}`,...(ha=(xa=h.parameters)==null?void 0:xa.docs)==null?void 0:ha.source}}};var fa,ka,ya;f.parameters={...f.parameters,docs:{...(fa=f.parameters)==null?void 0:fa.docs,source:{originalSource:`{
  render: () => <div className="flex -space-x-4">
      <Avatar className="border-2 border-white">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=User1" />
        <AvatarFallback>U1</AvatarFallback>
      </Avatar>
      <Avatar className="border-2 border-white">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=User2" />
        <AvatarFallback>U2</AvatarFallback>
      </Avatar>
      <Avatar className="border-2 border-white">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=User3" />
        <AvatarFallback>U3</AvatarFallback>
      </Avatar>
      <Avatar className="border-2 border-white">
        <AvatarFallback className="bg-gray-200 text-gray-600">+5</AvatarFallback>
      </Avatar>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple avatars overlapping to show a group of users.'
      }
    }
  }
}`,...(ya=(ka=f.parameters)==null?void 0:ka.docs)==null?void 0:ya.source}}};var Fa,Na,Sa;k.parameters={...k.parameters,docs:{...(Fa=k.parameters)==null?void 0:Fa.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-3">
      <Avatar>
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan" />
        <AvatarFallback>RC</AvatarFallback>
      </Avatar>
      <div>
        <p className="text-sm font-medium">Ryan Chen</p>
        <p className="text-xs text-muted-foreground">ryan@morningai.com</p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Avatar combined with user information text.'
      }
    }
  }
}`,...(Sa=(Na=k.parameters)==null?void 0:Na.docs)==null?void 0:Sa.source}}};const re=["Default","WithFallback","FallbackOnly","CustomSize","CustomColors","AvatarGroup","WithText"];export{f as AvatarGroup,h as CustomColors,x as CustomSize,A as Default,b as FallbackOnly,g as WithFallback,k as WithText,re as __namedExportsOrder,ee as default};
