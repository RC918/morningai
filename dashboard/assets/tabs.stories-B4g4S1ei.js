import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as i}from"./index-Dz3UJJSw.js";import{c as N,u as pe}from"./index-Bo7lbUv-.js";import{c as ve}from"./index-DiKooijE.js";import{c as Me,u as be}from"./index-M8eZJUAT.js";import{u as Ge}from"./index-DRuEWG1E.js";import{u as fe}from"./index-HmPO_Abe.js";import{P as A}from"./index-C7eB__Z-.js";import{u as Oe}from"./index-BwP8QHTI.js";import{P as He}from"./index-B6CVSQiA.js";import{c as P}from"./utils-D-KgF5mV.js";import{C as G,a as O,b as H,c as K,d as U}from"./card-DVL6yFjD.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-CYANIyVc.js";import"./index-fUCaa9pg.js";var $="rovingFocusGroup.onEntryFocus",Ke={bubbles:!1,cancelable:!0},_="RovingFocusGroup",[B,Te,Ue]=Me(_),[$e,ge]=ve(_,[Ue]),[Be,ze]=$e(_),xe=i.forwardRef((a,s)=>e.jsx(B.Provider,{scope:a.__scopeRovingFocusGroup,children:e.jsx(B.Slot,{scope:a.__scopeRovingFocusGroup,children:e.jsx(Ye,{...a,ref:s})})}));xe.displayName=_;var Ye=i.forwardRef((a,s)=>{const{__scopeRovingFocusGroup:n,orientation:t,loop:l=!1,dir:u,currentTabStopId:o,defaultCurrentTabStopId:p,onCurrentTabStopIdChange:x,onEntryFocus:v,preventScrollOnEntryFocus:r=!1,...d}=a,T=i.useRef(null),F=Ge(s,T),E=be(u),[S,c]=pe({prop:o,defaultProp:p??null,onChange:x,caller:_}),[C,L]=i.useState(!1),g=Oe(v),h=Te(n),V=i.useRef(!1),[Se,Y]=i.useState(0);return i.useEffect(()=>{const m=T.current;if(m)return m.addEventListener($,g),()=>m.removeEventListener($,g)},[g]),e.jsx(Be,{scope:n,orientation:t,dir:E,loop:l,currentTabStopId:S,onItemFocus:i.useCallback(m=>c(m),[c]),onItemShiftTab:i.useCallback(()=>L(!0),[]),onFocusableItemAdd:i.useCallback(()=>Y(m=>m+1),[]),onFocusableItemRemove:i.useCallback(()=>Y(m=>m-1),[]),children:e.jsx(A.div,{tabIndex:C||Se===0?-1:0,"data-orientation":t,...d,ref:F,style:{outline:"none",...a.style},onMouseDown:N(a.onMouseDown,()=>{V.current=!0}),onFocus:N(a.onFocus,m=>{const Pe=!V.current;if(m.target===m.currentTarget&&Pe&&!C){const W=new CustomEvent($,Ke);if(m.currentTarget.dispatchEvent(W),!W.defaultPrevented){const M=h().filter(I=>I.focusable),De=M.find(I=>I.active),Le=M.find(I=>I.id===S),Ve=[De,Le,...M].filter(Boolean).map(I=>I.ref.current);he(Ve,r)}}V.current=!1}),onBlur:N(a.onBlur,()=>L(!1))})})}),Ne="RovingFocusGroupItem",Ce=i.forwardRef((a,s)=>{const{__scopeRovingFocusGroup:n,focusable:t=!0,active:l=!1,tabStopId:u,children:o,...p}=a,x=fe(),v=u||x,r=ze(Ne,n),d=r.currentTabStopId===v,T=Te(n),{onFocusableItemAdd:F,onFocusableItemRemove:E,currentTabStopId:S}=r;return i.useEffect(()=>{if(t)return F(),()=>E()},[t,F,E]),e.jsx(B.ItemSlot,{scope:n,id:v,focusable:t,active:l,children:e.jsx(A.span,{tabIndex:d?0:-1,"data-orientation":r.orientation,...p,ref:s,onMouseDown:N(a.onMouseDown,c=>{t?r.onItemFocus(v):c.preventDefault()}),onFocus:N(a.onFocus,()=>r.onItemFocus(v)),onKeyDown:N(a.onKeyDown,c=>{if(c.key==="Tab"&&c.shiftKey){r.onItemShiftTab();return}if(c.target!==c.currentTarget)return;const C=Je(c,r.orientation,r.dir);if(C!==void 0){if(c.metaKey||c.ctrlKey||c.altKey||c.shiftKey)return;c.preventDefault();let g=T().filter(h=>h.focusable).map(h=>h.ref.current);if(C==="last")g.reverse();else if(C==="prev"||C==="next"){C==="prev"&&g.reverse();const h=g.indexOf(c.currentTarget);g=r.loop?Qe(g,h+1):g.slice(h+1)}setTimeout(()=>he(g))}}),children:typeof o=="function"?o({isCurrentTabStop:d,hasTabStop:S!=null}):o})})});Ce.displayName=Ne;var We={ArrowLeft:"prev",ArrowUp:"prev",ArrowRight:"next",ArrowDown:"next",PageUp:"first",Home:"first",PageDown:"last",End:"last"};function qe(a,s){return s!=="rtl"?a:a==="ArrowLeft"?"ArrowRight":a==="ArrowRight"?"ArrowLeft":a}function Je(a,s,n){const t=qe(a.key,n);if(!(s==="vertical"&&["ArrowLeft","ArrowRight"].includes(t))&&!(s==="horizontal"&&["ArrowUp","ArrowDown"].includes(t)))return We[t]}function he(a,s=!1){const n=document.activeElement;for(const t of a)if(t===n||(t.focus({preventScroll:s}),document.activeElement!==n))return}function Qe(a,s){return a.map((n,t)=>a[(s+t)%a.length])}var Xe=xe,Ze=Ce,D="Tabs",[ea]=ve(D,[ge]),ye=ge(),[aa,z]=ea(D),we=i.forwardRef((a,s)=>{const{__scopeTabs:n,value:t,onValueChange:l,defaultValue:u,orientation:o="horizontal",dir:p,activationMode:x="automatic",...v}=a,r=be(p),[d,T]=pe({prop:t,onChange:l,defaultProp:u??"",caller:D});return e.jsx(aa,{scope:n,baseId:fe(),value:d,onValueChange:T,orientation:o,dir:r,activationMode:x,children:e.jsx(A.div,{dir:r,"data-orientation":o,...v,ref:s})})});we.displayName=D;var je="TabsList",Ie=i.forwardRef((a,s)=>{const{__scopeTabs:n,loop:t=!0,...l}=a,u=z(je,n),o=ye(n);return e.jsx(Xe,{asChild:!0,...o,orientation:u.orientation,dir:u.dir,loop:t,children:e.jsx(A.div,{role:"tablist","aria-orientation":u.orientation,...l,ref:s})})});Ie.displayName=je;var Ae="TabsTrigger",ke=i.forwardRef((a,s)=>{const{__scopeTabs:n,value:t,disabled:l=!1,...u}=a,o=z(Ae,n),p=ye(n),x=Fe(o.baseId,t),v=Ee(o.baseId,t),r=t===o.value;return e.jsx(Ze,{asChild:!0,...p,focusable:!l,active:r,children:e.jsx(A.button,{type:"button",role:"tab","aria-selected":r,"aria-controls":v,"data-state":r?"active":"inactive","data-disabled":l?"":void 0,disabled:l,id:x,...u,ref:s,onMouseDown:N(a.onMouseDown,d=>{!l&&d.button===0&&d.ctrlKey===!1?o.onValueChange(t):d.preventDefault()}),onKeyDown:N(a.onKeyDown,d=>{[" ","Enter"].includes(d.key)&&o.onValueChange(t)}),onFocus:N(a.onFocus,()=>{const d=o.activationMode!=="manual";!r&&!l&&d&&o.onValueChange(t)})})})});ke.displayName=Ae;var _e="TabsContent",Re=i.forwardRef((a,s)=>{const{__scopeTabs:n,value:t,forceMount:l,children:u,...o}=a,p=z(_e,n),x=Fe(p.baseId,t),v=Ee(p.baseId,t),r=t===p.value,d=i.useRef(r);return i.useEffect(()=>{const T=requestAnimationFrame(()=>d.current=!1);return()=>cancelAnimationFrame(T)},[]),e.jsx(He,{present:l||r,children:({present:T})=>e.jsx(A.div,{"data-state":r?"active":"inactive","data-orientation":p.orientation,role:"tabpanel","aria-labelledby":x,hidden:!T,id:v,tabIndex:0,...o,ref:s,style:{...a.style,animationDuration:d.current?"0s":void 0},children:T&&u})})});Re.displayName=_e;function Fe(a,s){return`${a}-trigger-${s}`}function Ee(a,s){return`${a}-content-${s}`}var sa=we,ta=Ie,ra=ke,na=Re;function k({className:a,...s}){return e.jsx(sa,{"data-slot":"tabs",className:P("flex flex-col gap-2",a),...s})}function R({className:a,...s}){return e.jsx(ta,{"data-slot":"tabs-list",className:P("bg-muted text-muted-foreground inline-flex h-9 w-fit items-center justify-center rounded-lg p-[3px]",a),...s})}function b({className:a,...s}){return e.jsx(ra,{"data-slot":"tabs-trigger",className:P("data-[state=active]:bg-background dark:data-[state=active]:text-foreground focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:outline-ring dark:data-[state=active]:border-input dark:data-[state=active]:bg-input/30 text-foreground dark:text-muted-foreground inline-flex h-[calc(100%-1px)] flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-2 py-1 text-sm font-medium whitespace-nowrap transition-[color,box-shadow] focus-visible:ring-[3px] focus-visible:outline-1 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:shadow-sm [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",a),...s})}function f({className:a,...s}){return e.jsx(na,{"data-slot":"tabs-content",className:P("flex-1 outline-none",a),...s})}k.__docgenInfo={description:"",methods:[],displayName:"Tabs"};R.__docgenInfo={description:"",methods:[],displayName:"TabsList"};b.__docgenInfo={description:"",methods:[],displayName:"TabsTrigger"};f.__docgenInfo={description:"",methods:[],displayName:"TabsContent"};k.__docgenInfo={description:"",methods:[],displayName:"Tabs"};R.__docgenInfo={description:"",methods:[],displayName:"TabsList"};b.__docgenInfo={description:"",methods:[],displayName:"TabsTrigger"};f.__docgenInfo={description:"",methods:[],displayName:"TabsContent"};const ha={title:"UI/Tabs",component:k,parameters:{layout:"padded"},tags:["autodocs"]},y={render:()=>e.jsxs(k,{defaultValue:"account",className:"w-full max-w-md",children:[e.jsxs(R,{children:[e.jsx(b,{value:"account",children:"Account"}),e.jsx(b,{value:"password",children:"Password"}),e.jsx(b,{value:"notifications",children:"Notifications"})]}),e.jsx(f,{value:"account",children:e.jsxs(G,{children:[e.jsxs(O,{children:[e.jsx(H,{children:"Account"}),e.jsx(K,{children:"Make changes to your account here."})]}),e.jsxs(U,{className:"space-y-2",children:[e.jsxs("div",{className:"space-y-1",children:[e.jsx("label",{className:"text-sm font-medium",children:"Name"}),e.jsx("input",{className:"w-full px-3 py-2 border rounded-md",defaultValue:"Ryan Chen"})]}),e.jsxs("div",{className:"space-y-1",children:[e.jsx("label",{className:"text-sm font-medium",children:"Email"}),e.jsx("input",{className:"w-full px-3 py-2 border rounded-md",defaultValue:"ryan@morningai.com"})]})]})]})}),e.jsx(f,{value:"password",children:e.jsxs(G,{children:[e.jsxs(O,{children:[e.jsx(H,{children:"Password"}),e.jsx(K,{children:"Change your password here."})]}),e.jsxs(U,{className:"space-y-2",children:[e.jsxs("div",{className:"space-y-1",children:[e.jsx("label",{className:"text-sm font-medium",children:"Current Password"}),e.jsx("input",{type:"password",className:"w-full px-3 py-2 border rounded-md"})]}),e.jsxs("div",{className:"space-y-1",children:[e.jsx("label",{className:"text-sm font-medium",children:"New Password"}),e.jsx("input",{type:"password",className:"w-full px-3 py-2 border rounded-md"})]})]})]})}),e.jsx(f,{value:"notifications",children:e.jsxs(G,{children:[e.jsxs(O,{children:[e.jsx(H,{children:"Notifications"}),e.jsx(K,{children:"Manage your notification preferences."})]}),e.jsxs(U,{className:"space-y-2",children:[e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsx("label",{className:"text-sm font-medium",children:"Email notifications"}),e.jsx("input",{type:"checkbox",defaultChecked:!0})]}),e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsx("label",{className:"text-sm font-medium",children:"Push notifications"}),e.jsx("input",{type:"checkbox"})]})]})]})})]})},w={render:()=>e.jsxs(k,{defaultValue:"overview",className:"w-full max-w-md",children:[e.jsxs(R,{children:[e.jsx(b,{value:"overview",children:"Overview"}),e.jsx(b,{value:"analytics",children:"Analytics"}),e.jsx(b,{value:"reports",children:"Reports"})]}),e.jsx(f,{value:"overview",className:"mt-4",children:e.jsx("p",{className:"text-sm text-muted-foreground",children:"View your dashboard overview with key metrics and insights."})}),e.jsx(f,{value:"analytics",className:"mt-4",children:e.jsx("p",{className:"text-sm text-muted-foreground",children:"Detailed analytics and performance metrics for your account."})}),e.jsx(f,{value:"reports",className:"mt-4",children:e.jsx("p",{className:"text-sm text-muted-foreground",children:"Generate and download custom reports for your data."})})]}),parameters:{docs:{description:{story:"Simple tabs with text content only."}}}},j={render:()=>e.jsxs(k,{defaultValue:"all",className:"w-full",children:[e.jsxs(R,{className:"w-full",children:[e.jsx(b,{value:"all",className:"flex-1",children:"All"}),e.jsx(b,{value:"active",className:"flex-1",children:"Active"}),e.jsx(b,{value:"completed",className:"flex-1",children:"Completed"}),e.jsx(b,{value:"archived",className:"flex-1",children:"Archived"})]}),e.jsx(f,{value:"all",className:"mt-4",children:e.jsxs("div",{className:"space-y-2",children:[e.jsx("div",{className:"p-3 border rounded-md",children:"Task 1"}),e.jsx("div",{className:"p-3 border rounded-md",children:"Task 2"}),e.jsx("div",{className:"p-3 border rounded-md",children:"Task 3"})]})}),e.jsx(f,{value:"active",className:"mt-4",children:e.jsxs("div",{className:"space-y-2",children:[e.jsx("div",{className:"p-3 border rounded-md",children:"Active Task 1"}),e.jsx("div",{className:"p-3 border rounded-md",children:"Active Task 2"})]})}),e.jsx(f,{value:"completed",className:"mt-4",children:e.jsx("div",{className:"space-y-2",children:e.jsx("div",{className:"p-3 border rounded-md",children:"Completed Task 1"})})}),e.jsx(f,{value:"archived",className:"mt-4",children:e.jsx("p",{className:"text-sm text-muted-foreground",children:"No archived tasks"})})]}),parameters:{docs:{description:{story:"Tabs with full-width triggers that distribute evenly."}}}};var q,J,Q;y.parameters={...y.parameters,docs:{...(q=y.parameters)==null?void 0:q.docs,source:{originalSource:`{
  render: () => <Tabs defaultValue="account" className="w-full max-w-md">
      <TabsList>
        <TabsTrigger value="account">Account</TabsTrigger>
        <TabsTrigger value="password">Password</TabsTrigger>
        <TabsTrigger value="notifications">Notifications</TabsTrigger>
      </TabsList>
      <TabsContent value="account">
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <CardDescription>
              Make changes to your account here.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="space-y-1">
              <label className="text-sm font-medium">Name</label>
              <input className="w-full px-3 py-2 border rounded-md" defaultValue="Ryan Chen" />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">Email</label>
              <input className="w-full px-3 py-2 border rounded-md" defaultValue="ryan@morningai.com" />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="password">
        <Card>
          <CardHeader>
            <CardTitle>Password</CardTitle>
            <CardDescription>
              Change your password here.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="space-y-1">
              <label className="text-sm font-medium">Current Password</label>
              <input type="password" className="w-full px-3 py-2 border rounded-md" />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">New Password</label>
              <input type="password" className="w-full px-3 py-2 border rounded-md" />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="notifications">
        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>
              Manage your notification preferences.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Email notifications</label>
              <input type="checkbox" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Push notifications</label>
              <input type="checkbox" />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
}`,...(Q=(J=y.parameters)==null?void 0:J.docs)==null?void 0:Q.source}}};var X,Z,ee;w.parameters={...w.parameters,docs:{...(X=w.parameters)==null?void 0:X.docs,source:{originalSource:`{
  render: () => <Tabs defaultValue="overview" className="w-full max-w-md">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="analytics">Analytics</TabsTrigger>
        <TabsTrigger value="reports">Reports</TabsTrigger>
      </TabsList>
      <TabsContent value="overview" className="mt-4">
        <p className="text-sm text-muted-foreground">
          View your dashboard overview with key metrics and insights.
        </p>
      </TabsContent>
      <TabsContent value="analytics" className="mt-4">
        <p className="text-sm text-muted-foreground">
          Detailed analytics and performance metrics for your account.
        </p>
      </TabsContent>
      <TabsContent value="reports" className="mt-4">
        <p className="text-sm text-muted-foreground">
          Generate and download custom reports for your data.
        </p>
      </TabsContent>
    </Tabs>,
  parameters: {
    docs: {
      description: {
        story: 'Simple tabs with text content only.'
      }
    }
  }
}`,...(ee=(Z=w.parameters)==null?void 0:Z.docs)==null?void 0:ee.source}}};var ae,se,te;j.parameters={...j.parameters,docs:{...(ae=j.parameters)==null?void 0:ae.docs,source:{originalSource:`{
  render: () => <Tabs defaultValue="all" className="w-full">
      <TabsList className="w-full">
        <TabsTrigger value="all" className="flex-1">All</TabsTrigger>
        <TabsTrigger value="active" className="flex-1">Active</TabsTrigger>
        <TabsTrigger value="completed" className="flex-1">Completed</TabsTrigger>
        <TabsTrigger value="archived" className="flex-1">Archived</TabsTrigger>
      </TabsList>
      <TabsContent value="all" className="mt-4">
        <div className="space-y-2">
          <div className="p-3 border rounded-md">Task 1</div>
          <div className="p-3 border rounded-md">Task 2</div>
          <div className="p-3 border rounded-md">Task 3</div>
        </div>
      </TabsContent>
      <TabsContent value="active" className="mt-4">
        <div className="space-y-2">
          <div className="p-3 border rounded-md">Active Task 1</div>
          <div className="p-3 border rounded-md">Active Task 2</div>
        </div>
      </TabsContent>
      <TabsContent value="completed" className="mt-4">
        <div className="space-y-2">
          <div className="p-3 border rounded-md">Completed Task 1</div>
        </div>
      </TabsContent>
      <TabsContent value="archived" className="mt-4">
        <p className="text-sm text-muted-foreground">No archived tasks</p>
      </TabsContent>
    </Tabs>,
  parameters: {
    docs: {
      description: {
        story: 'Tabs with full-width triggers that distribute evenly.'
      }
    }
  }
}`,...(te=(se=j.parameters)==null?void 0:se.docs)==null?void 0:te.source}}};var re,ne,oe;y.parameters={...y.parameters,docs:{...(re=y.parameters)==null?void 0:re.docs,source:{originalSource:`{
  render: () => <Tabs defaultValue="account" className="w-full max-w-md">
      <TabsList>
        <TabsTrigger value="account">Account</TabsTrigger>
        <TabsTrigger value="password">Password</TabsTrigger>
        <TabsTrigger value="notifications">Notifications</TabsTrigger>
      </TabsList>
      <TabsContent value="account">
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <CardDescription>
              Make changes to your account here.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="space-y-1">
              <label className="text-sm font-medium">Name</label>
              <input className="w-full px-3 py-2 border rounded-md" defaultValue="Ryan Chen" />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">Email</label>
              <input className="w-full px-3 py-2 border rounded-md" defaultValue="ryan@morningai.com" />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="password">
        <Card>
          <CardHeader>
            <CardTitle>Password</CardTitle>
            <CardDescription>
              Change your password here.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="space-y-1">
              <label className="text-sm font-medium">Current Password</label>
              <input type="password" className="w-full px-3 py-2 border rounded-md" />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">New Password</label>
              <input type="password" className="w-full px-3 py-2 border rounded-md" />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="notifications">
        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>
              Manage your notification preferences.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Email notifications</label>
              <input type="checkbox" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Push notifications</label>
              <input type="checkbox" />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
}`,...(oe=(ne=y.parameters)==null?void 0:ne.docs)==null?void 0:oe.source}}};var ie,de,ce;w.parameters={...w.parameters,docs:{...(ie=w.parameters)==null?void 0:ie.docs,source:{originalSource:`{
  render: () => <Tabs defaultValue="overview" className="w-full max-w-md">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="analytics">Analytics</TabsTrigger>
        <TabsTrigger value="reports">Reports</TabsTrigger>
      </TabsList>
      <TabsContent value="overview" className="mt-4">
        <p className="text-sm text-muted-foreground">
          View your dashboard overview with key metrics and insights.
        </p>
      </TabsContent>
      <TabsContent value="analytics" className="mt-4">
        <p className="text-sm text-muted-foreground">
          Detailed analytics and performance metrics for your account.
        </p>
      </TabsContent>
      <TabsContent value="reports" className="mt-4">
        <p className="text-sm text-muted-foreground">
          Generate and download custom reports for your data.
        </p>
      </TabsContent>
    </Tabs>,
  parameters: {
    docs: {
      description: {
        story: 'Simple tabs with text content only.'
      }
    }
  }
}`,...(ce=(de=w.parameters)==null?void 0:de.docs)==null?void 0:ce.source}}};var le,ue,me;j.parameters={...j.parameters,docs:{...(le=j.parameters)==null?void 0:le.docs,source:{originalSource:`{
  render: () => <Tabs defaultValue="all" className="w-full">
      <TabsList className="w-full">
        <TabsTrigger value="all" className="flex-1">All</TabsTrigger>
        <TabsTrigger value="active" className="flex-1">Active</TabsTrigger>
        <TabsTrigger value="completed" className="flex-1">Completed</TabsTrigger>
        <TabsTrigger value="archived" className="flex-1">Archived</TabsTrigger>
      </TabsList>
      <TabsContent value="all" className="mt-4">
        <div className="space-y-2">
          <div className="p-3 border rounded-md">Task 1</div>
          <div className="p-3 border rounded-md">Task 2</div>
          <div className="p-3 border rounded-md">Task 3</div>
        </div>
      </TabsContent>
      <TabsContent value="active" className="mt-4">
        <div className="space-y-2">
          <div className="p-3 border rounded-md">Active Task 1</div>
          <div className="p-3 border rounded-md">Active Task 2</div>
        </div>
      </TabsContent>
      <TabsContent value="completed" className="mt-4">
        <div className="space-y-2">
          <div className="p-3 border rounded-md">Completed Task 1</div>
        </div>
      </TabsContent>
      <TabsContent value="archived" className="mt-4">
        <p className="text-sm text-muted-foreground">No archived tasks</p>
      </TabsContent>
    </Tabs>,
  parameters: {
    docs: {
      description: {
        story: 'Tabs with full-width triggers that distribute evenly.'
      }
    }
  }
}`,...(me=(ue=j.parameters)==null?void 0:ue.docs)==null?void 0:me.source}}};const ya=["Default","Simple","FullWidth"];export{y as Default,j as FullWidth,w as Simple,ya as __namedExportsOrder,ha as default};
