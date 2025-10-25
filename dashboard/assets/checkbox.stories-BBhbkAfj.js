import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{C as s}from"./checkbox-eZoktWGv.js";import{L as a}from"./label-WhgGRHqT.js";import"./storybook-vendor-CPzy2iGn.js";import"./react-vendor-Bzgz95E1.js";import"./index-CXs_xfTS.js";import"./index-CfloHgh8.js";import"./index-Gg2jh08l.js";import"./index-BmE017Ss.js";import"./index-C8zJyAUy.js";import"./index-DY-33XIg.js";import"./index-DRUeUdNs.js";import"./index-CAPShSkS.js";import"./utils-D-KgF5mV.js";import"./check-SZfaZqqj.js";import"./createLucideIcon-DgPn5ReF.js";const Re={title:"UI/Checkbox",component:s,parameters:{layout:"centered",docs:{description:{component:`
The Checkbox component allows users to select one or more options from a set. It's built on top of Radix UI's Checkbox primitive for maximum accessibility.

### Usage Guidelines
- Use for binary choices (yes/no, on/off)
- Use for selecting multiple items from a list
- Always pair with a descriptive label
- Use indeterminate state for "select all" functionality
- Group related checkboxes together

### Accessibility
- Full keyboard support (Space to toggle, Tab to navigate)
- Screen reader announces checked/unchecked state
- Proper ARIA attributes (aria-checked, aria-label)
- Focus indicators for keyboard navigation
- Supports disabled state
        `}}},tags:["autodocs"],argTypes:{checked:{control:"boolean",description:"Whether the checkbox is checked",table:{type:{summary:'boolean | "indeterminate"'},defaultValue:{summary:"false"}}},disabled:{control:"boolean",description:"Whether the checkbox is disabled",table:{type:{summary:"boolean"},defaultValue:{summary:"false"}}},onCheckedChange:{action:"checkedChanged",description:"Function called when checked state changes",table:{type:{summary:"(checked: boolean) => void"}}}}},t={render:()=>e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"terms"}),e.jsx(a,{htmlFor:"terms",children:"Accept terms and conditions"})]})},r={render:()=>e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"checked",defaultChecked:!0}),e.jsx(a,{htmlFor:"checked",children:"This checkbox is checked by default"})]}),parameters:{docs:{description:{story:"Checkbox with default checked state."}}}},c={render:()=>e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"disabled",disabled:!0}),e.jsx(a,{htmlFor:"disabled",children:"This checkbox is disabled"})]}),parameters:{docs:{description:{story:"Checkbox in disabled state - user cannot interact with it."}}}},i={render:()=>e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"disabled-checked",disabled:!0,defaultChecked:!0}),e.jsx(a,{htmlFor:"disabled-checked",children:"Disabled and checked"})]}),parameters:{docs:{description:{story:"Checkbox that is both disabled and checked."}}}},o={render:()=>e.jsx(s,{}),parameters:{docs:{description:{story:"Checkbox without a label - not recommended for accessibility."}}}},d={render:()=>e.jsxs("div",{className:"space-y-4",children:[e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"option1"}),e.jsx(a,{htmlFor:"option1",children:"Option 1"})]}),e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"option2"}),e.jsx(a,{htmlFor:"option2",children:"Option 2"})]}),e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"option3"}),e.jsx(a,{htmlFor:"option3",children:"Option 3"})]})]}),parameters:{docs:{description:{story:"Multiple checkboxes in a group for selecting multiple options."}}}},l={render:()=>e.jsxs("div",{className:"flex items-start space-x-2 max-w-md",children:[e.jsx(s,{id:"long-label",className:"mt-1"}),e.jsx(a,{htmlFor:"long-label",className:"leading-relaxed",children:"I agree to the terms and conditions, privacy policy, and all other legal documents that govern the use of this application and its services"})]}),parameters:{docs:{description:{story:"Checkbox with very long label text to test text wrapping."}}}},n={render:()=>e.jsxs("div",{className:"flex items-start space-x-2 max-w-md",children:[e.jsx(s,{id:"with-description",className:"mt-1"}),e.jsxs("div",{className:"grid gap-1.5 leading-none",children:[e.jsx(a,{htmlFor:"with-description",children:"Marketing emails"}),e.jsx("p",{className:"text-sm text-muted-foreground",children:"Receive emails about new products, features, and more."})]})]}),parameters:{docs:{description:{story:"Checkbox with label and additional description text."}}}},m={render:()=>e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"interactive",onCheckedChange:ge=>console.log("Checked:",ge)}),e.jsx(a,{htmlFor:"interactive",children:"Click me (check console)"})]}),parameters:{docs:{description:{story:"Interactive checkbox that logs state changes to console."}}}},p={render:()=>e.jsx("form",{className:"space-y-4",children:e.jsxs("div",{className:"space-y-2",children:[e.jsx("h3",{className:"text-sm font-medium",children:"Select your interests:"}),e.jsxs("div",{className:"space-y-2",children:[e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"tech"}),e.jsx(a,{htmlFor:"tech",children:"Technology"})]}),e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"design"}),e.jsx(a,{htmlFor:"design",children:"Design"})]}),e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"business"}),e.jsx(a,{htmlFor:"business",children:"Business"})]}),e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(s,{id:"marketing"}),e.jsx(a,{htmlFor:"marketing",children:"Marketing"})]})]})]})}),parameters:{docs:{description:{story:"Example of checkboxes used in a form context."}}}};var h,x,b;t.parameters={...t.parameters,docs:{...(h=t.parameters)==null?void 0:h.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="terms" />
      <Label htmlFor="terms">Accept terms and conditions</Label>
    </div>
}`,...(b=(x=t.parameters)==null?void 0:x.docs)==null?void 0:b.source}}};var u,k,v;r.parameters={...r.parameters,docs:{...(u=r.parameters)==null?void 0:u.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="checked" defaultChecked />
      <Label htmlFor="checked">This checkbox is checked by default</Label>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox with default checked state.'
      }
    }
  }
}`,...(v=(k=r.parameters)==null?void 0:k.docs)==null?void 0:v.source}}};var g,f,C;c.parameters={...c.parameters,docs:{...(g=c.parameters)==null?void 0:g.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="disabled" disabled />
      <Label htmlFor="disabled">This checkbox is disabled</Label>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox in disabled state - user cannot interact with it.'
      }
    }
  }
}`,...(C=(f=c.parameters)==null?void 0:f.docs)==null?void 0:C.source}}};var y,N,L;i.parameters={...i.parameters,docs:{...(y=i.parameters)==null?void 0:y.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="disabled-checked" disabled defaultChecked />
      <Label htmlFor="disabled-checked">Disabled and checked</Label>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox that is both disabled and checked.'
      }
    }
  }
}`,...(L=(N=i.parameters)==null?void 0:N.docs)==null?void 0:L.source}}};var j,F,w;o.parameters={...o.parameters,docs:{...(j=o.parameters)==null?void 0:j.docs,source:{originalSource:`{
  render: () => <Checkbox />,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox without a label - not recommended for accessibility.'
      }
    }
  }
}`,...(w=(F=o.parameters)==null?void 0:F.docs)==null?void 0:w.source}}};var S,D,I;d.parameters={...d.parameters,docs:{...(S=d.parameters)==null?void 0:S.docs,source:{originalSource:`{
  render: () => <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Checkbox id="option1" />
        <Label htmlFor="option1">Option 1</Label>
      </div>
      <div className="flex items-center space-x-2">
        <Checkbox id="option2" />
        <Label htmlFor="option2">Option 2</Label>
      </div>
      <div className="flex items-center space-x-2">
        <Checkbox id="option3" />
        <Label htmlFor="option3">Option 3</Label>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple checkboxes in a group for selecting multiple options.'
      }
    }
  }
}`,...(I=(D=d.parameters)==null?void 0:D.docs)==null?void 0:I.source}}};var T,M,O;l.parameters={...l.parameters,docs:{...(T=l.parameters)==null?void 0:T.docs,source:{originalSource:`{
  render: () => <div className="flex items-start space-x-2 max-w-md">
      <Checkbox id="long-label" className="mt-1" />
      <Label htmlFor="long-label" className="leading-relaxed">
        I agree to the terms and conditions, privacy policy, and all other legal documents that govern the use of this application and its services
      </Label>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox with very long label text to test text wrapping.'
      }
    }
  }
}`,...(O=(M=l.parameters)==null?void 0:M.docs)==null?void 0:O.source}}};var A,E,R;n.parameters={...n.parameters,docs:{...(A=n.parameters)==null?void 0:A.docs,source:{originalSource:`{
  render: () => <div className="flex items-start space-x-2 max-w-md">
      <Checkbox id="with-description" className="mt-1" />
      <div className="grid gap-1.5 leading-none">
        <Label htmlFor="with-description">Marketing emails</Label>
        <p className="text-sm text-muted-foreground">
          Receive emails about new products, features, and more.
        </p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox with label and additional description text.'
      }
    }
  }
}`,...(R=(E=n.parameters)==null?void 0:E.docs)==null?void 0:R.source}}};var U,W,B;m.parameters={...m.parameters,docs:{...(U=m.parameters)==null?void 0:U.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="interactive" onCheckedChange={checked => console.log('Checked:', checked)} />
      <Label htmlFor="interactive">Click me (check console)</Label>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Interactive checkbox that logs state changes to console.'
      }
    }
  }
}`,...(B=(W=m.parameters)==null?void 0:W.docs)==null?void 0:B.source}}};var G,V,_;p.parameters={...p.parameters,docs:{...(G=p.parameters)==null?void 0:G.docs,source:{originalSource:`{
  render: () => <form className="space-y-4">
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Select your interests:</h3>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox id="tech" />
            <Label htmlFor="tech">Technology</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="design" />
            <Label htmlFor="design">Design</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="business" />
            <Label htmlFor="business">Business</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="marketing" />
            <Label htmlFor="marketing">Marketing</Label>
          </div>
        </div>
      </div>
    </form>,
  parameters: {
    docs: {
      description: {
        story: 'Example of checkboxes used in a form context.'
      }
    }
  }
}`,...(_=(V=p.parameters)==null?void 0:V.docs)==null?void 0:_.source}}};var P,q,z;t.parameters={...t.parameters,docs:{...(P=t.parameters)==null?void 0:P.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="terms" />
      <Label htmlFor="terms">Accept terms and conditions</Label>
    </div>
}`,...(z=(q=t.parameters)==null?void 0:q.docs)==null?void 0:z.source}}};var H,J,K;r.parameters={...r.parameters,docs:{...(H=r.parameters)==null?void 0:H.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="checked" defaultChecked />
      <Label htmlFor="checked">This checkbox is checked by default</Label>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox with default checked state.'
      }
    }
  }
}`,...(K=(J=r.parameters)==null?void 0:J.docs)==null?void 0:K.source}}};var Q,X,Y;c.parameters={...c.parameters,docs:{...(Q=c.parameters)==null?void 0:Q.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="disabled" disabled />
      <Label htmlFor="disabled">This checkbox is disabled</Label>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox in disabled state - user cannot interact with it.'
      }
    }
  }
}`,...(Y=(X=c.parameters)==null?void 0:X.docs)==null?void 0:Y.source}}};var Z,$,ee;i.parameters={...i.parameters,docs:{...(Z=i.parameters)==null?void 0:Z.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="disabled-checked" disabled defaultChecked />
      <Label htmlFor="disabled-checked">Disabled and checked</Label>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox that is both disabled and checked.'
      }
    }
  }
}`,...(ee=($=i.parameters)==null?void 0:$.docs)==null?void 0:ee.source}}};var se,ae,te;o.parameters={...o.parameters,docs:{...(se=o.parameters)==null?void 0:se.docs,source:{originalSource:`{
  render: () => <Checkbox />,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox without a label - not recommended for accessibility.'
      }
    }
  }
}`,...(te=(ae=o.parameters)==null?void 0:ae.docs)==null?void 0:te.source}}};var re,ce,ie;d.parameters={...d.parameters,docs:{...(re=d.parameters)==null?void 0:re.docs,source:{originalSource:`{
  render: () => <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Checkbox id="option1" />
        <Label htmlFor="option1">Option 1</Label>
      </div>
      <div className="flex items-center space-x-2">
        <Checkbox id="option2" />
        <Label htmlFor="option2">Option 2</Label>
      </div>
      <div className="flex items-center space-x-2">
        <Checkbox id="option3" />
        <Label htmlFor="option3">Option 3</Label>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple checkboxes in a group for selecting multiple options.'
      }
    }
  }
}`,...(ie=(ce=d.parameters)==null?void 0:ce.docs)==null?void 0:ie.source}}};var oe,de,le;l.parameters={...l.parameters,docs:{...(oe=l.parameters)==null?void 0:oe.docs,source:{originalSource:`{
  render: () => <div className="flex items-start space-x-2 max-w-md">
      <Checkbox id="long-label" className="mt-1" />
      <Label htmlFor="long-label" className="leading-relaxed">
        I agree to the terms and conditions, privacy policy, and all other legal documents that govern the use of this application and its services
      </Label>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox with very long label text to test text wrapping.'
      }
    }
  }
}`,...(le=(de=l.parameters)==null?void 0:de.docs)==null?void 0:le.source}}};var ne,me,pe;n.parameters={...n.parameters,docs:{...(ne=n.parameters)==null?void 0:ne.docs,source:{originalSource:`{
  render: () => <div className="flex items-start space-x-2 max-w-md">
      <Checkbox id="with-description" className="mt-1" />
      <div className="grid gap-1.5 leading-none">
        <Label htmlFor="with-description">Marketing emails</Label>
        <p className="text-sm text-muted-foreground">
          Receive emails about new products, features, and more.
        </p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox with label and additional description text.'
      }
    }
  }
}`,...(pe=(me=n.parameters)==null?void 0:me.docs)==null?void 0:pe.source}}};var he,xe,be;m.parameters={...m.parameters,docs:{...(he=m.parameters)==null?void 0:he.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="interactive" onCheckedChange={checked => console.log('Checked:', checked)} />
      <Label htmlFor="interactive">Click me (check console)</Label>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Interactive checkbox that logs state changes to console.'
      }
    }
  }
}`,...(be=(xe=m.parameters)==null?void 0:xe.docs)==null?void 0:be.source}}};var ue,ke,ve;p.parameters={...p.parameters,docs:{...(ue=p.parameters)==null?void 0:ue.docs,source:{originalSource:`{
  render: () => <form className="space-y-4">
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Select your interests:</h3>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox id="tech" />
            <Label htmlFor="tech">Technology</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="design" />
            <Label htmlFor="design">Design</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="business" />
            <Label htmlFor="business">Business</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="marketing" />
            <Label htmlFor="marketing">Marketing</Label>
          </div>
        </div>
      </div>
    </form>,
  parameters: {
    docs: {
      description: {
        story: 'Example of checkboxes used in a form context.'
      }
    }
  }
}`,...(ve=(ke=p.parameters)==null?void 0:ke.docs)==null?void 0:ve.source}}};const Ue=["Default","Checked","Disabled","DisabledChecked","WithoutLabel","MultipleCheckboxes","LongLabel","WithDescription","Interactive","FormExample"];export{r as Checked,t as Default,c as Disabled,i as DisabledChecked,p as FormExample,m as Interactive,l as LongLabel,d as MultipleCheckboxes,n as WithDescription,o as WithoutLabel,Ue as __namedExportsOrder,Re as default};
