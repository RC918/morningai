import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{B as a}from"./badge-BEslsuGz.js";import"./index-Dz3UJJSw.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-DRuEWG1E.js";import"./index-CGrAONsN.js";import"./utils-D-KgF5mV.js";const fa={title:"UI/Badge",component:a,parameters:{layout:"centered",docs:{description:{component:`
The Badge component is used to highlight status, counts, or categories in a compact visual format. It's perfect for displaying metadata or drawing attention to specific information.

### Usage Guidelines
- Use for status indicators (active, pending, error)
- Display counts or notifications
- Tag items with categories
- Keep text short and concise
- Choose appropriate variant for the context
- Use sparingly to maintain visual hierarchy

### Accessibility
- Semantic HTML structure
- Screen reader compatible
- Sufficient color contrast
- Can be made focusable if interactive
        `}}},tags:["autodocs"],argTypes:{variant:{control:"select",options:["default","secondary","destructive","outline"],description:"Visual style variant of the badge",table:{type:{summary:"string"},defaultValue:{summary:"default"}}},children:{control:"text",description:"Content to display in the badge",table:{type:{summary:"ReactNode"}}}}},r={args:{children:"Badge"}},s={args:{children:"Secondary",variant:"secondary"}},t={args:{children:"Destructive",variant:"destructive"}},n={args:{children:"Outline",variant:"outline"}},i={render:()=>e.jsxs(a,{children:[e.jsx("span",{className:"mr-1",children:"✓"}),"Success"]})},d={render:()=>e.jsxs("div",{className:"flex gap-2",children:[e.jsx(a,{variant:"default",children:"Active"}),e.jsx(a,{variant:"secondary",children:"Pending"}),e.jsx(a,{variant:"destructive",children:"Error"}),e.jsx(a,{variant:"outline",children:"Draft"})]})},c={render:()=>e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(a,{className:"text-xs",children:"Small"}),e.jsx(a,{children:"Medium"}),e.jsx(a,{className:"text-base px-3 py-1",children:"Large"})]})},o={render:()=>e.jsxs("div",{className:"flex gap-2",children:[e.jsx(a,{children:"New 3"}),e.jsx(a,{variant:"destructive",children:"Errors 12"}),e.jsx(a,{variant:"secondary",children:"Pending 5"})]})},l={render:()=>e.jsx(a,{className:"cursor-pointer hover:opacity-80",onClick:()=>alert("Badge clicked!"),children:"Click me"}),parameters:{docs:{description:{story:"Interactive badge with click handler."}}}},m={args:{children:"This is a very long badge text that might wrap"},parameters:{docs:{description:{story:"Badge with long text to test wrapping behavior."}}}},g={args:{children:"1"},parameters:{docs:{description:{story:"Badge with minimal single character content."}}}},p={render:()=>e.jsxs("div",{className:"flex gap-2",children:[e.jsx(a,{children:"🔥 Hot"}),e.jsx(a,{variant:"secondary",children:"⭐ Featured"}),e.jsx(a,{variant:"destructive",children:"❌ Error"})]}),parameters:{docs:{description:{story:"Badges with emoji icons for visual emphasis."}}}},u={render:()=>e.jsxs("div",{className:"flex gap-2",children:[e.jsx(a,{children:"1"}),e.jsx(a,{variant:"secondary",children:"99+"}),e.jsx(a,{variant:"destructive",children:"-5"}),e.jsx(a,{variant:"outline",children:"0"})]}),parameters:{docs:{description:{story:"Badges displaying numeric values."}}}},v={args:{children:""},parameters:{docs:{description:{story:"Badge with no content - should maintain minimum size."}}}},h={render:()=>e.jsxs("div",{className:"flex flex-wrap gap-2 max-w-md",children:[e.jsx(a,{children:"React"}),e.jsx(a,{variant:"secondary",children:"TypeScript"}),e.jsx(a,{variant:"outline",children:"Tailwind"}),e.jsx(a,{children:"Vite"}),e.jsx(a,{variant:"secondary",children:"Storybook"}),e.jsx(a,{variant:"outline",children:"ESLint"}),e.jsx(a,{children:"Prettier"}),e.jsx(a,{variant:"secondary",children:"pnpm"})]}),parameters:{docs:{description:{story:"Multiple badges used as tags with wrapping."}}}},B={render:()=>e.jsxs("p",{className:"max-w-md",children:["This is a paragraph with an inline ",e.jsx(a,{children:"badge"})," component. It should flow naturally with the surrounding text and maintain proper spacing."]}),parameters:{docs:{description:{story:"Badge used inline within text content."}}}},x={render:()=>e.jsxs("div",{className:"space-y-4",children:[e.jsxs("div",{children:[e.jsx("h3",{className:"text-sm font-medium mb-2",children:"Default"}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx(a,{children:"Active"}),e.jsx(a,{children:"New"}),e.jsx(a,{children:"Featured"})]})]}),e.jsxs("div",{children:[e.jsx("h3",{className:"text-sm font-medium mb-2",children:"Secondary"}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx(a,{variant:"secondary",children:"Pending"}),e.jsx(a,{variant:"secondary",children:"Draft"}),e.jsx(a,{variant:"secondary",children:"Review"})]})]}),e.jsxs("div",{children:[e.jsx("h3",{className:"text-sm font-medium mb-2",children:"Destructive"}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx(a,{variant:"destructive",children:"Error"}),e.jsx(a,{variant:"destructive",children:"Failed"}),e.jsx(a,{variant:"destructive",children:"Blocked"})]})]}),e.jsxs("div",{children:[e.jsx("h3",{className:"text-sm font-medium mb-2",children:"Outline"}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx(a,{variant:"outline",children:"Info"}),e.jsx(a,{variant:"outline",children:"Note"}),e.jsx(a,{variant:"outline",children:"Optional"})]})]})]}),parameters:{docs:{description:{story:"Comprehensive showcase of all badge variants with examples."}}}};var y,f,N;r.parameters={...r.parameters,docs:{...(y=r.parameters)==null?void 0:y.docs,source:{originalSource:`{
  args: {
    children: 'Badge'
  }
}`,...(N=(f=r.parameters)==null?void 0:f.docs)==null?void 0:N.source}}};var j,w,S;s.parameters={...s.parameters,docs:{...(j=s.parameters)==null?void 0:j.docs,source:{originalSource:`{
  args: {
    children: 'Secondary',
    variant: 'secondary'
  }
}`,...(S=(w=s.parameters)==null?void 0:w.docs)==null?void 0:S.source}}};var b,E,k;t.parameters={...t.parameters,docs:{...(b=t.parameters)==null?void 0:b.docs,source:{originalSource:`{
  args: {
    children: 'Destructive',
    variant: 'destructive'
  }
}`,...(k=(E=t.parameters)==null?void 0:E.docs)==null?void 0:k.source}}};var D,T,C;n.parameters={...n.parameters,docs:{...(D=n.parameters)==null?void 0:D.docs,source:{originalSource:`{
  args: {
    children: 'Outline',
    variant: 'outline'
  }
}`,...(C=(T=n.parameters)==null?void 0:T.docs)==null?void 0:C.source}}};var I,O,P;i.parameters={...i.parameters,docs:{...(I=i.parameters)==null?void 0:I.docs,source:{originalSource:`{
  render: () => <Badge>
      <span className="mr-1">✓</span>
      Success
    </Badge>
}`,...(P=(O=i.parameters)==null?void 0:O.docs)==null?void 0:P.source}}};var A,F,L;d.parameters={...d.parameters,docs:{...(A=d.parameters)==null?void 0:A.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge variant="default">Active</Badge>
      <Badge variant="secondary">Pending</Badge>
      <Badge variant="destructive">Error</Badge>
      <Badge variant="outline">Draft</Badge>
    </div>
}`,...(L=(F=d.parameters)==null?void 0:F.docs)==null?void 0:L.source}}};var M,R,V;c.parameters={...c.parameters,docs:{...(M=c.parameters)==null?void 0:M.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-2">
      <Badge className="text-xs">Small</Badge>
      <Badge>Medium</Badge>
      <Badge className="text-base px-3 py-1">Large</Badge>
    </div>
}`,...(V=(R=c.parameters)==null?void 0:R.docs)==null?void 0:V.source}}};var W,z,H;o.parameters={...o.parameters,docs:{...(W=o.parameters)==null?void 0:W.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge>New 3</Badge>
      <Badge variant="destructive">Errors 12</Badge>
      <Badge variant="secondary">Pending 5</Badge>
    </div>
}`,...(H=(z=o.parameters)==null?void 0:z.docs)==null?void 0:H.source}}};var U,_,G;l.parameters={...l.parameters,docs:{...(U=l.parameters)==null?void 0:U.docs,source:{originalSource:`{
  render: () => <Badge className="cursor-pointer hover:opacity-80" onClick={() => alert('Badge clicked!')}>
      Click me
    </Badge>,
  parameters: {
    docs: {
      description: {
        story: 'Interactive badge with click handler.'
      }
    }
  }
}`,...(G=(_=l.parameters)==null?void 0:_.docs)==null?void 0:G.source}}};var K,q,J;m.parameters={...m.parameters,docs:{...(K=m.parameters)==null?void 0:K.docs,source:{originalSource:`{
  args: {
    children: 'This is a very long badge text that might wrap'
  },
  parameters: {
    docs: {
      description: {
        story: 'Badge with long text to test wrapping behavior.'
      }
    }
  }
}`,...(J=(q=m.parameters)==null?void 0:q.docs)==null?void 0:J.source}}};var Q,X,Y;g.parameters={...g.parameters,docs:{...(Q=g.parameters)==null?void 0:Q.docs,source:{originalSource:`{
  args: {
    children: '1'
  },
  parameters: {
    docs: {
      description: {
        story: 'Badge with minimal single character content.'
      }
    }
  }
}`,...(Y=(X=g.parameters)==null?void 0:X.docs)==null?void 0:Y.source}}};var Z,$,ee;p.parameters={...p.parameters,docs:{...(Z=p.parameters)==null?void 0:Z.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge>🔥 Hot</Badge>
      <Badge variant="secondary">⭐ Featured</Badge>
      <Badge variant="destructive">❌ Error</Badge>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Badges with emoji icons for visual emphasis.'
      }
    }
  }
}`,...(ee=($=p.parameters)==null?void 0:$.docs)==null?void 0:ee.source}}};var ae,re,se;u.parameters={...u.parameters,docs:{...(ae=u.parameters)==null?void 0:ae.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge>1</Badge>
      <Badge variant="secondary">99+</Badge>
      <Badge variant="destructive">-5</Badge>
      <Badge variant="outline">0</Badge>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Badges displaying numeric values.'
      }
    }
  }
}`,...(se=(re=u.parameters)==null?void 0:re.docs)==null?void 0:se.source}}};var te,ne,ie;v.parameters={...v.parameters,docs:{...(te=v.parameters)==null?void 0:te.docs,source:{originalSource:`{
  args: {
    children: ''
  },
  parameters: {
    docs: {
      description: {
        story: 'Badge with no content - should maintain minimum size.'
      }
    }
  }
}`,...(ie=(ne=v.parameters)==null?void 0:ne.docs)==null?void 0:ie.source}}};var de,ce,oe;h.parameters={...h.parameters,docs:{...(de=h.parameters)==null?void 0:de.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2 max-w-md">
      <Badge>React</Badge>
      <Badge variant="secondary">TypeScript</Badge>
      <Badge variant="outline">Tailwind</Badge>
      <Badge>Vite</Badge>
      <Badge variant="secondary">Storybook</Badge>
      <Badge variant="outline">ESLint</Badge>
      <Badge>Prettier</Badge>
      <Badge variant="secondary">pnpm</Badge>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple badges used as tags with wrapping.'
      }
    }
  }
}`,...(oe=(ce=h.parameters)==null?void 0:ce.docs)==null?void 0:oe.source}}};var le,me,ge;B.parameters={...B.parameters,docs:{...(le=B.parameters)==null?void 0:le.docs,source:{originalSource:`{
  render: () => <p className="max-w-md">
      This is a paragraph with an inline <Badge>badge</Badge> component. It should flow naturally with the surrounding text and maintain proper spacing.
    </p>,
  parameters: {
    docs: {
      description: {
        story: 'Badge used inline within text content.'
      }
    }
  }
}`,...(ge=(me=B.parameters)==null?void 0:me.docs)==null?void 0:ge.source}}};var pe,ue,ve;x.parameters={...x.parameters,docs:{...(pe=x.parameters)==null?void 0:pe.docs,source:{originalSource:`{
  render: () => <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium mb-2">Default</h3>
        <div className="flex gap-2">
          <Badge>Active</Badge>
          <Badge>New</Badge>
          <Badge>Featured</Badge>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-medium mb-2">Secondary</h3>
        <div className="flex gap-2">
          <Badge variant="secondary">Pending</Badge>
          <Badge variant="secondary">Draft</Badge>
          <Badge variant="secondary">Review</Badge>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-medium mb-2">Destructive</h3>
        <div className="flex gap-2">
          <Badge variant="destructive">Error</Badge>
          <Badge variant="destructive">Failed</Badge>
          <Badge variant="destructive">Blocked</Badge>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-medium mb-2">Outline</h3>
        <div className="flex gap-2">
          <Badge variant="outline">Info</Badge>
          <Badge variant="outline">Note</Badge>
          <Badge variant="outline">Optional</Badge>
        </div>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Comprehensive showcase of all badge variants with examples.'
      }
    }
  }
}`,...(ve=(ue=x.parameters)==null?void 0:ue.docs)==null?void 0:ve.source}}};var he,Be,xe;r.parameters={...r.parameters,docs:{...(he=r.parameters)==null?void 0:he.docs,source:{originalSource:`{
  args: {
    children: 'Badge'
  }
}`,...(xe=(Be=r.parameters)==null?void 0:Be.docs)==null?void 0:xe.source}}};var ye,fe,Ne;s.parameters={...s.parameters,docs:{...(ye=s.parameters)==null?void 0:ye.docs,source:{originalSource:`{
  args: {
    children: 'Secondary',
    variant: 'secondary'
  }
}`,...(Ne=(fe=s.parameters)==null?void 0:fe.docs)==null?void 0:Ne.source}}};var je,we,Se;t.parameters={...t.parameters,docs:{...(je=t.parameters)==null?void 0:je.docs,source:{originalSource:`{
  args: {
    children: 'Destructive',
    variant: 'destructive'
  }
}`,...(Se=(we=t.parameters)==null?void 0:we.docs)==null?void 0:Se.source}}};var be,Ee,ke;n.parameters={...n.parameters,docs:{...(be=n.parameters)==null?void 0:be.docs,source:{originalSource:`{
  args: {
    children: 'Outline',
    variant: 'outline'
  }
}`,...(ke=(Ee=n.parameters)==null?void 0:Ee.docs)==null?void 0:ke.source}}};var De,Te,Ce;i.parameters={...i.parameters,docs:{...(De=i.parameters)==null?void 0:De.docs,source:{originalSource:`{
  render: () => <Badge>
      <span className="mr-1">✓</span>
      Success
    </Badge>
}`,...(Ce=(Te=i.parameters)==null?void 0:Te.docs)==null?void 0:Ce.source}}};var Ie,Oe,Pe;d.parameters={...d.parameters,docs:{...(Ie=d.parameters)==null?void 0:Ie.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge variant="default">Active</Badge>
      <Badge variant="secondary">Pending</Badge>
      <Badge variant="destructive">Error</Badge>
      <Badge variant="outline">Draft</Badge>
    </div>
}`,...(Pe=(Oe=d.parameters)==null?void 0:Oe.docs)==null?void 0:Pe.source}}};var Ae,Fe,Le;c.parameters={...c.parameters,docs:{...(Ae=c.parameters)==null?void 0:Ae.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-2">
      <Badge className="text-xs">Small</Badge>
      <Badge>Medium</Badge>
      <Badge className="text-base px-3 py-1">Large</Badge>
    </div>
}`,...(Le=(Fe=c.parameters)==null?void 0:Fe.docs)==null?void 0:Le.source}}};var Me,Re,Ve;o.parameters={...o.parameters,docs:{...(Me=o.parameters)==null?void 0:Me.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge>New 3</Badge>
      <Badge variant="destructive">Errors 12</Badge>
      <Badge variant="secondary">Pending 5</Badge>
    </div>
}`,...(Ve=(Re=o.parameters)==null?void 0:Re.docs)==null?void 0:Ve.source}}};var We,ze,He;l.parameters={...l.parameters,docs:{...(We=l.parameters)==null?void 0:We.docs,source:{originalSource:`{
  render: () => <Badge className="cursor-pointer hover:opacity-80" onClick={() => alert('Badge clicked!')}>
      Click me
    </Badge>,
  parameters: {
    docs: {
      description: {
        story: 'Interactive badge with click handler.'
      }
    }
  }
}`,...(He=(ze=l.parameters)==null?void 0:ze.docs)==null?void 0:He.source}}};var Ue,_e,Ge;m.parameters={...m.parameters,docs:{...(Ue=m.parameters)==null?void 0:Ue.docs,source:{originalSource:`{
  args: {
    children: 'This is a very long badge text that might wrap'
  },
  parameters: {
    docs: {
      description: {
        story: 'Badge with long text to test wrapping behavior.'
      }
    }
  }
}`,...(Ge=(_e=m.parameters)==null?void 0:_e.docs)==null?void 0:Ge.source}}};var Ke,qe,Je;g.parameters={...g.parameters,docs:{...(Ke=g.parameters)==null?void 0:Ke.docs,source:{originalSource:`{
  args: {
    children: '1'
  },
  parameters: {
    docs: {
      description: {
        story: 'Badge with minimal single character content.'
      }
    }
  }
}`,...(Je=(qe=g.parameters)==null?void 0:qe.docs)==null?void 0:Je.source}}};var Qe,Xe,Ye;p.parameters={...p.parameters,docs:{...(Qe=p.parameters)==null?void 0:Qe.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge>🔥 Hot</Badge>
      <Badge variant="secondary">⭐ Featured</Badge>
      <Badge variant="destructive">❌ Error</Badge>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Badges with emoji icons for visual emphasis.'
      }
    }
  }
}`,...(Ye=(Xe=p.parameters)==null?void 0:Xe.docs)==null?void 0:Ye.source}}};var Ze,$e,ea;u.parameters={...u.parameters,docs:{...(Ze=u.parameters)==null?void 0:Ze.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Badge>1</Badge>
      <Badge variant="secondary">99+</Badge>
      <Badge variant="destructive">-5</Badge>
      <Badge variant="outline">0</Badge>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Badges displaying numeric values.'
      }
    }
  }
}`,...(ea=($e=u.parameters)==null?void 0:$e.docs)==null?void 0:ea.source}}};var aa,ra,sa;v.parameters={...v.parameters,docs:{...(aa=v.parameters)==null?void 0:aa.docs,source:{originalSource:`{
  args: {
    children: ''
  },
  parameters: {
    docs: {
      description: {
        story: 'Badge with no content - should maintain minimum size.'
      }
    }
  }
}`,...(sa=(ra=v.parameters)==null?void 0:ra.docs)==null?void 0:sa.source}}};var ta,na,ia;h.parameters={...h.parameters,docs:{...(ta=h.parameters)==null?void 0:ta.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2 max-w-md">
      <Badge>React</Badge>
      <Badge variant="secondary">TypeScript</Badge>
      <Badge variant="outline">Tailwind</Badge>
      <Badge>Vite</Badge>
      <Badge variant="secondary">Storybook</Badge>
      <Badge variant="outline">ESLint</Badge>
      <Badge>Prettier</Badge>
      <Badge variant="secondary">pnpm</Badge>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple badges used as tags with wrapping.'
      }
    }
  }
}`,...(ia=(na=h.parameters)==null?void 0:na.docs)==null?void 0:ia.source}}};var da,ca,oa;B.parameters={...B.parameters,docs:{...(da=B.parameters)==null?void 0:da.docs,source:{originalSource:`{
  render: () => <p className="max-w-md">
      This is a paragraph with an inline <Badge>badge</Badge> component. It should flow naturally with the surrounding text and maintain proper spacing.
    </p>,
  parameters: {
    docs: {
      description: {
        story: 'Badge used inline within text content.'
      }
    }
  }
}`,...(oa=(ca=B.parameters)==null?void 0:ca.docs)==null?void 0:oa.source}}};var la,ma,ga;x.parameters={...x.parameters,docs:{...(la=x.parameters)==null?void 0:la.docs,source:{originalSource:`{
  render: () => <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium mb-2">Default</h3>
        <div className="flex gap-2">
          <Badge>Active</Badge>
          <Badge>New</Badge>
          <Badge>Featured</Badge>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-medium mb-2">Secondary</h3>
        <div className="flex gap-2">
          <Badge variant="secondary">Pending</Badge>
          <Badge variant="secondary">Draft</Badge>
          <Badge variant="secondary">Review</Badge>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-medium mb-2">Destructive</h3>
        <div className="flex gap-2">
          <Badge variant="destructive">Error</Badge>
          <Badge variant="destructive">Failed</Badge>
          <Badge variant="destructive">Blocked</Badge>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-medium mb-2">Outline</h3>
        <div className="flex gap-2">
          <Badge variant="outline">Info</Badge>
          <Badge variant="outline">Note</Badge>
          <Badge variant="outline">Optional</Badge>
        </div>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Comprehensive showcase of all badge variants with examples.'
      }
    }
  }
}`,...(ga=(ma=x.parameters)==null?void 0:ma.docs)==null?void 0:ga.source}}};const Na=["Default","Secondary","Destructive","Outline","WithIcon","StatusBadges","Sizes","WithCount","Clickable","LongText","SingleCharacter","WithEmoji","Numbers","Empty","MultipleBadges","InText","AllVariants"];export{x as AllVariants,l as Clickable,r as Default,t as Destructive,v as Empty,B as InText,m as LongText,h as MultipleBadges,u as Numbers,n as Outline,s as Secondary,g as SingleCharacter,c as Sizes,d as StatusBadges,o as WithCount,p as WithEmoji,i as WithIcon,Na as __namedExportsOrder,fa as default};
