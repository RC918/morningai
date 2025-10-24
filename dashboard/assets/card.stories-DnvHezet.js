import{j as e}from"./jsx-runtime-D_zvdyIk.js";import"./index-Dz3UJJSw.js";import{c as u}from"./utils-ClSdSIbF.js";import{B as x}from"./button-CtW_o4fY.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-CN2Y8dJ9.js";function n({className:r,...a}){return e.jsx("div",{"data-slot":"card",className:u("bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm",r),...a})}function C({className:r,...a}){return e.jsx("div",{"data-slot":"card-header",className:u("@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-1.5 px-6 has-data-[slot=card-action]:grid-cols-[1fr_auto] [.border-b]:pb-6",r),...a})}function p({className:r,...a}){return e.jsx("div",{"data-slot":"card-title",className:u("leading-none font-semibold",r),...a})}function m({className:r,...a}){return e.jsx("div",{"data-slot":"card-description",className:u("text-muted-foreground text-sm",r),...a})}function l({className:r,...a}){return e.jsx("div",{"data-slot":"card-content",className:u("px-6",r),...a})}function h({className:r,...a}){return e.jsx("div",{"data-slot":"card-footer",className:u("flex items-center px-6 [.border-t]:pt-6",r),...a})}n.__docgenInfo={description:"",methods:[],displayName:"Card"};C.__docgenInfo={description:"",methods:[],displayName:"CardHeader"};h.__docgenInfo={description:"",methods:[],displayName:"CardFooter"};p.__docgenInfo={description:"",methods:[],displayName:"CardTitle"};m.__docgenInfo={description:"",methods:[],displayName:"CardDescription"};l.__docgenInfo={description:"",methods:[],displayName:"CardContent"};n.__docgenInfo={description:"",methods:[],displayName:"Card"};C.__docgenInfo={description:"",methods:[],displayName:"CardHeader"};h.__docgenInfo={description:"",methods:[],displayName:"CardFooter"};p.__docgenInfo={description:"",methods:[],displayName:"CardTitle"};m.__docgenInfo={description:"",methods:[],displayName:"CardDescription"};l.__docgenInfo={description:"",methods:[],displayName:"CardContent"};const de={title:"UI/Card",component:n,parameters:{layout:"centered"},tags:["autodocs"]},t={render:()=>e.jsxs(n,{className:"w-[350px]",children:[e.jsxs(C,{children:[e.jsx(p,{children:"Card Title"}),e.jsx(m,{children:"Card Description"})]}),e.jsx(l,{children:e.jsx("p",{children:"Card Content"})}),e.jsx(h,{children:e.jsx(x,{children:"Action"})})]})},d={render:()=>e.jsxs(n,{className:"w-[350px]",children:[e.jsxs(C,{children:[e.jsx(p,{children:"Notification"}),e.jsx(m,{children:"You have 3 unread messages."})]}),e.jsx(l,{children:e.jsx("p",{children:"Check your inbox for new updates."})})]})},s={render:()=>e.jsx(n,{className:"w-[350px]",children:e.jsx(l,{className:"pt-6",children:e.jsx("p",{children:"This card has no header, just content."})})})},o={render:()=>e.jsxs(n,{className:"w-[350px]",children:[e.jsxs(C,{children:[e.jsx(p,{children:"Recent Activity"}),e.jsx(m,{children:"Your latest actions"})]}),e.jsx(l,{children:e.jsxs("ul",{className:"space-y-2",children:[e.jsx("li",{children:"✓ Completed task A"}),e.jsx("li",{children:"✓ Updated profile"}),e.jsx("li",{children:"✓ Sent message"})]})})]})},i={render:()=>e.jsxs(n,{className:"w-[350px]",children:[e.jsxs(C,{children:[e.jsx(p,{children:"Confirm Action"}),e.jsx(m,{children:"Are you sure you want to proceed?"})]}),e.jsx(l,{children:e.jsx("p",{children:"This action cannot be undone."})}),e.jsxs(h,{className:"flex justify-between",children:[e.jsx(x,{variant:"outline",children:"Cancel"}),e.jsx(x,{children:"Confirm"})]})]})},c={render:()=>e.jsxs(n,{className:"w-[600px]",children:[e.jsxs(C,{children:[e.jsx(p,{children:"Wide Card"}),e.jsx(m,{children:"This card is wider than the default"})]}),e.jsx(l,{children:e.jsx("p",{children:"Content can span across a wider area for more complex layouts."})})]})};var f,j,N;t.parameters={...t.parameters,docs:{...(f=t.parameters)==null?void 0:f.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card Description</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card Content</p>
      </CardContent>
      <CardFooter>
        <Button>Action</Button>
      </CardFooter>
    </Card>
}`,...(N=(j=t.parameters)==null?void 0:j.docs)==null?void 0:N.source}}};var g,w,y;d.parameters={...d.parameters,docs:{...(g=d.parameters)==null?void 0:g.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Notification</CardTitle>
        <CardDescription>You have 3 unread messages.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Check your inbox for new updates.</p>
      </CardContent>
    </Card>
}`,...(y=(w=d.parameters)==null?void 0:w.docs)==null?void 0:y.source}}};var T,D,_;s.parameters={...s.parameters,docs:{...(T=s.parameters)==null?void 0:T.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardContent className="pt-6">
        <p>This card has no header, just content.</p>
      </CardContent>
    </Card>
}`,...(_=(D=s.parameters)==null?void 0:D.docs)==null?void 0:_.source}}};var H,b,B;o.parameters={...o.parameters,docs:{...(H=o.parameters)==null?void 0:H.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Your latest actions</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          <li>✓ Completed task A</li>
          <li>✓ Updated profile</li>
          <li>✓ Sent message</li>
        </ul>
      </CardContent>
    </Card>
}`,...(B=(b=o.parameters)==null?void 0:b.docs)==null?void 0:B.source}}};var v,A,S;i.parameters={...i.parameters,docs:{...(v=i.parameters)==null?void 0:v.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Confirm Action</CardTitle>
        <CardDescription>Are you sure you want to proceed?</CardDescription>
      </CardHeader>
      <CardContent>
        <p>This action cannot be undone.</p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline">Cancel</Button>
        <Button>Confirm</Button>
      </CardFooter>
    </Card>
}`,...(S=(A=i.parameters)==null?void 0:A.docs)==null?void 0:S.source}}};var F,I,W;c.parameters={...c.parameters,docs:{...(F=c.parameters)==null?void 0:F.docs,source:{originalSource:`{
  render: () => <Card className="w-[600px]">
      <CardHeader>
        <CardTitle>Wide Card</CardTitle>
        <CardDescription>This card is wider than the default</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Content can span across a wider area for more complex layouts.</p>
      </CardContent>
    </Card>
}`,...(W=(I=c.parameters)==null?void 0:I.docs)==null?void 0:W.source}}};var k,Y,R;t.parameters={...t.parameters,docs:{...(k=t.parameters)==null?void 0:k.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card Description</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card Content</p>
      </CardContent>
      <CardFooter>
        <Button>Action</Button>
      </CardFooter>
    </Card>
}`,...(R=(Y=t.parameters)==null?void 0:Y.docs)==null?void 0:R.source}}};var U,E,L;d.parameters={...d.parameters,docs:{...(U=d.parameters)==null?void 0:U.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Notification</CardTitle>
        <CardDescription>You have 3 unread messages.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Check your inbox for new updates.</p>
      </CardContent>
    </Card>
}`,...(L=(E=d.parameters)==null?void 0:E.docs)==null?void 0:L.source}}};var M,O,q;s.parameters={...s.parameters,docs:{...(M=s.parameters)==null?void 0:M.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardContent className="pt-6">
        <p>This card has no header, just content.</p>
      </CardContent>
    </Card>
}`,...(q=(O=s.parameters)==null?void 0:O.docs)==null?void 0:q.source}}};var z,G,J;o.parameters={...o.parameters,docs:{...(z=o.parameters)==null?void 0:z.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Your latest actions</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          <li>✓ Completed task A</li>
          <li>✓ Updated profile</li>
          <li>✓ Sent message</li>
        </ul>
      </CardContent>
    </Card>
}`,...(J=(G=o.parameters)==null?void 0:G.docs)==null?void 0:J.source}}};var K,P,Q;i.parameters={...i.parameters,docs:{...(K=i.parameters)==null?void 0:K.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Confirm Action</CardTitle>
        <CardDescription>Are you sure you want to proceed?</CardDescription>
      </CardHeader>
      <CardContent>
        <p>This action cannot be undone.</p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline">Cancel</Button>
        <Button>Confirm</Button>
      </CardFooter>
    </Card>
}`,...(Q=(P=i.parameters)==null?void 0:P.docs)==null?void 0:Q.source}}};var V,X,Z;c.parameters={...c.parameters,docs:{...(V=c.parameters)==null?void 0:V.docs,source:{originalSource:`{
  render: () => <Card className="w-[600px]">
      <CardHeader>
        <CardTitle>Wide Card</CardTitle>
        <CardDescription>This card is wider than the default</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Content can span across a wider area for more complex layouts.</p>
      </CardContent>
    </Card>
}`,...(Z=(X=c.parameters)==null?void 0:X.docs)==null?void 0:Z.source}}};const se=["Default","WithoutFooter","WithoutHeader","WithList","WithMultipleButtons","Wide"];export{t as Default,c as Wide,o as WithList,i as WithMultipleButtons,d as WithoutFooter,s as WithoutHeader,se as __namedExportsOrder,de as default};
