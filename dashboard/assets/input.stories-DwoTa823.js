import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{I as r}from"./input-Cv5CY2yx.js";import{L as a}from"./label-B-2P1Ax_.js";import"./index-Dz3UJJSw.js";import"./_commonjsHelpers-CqkleIqs.js";import"./utils-D-KgF5mV.js";import"./index-C7eB__Z-.js";import"./index-CYANIyVc.js";import"./index-fUCaa9pg.js";import"./index-DRuEWG1E.js";const Mr={title:"UI/Input",component:r,parameters:{layout:"centered",docs:{description:{component:`
The Input component provides a consistent interface for text entry across the application. It supports various input types and states.

### Usage Guidelines
- Always pair with a Label for accessibility
- Use appropriate input type for the data (email, password, number, etc.)
- Provide clear placeholder text
- Show validation errors below the input
- Use helper text for additional context
- Disable when input is not available

### Accessibility
- Proper label associations with htmlFor/id
- Placeholder text for guidance
- Error messages announced to screen readers
- Keyboard navigation support
- Focus indicators
        `}}},tags:["autodocs"],argTypes:{type:{control:"select",options:["text","email","password","number","tel","url","search"],description:"The type of input field",table:{type:{summary:"string"},defaultValue:{summary:"text"}}},disabled:{control:"boolean",description:"Whether the input is disabled",table:{type:{summary:"boolean"},defaultValue:{summary:"false"}}},placeholder:{control:"text",description:"Placeholder text shown when input is empty",table:{type:{summary:"string"}}}}},s={args:{placeholder:"Enter text..."}},t={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"email",children:"Email"}),e.jsx(r,{type:"email",id:"email",placeholder:"Email"})]})},l={args:{defaultValue:"Hello World"}},i={args:{placeholder:"Disabled input",disabled:!0}},o={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"password",children:"Password"}),e.jsx(r,{type:"password",id:"password",placeholder:"Enter password"})]})},d={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"email-input",children:"Email"}),e.jsx(r,{type:"email",id:"email-input",placeholder:"name@example.com"})]})},n={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"number",children:"Number"}),e.jsx(r,{type:"number",id:"number",placeholder:"0"})]})},m={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"search",children:"Search"}),e.jsx(r,{type:"search",id:"search",placeholder:"Search..."})]})},c={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"email-helper",children:"Email"}),e.jsx(r,{type:"email",id:"email-helper",placeholder:"Email"}),e.jsx("p",{className:"text-sm text-muted-foreground",children:"We'll never share your email with anyone else."})]})},p={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"email-error",children:"Email"}),e.jsx(r,{type:"email",id:"email-error",placeholder:"Email",className:"border-red-500"}),e.jsx("p",{className:"text-sm text-red-500",children:"Please enter a valid email address."})]})},u={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"picture",children:"Picture"}),e.jsx(r,{id:"picture",type:"file"})]}),parameters:{docs:{description:{story:"File input for uploading files."}}}},h={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"long-placeholder",children:"Input"}),e.jsx(r,{id:"long-placeholder",placeholder:"This is a very long placeholder text that might get truncated depending on the input width"})]}),parameters:{docs:{description:{story:"Input with very long placeholder text to test truncation."}}}},g={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"long-value",children:"Input"}),e.jsx(r,{id:"long-value",defaultValue:"This is a very long input value that extends beyond the visible area and requires horizontal scrolling to see the full content"})]}),parameters:{docs:{description:{story:"Input with very long value to test overflow behavior."}}}},x={render:()=>e.jsxs("div",{className:"grid w-32 items-center gap-1.5",children:[e.jsx(a,{htmlFor:"min-width",children:"Narrow"}),e.jsx(r,{id:"min-width",placeholder:"Text"})]}),parameters:{docs:{description:{story:"Input with minimal width constraint."}}}},w={render:()=>e.jsxs("div",{className:"grid w-full max-w-4xl items-center gap-1.5",children:[e.jsx(a,{htmlFor:"full-width",children:"Full Width Input"}),e.jsx(r,{id:"full-width",placeholder:"This input spans the full width"})]}),parameters:{docs:{description:{story:"Input that spans full width of container."}}}},v={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"readonly",children:"Read Only"}),e.jsx(r,{id:"readonly",defaultValue:"This value cannot be changed",readOnly:!0})]}),parameters:{docs:{description:{story:"Read-only input that displays but cannot be edited."}}}},b={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"maxlength",children:"Username (max 10 characters)"}),e.jsx(r,{id:"maxlength",placeholder:"Username",maxLength:10}),e.jsx("p",{className:"text-sm text-muted-foreground",children:"Maximum 10 characters allowed."})]}),parameters:{docs:{description:{story:"Input with maximum length constraint."}}}},f={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsx(a,{htmlFor:"pattern",children:"Phone Number"}),e.jsx(r,{id:"pattern",type:"tel",placeholder:"(123) 456-7890",pattern:"[0-9]{3}-[0-9]{3}-[0-9]{4}"}),e.jsx("p",{className:"text-sm text-muted-foreground",children:"Format: 123-456-7890"})]}),parameters:{docs:{description:{story:"Input with pattern validation for phone numbers."}}}},y={render:()=>e.jsxs("div",{className:"grid w-full max-w-sm items-center gap-1.5",children:[e.jsxs(a,{htmlFor:"required",children:["Email ",e.jsx("span",{className:"text-red-500",children:"*"})]}),e.jsx(r,{id:"required",type:"email",placeholder:"Email",required:!0}),e.jsx("p",{className:"text-sm text-muted-foreground",children:"This field is required."})]}),parameters:{docs:{description:{story:"Required input field with visual indicator."}}}};var N,L,I;s.parameters={...s.parameters,docs:{...(N=s.parameters)==null?void 0:N.docs,source:{originalSource:`{
  args: {
    placeholder: 'Enter text...'
  }
}`,...(I=(L=s.parameters)==null?void 0:L.docs)==null?void 0:I.source}}};var F,j,S;t.parameters={...t.parameters,docs:{...(F=t.parameters)==null?void 0:F.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email">Email</Label>
      <Input type="email" id="email" placeholder="Email" />
    </div>
}`,...(S=(j=t.parameters)==null?void 0:j.docs)==null?void 0:S.source}}};var E,W,T;l.parameters={...l.parameters,docs:{...(E=l.parameters)==null?void 0:E.docs,source:{originalSource:`{
  args: {
    defaultValue: 'Hello World'
  }
}`,...(T=(W=l.parameters)==null?void 0:W.docs)==null?void 0:T.source}}};var P,q,V;i.parameters={...i.parameters,docs:{...(P=i.parameters)==null?void 0:P.docs,source:{originalSource:`{
  args: {
    placeholder: 'Disabled input',
    disabled: true
  }
}`,...(V=(q=i.parameters)==null?void 0:q.docs)==null?void 0:V.source}}};var R,U,O;o.parameters={...o.parameters,docs:{...(R=o.parameters)==null?void 0:R.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="password">Password</Label>
      <Input type="password" id="password" placeholder="Enter password" />
    </div>
}`,...(O=(U=o.parameters)==null?void 0:U.docs)==null?void 0:O.source}}};var D,M,H;d.parameters={...d.parameters,docs:{...(D=d.parameters)==null?void 0:D.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-input">Email</Label>
      <Input type="email" id="email-input" placeholder="name@example.com" />
    </div>
}`,...(H=(M=d.parameters)==null?void 0:M.docs)==null?void 0:H.source}}};var z,A,_;n.parameters={...n.parameters,docs:{...(z=n.parameters)==null?void 0:z.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="number">Number</Label>
      <Input type="number" id="number" placeholder="0" />
    </div>
}`,...(_=(A=n.parameters)==null?void 0:A.docs)==null?void 0:_.source}}};var G,K,k;m.parameters={...m.parameters,docs:{...(G=m.parameters)==null?void 0:G.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="search">Search</Label>
      <Input type="search" id="search" placeholder="Search..." />
    </div>
}`,...(k=(K=m.parameters)==null?void 0:K.docs)==null?void 0:k.source}}};var B,C,J;c.parameters={...c.parameters,docs:{...(B=c.parameters)==null?void 0:B.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-helper">Email</Label>
      <Input type="email" id="email-helper" placeholder="Email" />
      <p className="text-sm text-muted-foreground">
        We'll never share your email with anyone else.
      </p>
    </div>
}`,...(J=(C=c.parameters)==null?void 0:C.docs)==null?void 0:J.source}}};var Q,X,Y;p.parameters={...p.parameters,docs:{...(Q=p.parameters)==null?void 0:Q.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-error">Email</Label>
      <Input type="email" id="email-error" placeholder="Email" className="border-red-500" />
      <p className="text-sm text-red-500">
        Please enter a valid email address.
      </p>
    </div>
}`,...(Y=(X=p.parameters)==null?void 0:X.docs)==null?void 0:Y.source}}};var Z,$,ee;u.parameters={...u.parameters,docs:{...(Z=u.parameters)==null?void 0:Z.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="picture">Picture</Label>
      <Input id="picture" type="file" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'File input for uploading files.'
      }
    }
  }
}`,...(ee=($=u.parameters)==null?void 0:$.docs)==null?void 0:ee.source}}};var re,ae,se;h.parameters={...h.parameters,docs:{...(re=h.parameters)==null?void 0:re.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="long-placeholder">Input</Label>
      <Input id="long-placeholder" placeholder="This is a very long placeholder text that might get truncated depending on the input width" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input with very long placeholder text to test truncation.'
      }
    }
  }
}`,...(se=(ae=h.parameters)==null?void 0:ae.docs)==null?void 0:se.source}}};var te,le,ie;g.parameters={...g.parameters,docs:{...(te=g.parameters)==null?void 0:te.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="long-value">Input</Label>
      <Input id="long-value" defaultValue="This is a very long input value that extends beyond the visible area and requires horizontal scrolling to see the full content" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input with very long value to test overflow behavior.'
      }
    }
  }
}`,...(ie=(le=g.parameters)==null?void 0:le.docs)==null?void 0:ie.source}}};var oe,de,ne;x.parameters={...x.parameters,docs:{...(oe=x.parameters)==null?void 0:oe.docs,source:{originalSource:`{
  render: () => <div className="grid w-32 items-center gap-1.5">
      <Label htmlFor="min-width">Narrow</Label>
      <Input id="min-width" placeholder="Text" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input with minimal width constraint.'
      }
    }
  }
}`,...(ne=(de=x.parameters)==null?void 0:de.docs)==null?void 0:ne.source}}};var me,ce,pe;w.parameters={...w.parameters,docs:{...(me=w.parameters)==null?void 0:me.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-4xl items-center gap-1.5">
      <Label htmlFor="full-width">Full Width Input</Label>
      <Input id="full-width" placeholder="This input spans the full width" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input that spans full width of container.'
      }
    }
  }
}`,...(pe=(ce=w.parameters)==null?void 0:ce.docs)==null?void 0:pe.source}}};var ue,he,ge;v.parameters={...v.parameters,docs:{...(ue=v.parameters)==null?void 0:ue.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="readonly">Read Only</Label>
      <Input id="readonly" defaultValue="This value cannot be changed" readOnly />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Read-only input that displays but cannot be edited.'
      }
    }
  }
}`,...(ge=(he=v.parameters)==null?void 0:he.docs)==null?void 0:ge.source}}};var xe,we,ve;b.parameters={...b.parameters,docs:{...(xe=b.parameters)==null?void 0:xe.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="maxlength">Username (max 10 characters)</Label>
      <Input id="maxlength" placeholder="Username" maxLength={10} />
      <p className="text-sm text-muted-foreground">
        Maximum 10 characters allowed.
      </p>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input with maximum length constraint.'
      }
    }
  }
}`,...(ve=(we=b.parameters)==null?void 0:we.docs)==null?void 0:ve.source}}};var be,fe,ye;f.parameters={...f.parameters,docs:{...(be=f.parameters)==null?void 0:be.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="pattern">Phone Number</Label>
      <Input id="pattern" type="tel" placeholder="(123) 456-7890" pattern="[0-9]{3}-[0-9]{3}-[0-9]{4}" />
      <p className="text-sm text-muted-foreground">
        Format: 123-456-7890
      </p>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input with pattern validation for phone numbers.'
      }
    }
  }
}`,...(ye=(fe=f.parameters)==null?void 0:fe.docs)==null?void 0:ye.source}}};var Ne,Le,Ie;y.parameters={...y.parameters,docs:{...(Ne=y.parameters)==null?void 0:Ne.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="required">
        Email <span className="text-red-500">*</span>
      </Label>
      <Input id="required" type="email" placeholder="Email" required />
      <p className="text-sm text-muted-foreground">
        This field is required.
      </p>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Required input field with visual indicator.'
      }
    }
  }
}`,...(Ie=(Le=y.parameters)==null?void 0:Le.docs)==null?void 0:Ie.source}}};var Fe,je,Se;s.parameters={...s.parameters,docs:{...(Fe=s.parameters)==null?void 0:Fe.docs,source:{originalSource:`{
  args: {
    placeholder: 'Enter text...'
  }
}`,...(Se=(je=s.parameters)==null?void 0:je.docs)==null?void 0:Se.source}}};var Ee,We,Te;t.parameters={...t.parameters,docs:{...(Ee=t.parameters)==null?void 0:Ee.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email">Email</Label>
      <Input type="email" id="email" placeholder="Email" />
    </div>
}`,...(Te=(We=t.parameters)==null?void 0:We.docs)==null?void 0:Te.source}}};var Pe,qe,Ve;l.parameters={...l.parameters,docs:{...(Pe=l.parameters)==null?void 0:Pe.docs,source:{originalSource:`{
  args: {
    defaultValue: 'Hello World'
  }
}`,...(Ve=(qe=l.parameters)==null?void 0:qe.docs)==null?void 0:Ve.source}}};var Re,Ue,Oe;i.parameters={...i.parameters,docs:{...(Re=i.parameters)==null?void 0:Re.docs,source:{originalSource:`{
  args: {
    placeholder: 'Disabled input',
    disabled: true
  }
}`,...(Oe=(Ue=i.parameters)==null?void 0:Ue.docs)==null?void 0:Oe.source}}};var De,Me,He;o.parameters={...o.parameters,docs:{...(De=o.parameters)==null?void 0:De.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="password">Password</Label>
      <Input type="password" id="password" placeholder="Enter password" />
    </div>
}`,...(He=(Me=o.parameters)==null?void 0:Me.docs)==null?void 0:He.source}}};var ze,Ae,_e;d.parameters={...d.parameters,docs:{...(ze=d.parameters)==null?void 0:ze.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-input">Email</Label>
      <Input type="email" id="email-input" placeholder="name@example.com" />
    </div>
}`,...(_e=(Ae=d.parameters)==null?void 0:Ae.docs)==null?void 0:_e.source}}};var Ge,Ke,ke;n.parameters={...n.parameters,docs:{...(Ge=n.parameters)==null?void 0:Ge.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="number">Number</Label>
      <Input type="number" id="number" placeholder="0" />
    </div>
}`,...(ke=(Ke=n.parameters)==null?void 0:Ke.docs)==null?void 0:ke.source}}};var Be,Ce,Je;m.parameters={...m.parameters,docs:{...(Be=m.parameters)==null?void 0:Be.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="search">Search</Label>
      <Input type="search" id="search" placeholder="Search..." />
    </div>
}`,...(Je=(Ce=m.parameters)==null?void 0:Ce.docs)==null?void 0:Je.source}}};var Qe,Xe,Ye;c.parameters={...c.parameters,docs:{...(Qe=c.parameters)==null?void 0:Qe.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-helper">Email</Label>
      <Input type="email" id="email-helper" placeholder="Email" />
      <p className="text-sm text-muted-foreground">
        We'll never share your email with anyone else.
      </p>
    </div>
}`,...(Ye=(Xe=c.parameters)==null?void 0:Xe.docs)==null?void 0:Ye.source}}};var Ze,$e,er;p.parameters={...p.parameters,docs:{...(Ze=p.parameters)==null?void 0:Ze.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-error">Email</Label>
      <Input type="email" id="email-error" placeholder="Email" className="border-red-500" />
      <p className="text-sm text-red-500">
        Please enter a valid email address.
      </p>
    </div>
}`,...(er=($e=p.parameters)==null?void 0:$e.docs)==null?void 0:er.source}}};var rr,ar,sr;u.parameters={...u.parameters,docs:{...(rr=u.parameters)==null?void 0:rr.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="picture">Picture</Label>
      <Input id="picture" type="file" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'File input for uploading files.'
      }
    }
  }
}`,...(sr=(ar=u.parameters)==null?void 0:ar.docs)==null?void 0:sr.source}}};var tr,lr,ir;h.parameters={...h.parameters,docs:{...(tr=h.parameters)==null?void 0:tr.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="long-placeholder">Input</Label>
      <Input id="long-placeholder" placeholder="This is a very long placeholder text that might get truncated depending on the input width" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input with very long placeholder text to test truncation.'
      }
    }
  }
}`,...(ir=(lr=h.parameters)==null?void 0:lr.docs)==null?void 0:ir.source}}};var or,dr,nr;g.parameters={...g.parameters,docs:{...(or=g.parameters)==null?void 0:or.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="long-value">Input</Label>
      <Input id="long-value" defaultValue="This is a very long input value that extends beyond the visible area and requires horizontal scrolling to see the full content" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input with very long value to test overflow behavior.'
      }
    }
  }
}`,...(nr=(dr=g.parameters)==null?void 0:dr.docs)==null?void 0:nr.source}}};var mr,cr,pr;x.parameters={...x.parameters,docs:{...(mr=x.parameters)==null?void 0:mr.docs,source:{originalSource:`{
  render: () => <div className="grid w-32 items-center gap-1.5">
      <Label htmlFor="min-width">Narrow</Label>
      <Input id="min-width" placeholder="Text" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input with minimal width constraint.'
      }
    }
  }
}`,...(pr=(cr=x.parameters)==null?void 0:cr.docs)==null?void 0:pr.source}}};var ur,hr,gr;w.parameters={...w.parameters,docs:{...(ur=w.parameters)==null?void 0:ur.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-4xl items-center gap-1.5">
      <Label htmlFor="full-width">Full Width Input</Label>
      <Input id="full-width" placeholder="This input spans the full width" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input that spans full width of container.'
      }
    }
  }
}`,...(gr=(hr=w.parameters)==null?void 0:hr.docs)==null?void 0:gr.source}}};var xr,wr,vr;v.parameters={...v.parameters,docs:{...(xr=v.parameters)==null?void 0:xr.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="readonly">Read Only</Label>
      <Input id="readonly" defaultValue="This value cannot be changed" readOnly />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Read-only input that displays but cannot be edited.'
      }
    }
  }
}`,...(vr=(wr=v.parameters)==null?void 0:wr.docs)==null?void 0:vr.source}}};var br,fr,yr;b.parameters={...b.parameters,docs:{...(br=b.parameters)==null?void 0:br.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="maxlength">Username (max 10 characters)</Label>
      <Input id="maxlength" placeholder="Username" maxLength={10} />
      <p className="text-sm text-muted-foreground">
        Maximum 10 characters allowed.
      </p>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input with maximum length constraint.'
      }
    }
  }
}`,...(yr=(fr=b.parameters)==null?void 0:fr.docs)==null?void 0:yr.source}}};var Nr,Lr,Ir;f.parameters={...f.parameters,docs:{...(Nr=f.parameters)==null?void 0:Nr.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="pattern">Phone Number</Label>
      <Input id="pattern" type="tel" placeholder="(123) 456-7890" pattern="[0-9]{3}-[0-9]{3}-[0-9]{4}" />
      <p className="text-sm text-muted-foreground">
        Format: 123-456-7890
      </p>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input with pattern validation for phone numbers.'
      }
    }
  }
}`,...(Ir=(Lr=f.parameters)==null?void 0:Lr.docs)==null?void 0:Ir.source}}};var Fr,jr,Sr;y.parameters={...y.parameters,docs:{...(Fr=y.parameters)==null?void 0:Fr.docs,source:{originalSource:`{
  render: () => <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="required">
        Email <span className="text-red-500">*</span>
      </Label>
      <Input id="required" type="email" placeholder="Email" required />
      <p className="text-sm text-muted-foreground">
        This field is required.
      </p>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Required input field with visual indicator.'
      }
    }
  }
}`,...(Sr=(jr=y.parameters)==null?void 0:jr.docs)==null?void 0:Sr.source}}};const Hr=["Default","WithLabel","WithValue","Disabled","Password","Email","Number","Search","WithHelperText","WithError","File","LongPlaceholder","LongValue","MinWidth","FullWidth","ReadOnly","WithMaxLength","WithPattern","Required"];export{s as Default,i as Disabled,d as Email,u as File,w as FullWidth,h as LongPlaceholder,g as LongValue,x as MinWidth,n as Number,o as Password,v as ReadOnly,y as Required,m as Search,p as WithError,c as WithHelperText,t as WithLabel,b as WithMaxLength,f as WithPattern,l as WithValue,Hr as __namedExportsOrder,Mr as default};
