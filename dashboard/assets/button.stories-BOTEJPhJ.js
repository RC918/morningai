import{j as B}from"./jsx-runtime-D_zvdyIk.js";import{B as v}from"./button-CRXPg0Vw.js";import"./storybook-vendor-CPzy2iGn.js";import"./react-vendor-Bzgz95E1.js";import"./index-CXs_xfTS.js";import"./index-CGrAONsN.js";import"./utils-D-KgF5mV.js";const Cr={title:"UI/Button",component:v,parameters:{layout:"centered",docs:{description:{component:`
The Button component is the primary interactive element in our design system. It provides consistent styling and behavior across the application.

### Usage Guidelines
- Use \`default\` variant for primary actions
- Use \`destructive\` for dangerous actions (delete, remove)
- Use \`outline\` for secondary actions
- Use \`ghost\` for subtle actions in toolbars
- Use \`link\` for navigation that looks like text
- Use \`icon\` size for buttons containing only icons

### Accessibility
- Automatically includes proper ARIA attributes
- Supports keyboard navigation (Enter/Space)
- Maintains focus management
- Screen reader compatible
        `}}},tags:["autodocs"],argTypes:{variant:{control:"select",options:["default","destructive","outline","secondary","ghost","link"],description:"Visual style variant of the button",table:{type:{summary:"string"},defaultValue:{summary:"default"}}},size:{control:"select",options:["default","sm","lg","icon"],description:"Size of the button",table:{type:{summary:"string"},defaultValue:{summary:"default"}}},disabled:{control:"boolean",description:"Whether the button is disabled",table:{type:{summary:"boolean"},defaultValue:{summary:"false"}}},onClick:{action:"clicked",description:"Function called when button is clicked",table:{type:{summary:"() => void"}}},children:{control:"text",description:"Content to display inside the button",table:{type:{summary:"ReactNode"}}}}},e={args:{children:"Button",variant:"default"}},r={args:{children:"Delete",variant:"destructive"}},n={args:{children:"Outline",variant:"outline"}},t={args:{children:"Secondary",variant:"secondary"}},s={args:{children:"Ghost",variant:"ghost"}},a={args:{children:"Link",variant:"link"}},o={args:{children:"Small Button",size:"sm"}},i={args:{children:"Large Button",size:"lg"}},c={args:{children:"🔍",size:"icon"}},d={args:{children:"Disabled",disabled:!0}},m={args:{children:"Click Me",onClick:()=>alert("Button clicked!")}},p={args:{children:"This is a very long button text that might wrap or truncate depending on the container width"},parameters:{docs:{description:{story:"Button with very long text content to test text wrapping and layout behavior."}}}},u={args:{children:"A",size:"sm"},parameters:{docs:{description:{story:"Button with minimal content to test minimum size constraints."}}}},l={args:{children:""},parameters:{docs:{description:{story:"Button with no content - should maintain minimum height and padding."}}}},g={args:{children:"🚀 Launch"},parameters:{docs:{description:{story:"Button with emoji content to test unicode character support."}}}},h={args:{children:`Line 1
Line 2
Line 3`},parameters:{docs:{description:{story:"Button with multiline text (newlines) to test text handling."}}}},y={render:()=>B.jsxs(v,{disabled:!0,children:[B.jsx("span",{className:"mr-2",children:"⏳"}),"Loading..."]}),parameters:{docs:{description:{story:"Button in loading state with spinner icon."}}}},S={render:()=>B.jsxs(v,{children:[B.jsx("span",{className:"mr-2",children:"📁"}),"Open File"]}),parameters:{docs:{description:{story:"Button with icon and text content."}}}};var b,w,x;e.parameters={...e.parameters,docs:{...(b=e.parameters)==null?void 0:b.docs,source:{originalSource:`{
  args: {
    children: 'Button',
    variant: 'default'
  }
}`,...(x=(w=e.parameters)==null?void 0:w.docs)==null?void 0:x.source}}};var L,k,f;r.parameters={...r.parameters,docs:{...(L=r.parameters)==null?void 0:L.docs,source:{originalSource:`{
  args: {
    children: 'Delete',
    variant: 'destructive'
  }
}`,...(f=(k=r.parameters)==null?void 0:k.docs)==null?void 0:f.source}}};var z,C,D;n.parameters={...n.parameters,docs:{...(z=n.parameters)==null?void 0:z.docs,source:{originalSource:`{
  args: {
    children: 'Outline',
    variant: 'outline'
  }
}`,...(D=(C=n.parameters)==null?void 0:C.docs)==null?void 0:D.source}}};var j,O,T;t.parameters={...t.parameters,docs:{...(j=t.parameters)==null?void 0:j.docs,source:{originalSource:`{
  args: {
    children: 'Secondary',
    variant: 'secondary'
  }
}`,...(T=(O=t.parameters)==null?void 0:O.docs)==null?void 0:T.source}}};var U,A,E;s.parameters={...s.parameters,docs:{...(U=s.parameters)==null?void 0:U.docs,source:{originalSource:`{
  args: {
    children: 'Ghost',
    variant: 'ghost'
  }
}`,...(E=(A=s.parameters)==null?void 0:A.docs)==null?void 0:E.source}}};var I,N,W;a.parameters={...a.parameters,docs:{...(I=a.parameters)==null?void 0:I.docs,source:{originalSource:`{
  args: {
    children: 'Link',
    variant: 'link'
  }
}`,...(W=(N=a.parameters)==null?void 0:N.docs)==null?void 0:W.source}}};var G,M,F;o.parameters={...o.parameters,docs:{...(G=o.parameters)==null?void 0:G.docs,source:{originalSource:`{
  args: {
    children: 'Small Button',
    size: 'sm'
  }
}`,...(F=(M=o.parameters)==null?void 0:M.docs)==null?void 0:F.source}}};var V,R,_;i.parameters={...i.parameters,docs:{...(V=i.parameters)==null?void 0:V.docs,source:{originalSource:`{
  args: {
    children: 'Large Button',
    size: 'lg'
  }
}`,...(_=(R=i.parameters)==null?void 0:R.docs)==null?void 0:_.source}}};var q,H,J;c.parameters={...c.parameters,docs:{...(q=c.parameters)==null?void 0:q.docs,source:{originalSource:`{
  args: {
    children: '🔍',
    size: 'icon'
  }
}`,...(J=(H=c.parameters)==null?void 0:H.docs)==null?void 0:J.source}}};var K,P,Q;d.parameters={...d.parameters,docs:{...(K=d.parameters)==null?void 0:K.docs,source:{originalSource:`{
  args: {
    children: 'Disabled',
    disabled: true
  }
}`,...(Q=(P=d.parameters)==null?void 0:P.docs)==null?void 0:Q.source}}};var X,Y,Z;m.parameters={...m.parameters,docs:{...(X=m.parameters)==null?void 0:X.docs,source:{originalSource:`{
  args: {
    children: 'Click Me',
    onClick: () => alert('Button clicked!')
  }
}`,...(Z=(Y=m.parameters)==null?void 0:Y.docs)==null?void 0:Z.source}}};var $,ee,re;p.parameters={...p.parameters,docs:{...($=p.parameters)==null?void 0:$.docs,source:{originalSource:`{
  args: {
    children: 'This is a very long button text that might wrap or truncate depending on the container width'
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with very long text content to test text wrapping and layout behavior.'
      }
    }
  }
}`,...(re=(ee=p.parameters)==null?void 0:ee.docs)==null?void 0:re.source}}};var ne,te,se;u.parameters={...u.parameters,docs:{...(ne=u.parameters)==null?void 0:ne.docs,source:{originalSource:`{
  args: {
    children: 'A',
    size: 'sm'
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with minimal content to test minimum size constraints.'
      }
    }
  }
}`,...(se=(te=u.parameters)==null?void 0:te.docs)==null?void 0:se.source}}};var ae,oe,ie;l.parameters={...l.parameters,docs:{...(ae=l.parameters)==null?void 0:ae.docs,source:{originalSource:`{
  args: {
    children: ''
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with no content - should maintain minimum height and padding.'
      }
    }
  }
}`,...(ie=(oe=l.parameters)==null?void 0:oe.docs)==null?void 0:ie.source}}};var ce,de,me;g.parameters={...g.parameters,docs:{...(ce=g.parameters)==null?void 0:ce.docs,source:{originalSource:`{
  args: {
    children: '🚀 Launch'
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with emoji content to test unicode character support.'
      }
    }
  }
}`,...(me=(de=g.parameters)==null?void 0:de.docs)==null?void 0:me.source}}};var pe,ue,le;h.parameters={...h.parameters,docs:{...(pe=h.parameters)==null?void 0:pe.docs,source:{originalSource:`{
  args: {
    children: 'Line 1\\nLine 2\\nLine 3'
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with multiline text (newlines) to test text handling.'
      }
    }
  }
}`,...(le=(ue=h.parameters)==null?void 0:ue.docs)==null?void 0:le.source}}};var ge,he,ye;y.parameters={...y.parameters,docs:{...(ge=y.parameters)==null?void 0:ge.docs,source:{originalSource:`{
  render: () => <Button disabled>
      <span className="mr-2">⏳</span>
      Loading...
    </Button>,
  parameters: {
    docs: {
      description: {
        story: 'Button in loading state with spinner icon.'
      }
    }
  }
}`,...(ye=(he=y.parameters)==null?void 0:he.docs)==null?void 0:ye.source}}};var Se,Be,ve;S.parameters={...S.parameters,docs:{...(Se=S.parameters)==null?void 0:Se.docs,source:{originalSource:`{
  render: () => <Button>
      <span className="mr-2">📁</span>
      Open File
    </Button>,
  parameters: {
    docs: {
      description: {
        story: 'Button with icon and text content.'
      }
    }
  }
}`,...(ve=(Be=S.parameters)==null?void 0:Be.docs)==null?void 0:ve.source}}};var be,we,xe;e.parameters={...e.parameters,docs:{...(be=e.parameters)==null?void 0:be.docs,source:{originalSource:`{
  args: {
    children: 'Button',
    variant: 'default'
  }
}`,...(xe=(we=e.parameters)==null?void 0:we.docs)==null?void 0:xe.source}}};var Le,ke,fe;r.parameters={...r.parameters,docs:{...(Le=r.parameters)==null?void 0:Le.docs,source:{originalSource:`{
  args: {
    children: 'Delete',
    variant: 'destructive'
  }
}`,...(fe=(ke=r.parameters)==null?void 0:ke.docs)==null?void 0:fe.source}}};var ze,Ce,De;n.parameters={...n.parameters,docs:{...(ze=n.parameters)==null?void 0:ze.docs,source:{originalSource:`{
  args: {
    children: 'Outline',
    variant: 'outline'
  }
}`,...(De=(Ce=n.parameters)==null?void 0:Ce.docs)==null?void 0:De.source}}};var je,Oe,Te;t.parameters={...t.parameters,docs:{...(je=t.parameters)==null?void 0:je.docs,source:{originalSource:`{
  args: {
    children: 'Secondary',
    variant: 'secondary'
  }
}`,...(Te=(Oe=t.parameters)==null?void 0:Oe.docs)==null?void 0:Te.source}}};var Ue,Ae,Ee;s.parameters={...s.parameters,docs:{...(Ue=s.parameters)==null?void 0:Ue.docs,source:{originalSource:`{
  args: {
    children: 'Ghost',
    variant: 'ghost'
  }
}`,...(Ee=(Ae=s.parameters)==null?void 0:Ae.docs)==null?void 0:Ee.source}}};var Ie,Ne,We;a.parameters={...a.parameters,docs:{...(Ie=a.parameters)==null?void 0:Ie.docs,source:{originalSource:`{
  args: {
    children: 'Link',
    variant: 'link'
  }
}`,...(We=(Ne=a.parameters)==null?void 0:Ne.docs)==null?void 0:We.source}}};var Ge,Me,Fe;o.parameters={...o.parameters,docs:{...(Ge=o.parameters)==null?void 0:Ge.docs,source:{originalSource:`{
  args: {
    children: 'Small Button',
    size: 'sm'
  }
}`,...(Fe=(Me=o.parameters)==null?void 0:Me.docs)==null?void 0:Fe.source}}};var Ve,Re,_e;i.parameters={...i.parameters,docs:{...(Ve=i.parameters)==null?void 0:Ve.docs,source:{originalSource:`{
  args: {
    children: 'Large Button',
    size: 'lg'
  }
}`,...(_e=(Re=i.parameters)==null?void 0:Re.docs)==null?void 0:_e.source}}};var qe,He,Je;c.parameters={...c.parameters,docs:{...(qe=c.parameters)==null?void 0:qe.docs,source:{originalSource:`{
  args: {
    children: '🔍',
    size: 'icon'
  }
}`,...(Je=(He=c.parameters)==null?void 0:He.docs)==null?void 0:Je.source}}};var Ke,Pe,Qe;d.parameters={...d.parameters,docs:{...(Ke=d.parameters)==null?void 0:Ke.docs,source:{originalSource:`{
  args: {
    children: 'Disabled',
    disabled: true
  }
}`,...(Qe=(Pe=d.parameters)==null?void 0:Pe.docs)==null?void 0:Qe.source}}};var Xe,Ye,Ze;m.parameters={...m.parameters,docs:{...(Xe=m.parameters)==null?void 0:Xe.docs,source:{originalSource:`{
  args: {
    children: 'Click Me',
    onClick: () => alert('Button clicked!')
  }
}`,...(Ze=(Ye=m.parameters)==null?void 0:Ye.docs)==null?void 0:Ze.source}}};var $e,er,rr;p.parameters={...p.parameters,docs:{...($e=p.parameters)==null?void 0:$e.docs,source:{originalSource:`{
  args: {
    children: 'This is a very long button text that might wrap or truncate depending on the container width'
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with very long text content to test text wrapping and layout behavior.'
      }
    }
  }
}`,...(rr=(er=p.parameters)==null?void 0:er.docs)==null?void 0:rr.source}}};var nr,tr,sr;u.parameters={...u.parameters,docs:{...(nr=u.parameters)==null?void 0:nr.docs,source:{originalSource:`{
  args: {
    children: 'A',
    size: 'sm'
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with minimal content to test minimum size constraints.'
      }
    }
  }
}`,...(sr=(tr=u.parameters)==null?void 0:tr.docs)==null?void 0:sr.source}}};var ar,or,ir;l.parameters={...l.parameters,docs:{...(ar=l.parameters)==null?void 0:ar.docs,source:{originalSource:`{
  args: {
    children: ''
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with no content - should maintain minimum height and padding.'
      }
    }
  }
}`,...(ir=(or=l.parameters)==null?void 0:or.docs)==null?void 0:ir.source}}};var cr,dr,mr;g.parameters={...g.parameters,docs:{...(cr=g.parameters)==null?void 0:cr.docs,source:{originalSource:`{
  args: {
    children: '🚀 Launch'
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with emoji content to test unicode character support.'
      }
    }
  }
}`,...(mr=(dr=g.parameters)==null?void 0:dr.docs)==null?void 0:mr.source}}};var pr,ur,lr;h.parameters={...h.parameters,docs:{...(pr=h.parameters)==null?void 0:pr.docs,source:{originalSource:`{
  args: {
    children: 'Line 1\\nLine 2\\nLine 3'
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with multiline text (newlines) to test text handling.'
      }
    }
  }
}`,...(lr=(ur=h.parameters)==null?void 0:ur.docs)==null?void 0:lr.source}}};var gr,hr,yr;y.parameters={...y.parameters,docs:{...(gr=y.parameters)==null?void 0:gr.docs,source:{originalSource:`{
  render: () => <Button disabled>
      <span className="mr-2">⏳</span>
      Loading...
    </Button>,
  parameters: {
    docs: {
      description: {
        story: 'Button in loading state with spinner icon.'
      }
    }
  }
}`,...(yr=(hr=y.parameters)==null?void 0:hr.docs)==null?void 0:yr.source}}};var Sr,Br,vr;S.parameters={...S.parameters,docs:{...(Sr=S.parameters)==null?void 0:Sr.docs,source:{originalSource:`{
  render: () => <Button>
      <span className="mr-2">📁</span>
      Open File
    </Button>,
  parameters: {
    docs: {
      description: {
        story: 'Button with icon and text content.'
      }
    }
  }
}`,...(vr=(Br=S.parameters)==null?void 0:Br.docs)==null?void 0:vr.source}}};const Dr=["Default","Destructive","Outline","Secondary","Ghost","Link","Small","Large","Icon","Disabled","WithClick","LongText","SingleCharacter","EmptyButton","WithEmoji","MultilineText","Loading","WithIcon"];export{e as Default,r as Destructive,d as Disabled,l as EmptyButton,s as Ghost,c as Icon,i as Large,a as Link,y as Loading,p as LongText,h as MultilineText,n as Outline,t as Secondary,u as SingleCharacter,o as Small,m as WithClick,g as WithEmoji,S as WithIcon,Dr as __namedExportsOrder,Cr as default};
