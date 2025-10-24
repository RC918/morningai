import{j as e}from"./jsx-runtime-D_zvdyIk.js";import"./index-Dz3UJJSw.js";import{c as N}from"./utils-ClSdSIbF.js";import{B as y}from"./button-CtW_o4fY.js";import{B as v}from"./badge-BJ9Hlb5y.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-CN2Y8dJ9.js";function r({className:n,...o}){return e.jsx("div",{"data-slot":"card",className:N("bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm",n),...o})}function t({className:n,...o}){return e.jsx("div",{"data-slot":"card-header",className:N("@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-1.5 px-6 has-data-[slot=card-action]:grid-cols-[1fr_auto] [.border-b]:pb-6",n),...o})}function s({className:n,...o}){return e.jsx("div",{"data-slot":"card-title",className:N("leading-none font-semibold",n),...o})}function d({className:n,...o}){return e.jsx("div",{"data-slot":"card-description",className:N("text-muted-foreground text-sm",n),...o})}function a({className:n,...o}){return e.jsx("div",{"data-slot":"card-content",className:N("px-6",n),...o})}function T({className:n,...o}){return e.jsx("div",{"data-slot":"card-footer",className:N("flex items-center px-6 [.border-t]:pt-6",n),...o})}r.__docgenInfo={description:"",methods:[],displayName:"Card"};t.__docgenInfo={description:"",methods:[],displayName:"CardHeader"};T.__docgenInfo={description:"",methods:[],displayName:"CardFooter"};s.__docgenInfo={description:"",methods:[],displayName:"CardTitle"};d.__docgenInfo={description:"",methods:[],displayName:"CardDescription"};a.__docgenInfo={description:"",methods:[],displayName:"CardContent"};r.__docgenInfo={description:"",methods:[],displayName:"Card"};t.__docgenInfo={description:"",methods:[],displayName:"CardHeader"};T.__docgenInfo={description:"",methods:[],displayName:"CardFooter"};s.__docgenInfo={description:"",methods:[],displayName:"CardTitle"};d.__docgenInfo={description:"",methods:[],displayName:"CardDescription"};a.__docgenInfo={description:"",methods:[],displayName:"CardContent"};const ar={title:"UI/Card",component:r,parameters:{layout:"centered",docs:{description:{component:`
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
        `}}},tags:["autodocs"]},i={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Card Title"}),e.jsx(d,{children:"Card Description"})]}),e.jsx(a,{children:e.jsx("p",{children:"Card Content"})}),e.jsx(T,{children:e.jsx(y,{children:"Action"})})]})},c={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Notification"}),e.jsx(d,{children:"You have 3 unread messages."})]}),e.jsx(a,{children:e.jsx("p",{children:"Check your inbox for new updates."})})]})},l={render:()=>e.jsx(r,{className:"w-[350px]",children:e.jsx(a,{className:"pt-6",children:e.jsx("p",{children:"This card has no header, just content."})})})},p={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Recent Activity"}),e.jsx(d,{children:"Your latest actions"})]}),e.jsx(a,{children:e.jsxs("ul",{className:"space-y-2",children:[e.jsx("li",{children:"✓ Completed task A"}),e.jsx("li",{children:"✓ Updated profile"}),e.jsx("li",{children:"✓ Sent message"})]})})]})},C={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Confirm Action"}),e.jsx(d,{children:"Are you sure you want to proceed?"})]}),e.jsx(a,{children:e.jsx("p",{children:"This action cannot be undone."})}),e.jsxs(T,{className:"flex justify-between",children:[e.jsx(y,{variant:"outline",children:"Cancel"}),e.jsx(y,{children:"Confirm"})]})]})},m={render:()=>e.jsxs(r,{className:"w-[600px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Wide Card"}),e.jsx(d,{children:"This card is wider than the default"})]}),e.jsx(a,{children:e.jsx("p",{children:"Content can span across a wider area for more complex layouts."})})]}),parameters:{docs:{description:{story:"Card with wider width for more complex layouts."}}}},u={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"This is a very long card title that might wrap to multiple lines depending on the card width"}),e.jsx(d,{children:"Testing title wrapping behavior"})]}),e.jsx(a,{children:e.jsx("p",{children:"Card content goes here."})})]}),parameters:{docs:{description:{story:"Card with very long title to test text wrapping."}}}},h={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Article Preview"}),e.jsx(d,{children:"Latest blog post"})]}),e.jsx(a,{children:e.jsx("p",{className:"text-sm",children:"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."})}),e.jsx(T,{children:e.jsx(y,{children:"Read More"})})]}),parameters:{docs:{description:{story:"Card with long text content to test content overflow."}}}},x={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"A"}),e.jsx(d,{children:"B"})]}),e.jsx(a,{children:e.jsx("p",{children:"C"})})]}),parameters:{docs:{description:{story:"Card with minimal single-character content."}}}},f={render:()=>e.jsxs(r,{className:"w-[350px]",children:[e.jsxs(t,{children:[e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsx(s,{children:"Project Status"}),e.jsx(v,{children:"Active"})]}),e.jsx(d,{children:"Current project information"})]}),e.jsx(a,{children:e.jsxs("div",{className:"space-y-2",children:[e.jsxs("div",{className:"flex justify-between",children:[e.jsx("span",{children:"Tasks completed:"}),e.jsx(v,{variant:"secondary",children:"12/20"})]}),e.jsxs("div",{className:"flex justify-between",children:[e.jsx("span",{children:"Priority:"}),e.jsx(v,{variant:"destructive",children:"High"})]})]})})]}),parameters:{docs:{description:{story:"Card with Badge components for status indicators."}}}},w={render:()=>e.jsxs(r,{className:"w-[200px]",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Narrow"}),e.jsx(d,{children:"Small card"})]}),e.jsx(a,{children:e.jsx("p",{className:"text-sm",children:"Compact layout"})})]}),parameters:{docs:{description:{story:"Card with narrow width to test minimum size constraints."}}}},j={render:()=>e.jsxs(r,{className:"w-full max-w-4xl",children:[e.jsxs(t,{children:[e.jsx(s,{children:"Full Width Card"}),e.jsx(d,{children:"This card spans the full width of its container"})]}),e.jsx(a,{children:e.jsx("p",{children:"Content can be displayed across the full width, useful for dashboard layouts or detailed information displays."})}),e.jsxs(T,{className:"flex justify-between",children:[e.jsx(y,{variant:"outline",children:"Secondary Action"}),e.jsx(y,{children:"Primary Action"})]})]}),parameters:{docs:{description:{story:"Card that spans full width with maximum width constraint."}}}},g={render:()=>e.jsxs("div",{className:"space-y-4 w-[350px]",children:[e.jsxs(r,{children:[e.jsxs(t,{children:[e.jsx(s,{children:"Card 1"}),e.jsx(d,{children:"First card in stack"})]}),e.jsx(a,{children:e.jsx("p",{children:"Content for first card"})})]}),e.jsxs(r,{children:[e.jsxs(t,{children:[e.jsx(s,{children:"Card 2"}),e.jsx(d,{children:"Second card in stack"})]}),e.jsx(a,{children:e.jsx("p",{children:"Content for second card"})})]}),e.jsxs(r,{children:[e.jsxs(t,{children:[e.jsx(s,{children:"Card 3"}),e.jsx(d,{children:"Third card in stack"})]}),e.jsx(a,{children:e.jsx("p",{children:"Content for third card"})})]})]}),parameters:{docs:{description:{story:"Multiple cards stacked vertically with consistent spacing."}}}};var D,H,b;i.parameters={...i.parameters,docs:{...(D=i.parameters)==null?void 0:D.docs,source:{originalSource:`{
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
}`,...(b=(H=i.parameters)==null?void 0:H.docs)==null?void 0:b.source}}};var B,S,A;c.parameters={...c.parameters,docs:{...(B=c.parameters)==null?void 0:B.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Notification</CardTitle>
        <CardDescription>You have 3 unread messages.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Check your inbox for new updates.</p>
      </CardContent>
    </Card>
}`,...(A=(S=c.parameters)==null?void 0:S.docs)==null?void 0:A.source}}};var F,_,k;l.parameters={...l.parameters,docs:{...(F=l.parameters)==null?void 0:F.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardContent className="pt-6">
        <p>This card has no header, just content.</p>
      </CardContent>
    </Card>
}`,...(k=(_=l.parameters)==null?void 0:_.docs)==null?void 0:k.source}}};var W,I,P;p.parameters={...p.parameters,docs:{...(W=p.parameters)==null?void 0:W.docs,source:{originalSource:`{
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
}`,...(P=(I=p.parameters)==null?void 0:I.docs)==null?void 0:P.source}}};var L,M,q;C.parameters={...C.parameters,docs:{...(L=C.parameters)==null?void 0:L.docs,source:{originalSource:`{
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
}`,...(q=(M=C.parameters)==null?void 0:M.docs)==null?void 0:q.source}}};var U,R,Y;m.parameters={...m.parameters,docs:{...(U=m.parameters)==null?void 0:U.docs,source:{originalSource:`{
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
}`,...(Y=(R=m.parameters)==null?void 0:R.docs)==null?void 0:Y.source}}};var z,O,E;u.parameters={...u.parameters,docs:{...(z=u.parameters)==null?void 0:z.docs,source:{originalSource:`{
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
}`,...(E=(O=u.parameters)==null?void 0:O.docs)==null?void 0:E.source}}};var G,K,J;h.parameters={...h.parameters,docs:{...(G=h.parameters)==null?void 0:G.docs,source:{originalSource:`{
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
}`,...(J=(K=h.parameters)==null?void 0:K.docs)==null?void 0:J.source}}};var Q,V,X;x.parameters={...x.parameters,docs:{...(Q=x.parameters)==null?void 0:Q.docs,source:{originalSource:`{
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
}`,...(X=(V=x.parameters)==null?void 0:V.docs)==null?void 0:X.source}}};var Z,$,ee;f.parameters={...f.parameters,docs:{...(Z=f.parameters)==null?void 0:Z.docs,source:{originalSource:`{
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
}`,...(ee=($=f.parameters)==null?void 0:$.docs)==null?void 0:ee.source}}};var re,ae,te;w.parameters={...w.parameters,docs:{...(re=w.parameters)==null?void 0:re.docs,source:{originalSource:`{
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
}`,...(te=(ae=w.parameters)==null?void 0:ae.docs)==null?void 0:te.source}}};var se,de,ne;j.parameters={...j.parameters,docs:{...(se=j.parameters)==null?void 0:se.docs,source:{originalSource:`{
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
}`,...(ne=(de=j.parameters)==null?void 0:de.docs)==null?void 0:ne.source}}};var oe,ie,ce;g.parameters={...g.parameters,docs:{...(oe=g.parameters)==null?void 0:oe.docs,source:{originalSource:`{
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
}`,...(ce=(ie=g.parameters)==null?void 0:ie.docs)==null?void 0:ce.source}}};var le,pe,Ce;i.parameters={...i.parameters,docs:{...(le=i.parameters)==null?void 0:le.docs,source:{originalSource:`{
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
}`,...(Ce=(pe=i.parameters)==null?void 0:pe.docs)==null?void 0:Ce.source}}};var me,ue,he;c.parameters={...c.parameters,docs:{...(me=c.parameters)==null?void 0:me.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Notification</CardTitle>
        <CardDescription>You have 3 unread messages.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Check your inbox for new updates.</p>
      </CardContent>
    </Card>
}`,...(he=(ue=c.parameters)==null?void 0:ue.docs)==null?void 0:he.source}}};var xe,fe,we;l.parameters={...l.parameters,docs:{...(xe=l.parameters)==null?void 0:xe.docs,source:{originalSource:`{
  render: () => <Card className="w-[350px]">
      <CardContent className="pt-6">
        <p>This card has no header, just content.</p>
      </CardContent>
    </Card>
}`,...(we=(fe=l.parameters)==null?void 0:fe.docs)==null?void 0:we.source}}};var je,ge,ye;p.parameters={...p.parameters,docs:{...(je=p.parameters)==null?void 0:je.docs,source:{originalSource:`{
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
}`,...(ye=(ge=p.parameters)==null?void 0:ge.docs)==null?void 0:ye.source}}};var Ne,Te,ve;C.parameters={...C.parameters,docs:{...(Ne=C.parameters)==null?void 0:Ne.docs,source:{originalSource:`{
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
}`,...(ve=(Te=C.parameters)==null?void 0:Te.docs)==null?void 0:ve.source}}};var De,He,be;m.parameters={...m.parameters,docs:{...(De=m.parameters)==null?void 0:De.docs,source:{originalSource:`{
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
}`,...(be=(He=m.parameters)==null?void 0:He.docs)==null?void 0:be.source}}};var Be,Se,Ae;u.parameters={...u.parameters,docs:{...(Be=u.parameters)==null?void 0:Be.docs,source:{originalSource:`{
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
}`,...(Ae=(Se=u.parameters)==null?void 0:Se.docs)==null?void 0:Ae.source}}};var Fe,_e,ke;h.parameters={...h.parameters,docs:{...(Fe=h.parameters)==null?void 0:Fe.docs,source:{originalSource:`{
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
}`,...(ke=(_e=h.parameters)==null?void 0:_e.docs)==null?void 0:ke.source}}};var We,Ie,Pe;x.parameters={...x.parameters,docs:{...(We=x.parameters)==null?void 0:We.docs,source:{originalSource:`{
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
}`,...(Pe=(Ie=x.parameters)==null?void 0:Ie.docs)==null?void 0:Pe.source}}};var Le,Me,qe;f.parameters={...f.parameters,docs:{...(Le=f.parameters)==null?void 0:Le.docs,source:{originalSource:`{
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
}`,...(qe=(Me=f.parameters)==null?void 0:Me.docs)==null?void 0:qe.source}}};var Ue,Re,Ye;w.parameters={...w.parameters,docs:{...(Ue=w.parameters)==null?void 0:Ue.docs,source:{originalSource:`{
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
}`,...(Ye=(Re=w.parameters)==null?void 0:Re.docs)==null?void 0:Ye.source}}};var ze,Oe,Ee;j.parameters={...j.parameters,docs:{...(ze=j.parameters)==null?void 0:ze.docs,source:{originalSource:`{
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
}`,...(Ee=(Oe=j.parameters)==null?void 0:Oe.docs)==null?void 0:Ee.source}}};var Ge,Ke,Je;g.parameters={...g.parameters,docs:{...(Ge=g.parameters)==null?void 0:Ge.docs,source:{originalSource:`{
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
}`,...(Je=(Ke=g.parameters)==null?void 0:Ke.docs)==null?void 0:Je.source}}};const tr=["Default","WithoutFooter","WithoutHeader","WithList","WithMultipleButtons","Wide","LongTitle","LongContent","MinimalContent","WithBadges","Narrow","FullWidth","StackedCards"];export{i as Default,j as FullWidth,h as LongContent,u as LongTitle,x as MinimalContent,w as Narrow,g as StackedCards,m as Wide,f as WithBadges,p as WithList,C as WithMultipleButtons,c as WithoutFooter,l as WithoutHeader,tr as __namedExportsOrder,ar as default};
