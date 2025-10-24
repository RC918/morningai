import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as l}from"./index-Dz3UJJSw.js";import{u as Ve,c as rs}from"./utils-ClSdSIbF.js";import{c as cs,a as os,b as U}from"./createLucideIcon-CPl_Fi5k.js";import{u as is,a as ds,C as ns}from"./check-IE6dqsU4.js";import{P as ls}from"./index-WZXaWNJA.js";import{P as O}from"./index-CWPL_hnH.js";import{L as r}from"./label-CQdBpAJ_.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-CYANIyVc.js";import"./index-fUCaa9pg.js";var D="Checkbox",[ms]=cs(D),[ps,A]=ms(D);function hs(a){const{__scopeCheckbox:o,checked:n,children:h,defaultChecked:i,disabled:s,form:b,name:u,onCheckedChange:m,required:S,value:I="on",internal_do_not_use_render:p}=a,[x,R]=os({prop:n,defaultProp:i??!1,onChange:m,caller:D}),[E,_]=l.useState(null),[P,c]=l.useState(null),d=l.useRef(!1),T=E?!!b||!!E.closest("form"):!0,M={checked:x,disabled:s,setChecked:R,control:E,setControl:_,name:u,form:b,value:I,hasConsumerStoppedPropagationRef:d,required:S,defaultChecked:w(i)?!1:i,isFormControl:T,bubbleInput:P,setBubbleInput:c};return e.jsx(ps,{scope:o,...M,children:xs(p)?p(M):h})}var Xe="CheckboxTrigger",$e=l.forwardRef(({__scopeCheckbox:a,onKeyDown:o,onClick:n,...h},i)=>{const{control:s,value:b,disabled:u,checked:m,required:S,setControl:I,setChecked:p,hasConsumerStoppedPropagationRef:x,isFormControl:R,bubbleInput:E}=A(Xe,a),_=Ve(i,I),P=l.useRef(m);return l.useEffect(()=>{const c=s==null?void 0:s.form;if(c){const d=()=>p(P.current);return c.addEventListener("reset",d),()=>c.removeEventListener("reset",d)}},[s,p]),e.jsx(O.button,{type:"button",role:"checkbox","aria-checked":w(m)?"mixed":m,"aria-required":S,"data-state":ss(m),"data-disabled":u?"":void 0,disabled:u,value:b,...h,ref:_,onKeyDown:U(o,c=>{c.key==="Enter"&&c.preventDefault()}),onClick:U(n,c=>{p(d=>w(d)?!0:!d),E&&R&&(x.current=c.isPropagationStopped(),x.current||c.stopPropagation())})})});$e.displayName=Xe;var Je=l.forwardRef((a,o)=>{const{__scopeCheckbox:n,name:h,checked:i,defaultChecked:s,required:b,disabled:u,value:m,onCheckedChange:S,form:I,...p}=a;return e.jsx(hs,{__scopeCheckbox:n,checked:i,defaultChecked:s,disabled:u,required:b,onCheckedChange:S,name:h,form:I,value:m,internal_do_not_use_render:({isFormControl:x})=>e.jsxs(e.Fragment,{children:[e.jsx($e,{...p,ref:o,__scopeCheckbox:n}),x&&e.jsx(es,{__scopeCheckbox:n})]})})});Je.displayName=D;var Qe="CheckboxIndicator",Ye=l.forwardRef((a,o)=>{const{__scopeCheckbox:n,forceMount:h,...i}=a,s=A(Qe,n);return e.jsx(ls,{present:h||w(s.checked)||s.checked===!0,children:e.jsx(O.span,{"data-state":ss(s.checked),"data-disabled":s.disabled?"":void 0,...i,ref:o,style:{pointerEvents:"none",...a.style}})})});Ye.displayName=Qe;var Ze="CheckboxBubbleInput",es=l.forwardRef(({__scopeCheckbox:a,...o},n)=>{const{control:h,hasConsumerStoppedPropagationRef:i,checked:s,defaultChecked:b,required:u,disabled:m,name:S,value:I,form:p,bubbleInput:x,setBubbleInput:R}=A(Ze,a),E=Ve(n,R),_=is(s),P=ds(h);l.useEffect(()=>{const d=x;if(!d)return;const T=window.HTMLInputElement.prototype,B=Object.getOwnPropertyDescriptor(T,"checked").set,as=!i.current;if(_!==s&&B){const ts=new Event("click",{bubbles:as});d.indeterminate=w(s),B.call(d,w(s)?!1:s),d.dispatchEvent(ts)}},[x,_,s,i]);const c=l.useRef(w(s)?!1:s);return e.jsx(O.input,{type:"checkbox","aria-hidden":!0,defaultChecked:b??c.current,required:u,disabled:m,name:S,value:I,form:p,...o,tabIndex:-1,ref:E,style:{...o.style,...P,position:"absolute",pointerEvents:"none",opacity:0,margin:0,transform:"translateX(-100%)"}})});es.displayName=Ze;function xs(a){return typeof a=="function"}function w(a){return a==="indeterminate"}function ss(a){return w(a)?"indeterminate":a?"checked":"unchecked"}function t({className:a,...o}){return e.jsx(Je,{"data-slot":"checkbox",className:rs("peer border-input dark:bg-input/30 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground dark:data-[state=checked]:bg-primary data-[state=checked]:border-primary focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive size-4 shrink-0 rounded-[4px] border shadow-xs transition-shadow outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50",a),...o,children:e.jsx(Ye,{"data-slot":"checkbox-indicator",className:"flex items-center justify-center text-current transition-none",children:e.jsx(ns,{className:"size-3.5"})})})}t.__docgenInfo={description:"",methods:[],displayName:"Checkbox"};t.__docgenInfo={description:"",methods:[],displayName:"Checkbox"};const Fs={title:"UI/Checkbox",component:t,parameters:{layout:"centered",docs:{description:{component:`
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
        `}}},tags:["autodocs"],argTypes:{checked:{control:"boolean",description:"Whether the checkbox is checked",table:{type:{summary:'boolean | "indeterminate"'},defaultValue:{summary:"false"}}},disabled:{control:"boolean",description:"Whether the checkbox is disabled",table:{type:{summary:"boolean"},defaultValue:{summary:"false"}}},onCheckedChange:{action:"checkedChanged",description:"Function called when checked state changes",table:{type:{summary:"(checked: boolean) => void"}}}}},k={render:()=>e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"terms"}),e.jsx(r,{htmlFor:"terms",children:"Accept terms and conditions"})]})},f={render:()=>e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"checked",defaultChecked:!0}),e.jsx(r,{htmlFor:"checked",children:"This checkbox is checked by default"})]}),parameters:{docs:{description:{story:"Checkbox with default checked state."}}}},v={render:()=>e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"disabled",disabled:!0}),e.jsx(r,{htmlFor:"disabled",children:"This checkbox is disabled"})]}),parameters:{docs:{description:{story:"Checkbox in disabled state - user cannot interact with it."}}}},g={render:()=>e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"disabled-checked",disabled:!0,defaultChecked:!0}),e.jsx(r,{htmlFor:"disabled-checked",children:"Disabled and checked"})]}),parameters:{docs:{description:{story:"Checkbox that is both disabled and checked."}}}},C={render:()=>e.jsx(t,{}),parameters:{docs:{description:{story:"Checkbox without a label - not recommended for accessibility."}}}},y={render:()=>e.jsxs("div",{className:"space-y-4",children:[e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"option1"}),e.jsx(r,{htmlFor:"option1",children:"Option 1"})]}),e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"option2"}),e.jsx(r,{htmlFor:"option2",children:"Option 2"})]}),e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"option3"}),e.jsx(r,{htmlFor:"option3",children:"Option 3"})]})]}),parameters:{docs:{description:{story:"Multiple checkboxes in a group for selecting multiple options."}}}},N={render:()=>e.jsxs("div",{className:"flex items-start space-x-2 max-w-md",children:[e.jsx(t,{id:"long-label",className:"mt-1"}),e.jsx(r,{htmlFor:"long-label",className:"leading-relaxed",children:"I agree to the terms and conditions, privacy policy, and all other legal documents that govern the use of this application and its services"})]}),parameters:{docs:{description:{story:"Checkbox with very long label text to test text wrapping."}}}},L={render:()=>e.jsxs("div",{className:"flex items-start space-x-2 max-w-md",children:[e.jsx(t,{id:"with-description",className:"mt-1"}),e.jsxs("div",{className:"grid gap-1.5 leading-none",children:[e.jsx(r,{htmlFor:"with-description",children:"Marketing emails"}),e.jsx("p",{className:"text-sm text-muted-foreground",children:"Receive emails about new products, features, and more."})]})]}),parameters:{docs:{description:{story:"Checkbox with label and additional description text."}}}},j={render:()=>e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"interactive",onCheckedChange:a=>console.log("Checked:",a)}),e.jsx(r,{htmlFor:"interactive",children:"Click me (check console)"})]}),parameters:{docs:{description:{story:"Interactive checkbox that logs state changes to console."}}}},F={render:()=>e.jsx("form",{className:"space-y-4",children:e.jsxs("div",{className:"space-y-2",children:[e.jsx("h3",{className:"text-sm font-medium",children:"Select your interests:"}),e.jsxs("div",{className:"space-y-2",children:[e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"tech"}),e.jsx(r,{htmlFor:"tech",children:"Technology"})]}),e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"design"}),e.jsx(r,{htmlFor:"design",children:"Design"})]}),e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"business"}),e.jsx(r,{htmlFor:"business",children:"Business"})]}),e.jsxs("div",{className:"flex items-center space-x-2",children:[e.jsx(t,{id:"marketing"}),e.jsx(r,{htmlFor:"marketing",children:"Marketing"})]})]})]})}),parameters:{docs:{description:{story:"Example of checkboxes used in a form context."}}}};var W,q,z;k.parameters={...k.parameters,docs:{...(W=k.parameters)==null?void 0:W.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="terms" />
      <Label htmlFor="terms">Accept terms and conditions</Label>
    </div>
}`,...(z=(q=k.parameters)==null?void 0:q.docs)==null?void 0:z.source}}};var G,H,K;f.parameters={...f.parameters,docs:{...(G=f.parameters)==null?void 0:G.docs,source:{originalSource:`{
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
}`,...(K=(H=f.parameters)==null?void 0:H.docs)==null?void 0:K.source}}};var V,X,$;v.parameters={...v.parameters,docs:{...(V=v.parameters)==null?void 0:V.docs,source:{originalSource:`{
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
}`,...($=(X=v.parameters)==null?void 0:X.docs)==null?void 0:$.source}}};var J,Q,Y;g.parameters={...g.parameters,docs:{...(J=g.parameters)==null?void 0:J.docs,source:{originalSource:`{
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
}`,...(Y=(Q=g.parameters)==null?void 0:Q.docs)==null?void 0:Y.source}}};var Z,ee,se;C.parameters={...C.parameters,docs:{...(Z=C.parameters)==null?void 0:Z.docs,source:{originalSource:`{
  render: () => <Checkbox />,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox without a label - not recommended for accessibility.'
      }
    }
  }
}`,...(se=(ee=C.parameters)==null?void 0:ee.docs)==null?void 0:se.source}}};var ae,te,re;y.parameters={...y.parameters,docs:{...(ae=y.parameters)==null?void 0:ae.docs,source:{originalSource:`{
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
}`,...(re=(te=y.parameters)==null?void 0:te.docs)==null?void 0:re.source}}};var ce,oe,ie;N.parameters={...N.parameters,docs:{...(ce=N.parameters)==null?void 0:ce.docs,source:{originalSource:`{
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
}`,...(ie=(oe=N.parameters)==null?void 0:oe.docs)==null?void 0:ie.source}}};var de,ne,le;L.parameters={...L.parameters,docs:{...(de=L.parameters)==null?void 0:de.docs,source:{originalSource:`{
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
}`,...(le=(ne=L.parameters)==null?void 0:ne.docs)==null?void 0:le.source}}};var me,pe,he;j.parameters={...j.parameters,docs:{...(me=j.parameters)==null?void 0:me.docs,source:{originalSource:`{
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
}`,...(he=(pe=j.parameters)==null?void 0:pe.docs)==null?void 0:he.source}}};var xe,be,ue;F.parameters={...F.parameters,docs:{...(xe=F.parameters)==null?void 0:xe.docs,source:{originalSource:`{
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
}`,...(ue=(be=F.parameters)==null?void 0:be.docs)==null?void 0:ue.source}}};var ke,fe,ve;k.parameters={...k.parameters,docs:{...(ke=k.parameters)==null?void 0:ke.docs,source:{originalSource:`{
  render: () => <div className="flex items-center space-x-2">
      <Checkbox id="terms" />
      <Label htmlFor="terms">Accept terms and conditions</Label>
    </div>
}`,...(ve=(fe=k.parameters)==null?void 0:fe.docs)==null?void 0:ve.source}}};var ge,Ce,ye;f.parameters={...f.parameters,docs:{...(ge=f.parameters)==null?void 0:ge.docs,source:{originalSource:`{
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
}`,...(ye=(Ce=f.parameters)==null?void 0:Ce.docs)==null?void 0:ye.source}}};var Ne,Le,je;v.parameters={...v.parameters,docs:{...(Ne=v.parameters)==null?void 0:Ne.docs,source:{originalSource:`{
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
}`,...(je=(Le=v.parameters)==null?void 0:Le.docs)==null?void 0:je.source}}};var Fe,we,Se;g.parameters={...g.parameters,docs:{...(Fe=g.parameters)==null?void 0:Fe.docs,source:{originalSource:`{
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
}`,...(Se=(we=g.parameters)==null?void 0:we.docs)==null?void 0:Se.source}}};var Ie,Ee,_e;C.parameters={...C.parameters,docs:{...(Ie=C.parameters)==null?void 0:Ie.docs,source:{originalSource:`{
  render: () => <Checkbox />,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox without a label - not recommended for accessibility.'
      }
    }
  }
}`,...(_e=(Ee=C.parameters)==null?void 0:Ee.docs)==null?void 0:_e.source}}};var Re,Pe,De;y.parameters={...y.parameters,docs:{...(Re=y.parameters)==null?void 0:Re.docs,source:{originalSource:`{
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
}`,...(De=(Pe=y.parameters)==null?void 0:Pe.docs)==null?void 0:De.source}}};var Te,Me,Oe;N.parameters={...N.parameters,docs:{...(Te=N.parameters)==null?void 0:Te.docs,source:{originalSource:`{
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
}`,...(Oe=(Me=N.parameters)==null?void 0:Me.docs)==null?void 0:Oe.source}}};var Ae,Be,Ue;L.parameters={...L.parameters,docs:{...(Ae=L.parameters)==null?void 0:Ae.docs,source:{originalSource:`{
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
}`,...(Ue=(Be=L.parameters)==null?void 0:Be.docs)==null?void 0:Ue.source}}};var We,qe,ze;j.parameters={...j.parameters,docs:{...(We=j.parameters)==null?void 0:We.docs,source:{originalSource:`{
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
}`,...(ze=(qe=j.parameters)==null?void 0:qe.docs)==null?void 0:ze.source}}};var Ge,He,Ke;F.parameters={...F.parameters,docs:{...(Ge=F.parameters)==null?void 0:Ge.docs,source:{originalSource:`{
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
}`,...(Ke=(He=F.parameters)==null?void 0:He.docs)==null?void 0:Ke.source}}};const ws=["Default","Checked","Disabled","DisabledChecked","WithoutLabel","MultipleCheckboxes","LongLabel","WithDescription","Interactive","FormExample"];export{f as Checked,k as Default,v as Disabled,g as DisabledChecked,F as FormExample,j as Interactive,N as LongLabel,y as MultipleCheckboxes,L as WithDescription,C as WithoutLabel,ws as __namedExportsOrder,Fs as default};
