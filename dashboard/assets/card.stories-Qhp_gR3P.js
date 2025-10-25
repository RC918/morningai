import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{C as r,a as t,b as s,c as d,d as a,e as g}from"./card-BKJ3BdjB.js";import{B as f}from"./button-CRXPg0Vw.js";import{B as y}from"./badge-CFSTd3BP.js";import"./storybook-vendor-CPzy2iGn.js";import"./react-vendor-Bzgz95E1.js";import"./utils-D-KgF5mV.js";import"./index-CXs_xfTS.js";import"./index-CGrAONsN.js";const rr={title:"UI/Card",component:r,parameters:{layout:"centered",docs:{description:{component:`
The Card component is a foundational layout element that groups related information and actions. It's composed of multiple sub-components for maximum flexibility.

### Sub-components
- **Card**: Main container with border and shadow
- **CardHeader**: Optional header section
- **CardTitle**: Title text with appropriate sizing
- **CardDescription**: Subtitle or description text
- **CardContent**: Main content area
- **CardFooter**: Optional footer for actions

### Usage Guidelines
- Use for grouping related content and actions
- Include a title to describe the card's purpose
- Use description for additional context
- Place primary actions in the footer
- Keep content focused and concise
- Consider card width based on content

### Accessibility
- Semantic HTML structure
- Proper heading hierarchy
- Focus management for interactive elements
- Screen reader compatible
        `}}},tags:["autodocs"]},n={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Card Title"}),e.jsx(d,{children:"Card Description"})]}),e.jsx(a,{children:e.jsx("p",{children:"Card Content"})}),e.jsx(g,{children:e.jsx(f,{children:"Action"})})]})},i={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Notification"}),e.jsx(d,{children:"You have 3 unread messages."})]}),e.jsx(a,{children:e.jsx("p",{children:"Check your inbox for new updates."})})]})},o={render:()=>e.jsx(r,{className:"w-[350px]",children:e.jsx(a,{className:"pt-6",children:e.jsx("p",{children:"This card has no header, just content."})})})},c={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Recent Activity"}),e.jsx(d,{children:"Your latest actions"})]}),e.jsx(a,{children:e.jsxs("ul",{className:"space-y-2",children:[e.jsx("li",{children:"✓ Completed task A"}),e.jsx("li",{children:"✓ Updated profile"}),e.jsx("li",{children:"✓ Sent message"})]})})]})},l={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Confirm Action"}),e.jsx(d,{children:"Are you sure you want to proceed?"})]}),e.jsx(a,{children:e.jsx("p",{children:"This action cannot be undone."})}),e.jsxs(g,{className:"flex justify-between",children:[e.jsx(f,{variant:"outline",children:"Cancel"}),e.jsx(f,{children:"Confirm"})]})]})},C={render:()=>e.jsxs(r,{className:"w-[600px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Wide Card"}),e.jsx(d,{children:"This card is wider than the default"})]}),e.jsx(a,{children:e.jsx("p",{children:"Content can span across a wider area for more complex layouts."})})]}),parameters:{docs:{description:{story:"Card with wider width for more complex layouts."}}}},p={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"This is a very long card title that might wrap to multiple lines depending on the card width"}),e.jsx(d,{children:"Testing title wrapping behavior"})]}),e.jsx(a,{children:e.jsx("p",{children:"Card content goes here."})})]}),parameters:{docs:{description:{story:"Card with very long title to test text wrapping."}}}},m={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Article Preview"}),e.jsx(d,{children:"Latest blog post"})]}),e.jsx(a,{children:e.jsx("p",{className:"text-sm",children:"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."})}),e.jsx(g,{children:e.jsx(f,{children:"Read More"})})]}),parameters:{docs:{description:{story:"Card with long text content to test content overflow."}}}},u={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"A"}),e.jsx(d,{children:"B"})]}),e.jsx(a,{children:e.jsx("p",{children:"C"})})]}),parameters:{docs:{description:{story:"Card with minimal single-character content."}}}},h={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsx(s,{children:"Project Status"}),e.jsx(y,{children:"Active"})]}),e.jsx(d,{children:"Current project information"})]}),e.jsx(a,{children:e.jsxs("div",{className:"space-y-2",children:[e.jsxs("div",{className:"flex justify-between",children:[e.jsx("span",{children:"Tasks completed:"}),e.jsx(y,{variant:"secondary",children:"12/20"})]}),e.jsxs("div",{className:"flex justify-between",children:[e.jsx("span",{children:"Priority:"}),e.jsx(y,{variant:"destructive",children:"High"})]})]})})]}),parameters:{docs:{description:{story:"Card with Badge components for status indicators."}}}},x={render:()=>e.jsxs(r,{className:"w-[200px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Narrow"}),e.jsx(d,{children:"Small card"})]}),e.jsx(a,{children:e.jsx("p",{className:"text-sm",children:"Compact layout"})})]}),parameters:{docs:{description:{story:"Card with narrow width to test minimum size constraints."}}}},w={render:()=>e.jsxs(r,{className:"w-full max-w-4xl",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Full Width Card"}),e.jsx(d,{children:"This card spans the full width of its container"})]}),e.jsx(a,{children:e.jsx("p",{children:"Content can be displayed across the full width, useful for dashboard layouts or detailed information displays."})}),e.jsxs(g,{className:"flex justify-between",children:[e.jsx(f,{variant:"outline",children:"Secondary Action"}),e.jsx(f,{children:"Primary Action"})]})]}),parameters:{docs:{description:{story:"Card that spans full width with maximum width constraint."}}}},j={render:()=>e.jsxs("div",{className:"space-y-4 w-[350px]",children:[e.jsxs(r,{children:[e.jsxs(t,{children:[e.jsx(s,{children:"Card 1"}),e.jsx(d,{children:"First card in stack"})]}),e.jsx(a,{children:e.jsx("p",{children:"Content for first card"})})]}),e.jsxs(r,{children:[e.jsxs(t,{children:[e.jsx(s,{children:"Card 2"}),e.jsx(d,{children:"Second card in stack"})]}),e.jsx(a,{children:e.jsx("p",{children:"Content for second card"})})]}),e.jsxs(r,{children:[e.jsxs(t,{children:[e.jsx(s,{children:"Card 3"}),e.jsx(d,{children:"Third card in stack"})]}),e.jsx(a,{children:e.jsx("p",{children:"Content for third card"})})]})]}),parameters:{docs:{description:{story:"Multiple cards stacked vertically with consistent spacing."}}}};var T,v,N;n.parameters={...n.parameters,docs:{...(T=n.parameters)==null?void 0:T.docs,source:{originalSource:`{
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
}`,...(N=(v=n.parameters)==null?void 0:v.docs)==null?void 0:N.source}}};var D,H,B;i.parameters={...i.parameters,docs:{...(D=i.parameters)==null?void 0:D.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Notification</CardTitle>
        <CardDescription>You have 3 unread messages.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Check your inbox for new updates.</p>
      </CardContent>
    </Card>
}`,...(B=(H=i.parameters)==null?void 0:H.docs)==null?void 0:B.source}}};var S,b,A;o.parameters={...o.parameters,docs:{...(S=o.parameters)==null?void 0:S.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardContent className="pt-6">
        <p>This card has no header, just content.</p>
      </CardContent>
    </Card>
}`,...(A=(b=o.parameters)==null?void 0:b.docs)==null?void 0:A.source}}};var F,k,W;c.parameters={...c.parameters,docs:{...(F=c.parameters)==null?void 0:F.docs,source:{originalSource:`{
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
}`,...(W=(k=c.parameters)==null?void 0:k.docs)==null?void 0:W.source}}};var P,L,M;l.parameters={...l.parameters,docs:{...(P=l.parameters)==null?void 0:P.docs,source:{originalSource:`{
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
}`,...(M=(L=l.parameters)==null?void 0:L.docs)==null?void 0:M.source}}};var q,U,R;C.parameters={...C.parameters,docs:{...(q=C.parameters)==null?void 0:q.docs,source:{originalSource:`{
  render: () => <Card className="w-[600px]">
      <CardHeader>
        <CardTitle>Wide Card</CardTitle>
        <CardDescription>This card is wider than the default</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Content can span across a wider area for more complex layouts.</p>
      </CardContent>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with wider width for more complex layouts.'
      }
    }
  }
}`,...(R=(U=C.parameters)==null?void 0:U.docs)==null?void 0:R.source}}};var Y,z,I;p.parameters={...p.parameters,docs:{...(Y=p.parameters)==null?void 0:Y.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>This is a very long card title that might wrap to multiple lines depending on the card width</CardTitle>
        <CardDescription>Testing title wrapping behavior</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content goes here.</p>
      </CardContent>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with very long title to test text wrapping.'
      }
    }
  }
}`,...(I=(z=p.parameters)==null?void 0:z.docs)==null?void 0:I.source}}};var O,E,_;m.parameters={...m.parameters,docs:{...(O=m.parameters)==null?void 0:O.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Article Preview</CardTitle>
        <CardDescription>Latest blog post</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
        </p>
      </CardContent>
      <CardFooter>
        <Button>Read More</Button>
      </CardFooter>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with long text content to test content overflow.'
      }
    }
  }
}`,...(_=(E=m.parameters)==null?void 0:E.docs)==null?void 0:_.source}}};var G,K,J;u.parameters={...u.parameters,docs:{...(G=u.parameters)==null?void 0:G.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>A</CardTitle>
        <CardDescription>B</CardDescription>
      </CardHeader>
      <CardContent>
        <p>C</p>
      </CardContent>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with minimal single-character content.'
      }
    }
  }
}`,...(J=(K=u.parameters)==null?void 0:K.docs)==null?void 0:J.source}}};var Q,V,X;h.parameters={...h.parameters,docs:{...(Q=h.parameters)==null?void 0:Q.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Project Status</CardTitle>
          <Badge>Active</Badge>
        </div>
        <CardDescription>Current project information</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Tasks completed:</span>
            <Badge variant="secondary">12/20</Badge>
          </div>
          <div className="flex justify-between">
            <span>Priority:</span>
            <Badge variant="destructive">High</Badge>
          </div>
        </div>
      </CardContent>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with Badge components for status indicators.'
      }
    }
  }
}`,...(X=(V=h.parameters)==null?void 0:V.docs)==null?void 0:X.source}}};var Z,$,ee;x.parameters={...x.parameters,docs:{...(Z=x.parameters)==null?void 0:Z.docs,source:{originalSource:`{
  render: () => <Card className="w-[200px]">
      <CardHeader>
        <CardTitle>Narrow</CardTitle>
        <CardDescription>Small card</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">Compact layout</p>
      </CardContent>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with narrow width to test minimum size constraints.'
      }
    }
  }
}`,...(ee=($=x.parameters)==null?void 0:$.docs)==null?void 0:ee.source}}};var re,ae,te;w.parameters={...w.parameters,docs:{...(re=w.parameters)==null?void 0:re.docs,source:{originalSource:`{
  render: () => <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>Full Width Card</CardTitle>
        <CardDescription>This card spans the full width of its container</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Content can be displayed across the full width, useful for dashboard layouts or detailed information displays.</p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline">Secondary Action</Button>
        <Button>Primary Action</Button>
      </CardFooter>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card that spans full width with maximum width constraint.'
      }
    }
  }
}`,...(te=(ae=w.parameters)==null?void 0:ae.docs)==null?void 0:te.source}}};var se,de,ne;j.parameters={...j.parameters,docs:{...(se=j.parameters)==null?void 0:se.docs,source:{originalSource:`{
  render: () => <div className="space-y-4 w-[350px]">
      <Card>
        <CardHeader>
          <CardTitle>Card 1</CardTitle>
          <CardDescription>First card in stack</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Content for first card</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Card 2</CardTitle>
          <CardDescription>Second card in stack</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Content for second card</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Card 3</CardTitle>
          <CardDescription>Third card in stack</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Content for third card</p>
        </CardContent>
      </Card>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple cards stacked vertically with consistent spacing.'
      }
    }
  }
}`,...(ne=(de=j.parameters)==null?void 0:de.docs)==null?void 0:ne.source}}};var ie,oe,ce;n.parameters={...n.parameters,docs:{...(ie=n.parameters)==null?void 0:ie.docs,source:{originalSource:`{
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
}`,...(ce=(oe=n.parameters)==null?void 0:oe.docs)==null?void 0:ce.source}}};var le,Ce,pe;i.parameters={...i.parameters,docs:{...(le=i.parameters)==null?void 0:le.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Notification</CardTitle>
        <CardDescription>You have 3 unread messages.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Check your inbox for new updates.</p>
      </CardContent>
    </Card>
}`,...(pe=(Ce=i.parameters)==null?void 0:Ce.docs)==null?void 0:pe.source}}};var me,ue,he;o.parameters={...o.parameters,docs:{...(me=o.parameters)==null?void 0:me.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardContent className="pt-6">
        <p>This card has no header, just content.</p>
      </CardContent>
    </Card>
}`,...(he=(ue=o.parameters)==null?void 0:ue.docs)==null?void 0:he.source}}};var xe,we,je;c.parameters={...c.parameters,docs:{...(xe=c.parameters)==null?void 0:xe.docs,source:{originalSource:`{
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
}`,...(je=(we=c.parameters)==null?void 0:we.docs)==null?void 0:je.source}}};var fe,ge,ye;l.parameters={...l.parameters,docs:{...(fe=l.parameters)==null?void 0:fe.docs,source:{originalSource:`{
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
}`,...(ye=(ge=l.parameters)==null?void 0:ge.docs)==null?void 0:ye.source}}};var Te,ve,Ne;C.parameters={...C.parameters,docs:{...(Te=C.parameters)==null?void 0:Te.docs,source:{originalSource:`{
  render: () => <Card className="w-[600px]">
      <CardHeader>
        <CardTitle>Wide Card</CardTitle>
        <CardDescription>This card is wider than the default</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Content can span across a wider area for more complex layouts.</p>
      </CardContent>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with wider width for more complex layouts.'
      }
    }
  }
}`,...(Ne=(ve=C.parameters)==null?void 0:ve.docs)==null?void 0:Ne.source}}};var De,He,Be;p.parameters={...p.parameters,docs:{...(De=p.parameters)==null?void 0:De.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>This is a very long card title that might wrap to multiple lines depending on the card width</CardTitle>
        <CardDescription>Testing title wrapping behavior</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content goes here.</p>
      </CardContent>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with very long title to test text wrapping.'
      }
    }
  }
}`,...(Be=(He=p.parameters)==null?void 0:He.docs)==null?void 0:Be.source}}};var Se,be,Ae;m.parameters={...m.parameters,docs:{...(Se=m.parameters)==null?void 0:Se.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Article Preview</CardTitle>
        <CardDescription>Latest blog post</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
        </p>
      </CardContent>
      <CardFooter>
        <Button>Read More</Button>
      </CardFooter>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with long text content to test content overflow.'
      }
    }
  }
}`,...(Ae=(be=m.parameters)==null?void 0:be.docs)==null?void 0:Ae.source}}};var Fe,ke,We;u.parameters={...u.parameters,docs:{...(Fe=u.parameters)==null?void 0:Fe.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>A</CardTitle>
        <CardDescription>B</CardDescription>
      </CardHeader>
      <CardContent>
        <p>C</p>
      </CardContent>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with minimal single-character content.'
      }
    }
  }
}`,...(We=(ke=u.parameters)==null?void 0:ke.docs)==null?void 0:We.source}}};var Pe,Le,Me;h.parameters={...h.parameters,docs:{...(Pe=h.parameters)==null?void 0:Pe.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Project Status</CardTitle>
          <Badge>Active</Badge>
        </div>
        <CardDescription>Current project information</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Tasks completed:</span>
            <Badge variant="secondary">12/20</Badge>
          </div>
          <div className="flex justify-between">
            <span>Priority:</span>
            <Badge variant="destructive">High</Badge>
          </div>
        </div>
      </CardContent>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with Badge components for status indicators.'
      }
    }
  }
}`,...(Me=(Le=h.parameters)==null?void 0:Le.docs)==null?void 0:Me.source}}};var qe,Ue,Re;x.parameters={...x.parameters,docs:{...(qe=x.parameters)==null?void 0:qe.docs,source:{originalSource:`{
  render: () => <Card className="w-[200px]">
      <CardHeader>
        <CardTitle>Narrow</CardTitle>
        <CardDescription>Small card</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">Compact layout</p>
      </CardContent>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card with narrow width to test minimum size constraints.'
      }
    }
  }
}`,...(Re=(Ue=x.parameters)==null?void 0:Ue.docs)==null?void 0:Re.source}}};var Ye,ze,Ie;w.parameters={...w.parameters,docs:{...(Ye=w.parameters)==null?void 0:Ye.docs,source:{originalSource:`{
  render: () => <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>Full Width Card</CardTitle>
        <CardDescription>This card spans the full width of its container</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Content can be displayed across the full width, useful for dashboard layouts or detailed information displays.</p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline">Secondary Action</Button>
        <Button>Primary Action</Button>
      </CardFooter>
    </Card>,
  parameters: {
    docs: {
      description: {
        story: 'Card that spans full width with maximum width constraint.'
      }
    }
  }
}`,...(Ie=(ze=w.parameters)==null?void 0:ze.docs)==null?void 0:Ie.source}}};var Oe,Ee,_e;j.parameters={...j.parameters,docs:{...(Oe=j.parameters)==null?void 0:Oe.docs,source:{originalSource:`{
  render: () => <div className="space-y-4 w-[350px]">
      <Card>
        <CardHeader>
          <CardTitle>Card 1</CardTitle>
          <CardDescription>First card in stack</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Content for first card</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Card 2</CardTitle>
          <CardDescription>Second card in stack</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Content for second card</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Card 3</CardTitle>
          <CardDescription>Third card in stack</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Content for third card</p>
        </CardContent>
      </Card>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple cards stacked vertically with consistent spacing.'
      }
    }
  }
}`,...(_e=(Ee=j.parameters)==null?void 0:Ee.docs)==null?void 0:_e.source}}};const ar=["Default","WithoutFooter","WithoutHeader","WithList","WithMultipleButtons","Wide","LongTitle","LongContent","MinimalContent","WithBadges","Narrow","FullWidth","StackedCards"];export{n as Default,w as FullWidth,m as LongContent,p as LongTitle,u as MinimalContent,x as Narrow,j as StackedCards,C as Wide,h as WithBadges,c as WithList,l as WithMultipleButtons,i as WithoutFooter,o as WithoutHeader,ar as __namedExportsOrder,rr as default};
