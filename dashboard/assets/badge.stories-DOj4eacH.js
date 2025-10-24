import{j as e}from"./jsx-runtime-D_zvdyIk.js";import"./index-Dz3UJJSw.js";import{S as Be,c as xe}from"./utils-ClSdSIbF.js";import{c as fe}from"./index-CN2Y8dJ9.js";import"./_commonjsHelpers-CqkleIqs.js";const he=fe("inline-flex items-center justify-center rounded-md border px-2 py-0.5 text-xs font-medium w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive transition-[color,box-shadow] overflow-hidden",{variants:{variant:{default:"border-transparent bg-primary text-primary-foreground [a&]:hover:bg-primary/90",secondary:"border-transparent bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/90",destructive:"border-transparent bg-destructive text-white [a&]:hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60",outline:"text-foreground [a&]:hover:bg-accent [a&]:hover:text-accent-foreground"}},defaultVariants:{variant:"default"}});function r({className:ue,variant:ge,asChild:me=!1,...pe}){const ve=me?Be:"span";return e.jsx(ve,{"data-slot":"badge",className:xe(he({variant:ge}),ue),...pe})}r.__docgenInfo={description:"",methods:[],displayName:"Badge",props:{asChild:{defaultValue:{value:"false",computed:!1},required:!1}}};r.__docgenInfo={description:"",methods:[],displayName:"Badge",props:{asChild:{defaultValue:{value:"false",computed:!1},required:!1}}};const ke={title:"UI/Badge",component:r,parameters:{layout:"centered"},tags:["autodocs"],argTypes:{variant:{control:"select",options:["default","secondary","destructive","outline"]}}},a={args:{children:"Badge"}},s={args:{children:"Secondary",variant:"secondary"}},n={args:{children:"Destructive",variant:"destructive"}},t={args:{children:"Outline",variant:"outline"}},c={render:()=>e.jsxs(r,{children:[e.jsx("span",{className:"mr-1",children:"✓"}),"Success"]})},d={render:()=>e.jsxs("div",{className:"flex gap-2",children:[e.jsx(r,{variant:"default",children:"Active"}),e.jsx(r,{variant:"secondary",children:"Pending"}),e.jsx(r,{variant:"destructive",children:"Error"}),e.jsx(r,{variant:"outline",children:"Draft"})]})},o={render:()=>e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(r,{className:"text-xs",children:"Small"}),e.jsx(r,{children:"Medium"}),e.jsx(r,{className:"text-base px-3 py-1",children:"Large"})]})},i={render:()=>e.jsxs("div",{className:"flex gap-2",children:[e.jsx(r,{children:"New 3"}),e.jsx(r,{variant:"destructive",children:"Errors 12"}),e.jsx(r,{variant:"secondary",children:"Pending 5"})]})},l={render:()=>e.jsx(r,{className:"cursor-pointer hover:opacity-80",onClick:()=>alert("Badge clicked!"),children:"Click me"})};var u,g,m;a.parameters={...a.parameters,docs:{...(u=a.parameters)==null?void 0:u.docs,source:{originalSource:`{
  args: {
    children: 'Badge'
  }
}`,...(m=(g=a.parameters)==null?void 0:g.docs)==null?void 0:m.source}}};var p,v,B;s.parameters={...s.parameters,docs:{...(p=s.parameters)==null?void 0:p.docs,source:{originalSource:`{
  args: {
    children: 'Secondary',
    variant: 'secondary'
  }
}`,...(B=(v=s.parameters)==null?void 0:v.docs)==null?void 0:B.source}}};var x,f,h;n.parameters={...n.parameters,docs:{...(x=n.parameters)==null?void 0:x.docs,source:{originalSource:`{
  args: {
    children: 'Destructive',
    variant: 'destructive'
  }
}`,...(h=(f=n.parameters)==null?void 0:f.docs)==null?void 0:h.source}}};var S,y,b;t.parameters={...t.parameters,docs:{...(S=t.parameters)==null?void 0:S.docs,source:{originalSource:`{
  args: {
    children: 'Outline',
    variant: 'outline'
  }
}`,...(b=(y=t.parameters)==null?void 0:y.docs)==null?void 0:b.source}}};var N,j,k;c.parameters={...c.parameters,docs:{...(N=c.parameters)==null?void 0:N.docs,source:{originalSource:`{
  render: () => <Badge>
      <span className="mr-1">✓</span>
      Success
    </Badge>
}`,...(k=(j=c.parameters)==null?void 0:j.docs)==null?void 0:k.source}}};var C,D,w;d.parameters={...d.parameters,docs:{...(C=d.parameters)==null?void 0:C.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge variant="default">Active</Badge>
      <Badge variant="secondary">Pending</Badge>
      <Badge variant="destructive">Error</Badge>
      <Badge variant="outline">Draft</Badge>
    </div>
}`,...(w=(D=d.parameters)==null?void 0:D.docs)==null?void 0:w.source}}};var E,O,P;o.parameters={...o.parameters,docs:{...(E=o.parameters)==null?void 0:E.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-2">
      <Badge className="text-xs">Small</Badge>
      <Badge>Medium</Badge>
      <Badge className="text-base px-3 py-1">Large</Badge>
    </div>
}`,...(P=(O=o.parameters)==null?void 0:O.docs)==null?void 0:P.source}}};var _,I,V;i.parameters={...i.parameters,docs:{...(_=i.parameters)==null?void 0:_.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge>New 3</Badge>
      <Badge variant="destructive">Errors 12</Badge>
      <Badge variant="secondary">Pending 5</Badge>
    </div>
}`,...(V=(I=i.parameters)==null?void 0:I.docs)==null?void 0:V.source}}};var W,z,A;l.parameters={...l.parameters,docs:{...(W=l.parameters)==null?void 0:W.docs,source:{originalSource:`{
  render: () => <Badge className="cursor-pointer hover:opacity-80" onClick={() => alert('Badge clicked!')}>
      Click me
    </Badge>
}`,...(A=(z=l.parameters)==null?void 0:z.docs)==null?void 0:A.source}}};var L,M,q;a.parameters={...a.parameters,docs:{...(L=a.parameters)==null?void 0:L.docs,source:{originalSource:`{
  args: {
    children: 'Badge'
  }
}`,...(q=(M=a.parameters)==null?void 0:M.docs)==null?void 0:q.source}}};var R,T,U;s.parameters={...s.parameters,docs:{...(R=s.parameters)==null?void 0:R.docs,source:{originalSource:`{
  args: {
    children: 'Secondary',
    variant: 'secondary'
  }
}`,...(U=(T=s.parameters)==null?void 0:T.docs)==null?void 0:U.source}}};var F,G,H;n.parameters={...n.parameters,docs:{...(F=n.parameters)==null?void 0:F.docs,source:{originalSource:`{
  args: {
    children: 'Destructive',
    variant: 'destructive'
  }
}`,...(H=(G=n.parameters)==null?void 0:G.docs)==null?void 0:H.source}}};var J,K,Q;t.parameters={...t.parameters,docs:{...(J=t.parameters)==null?void 0:J.docs,source:{originalSource:`{
  args: {
    children: 'Outline',
    variant: 'outline'
  }
}`,...(Q=(K=t.parameters)==null?void 0:K.docs)==null?void 0:Q.source}}};var X,Y,Z;c.parameters={...c.parameters,docs:{...(X=c.parameters)==null?void 0:X.docs,source:{originalSource:`{
  render: () => <Badge>
      <span className="mr-1">✓</span>
      Success
    </Badge>
}`,...(Z=(Y=c.parameters)==null?void 0:Y.docs)==null?void 0:Z.source}}};var $,ee,re;d.parameters={...d.parameters,docs:{...($=d.parameters)==null?void 0:$.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge variant="default">Active</Badge>
      <Badge variant="secondary">Pending</Badge>
      <Badge variant="destructive">Error</Badge>
      <Badge variant="outline">Draft</Badge>
    </div>
}`,...(re=(ee=d.parameters)==null?void 0:ee.docs)==null?void 0:re.source}}};var ae,se,ne;o.parameters={...o.parameters,docs:{...(ae=o.parameters)==null?void 0:ae.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-2">
      <Badge className="text-xs">Small</Badge>
      <Badge>Medium</Badge>
      <Badge className="text-base px-3 py-1">Large</Badge>
    </div>
}`,...(ne=(se=o.parameters)==null?void 0:se.docs)==null?void 0:ne.source}}};var te,ce,de;i.parameters={...i.parameters,docs:{...(te=i.parameters)==null?void 0:te.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge>New 3</Badge>
      <Badge variant="destructive">Errors 12</Badge>
      <Badge variant="secondary">Pending 5</Badge>
    </div>
}`,...(de=(ce=i.parameters)==null?void 0:ce.docs)==null?void 0:de.source}}};var oe,ie,le;l.parameters={...l.parameters,docs:{...(oe=l.parameters)==null?void 0:oe.docs,source:{originalSource:`{
  render: () => <Badge className="cursor-pointer hover:opacity-80" onClick={() => alert('Badge clicked!')}>
      Click me
    </Badge>
}`,...(le=(ie=l.parameters)==null?void 0:ie.docs)==null?void 0:le.source}}};const Ce=["Default","Secondary","Destructive","Outline","WithIcon","StatusBadges","Sizes","WithCount","Clickable"];export{l as Clickable,a as Default,n as Destructive,t as Outline,s as Secondary,o as Sizes,d as StatusBadges,i as WithCount,c as WithIcon,Ce as __namedExportsOrder,ke as default};
