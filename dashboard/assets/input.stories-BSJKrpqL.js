import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{I as r}from"./input-Wn9FKRmr.js";import{L as u}from"./label-CQdBpAJ_.js";import"./index-Dz3UJJSw.js";import"./_commonjsHelpers-CqkleIqs.js";import"./utils-ClSdSIbF.js";import"./index-CWPL_hnH.js";import"./index-CYANIyVc.js";import"./index-fUCaa9pg.js";const _e={title:"UI/Input",component:r,parameters:{layout:"centered"},tags:["autodocs"],argTypes:{type:{control:"select",options:["text","email","password","number","tel","url","search"]},disabled:{control:"boolean"}}},a={args:{placeholder:"Enter text..."}},s={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(u,{htmlFor:"email",children:"Email"}),e.jsx(r,{type:"email",id:"email",placeholder:"Email"})]})},l={args:{defaultValue:"Hello World"}},m={args:{placeholder:"Disabled input",disabled:!0}},t={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(u,{htmlFor:"password",children:"Password"}),e.jsx(r,{type:"password",id:"password",placeholder:"Enter password"})]})},i={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(u,{htmlFor:"email-input",children:"Email"}),e.jsx(r,{type:"email",id:"email-input",placeholder:"name@example.com"})]})},o={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(u,{htmlFor:"number",children:"Number"}),e.jsx(r,{type:"number",id:"number",placeholder:"0"})]})},d={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(u,{htmlFor:"search",children:"Search"}),e.jsx(r,{type:"search",id:"search",placeholder:"Search..."})]})},c={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(u,{htmlFor:"email-helper",children:"Email"}),e.jsx(r,{type:"email",id:"email-helper",placeholder:"Email"}),e.jsx("p",{className:"text-sm text-muted-foreground",children:"We'll never share your email with anyone else."})]})},n={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(u,{htmlFor:"email-error",children:"Email"}),e.jsx(r,{type:"email",id:"email-error",placeholder:"Email",className:"border-red-500"}),e.jsx("p",{className:"text-sm text-red-500",children:"Please enter a valid email address."})]})},p={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(u,{htmlFor:"picture",children:"Picture"}),e.jsx(r,{id:"picture",type:"file"})]})};var h,g,x;a.parameters={...a.parameters,docs:{...(h=a.parameters)==null?void 0:h.docs,source:{originalSource:`{
  args: {
    placeholder: 'Enter text...'
  }
}`,...(x=(g=a.parameters)==null?void 0:g.docs)==null?void 0:x.source}}};var w,b,v;s.parameters={...s.parameters,docs:{...(w=s.parameters)==null?void 0:w.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email">Email</Label>
      <Input type="email" id="email" placeholder="Email" />
    </div>
}`,...(v=(b=s.parameters)==null?void 0:b.docs)==null?void 0:v.source}}};var f,N,L;l.parameters={...l.parameters,docs:{...(f=l.parameters)==null?void 0:f.docs,source:{originalSource:`{
  args: {
    defaultValue: 'Hello World'
  }
}`,...(L=(N=l.parameters)==null?void 0:N.docs)==null?void 0:L.source}}};var y,E,S;m.parameters={...m.parameters,docs:{...(y=m.parameters)==null?void 0:y.docs,source:{originalSource:`{
  args: {
    placeholder: 'Disabled input',
    disabled: true
  }
}`,...(S=(E=m.parameters)==null?void 0:E.docs)==null?void 0:S.source}}};var j,F,I;t.parameters={...t.parameters,docs:{...(j=t.parameters)==null?void 0:j.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="password">Password</Label>
      <Input type="password" id="password" placeholder="Enter password" />
    </div>
}`,...(I=(F=t.parameters)==null?void 0:F.docs)==null?void 0:I.source}}};var W,P,D;i.parameters={...i.parameters,docs:{...(W=i.parameters)==null?void 0:W.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-input">Email</Label>
      <Input type="email" id="email-input" placeholder="name@example.com" />
    </div>
}`,...(D=(P=i.parameters)==null?void 0:P.docs)==null?void 0:D.source}}};var H,V,T;o.parameters={...o.parameters,docs:{...(H=o.parameters)==null?void 0:H.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="number">Number</Label>
      <Input type="number" id="number" placeholder="0" />
    </div>
}`,...(T=(V=o.parameters)==null?void 0:V.docs)==null?void 0:T.source}}};var _,O,R;d.parameters={...d.parameters,docs:{...(_=d.parameters)==null?void 0:_.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="search">Search</Label>
      <Input type="search" id="search" placeholder="Search..." />
    </div>
}`,...(R=(O=d.parameters)==null?void 0:O.docs)==null?void 0:R.source}}};var U,k,q;c.parameters={...c.parameters,docs:{...(U=c.parameters)==null?void 0:U.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-helper">Email</Label>
      <Input type="email" id="email-helper" placeholder="Email" />
      <p className="text-sm text-muted-foreground">
        We'll never share your email with anyone else.
      </p>
    </div>
}`,...(q=(k=c.parameters)==null?void 0:k.docs)==null?void 0:q.source}}};var z,A,B;n.parameters={...n.parameters,docs:{...(z=n.parameters)==null?void 0:z.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-error">Email</Label>
      <Input type="email" id="email-error" placeholder="Email" className="border-red-500" />
      <p className="text-sm text-red-500">
        Please enter a valid email address.
      </p>
    </div>
}`,...(B=(A=n.parameters)==null?void 0:A.docs)==null?void 0:B.source}}};var C,G,J;p.parameters={...p.parameters,docs:{...(C=p.parameters)==null?void 0:C.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="picture">Picture</Label>
      <Input id="picture" type="file" />
    </div>
}`,...(J=(G=p.parameters)==null?void 0:G.docs)==null?void 0:J.source}}};var K,M,Q;a.parameters={...a.parameters,docs:{...(K=a.parameters)==null?void 0:K.docs,source:{originalSource:`{
  args: {
    placeholder: 'Enter text...'
  }
}`,...(Q=(M=a.parameters)==null?void 0:M.docs)==null?void 0:Q.source}}};var X,Y,Z;s.parameters={...s.parameters,docs:{...(X=s.parameters)==null?void 0:X.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email">Email</Label>
      <Input type="email" id="email" placeholder="Email" />
    </div>
}`,...(Z=(Y=s.parameters)==null?void 0:Y.docs)==null?void 0:Z.source}}};var $,ee,re;l.parameters={...l.parameters,docs:{...($=l.parameters)==null?void 0:$.docs,source:{originalSource:`{
  args: {
    defaultValue: 'Hello World'
  }
}`,...(re=(ee=l.parameters)==null?void 0:ee.docs)==null?void 0:re.source}}};var ae,se,le;m.parameters={...m.parameters,docs:{...(ae=m.parameters)==null?void 0:ae.docs,source:{originalSource:`{
  args: {
    placeholder: 'Disabled input',
    disabled: true
  }
}`,...(le=(se=m.parameters)==null?void 0:se.docs)==null?void 0:le.source}}};var me,te,ie;t.parameters={...t.parameters,docs:{...(me=t.parameters)==null?void 0:me.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="password">Password</Label>
      <Input type="password" id="password" placeholder="Enter password" />
    </div>
}`,...(ie=(te=t.parameters)==null?void 0:te.docs)==null?void 0:ie.source}}};var oe,de,ce;i.parameters={...i.parameters,docs:{...(oe=i.parameters)==null?void 0:oe.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-input">Email</Label>
      <Input type="email" id="email-input" placeholder="name@example.com" />
    </div>
}`,...(ce=(de=i.parameters)==null?void 0:de.docs)==null?void 0:ce.source}}};var ne,pe,ue;o.parameters={...o.parameters,docs:{...(ne=o.parameters)==null?void 0:ne.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="number">Number</Label>
      <Input type="number" id="number" placeholder="0" />
    </div>
}`,...(ue=(pe=o.parameters)==null?void 0:pe.docs)==null?void 0:ue.source}}};var he,ge,xe;d.parameters={...d.parameters,docs:{...(he=d.parameters)==null?void 0:he.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="search">Search</Label>
      <Input type="search" id="search" placeholder="Search..." />
    </div>
}`,...(xe=(ge=d.parameters)==null?void 0:ge.docs)==null?void 0:xe.source}}};var we,be,ve;c.parameters={...c.parameters,docs:{...(we=c.parameters)==null?void 0:we.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-helper">Email</Label>
      <Input type="email" id="email-helper" placeholder="Email" />
      <p className="text-sm text-muted-foreground">
        We'll never share your email with anyone else.
      </p>
    </div>
}`,...(ve=(be=c.parameters)==null?void 0:be.docs)==null?void 0:ve.source}}};var fe,Ne,Le;n.parameters={...n.parameters,docs:{...(fe=n.parameters)==null?void 0:fe.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-error">Email</Label>
      <Input type="email" id="email-error" placeholder="Email" className="border-red-500" />
      <p className="text-sm text-red-500">
        Please enter a valid email address.
      </p>
    </div>
}`,...(Le=(Ne=n.parameters)==null?void 0:Ne.docs)==null?void 0:Le.source}}};var ye,Ee,Se;p.parameters={...p.parameters,docs:{...(ye=p.parameters)==null?void 0:ye.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="picture">Picture</Label>
      <Input id="picture" type="file" />
    </div>
}`,...(Se=(Ee=p.parameters)==null?void 0:Ee.docs)==null?void 0:Se.source}}};const Oe=["Default","WithLabel","WithValue","Disabled","Password","Email","Number","Search","WithHelperText","WithError","File"];export{a as Default,m as Disabled,i as Email,p as File,o as Number,t as Password,d as Search,n as WithError,c as WithHelperText,s as WithLabel,l as WithValue,Oe as __namedExportsOrder,_e as default};
