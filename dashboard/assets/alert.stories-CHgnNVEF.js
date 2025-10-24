import{j as e}from"./jsx-runtime-D_zvdyIk.js";import"./index-Dz3UJJSw.js";import{c as le}from"./index-CGrAONsN.js";import{c as u}from"./utils-D-KgF5mV.js";import{I as h}from"./info-Dd4rymu9.js";import{c as A}from"./createLucideIcon-ClV4rtrr.js";import"./_commonjsHelpers-CqkleIqs.js";/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ce=[["path",{d:"M21.801 10A10 10 0 1 1 17 3.335",key:"yps3ct"}],["path",{d:"m9 11 3 3L22 4",key:"1pflzl"}]],se=A("circle-check-big",ce);/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const de=[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["path",{d:"m15 9-6 6",key:"1uzhvr"}],["path",{d:"m9 9 6 6",key:"z0biqf"}]],ae=A("circle-x",de);/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pe=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3",key:"wmoenq"}],["path",{d:"M12 9v4",key:"juzpu7"}],["path",{d:"M12 17h.01",key:"p32p05"}]],ie=A("triangle-alert",pe),me=le("relative w-full rounded-lg border px-4 py-3 text-sm grid has-[>svg]:grid-cols-[calc(var(--spacing)*4)_1fr] grid-cols-[0_1fr] has-[>svg]:gap-x-3 gap-y-0.5 items-start [&>svg]:size-4 [&>svg]:translate-y-0.5 [&>svg]:text-current",{variants:{variant:{default:"bg-card text-card-foreground",destructive:"text-destructive bg-card [&>svg]:text-current *:data-[slot=alert-description]:text-destructive/90"}},defaultVariants:{variant:"default"}});function r({className:s,variant:m,...oe}){return e.jsx("div",{"data-slot":"alert",role:"alert",className:u(me({variant:m}),s),...oe})}function t({className:s,...m}){return e.jsx("div",{"data-slot":"alert-title",className:u("col-start-2 line-clamp-1 min-h-4 font-medium tracking-tight",s),...m})}function n({className:s,...m}){return e.jsx("div",{"data-slot":"alert-description",className:u("text-muted-foreground col-start-2 grid justify-items-start gap-1 text-sm [&_p]:leading-relaxed",s),...m})}r.__docgenInfo={description:"",methods:[],displayName:"Alert"};t.__docgenInfo={description:"",methods:[],displayName:"AlertTitle"};n.__docgenInfo={description:"",methods:[],displayName:"AlertDescription"};r.__docgenInfo={description:"",methods:[],displayName:"Alert"};t.__docgenInfo={description:"",methods:[],displayName:"AlertTitle"};n.__docgenInfo={description:"",methods:[],displayName:"AlertDescription"};const Te={title:"UI/Alert",component:r,parameters:{layout:"padded"},tags:["autodocs"],argTypes:{variant:{control:"select",options:["default","destructive"]}}},a={args:{variant:"default"},render:s=>e.jsxs(r,{...s,children:[e.jsx(h,{}),e.jsx(t,{children:"Information"}),e.jsx(n,{children:"This is a default alert with some information for the user."})]})},i={args:{variant:"destructive"},render:s=>e.jsxs(r,{...s,children:[e.jsx(ae,{}),e.jsx(t,{children:"Error"}),e.jsx(n,{children:"Something went wrong. Please try again or contact support."})]})},o={render:()=>e.jsxs(r,{children:[e.jsx(se,{className:"text-green-600"}),e.jsx(t,{children:"Success"}),e.jsx(n,{children:"Your changes have been saved successfully."})]}),parameters:{docs:{description:{story:"Success alert using the default variant with a green icon."}}}},l={render:()=>e.jsxs(r,{children:[e.jsx(ie,{className:"text-yellow-600"}),e.jsx(t,{children:"Warning"}),e.jsx(n,{children:"This action cannot be undone. Please proceed with caution."})]}),parameters:{docs:{description:{story:"Warning alert using the default variant with a yellow icon."}}}},c={render:()=>e.jsxs(r,{children:[e.jsx(t,{children:"No Icon Alert"}),e.jsx(n,{children:"This alert doesn't have an icon, so the content spans the full width."})]}),parameters:{docs:{description:{story:"Alert without an icon - content automatically spans full width."}}}},d={render:()=>e.jsxs(r,{children:[e.jsx(h,{}),e.jsx(t,{children:"Detailed Information"}),e.jsxs(n,{children:[e.jsx("p",{children:"This alert contains multiple paragraphs of content to demonstrate how longer text is handled."}),e.jsx("p",{children:"The alert component automatically adjusts its height to accommodate the content, and the text maintains proper line spacing and readability."}),e.jsx("p",{children:"You can include multiple paragraphs, lists, or other content within the AlertDescription component."})]})]}),parameters:{docs:{description:{story:"Alert with longer content including multiple paragraphs."}}}},p={render:()=>e.jsxs("div",{className:"space-y-4",children:[e.jsxs(r,{children:[e.jsx(h,{}),e.jsx(t,{children:"Information"}),e.jsx(n,{children:"This is a default informational alert."})]}),e.jsxs(r,{children:[e.jsx(se,{className:"text-green-600"}),e.jsx(t,{children:"Success"}),e.jsx(n,{children:"Operation completed successfully."})]}),e.jsxs(r,{children:[e.jsx(ie,{className:"text-yellow-600"}),e.jsx(t,{children:"Warning"}),e.jsx(n,{children:"Please review before proceeding."})]}),e.jsxs(r,{variant:"destructive",children:[e.jsx(ae,{}),e.jsx(t,{children:"Error"}),e.jsx(n,{children:"An error occurred during processing."})]})]}),parameters:{docs:{description:{story:"All alert variants displayed together for comparison."}}}};var g,f,x;a.parameters={...a.parameters,docs:{...(g=a.parameters)==null?void 0:g.docs,source:{originalSource:`{
  args: {
    variant: 'default'
  },
  render: args => <Alert {...args}>
      <Info />
      <AlertTitle>Information</AlertTitle>
      <AlertDescription>
        This is a default alert with some information for the user.
      </AlertDescription>
    </Alert>
}`,...(x=(f=a.parameters)==null?void 0:f.docs)==null?void 0:x.source}}};var y,T,v;i.parameters={...i.parameters,docs:{...(y=i.parameters)==null?void 0:y.docs,source:{originalSource:`{
  args: {
    variant: 'destructive'
  },
  render: args => <Alert {...args}>
      <XCircle />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>
        Something went wrong. Please try again or contact support.
      </AlertDescription>
    </Alert>
}`,...(v=(T=i.parameters)==null?void 0:T.docs)==null?void 0:v.source}}};var j,D,w;o.parameters={...o.parameters,docs:{...(j=o.parameters)==null?void 0:j.docs,source:{originalSource:`{
  render: () => <Alert>
      <CheckCircle className="text-green-600" />
      <AlertTitle>Success</AlertTitle>
      <AlertDescription>
        Your changes have been saved successfully.
      </AlertDescription>
    </Alert>,
  parameters: {
    docs: {
      description: {
        story: 'Success alert using the default variant with a green icon.'
      }
    }
  }
}`,...(w=(D=o.parameters)==null?void 0:D.docs)==null?void 0:w.source}}};var I,N,S;l.parameters={...l.parameters,docs:{...(I=l.parameters)==null?void 0:I.docs,source:{originalSource:`{
  render: () => <Alert>
      <AlertTriangle className="text-yellow-600" />
      <AlertTitle>Warning</AlertTitle>
      <AlertDescription>
        This action cannot be undone. Please proceed with caution.
      </AlertDescription>
    </Alert>,
  parameters: {
    docs: {
      description: {
        story: 'Warning alert using the default variant with a yellow icon.'
      }
    }
  }
}`,...(S=(N=l.parameters)==null?void 0:N.docs)==null?void 0:S.source}}};var _,b,C;c.parameters={...c.parameters,docs:{...(_=c.parameters)==null?void 0:_.docs,source:{originalSource:`{
  render: () => <Alert>
      <AlertTitle>No Icon Alert</AlertTitle>
      <AlertDescription>
        This alert doesn't have an icon, so the content spans the full width.
      </AlertDescription>
    </Alert>,
  parameters: {
    docs: {
      description: {
        story: 'Alert without an icon - content automatically spans full width.'
      }
    }
  }
}`,...(C=(b=c.parameters)==null?void 0:b.docs)==null?void 0:C.source}}};var k,W,P;d.parameters={...d.parameters,docs:{...(k=d.parameters)==null?void 0:k.docs,source:{originalSource:`{
  render: () => <Alert>
      <Info />
      <AlertTitle>Detailed Information</AlertTitle>
      <AlertDescription>
        <p>This alert contains multiple paragraphs of content to demonstrate how longer text is handled.</p>
        <p>The alert component automatically adjusts its height to accommodate the content, and the text maintains proper line spacing and readability.</p>
        <p>You can include multiple paragraphs, lists, or other content within the AlertDescription component.</p>
      </AlertDescription>
    </Alert>,
  parameters: {
    docs: {
      description: {
        story: 'Alert with longer content including multiple paragraphs.'
      }
    }
  }
}`,...(P=(W=d.parameters)==null?void 0:W.docs)==null?void 0:P.source}}};var E,Y,z;p.parameters={...p.parameters,docs:{...(E=p.parameters)==null?void 0:E.docs,source:{originalSource:`{
  render: () => <div className="space-y-4">
      <Alert>
        <Info />
        <AlertTitle>Information</AlertTitle>
        <AlertDescription>
          This is a default informational alert.
        </AlertDescription>
      </Alert>
      
      <Alert>
        <CheckCircle className="text-green-600" />
        <AlertTitle>Success</AlertTitle>
        <AlertDescription>
          Operation completed successfully.
        </AlertDescription>
      </Alert>
      
      <Alert>
        <AlertTriangle className="text-yellow-600" />
        <AlertTitle>Warning</AlertTitle>
        <AlertDescription>
          Please review before proceeding.
        </AlertDescription>
      </Alert>
      
      <Alert variant="destructive">
        <XCircle />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          An error occurred during processing.
        </AlertDescription>
      </Alert>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'All alert variants displayed together for comparison.'
      }
    }
  }
}`,...(z=(Y=p.parameters)==null?void 0:Y.docs)==null?void 0:z.source}}};var X,L,O;a.parameters={...a.parameters,docs:{...(X=a.parameters)==null?void 0:X.docs,source:{originalSource:`{
  args: {
    variant: 'default'
  },
  render: args => <Alert {...args}>
      <Info />
      <AlertTitle>Information</AlertTitle>
      <AlertDescription>
        This is a default alert with some information for the user.
      </AlertDescription>
    </Alert>
}`,...(O=(L=a.parameters)==null?void 0:L.docs)==null?void 0:O.source}}};var V,M,q;i.parameters={...i.parameters,docs:{...(V=i.parameters)==null?void 0:V.docs,source:{originalSource:`{
  args: {
    variant: 'destructive'
  },
  render: args => <Alert {...args}>
      <XCircle />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>
        Something went wrong. Please try again or contact support.
      </AlertDescription>
    </Alert>
}`,...(q=(M=i.parameters)==null?void 0:M.docs)==null?void 0:q.source}}};var $,B,R;o.parameters={...o.parameters,docs:{...($=o.parameters)==null?void 0:$.docs,source:{originalSource:`{
  render: () => <Alert>
      <CheckCircle className="text-green-600" />
      <AlertTitle>Success</AlertTitle>
      <AlertDescription>
        Your changes have been saved successfully.
      </AlertDescription>
    </Alert>,
  parameters: {
    docs: {
      description: {
        story: 'Success alert using the default variant with a green icon.'
      }
    }
  }
}`,...(R=(B=o.parameters)==null?void 0:B.docs)==null?void 0:R.source}}};var U,F,G;l.parameters={...l.parameters,docs:{...(U=l.parameters)==null?void 0:U.docs,source:{originalSource:`{
  render: () => <Alert>
      <AlertTriangle className="text-yellow-600" />
      <AlertTitle>Warning</AlertTitle>
      <AlertDescription>
        This action cannot be undone. Please proceed with caution.
      </AlertDescription>
    </Alert>,
  parameters: {
    docs: {
      description: {
        story: 'Warning alert using the default variant with a yellow icon.'
      }
    }
  }
}`,...(G=(F=l.parameters)==null?void 0:F.docs)==null?void 0:G.source}}};var H,J,K;c.parameters={...c.parameters,docs:{...(H=c.parameters)==null?void 0:H.docs,source:{originalSource:`{
  render: () => <Alert>
      <AlertTitle>No Icon Alert</AlertTitle>
      <AlertDescription>
        This alert doesn't have an icon, so the content spans the full width.
      </AlertDescription>
    </Alert>,
  parameters: {
    docs: {
      description: {
        story: 'Alert without an icon - content automatically spans full width.'
      }
    }
  }
}`,...(K=(J=c.parameters)==null?void 0:J.docs)==null?void 0:K.source}}};var Q,Z,ee;d.parameters={...d.parameters,docs:{...(Q=d.parameters)==null?void 0:Q.docs,source:{originalSource:`{
  render: () => <Alert>
      <Info />
      <AlertTitle>Detailed Information</AlertTitle>
      <AlertDescription>
        <p>This alert contains multiple paragraphs of content to demonstrate how longer text is handled.</p>
        <p>The alert component automatically adjusts its height to accommodate the content, and the text maintains proper line spacing and readability.</p>
        <p>You can include multiple paragraphs, lists, or other content within the AlertDescription component.</p>
      </AlertDescription>
    </Alert>,
  parameters: {
    docs: {
      description: {
        story: 'Alert with longer content including multiple paragraphs.'
      }
    }
  }
}`,...(ee=(Z=d.parameters)==null?void 0:Z.docs)==null?void 0:ee.source}}};var re,te,ne;p.parameters={...p.parameters,docs:{...(re=p.parameters)==null?void 0:re.docs,source:{originalSource:`{
  render: () => <div className="space-y-4">
      <Alert>
        <Info />
        <AlertTitle>Information</AlertTitle>
        <AlertDescription>
          This is a default informational alert.
        </AlertDescription>
      </Alert>
      
      <Alert>
        <CheckCircle className="text-green-600" />
        <AlertTitle>Success</AlertTitle>
        <AlertDescription>
          Operation completed successfully.
        </AlertDescription>
      </Alert>
      
      <Alert>
        <AlertTriangle className="text-yellow-600" />
        <AlertTitle>Warning</AlertTitle>
        <AlertDescription>
          Please review before proceeding.
        </AlertDescription>
      </Alert>
      
      <Alert variant="destructive">
        <XCircle />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          An error occurred during processing.
        </AlertDescription>
      </Alert>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'All alert variants displayed together for comparison.'
      }
    }
  }
}`,...(ne=(te=p.parameters)==null?void 0:te.docs)==null?void 0:ne.source}}};const ve=["Default","Destructive","Success","Warning","WithoutIcon","LongContent","AllVariants"];export{p as AllVariants,a as Default,i as Destructive,d as LongContent,o as Success,l as Warning,c as WithoutIcon,ve as __namedExportsOrder,Te as default};
