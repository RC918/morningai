import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{B as u}from"./button-6x4QkhmZ.js";import{C as x,a as g,b as f,c as b,d as N}from"./card-DVL6yFjD.js";import{I as y}from"./input-Cv5CY2yx.js";import"./index-Dz3UJJSw.js";import{c as p}from"./utils-D-KgF5mV.js";import"./index-DRuEWG1E.js";import"./index-CGrAONsN.js";import"./_commonjsHelpers-CqkleIqs.js";function m({className:a,size:n="md"}){const c={sm:"w-4 h-4",md:"w-6 h-6",lg:"w-8 h-8"};return e.jsx("div",{className:p("spinner border-2 border-gray-200 border-t-primary rounded-full",c[n],a),role:"status","aria-label":"Loading",children:e.jsx("span",{className:"sr-only",children:"Loading..."})})}function s({className:a,variant:n="default"}){const c={default:"h-4 w-full",text:"h-4 w-3/4",title:"h-6 w-1/2",avatar:"h-12 w-12 rounded-full",button:"h-10 w-24",card:"h-32 w-full"};return e.jsx("div",{className:p("skeleton rounded-md bg-gray-200 dark:bg-gray-700",c[n],a),"aria-hidden":"true"})}function v({className:a}){return e.jsxs("div",{className:p("flex space-x-1",a),role:"status","aria-label":"Loading",children:[e.jsx("div",{className:"w-2 h-2 bg-current rounded-full animate-bounce",style:{animationDelay:"0ms"}}),e.jsx("div",{className:"w-2 h-2 bg-current rounded-full animate-bounce",style:{animationDelay:"150ms"}}),e.jsx("div",{className:"w-2 h-2 bg-current rounded-full animate-bounce",style:{animationDelay:"300ms"}}),e.jsx("span",{className:"sr-only",children:"Loading..."})]})}function l({value:a=0,className:n,showLabel:c=!1}){return e.jsxs("div",{className:p("w-full",n),children:[e.jsx("div",{className:"w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden",children:e.jsx("div",{className:"progress-fill bg-primary h-full rounded-full transition-all duration-500",style:{width:`${Math.min(100,Math.max(0,a))}%`},role:"progressbar","aria-valuenow":a,"aria-valuemin":"0","aria-valuemax":"100"})}),c&&e.jsxs("div",{className:"text-sm text-muted-foreground mt-1 text-right",children:[Math.round(a),"%"]})]})}function h({className:a}){return e.jsxs("div",{className:p("flex space-x-2",a),role:"status","aria-label":"Loading",children:[e.jsx("div",{className:"w-3 h-3 bg-primary rounded-full animate-pulse"}),e.jsx("div",{className:"w-3 h-3 bg-primary rounded-full animate-pulse",style:{animationDelay:"0.2s"}}),e.jsx("div",{className:"w-3 h-3 bg-primary rounded-full animate-pulse",style:{animationDelay:"0.4s"}}),e.jsx("span",{className:"sr-only",children:"Loading..."})]})}m.__docgenInfo={description:"",methods:[],displayName:"Spinner",props:{size:{defaultValue:{value:"'md'",computed:!1},required:!1}}};s.__docgenInfo={description:"",methods:[],displayName:"Skeleton",props:{variant:{defaultValue:{value:"'default'",computed:!1},required:!1}}};v.__docgenInfo={description:"",methods:[],displayName:"LoadingDots"};l.__docgenInfo={description:"",methods:[],displayName:"ProgressBar",props:{value:{defaultValue:{value:"0",computed:!1},required:!1},showLabel:{defaultValue:{value:"false",computed:!1},required:!1}}};h.__docgenInfo={description:"",methods:[],displayName:"PulseLoader"};m.__docgenInfo={description:"",methods:[],displayName:"Spinner",props:{size:{defaultValue:{value:"'md'",computed:!1},required:!1}}};s.__docgenInfo={description:"",methods:[],displayName:"Skeleton",props:{variant:{defaultValue:{value:"'default'",computed:!1},required:!1}}};v.__docgenInfo={description:"",methods:[],displayName:"LoadingDots"};l.__docgenInfo={description:"",methods:[],displayName:"ProgressBar",props:{value:{defaultValue:{value:"0",computed:!1},required:!1},showLabel:{defaultValue:{value:"false",computed:!1},required:!1}}};h.__docgenInfo={description:"",methods:[],displayName:"PulseLoader"};const oe={title:"UI/Micro Interactions",parameters:{layout:"padded"},tags:["autodocs"]},t={render:()=>e.jsx("div",{className:"space-y-8",children:e.jsxs("div",{children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Button Press Animation"}),e.jsxs("div",{className:"flex gap-4",children:[e.jsx(u,{children:"Click Me"}),e.jsx(u,{variant:"outline",children:"Outline Button"}),e.jsx(u,{variant:"destructive",children:"Delete"})]}),e.jsx("p",{className:"text-sm text-muted-foreground mt-2",children:"Click buttons to see the press animation effect"})]})}),parameters:{docs:{description:{story:"Buttons have a subtle press animation when clicked, providing tactile feedback."}}}},r={render:()=>e.jsx("div",{className:"space-y-8",children:e.jsxs("div",{children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Interactive Cards"}),e.jsxs("div",{className:"grid grid-cols-1 md:grid-cols-2 gap-4",children:[e.jsxs(x,{interactive:!0,children:[e.jsxs(g,{children:[e.jsx(f,{children:"Hover Me"}),e.jsx(b,{children:"This card lifts on hover"})]}),e.jsx(N,{children:e.jsx("p",{className:"text-sm",children:"Interactive cards provide visual feedback when hovered."})})]}),e.jsxs(x,{children:[e.jsxs(g,{children:[e.jsx(f,{children:"Static Card"}),e.jsx(b,{children:"This card doesn't have hover effect"})]}),e.jsx(N,{children:e.jsx("p",{className:"text-sm",children:"Regular cards remain static for non-interactive content."})})]})]})]})}),parameters:{docs:{description:{story:"Interactive cards lift and cast a shadow on hover, indicating they are clickable."}}}},i={render:()=>e.jsx("div",{className:"space-y-8",children:e.jsxs("div",{children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Input Focus Glow"}),e.jsxs("div",{className:"space-y-4 max-w-md",children:[e.jsxs("div",{children:[e.jsx("label",{className:"block text-sm font-medium mb-2",children:"Email"}),e.jsx(y,{type:"email",placeholder:"Enter your email"})]}),e.jsxs("div",{children:[e.jsx("label",{className:"block text-sm font-medium mb-2",children:"Password"}),e.jsx(y,{type:"password",placeholder:"Enter your password"})]})]}),e.jsx("p",{className:"text-sm text-muted-foreground mt-2",children:"Focus on inputs to see the glow effect"})]})}),parameters:{docs:{description:{story:"Input fields have a subtle glow effect when focused, improving accessibility."}}}},d={render:()=>e.jsxs("div",{className:"space-y-8",children:[e.jsxs("div",{children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Spinner"}),e.jsxs("div",{className:"flex gap-4 items-center",children:[e.jsx(m,{size:"sm"}),e.jsx(m,{size:"md"}),e.jsx(m,{size:"lg"})]})]}),e.jsxs("div",{children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Skeleton Loaders"}),e.jsxs("div",{className:"space-y-4 max-w-md",children:[e.jsx(s,{variant:"title"}),e.jsx(s,{variant:"text"}),e.jsx(s,{variant:"text"}),e.jsxs("div",{className:"flex gap-4",children:[e.jsx(s,{variant:"avatar"}),e.jsxs("div",{className:"flex-1 space-y-2",children:[e.jsx(s,{variant:"text"}),e.jsx(s,{variant:"text"})]})]})]})]}),e.jsxs("div",{children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Loading Dots"}),e.jsx(v,{})]}),e.jsxs("div",{children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Progress Bar"}),e.jsxs("div",{className:"space-y-4 max-w-md",children:[e.jsx(l,{value:25,showLabel:!0}),e.jsx(l,{value:50,showLabel:!0}),e.jsx(l,{value:75,showLabel:!0}),e.jsx(l,{value:100,showLabel:!0})]})]}),e.jsxs("div",{children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Pulse Loader"}),e.jsx(h,{})]})]}),parameters:{docs:{description:{story:"Various loading state components with smooth animations."}}}},o={render:()=>e.jsx("div",{className:"space-y-8",children:e.jsxs("div",{children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Staggered Animation"}),e.jsx("div",{className:"space-y-2 max-w-md",children:[1,2,3,4,5].map(a=>e.jsxs("div",{className:"stagger-item p-4 bg-card border rounded-lg",children:[e.jsxs("p",{className:"font-medium",children:["Item ",a]}),e.jsx("p",{className:"text-sm text-muted-foreground",children:"This item animates in with a stagger effect"})]},a))}),e.jsx("p",{className:"text-sm text-muted-foreground mt-4",children:"Reload the story to see the staggered animation"})]})}),parameters:{docs:{description:{story:"List items animate in with a staggered delay, creating a smooth entrance effect."}}}};var j,w,C;t.parameters={...t.parameters,docs:{...(j=t.parameters)==null?void 0:j.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Button Press Animation</h3>
        <div className="flex gap-4">
          <Button>Click Me</Button>
          <Button variant="outline">Outline Button</Button>
          <Button variant="destructive">Delete</Button>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Click buttons to see the press animation effect
        </p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Buttons have a subtle press animation when clicked, providing tactile feedback.'
      }
    }
  }
}`,...(C=(w=t.parameters)==null?void 0:w.docs)==null?void 0:C.source}}};var S,k,L;r.parameters={...r.parameters,docs:{...(S=r.parameters)==null?void 0:S.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Interactive Cards</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card interactive>
            <CardHeader>
              <CardTitle>Hover Me</CardTitle>
              <CardDescription>This card lifts on hover</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">Interactive cards provide visual feedback when hovered.</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Static Card</CardTitle>
              <CardDescription>This card doesn't have hover effect</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">Regular cards remain static for non-interactive content.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Interactive cards lift and cast a shadow on hover, indicating they are clickable.'
      }
    }
  }
}`,...(L=(k=r.parameters)==null?void 0:k.docs)==null?void 0:L.source}}};var I,B,P;i.parameters={...i.parameters,docs:{...(I=i.parameters)==null?void 0:I.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Input Focus Glow</h3>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium mb-2">Email</label>
            <Input type="email" placeholder="Enter your email" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Password</label>
            <Input type="password" placeholder="Enter your password" />
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Focus on inputs to see the glow effect
        </p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input fields have a subtle glow effect when focused, improving accessibility.'
      }
    }
  }
}`,...(P=(B=i.parameters)==null?void 0:B.docs)==null?void 0:P.source}}};var D,_,T;d.parameters={...d.parameters,docs:{...(D=d.parameters)==null?void 0:D.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Spinner</h3>
        <div className="flex gap-4 items-center">
          <Spinner size="sm" />
          <Spinner size="md" />
          <Spinner size="lg" />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Skeleton Loaders</h3>
        <div className="space-y-4 max-w-md">
          <Skeleton variant="title" />
          <Skeleton variant="text" />
          <Skeleton variant="text" />
          <div className="flex gap-4">
            <Skeleton variant="avatar" />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" />
              <Skeleton variant="text" />
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Loading Dots</h3>
        <LoadingDots />
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Progress Bar</h3>
        <div className="space-y-4 max-w-md">
          <ProgressBar value={25} showLabel />
          <ProgressBar value={50} showLabel />
          <ProgressBar value={75} showLabel />
          <ProgressBar value={100} showLabel />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Pulse Loader</h3>
        <PulseLoader />
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Various loading state components with smooth animations.'
      }
    }
  }
}`,...(T=(_=d.parameters)==null?void 0:_.docs)==null?void 0:T.source}}};var E,H,z;o.parameters={...o.parameters,docs:{...(E=o.parameters)==null?void 0:E.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Staggered Animation</h3>
        <div className="space-y-2 max-w-md">
          {[1, 2, 3, 4, 5].map(item => <div key={item} className="stagger-item p-4 bg-card border rounded-lg">
              <p className="font-medium">Item {item}</p>
              <p className="text-sm text-muted-foreground">
                This item animates in with a stagger effect
              </p>
            </div>)}
        </div>
        <p className="text-sm text-muted-foreground mt-4">
          Reload the story to see the staggered animation
        </p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'List items animate in with a staggered delay, creating a smooth entrance effect.'
      }
    }
  }
}`,...(z=(H=o.parameters)==null?void 0:H.docs)==null?void 0:z.source}}};var V,M,q;t.parameters={...t.parameters,docs:{...(V=t.parameters)==null?void 0:V.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Button Press Animation</h3>
        <div className="flex gap-4">
          <Button>Click Me</Button>
          <Button variant="outline">Outline Button</Button>
          <Button variant="destructive">Delete</Button>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Click buttons to see the press animation effect
        </p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Buttons have a subtle press animation when clicked, providing tactile feedback.'
      }
    }
  }
}`,...(q=(M=t.parameters)==null?void 0:M.docs)==null?void 0:q.source}}};var F,R,A;r.parameters={...r.parameters,docs:{...(F=r.parameters)==null?void 0:F.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Interactive Cards</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card interactive>
            <CardHeader>
              <CardTitle>Hover Me</CardTitle>
              <CardDescription>This card lifts on hover</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">Interactive cards provide visual feedback when hovered.</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Static Card</CardTitle>
              <CardDescription>This card doesn't have hover effect</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">Regular cards remain static for non-interactive content.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Interactive cards lift and cast a shadow on hover, indicating they are clickable.'
      }
    }
  }
}`,...(A=(R=r.parameters)==null?void 0:R.docs)==null?void 0:A.source}}};var O,G,U;i.parameters={...i.parameters,docs:{...(O=i.parameters)==null?void 0:O.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Input Focus Glow</h3>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium mb-2">Email</label>
            <Input type="email" placeholder="Enter your email" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Password</label>
            <Input type="password" placeholder="Enter your password" />
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Focus on inputs to see the glow effect
        </p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Input fields have a subtle glow effect when focused, improving accessibility.'
      }
    }
  }
}`,...(U=(G=i.parameters)==null?void 0:G.docs)==null?void 0:U.source}}};var $,J,K;d.parameters={...d.parameters,docs:{...($=d.parameters)==null?void 0:$.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Spinner</h3>
        <div className="flex gap-4 items-center">
          <Spinner size="sm" />
          <Spinner size="md" />
          <Spinner size="lg" />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Skeleton Loaders</h3>
        <div className="space-y-4 max-w-md">
          <Skeleton variant="title" />
          <Skeleton variant="text" />
          <Skeleton variant="text" />
          <div className="flex gap-4">
            <Skeleton variant="avatar" />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" />
              <Skeleton variant="text" />
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Loading Dots</h3>
        <LoadingDots />
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Progress Bar</h3>
        <div className="space-y-4 max-w-md">
          <ProgressBar value={25} showLabel />
          <ProgressBar value={50} showLabel />
          <ProgressBar value={75} showLabel />
          <ProgressBar value={100} showLabel />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Pulse Loader</h3>
        <PulseLoader />
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Various loading state components with smooth animations.'
      }
    }
  }
}`,...(K=(J=d.parameters)==null?void 0:J.docs)==null?void 0:K.source}}};var Q,W,X;o.parameters={...o.parameters,docs:{...(Q=o.parameters)==null?void 0:Q.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Staggered Animation</h3>
        <div className="space-y-2 max-w-md">
          {[1, 2, 3, 4, 5].map(item => <div key={item} className="stagger-item p-4 bg-card border rounded-lg">
              <p className="font-medium">Item {item}</p>
              <p className="text-sm text-muted-foreground">
                This item animates in with a stagger effect
              </p>
            </div>)}
        </div>
        <p className="text-sm text-muted-foreground mt-4">
          Reload the story to see the staggered animation
        </p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'List items animate in with a staggered delay, creating a smooth entrance effect.'
      }
    }
  }
}`,...(X=(W=o.parameters)==null?void 0:W.docs)==null?void 0:X.source}}};const le=["ButtonInteractions","CardHoverEffects","InputFocusEffects","LoadingStates","StaggeredList"];export{t as ButtonInteractions,r as CardHoverEffects,i as InputFocusEffects,d as LoadingStates,o as StaggeredList,le as __namedExportsOrder,oe as default};
