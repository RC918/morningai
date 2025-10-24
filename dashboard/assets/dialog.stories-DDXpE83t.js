import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as s}from"./index-Dz3UJJSw.js";import{d as Ue,a as $e,c as Ve,b as F,e as Ge}from"./createLucideIcon-CPl_Fi5k.js";import{u as w,b as Ye,c as I}from"./utils-ClSdSIbF.js";import{u as O,P as ze,h as Ke,R as Xe,a as Ze,F as Je,D as Qe}from"./index-DmZd5CDD.js";import{P as A}from"./index-WZXaWNJA.js";import{P as S}from"./index-CWPL_hnH.js";import{B as d}from"./button-CtW_o4fY.js";import{I as W}from"./input-Wn9FKRmr.js";import{L as U}from"./label-CQdBpAJ_.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-CYANIyVc.js";import"./index-fUCaa9pg.js";import"./index-CN2Y8dJ9.js";/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const eo=[["path",{d:"M18 6 6 18",key:"1bl5f8"}],["path",{d:"m6 6 12 12",key:"d8bk6v"}]],oo=Ue("x",eo);var P="Dialog",[be]=Ve(P),[ao,u]=be(P),Be=o=>{const{__scopeDialog:a,children:i,open:r,defaultOpen:n,onOpenChange:t,modal:l=!0}=o,c=s.useRef(null),p=s.useRef(null),[B,R]=$e({prop:r,defaultProp:n??!1,onChange:t,caller:P});return e.jsx(ao,{scope:a,triggerRef:c,contentRef:p,contentId:O(),titleId:O(),descriptionId:O(),open:B,onOpenChange:R,onOpenToggle:s.useCallback(()=>R(We=>!We),[R]),modal:l,children:i})};Be.displayName=P;var Ie="DialogTrigger",Fe=s.forwardRef((o,a)=>{const{__scopeDialog:i,...r}=o,n=u(Ie,i),t=w(a,n.triggerRef);return e.jsx(S.button,{type:"button","aria-haspopup":"dialog","aria-expanded":n.open,"aria-controls":n.contentId,"data-state":M(n.open),...r,ref:t,onClick:F(o.onClick,n.onOpenToggle)})});Fe.displayName=Ie;var H="DialogPortal",[to,Se]=be(H,{forceMount:void 0}),Ee=o=>{const{__scopeDialog:a,forceMount:i,children:r,container:n}=o,t=u(H,a);return e.jsx(to,{scope:a,forceMount:i,children:s.Children.map(r,l=>e.jsx(A,{present:i||t.open,children:e.jsx(ze,{asChild:!0,container:n,children:l})}))})};Ee.displayName=H;var E="DialogOverlay",Pe=s.forwardRef((o,a)=>{const i=Se(E,o.__scopeDialog),{forceMount:r=i.forceMount,...n}=o,t=u(E,o.__scopeDialog);return t.modal?e.jsx(A,{present:r||t.open,children:e.jsx(no,{...n,ref:a})}):null});Pe.displayName=E;var io=Ye("DialogOverlay.RemoveScroll"),no=s.forwardRef((o,a)=>{const{__scopeDialog:i,...r}=o,n=u(E,i);return e.jsx(Xe,{as:io,allowPinchZoom:!0,shards:[n.contentRef],children:e.jsx(S.div,{"data-state":M(n.open),...r,ref:a,style:{pointerEvents:"auto",...r.style}})})}),_="DialogContent",Re=s.forwardRef((o,a)=>{const i=Se(_,o.__scopeDialog),{forceMount:r=i.forceMount,...n}=o,t=u(_,o.__scopeDialog);return e.jsx(A,{present:r||t.open,children:t.modal?e.jsx(ro,{...n,ref:a}):e.jsx(so,{...n,ref:a})})});Re.displayName=_;var ro=s.forwardRef((o,a)=>{const i=u(_,o.__scopeDialog),r=s.useRef(null),n=w(a,i.contentRef,r);return s.useEffect(()=>{const t=r.current;if(t)return Ke(t)},[]),e.jsx(Oe,{...o,ref:n,trapFocus:i.open,disableOutsidePointerEvents:!0,onCloseAutoFocus:F(o.onCloseAutoFocus,t=>{var l;t.preventDefault(),(l=i.triggerRef.current)==null||l.focus()}),onPointerDownOutside:F(o.onPointerDownOutside,t=>{const l=t.detail.originalEvent,c=l.button===0&&l.ctrlKey===!0;(l.button===2||c)&&t.preventDefault()}),onFocusOutside:F(o.onFocusOutside,t=>t.preventDefault())})}),so=s.forwardRef((o,a)=>{const i=u(_,o.__scopeDialog),r=s.useRef(!1),n=s.useRef(!1);return e.jsx(Oe,{...o,ref:a,trapFocus:!1,disableOutsidePointerEvents:!1,onCloseAutoFocus:t=>{var l,c;(l=o.onCloseAutoFocus)==null||l.call(o,t),t.defaultPrevented||(r.current||(c=i.triggerRef.current)==null||c.focus(),t.preventDefault()),r.current=!1,n.current=!1},onInteractOutside:t=>{var p,B;(p=o.onInteractOutside)==null||p.call(o,t),t.defaultPrevented||(r.current=!0,t.detail.originalEvent.type==="pointerdown"&&(n.current=!0));const l=t.target;((B=i.triggerRef.current)==null?void 0:B.contains(l))&&t.preventDefault(),t.detail.originalEvent.type==="focusin"&&n.current&&t.preventDefault()}})}),Oe=s.forwardRef((o,a)=>{const{__scopeDialog:i,trapFocus:r,onOpenAutoFocus:n,onCloseAutoFocus:t,...l}=o,c=u(_,i),p=s.useRef(null),B=w(a,p);return Ze(),e.jsxs(e.Fragment,{children:[e.jsx(Je,{asChild:!0,loop:!0,trapped:r,onMountAutoFocus:n,onUnmountAutoFocus:t,children:e.jsx(Qe,{role:"dialog",id:c.contentId,"aria-describedby":c.descriptionId,"aria-labelledby":c.titleId,"data-state":M(c.open),...l,ref:B,onDismiss:()=>c.onOpenChange(!1)})}),e.jsxs(e.Fragment,{children:[e.jsx(lo,{titleId:c.titleId}),e.jsx(uo,{contentRef:p,descriptionId:c.descriptionId})]})]})}),q="DialogTitle",we=s.forwardRef((o,a)=>{const{__scopeDialog:i,...r}=o,n=u(q,i);return e.jsx(S.h2,{id:n.titleId,...r,ref:a})});we.displayName=q;var Ae="DialogDescription",He=s.forwardRef((o,a)=>{const{__scopeDialog:i,...r}=o,n=u(Ae,i);return e.jsx(S.p,{id:n.descriptionId,...r,ref:a})});He.displayName=Ae;var qe="DialogClose",Me=s.forwardRef((o,a)=>{const{__scopeDialog:i,...r}=o,n=u(qe,i);return e.jsx(S.button,{type:"button",...r,ref:a,onClick:F(o.onClick,()=>n.onOpenChange(!1))})});Me.displayName=qe;function M(o){return o?"open":"closed"}var Le="DialogTitleWarning",[Oo,ke]=Ge(Le,{contentName:_,titleName:q,docsSlug:"dialog"}),lo=({titleId:o})=>{const a=ke(Le),i=`\`${a.contentName}\` requires a \`${a.titleName}\` for the component to be accessible for screen reader users.

If you want to hide the \`${a.titleName}\`, you can wrap it with our VisuallyHidden component.

For more information, see https://radix-ui.com/primitives/docs/components/${a.docsSlug}`;return s.useEffect(()=>{o&&(document.getElementById(o)||console.error(i))},[i,o]),null},co="DialogDescriptionWarning",uo=({contentRef:o,descriptionId:a})=>{const r=`Warning: Missing \`Description\` or \`aria-describedby={undefined}\` for {${ke(co).contentName}}.`;return s.useEffect(()=>{var t;const n=(t=o.current)==null?void 0:t.getAttribute("aria-describedby");a&&n&&(document.getElementById(a)||console.warn(r))},[r,o,a]),null},go=Be,po=Fe,mo=Ee,Do=Pe,ho=Re,fo=we,xo=He,vo=Me;function g({...o}){return e.jsx(go,{"data-slot":"dialog",...o})}function y({...o}){return e.jsx(po,{"data-slot":"dialog-trigger",...o})}function L({...o}){return e.jsx(mo,{"data-slot":"dialog-portal",...o})}function k({className:o,...a}){return e.jsx(Do,{"data-slot":"dialog-overlay",className:I("data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-[9999] bg-black/50",o),...a})}function j({className:o,children:a,...i}){return e.jsxs(L,{"data-slot":"dialog-portal",children:[e.jsx(k,{}),e.jsxs(ho,{"data-slot":"dialog-content",className:I("bg-background data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 fixed top-[50%] left-[50%] z-[10000] grid w-full max-w-[calc(100%-2rem)] translate-x-[-50%] translate-y-[-50%] gap-4 rounded-lg border p-6 shadow-lg duration-200 sm:max-w-lg",o),...i,children:[a,e.jsxs(vo,{className:"ring-offset-background focus:ring-ring data-[state=open]:bg-accent data-[state=open]:text-muted-foreground absolute top-4 right-4 rounded-xs opacity-70 transition-opacity hover:opacity-100 focus:ring-2 focus:ring-offset-2 focus:outline-hidden disabled:pointer-events-none [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",children:[e.jsx(oo,{}),e.jsx("span",{className:"sr-only",children:"Close"})]})]})]})}function C({className:o,...a}){return e.jsx("div",{"data-slot":"dialog-header",className:I("flex flex-col gap-2 text-center sm:text-left",o),...a})}function N({className:o,...a}){return e.jsx("div",{"data-slot":"dialog-footer",className:I("flex flex-col-reverse gap-2 sm:flex-row sm:justify-end",o),...a})}function T({className:o,...a}){return e.jsx(fo,{"data-slot":"dialog-title",className:I("text-lg leading-none font-semibold",o),...a})}function b({className:o,...a}){return e.jsx(xo,{"data-slot":"dialog-description",className:I("text-muted-foreground text-sm",o),...a})}g.__docgenInfo={description:"",methods:[],displayName:"Dialog"};j.__docgenInfo={description:"",methods:[],displayName:"DialogContent"};b.__docgenInfo={description:"",methods:[],displayName:"DialogDescription"};N.__docgenInfo={description:"",methods:[],displayName:"DialogFooter"};C.__docgenInfo={description:"",methods:[],displayName:"DialogHeader"};k.__docgenInfo={description:"",methods:[],displayName:"DialogOverlay"};L.__docgenInfo={description:"",methods:[],displayName:"DialogPortal"};T.__docgenInfo={description:"",methods:[],displayName:"DialogTitle"};y.__docgenInfo={description:"",methods:[],displayName:"DialogTrigger"};g.__docgenInfo={description:"",methods:[],displayName:"Dialog"};j.__docgenInfo={description:"",methods:[],displayName:"DialogContent"};b.__docgenInfo={description:"",methods:[],displayName:"DialogDescription"};N.__docgenInfo={description:"",methods:[],displayName:"DialogFooter"};C.__docgenInfo={description:"",methods:[],displayName:"DialogHeader"};k.__docgenInfo={description:"",methods:[],displayName:"DialogOverlay"};L.__docgenInfo={description:"",methods:[],displayName:"DialogPortal"};T.__docgenInfo={description:"",methods:[],displayName:"DialogTitle"};y.__docgenInfo={description:"",methods:[],displayName:"DialogTrigger"};const wo={title:"UI/Dialog",component:g,parameters:{layout:"centered"},tags:["autodocs"]},m={render:()=>e.jsxs(g,{children:[e.jsx(y,{asChild:!0,children:e.jsx(d,{children:"Open Dialog"})}),e.jsxs(j,{children:[e.jsxs(C,{children:[e.jsx(T,{children:"Dialog Title"}),e.jsx(b,{children:"This is a dialog description. You can put any content here."})]}),e.jsx("div",{className:"py-4",children:e.jsx("p",{children:"Dialog content goes here."})}),e.jsx(N,{children:e.jsx(d,{children:"Close"})})]})]})},D={render:()=>e.jsxs(g,{children:[e.jsx(y,{asChild:!0,children:e.jsx(d,{children:"Edit Profile"})}),e.jsxs(j,{className:"sm:max-w-[425px]",children:[e.jsxs(C,{children:[e.jsx(T,{children:"Edit profile"}),e.jsx(b,{children:"Make changes to your profile here. Click save when you're done."})]}),e.jsxs("div",{className:"grid gap-4 py-4",children:[e.jsxs("div",{className:"grid grid-cols-4 items-center gap-4",children:[e.jsx(U,{htmlFor:"name",className:"text-right",children:"Name"}),e.jsx(W,{id:"name",defaultValue:"Pedro Duarte",className:"col-span-3"})]}),e.jsxs("div",{className:"grid grid-cols-4 items-center gap-4",children:[e.jsx(U,{htmlFor:"username",className:"text-right",children:"Username"}),e.jsx(W,{id:"username",defaultValue:"@peduarte",className:"col-span-3"})]})]}),e.jsx(N,{children:e.jsx(d,{type:"submit",children:"Save changes"})})]})]})},h={render:()=>e.jsxs(g,{children:[e.jsx(y,{asChild:!0,children:e.jsx(d,{variant:"destructive",children:"Delete Account"})}),e.jsxs(j,{children:[e.jsxs(C,{children:[e.jsx(T,{children:"Are you absolutely sure?"}),e.jsx(b,{children:"This action cannot be undone. This will permanently delete your account and remove your data from our servers."})]}),e.jsxs(N,{children:[e.jsx(d,{variant:"outline",children:"Cancel"}),e.jsx(d,{variant:"destructive",children:"Delete"})]})]})]})},f={render:()=>e.jsxs(g,{children:[e.jsx(y,{asChild:!0,children:e.jsx(d,{children:"Open"})}),e.jsxs(j,{children:[e.jsx(C,{children:e.jsx(T,{children:"Simple Dialog"})}),e.jsx("div",{className:"py-4",children:e.jsx("p",{children:"This dialog has no description."})}),e.jsx(N,{children:e.jsx(d,{children:"OK"})})]})]})},x={render:()=>e.jsxs(g,{children:[e.jsx(y,{asChild:!0,children:e.jsx(d,{children:"View Terms"})}),e.jsxs(j,{className:"max-h-[80vh] overflow-y-auto",children:[e.jsxs(C,{children:[e.jsx(T,{children:"Terms and Conditions"}),e.jsx(b,{children:"Please read our terms and conditions carefully."})]}),e.jsxs("div",{className:"py-4 space-y-4",children:[e.jsx("p",{children:"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."}),e.jsx("p",{children:"Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."}),e.jsx("p",{children:"Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."}),e.jsx("p",{children:"Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."}),e.jsx("p",{children:"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."}),e.jsx("p",{children:"Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."})]}),e.jsx(N,{children:e.jsx(d,{children:"Accept"})})]})]})},v={render:()=>e.jsxs(g,{children:[e.jsx(y,{asChild:!0,children:e.jsx(d,{children:"Save Changes"})}),e.jsxs(j,{children:[e.jsxs(C,{children:[e.jsx(T,{children:"Unsaved Changes"}),e.jsx(b,{children:"You have unsaved changes. What would you like to do?"})]}),e.jsxs(N,{className:"sm:justify-between",children:[e.jsx(d,{variant:"outline",children:"Cancel"}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx(d,{variant:"secondary",children:"Don't Save"}),e.jsx(d,{children:"Save"})]})]})]})]})};var $,V,G;m.parameters={...m.parameters,docs:{...($=m.parameters)==null?void 0:$.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Dialog Title</DialogTitle>
          <DialogDescription>
            This is a dialog description. You can put any content here.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p>Dialog content goes here.</p>
        </div>
        <DialogFooter>
          <Button>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(G=(V=m.parameters)==null?void 0:V.docs)==null?void 0:G.source}}};var Y,z,K;D.parameters={...D.parameters,docs:{...(Y=D.parameters)==null?void 0:Y.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Edit Profile</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit profile</DialogTitle>
          <DialogDescription>
            Make changes to your profile here. Click save when you're done.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              Name
            </Label>
            <Input id="name" defaultValue="Pedro Duarte" className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="username" className="text-right">
              Username
            </Label>
            <Input id="username" defaultValue="@peduarte" className="col-span-3" />
          </div>
        </div>
        <DialogFooter>
          <Button type="submit">Save changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(K=(z=D.parameters)==null?void 0:z.docs)==null?void 0:K.source}}};var X,Z,J;h.parameters={...h.parameters,docs:{...(X=h.parameters)==null?void 0:X.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive">Delete Account</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Are you absolutely sure?</DialogTitle>
          <DialogDescription>
            This action cannot be undone. This will permanently delete your
            account and remove your data from our servers.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive">Delete</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(J=(Z=h.parameters)==null?void 0:Z.docs)==null?void 0:J.source}}};var Q,ee,oe;f.parameters={...f.parameters,docs:{...(Q=f.parameters)==null?void 0:Q.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Open</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Simple Dialog</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <p>This dialog has no description.</p>
        </div>
        <DialogFooter>
          <Button>OK</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(oe=(ee=f.parameters)==null?void 0:ee.docs)==null?void 0:oe.source}}};var ae,te,ie;x.parameters={...x.parameters,docs:{...(ae=x.parameters)==null?void 0:ae.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>View Terms</Button>
      </DialogTrigger>
      <DialogContent className="max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Terms and Conditions</DialogTitle>
          <DialogDescription>
            Please read our terms and conditions carefully.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 space-y-4">
          <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
          <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
          <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
          <p>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
          <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
          <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
        </div>
        <DialogFooter>
          <Button>Accept</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(ie=(te=x.parameters)==null?void 0:te.docs)==null?void 0:ie.source}}};var ne,re,se;v.parameters={...v.parameters,docs:{...(ne=v.parameters)==null?void 0:ne.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Save Changes</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Unsaved Changes</DialogTitle>
          <DialogDescription>
            You have unsaved changes. What would you like to do?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="sm:justify-between">
          <Button variant="outline">Cancel</Button>
          <div className="flex gap-2">
            <Button variant="secondary">Don't Save</Button>
            <Button>Save</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(se=(re=v.parameters)==null?void 0:re.docs)==null?void 0:se.source}}};var le,ce,de;m.parameters={...m.parameters,docs:{...(le=m.parameters)==null?void 0:le.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Dialog Title</DialogTitle>
          <DialogDescription>
            This is a dialog description. You can put any content here.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p>Dialog content goes here.</p>
        </div>
        <DialogFooter>
          <Button>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(de=(ce=m.parameters)==null?void 0:ce.docs)==null?void 0:de.source}}};var ue,ge,pe;D.parameters={...D.parameters,docs:{...(ue=D.parameters)==null?void 0:ue.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Edit Profile</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit profile</DialogTitle>
          <DialogDescription>
            Make changes to your profile here. Click save when you're done.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              Name
            </Label>
            <Input id="name" defaultValue="Pedro Duarte" className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="username" className="text-right">
              Username
            </Label>
            <Input id="username" defaultValue="@peduarte" className="col-span-3" />
          </div>
        </div>
        <DialogFooter>
          <Button type="submit">Save changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(pe=(ge=D.parameters)==null?void 0:ge.docs)==null?void 0:pe.source}}};var me,De,he;h.parameters={...h.parameters,docs:{...(me=h.parameters)==null?void 0:me.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive">Delete Account</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Are you absolutely sure?</DialogTitle>
          <DialogDescription>
            This action cannot be undone. This will permanently delete your
            account and remove your data from our servers.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive">Delete</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(he=(De=h.parameters)==null?void 0:De.docs)==null?void 0:he.source}}};var fe,xe,ve;f.parameters={...f.parameters,docs:{...(fe=f.parameters)==null?void 0:fe.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Open</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Simple Dialog</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <p>This dialog has no description.</p>
        </div>
        <DialogFooter>
          <Button>OK</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(ve=(xe=f.parameters)==null?void 0:xe.docs)==null?void 0:ve.source}}};var ye,je,Ce;x.parameters={...x.parameters,docs:{...(ye=x.parameters)==null?void 0:ye.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>View Terms</Button>
      </DialogTrigger>
      <DialogContent className="max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Terms and Conditions</DialogTitle>
          <DialogDescription>
            Please read our terms and conditions carefully.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 space-y-4">
          <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
          <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
          <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
          <p>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
          <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
          <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
        </div>
        <DialogFooter>
          <Button>Accept</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(Ce=(je=x.parameters)==null?void 0:je.docs)==null?void 0:Ce.source}}};var Ne,Te,_e;v.parameters={...v.parameters,docs:{...(Ne=v.parameters)==null?void 0:Ne.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Save Changes</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Unsaved Changes</DialogTitle>
          <DialogDescription>
            You have unsaved changes. What would you like to do?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="sm:justify-between">
          <Button variant="outline">Cancel</Button>
          <div className="flex gap-2">
            <Button variant="secondary">Don't Save</Button>
            <Button>Save</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...(_e=(Te=v.parameters)==null?void 0:Te.docs)==null?void 0:_e.source}}};const Ao=["Default","WithForm","Confirmation","WithoutDescription","LongContent","MultipleButtons"];export{h as Confirmation,m as Default,x as LongContent,v as MultipleButtons,D as WithForm,f as WithoutDescription,Ao as __namedExportsOrder,wo as default};
