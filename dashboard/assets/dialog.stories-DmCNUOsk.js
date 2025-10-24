import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as l}from"./index-Dz3UJJSw.js";import{u as Wo,c as R}from"./index-Bo7lbUv-.js";import{u as $,c as Mo}from"./index-DRuEWG1E.js";import{c as ko,a as Uo}from"./index-DiKooijE.js";import{u as V}from"./index-HmPO_Abe.js";import{P as Vo,D as $o}from"./index-CevHeI5L.js";import{h as Yo,R as zo,u as Go,F as Ko}from"./index-DTuDuRIS.js";import{P as Y}from"./index-B6CVSQiA.js";import{P as q}from"./index-C7eB__Z-.js";import{c as L}from"./utils-D-KgF5mV.js";import{c as Jo}from"./createLucideIcon-ClV4rtrr.js";import{B as s}from"./button-6x4QkhmZ.js";import{I as O}from"./input-Cv5CY2yx.js";import{L as E}from"./label-B-2P1Ax_.js";import{B as W}from"./badge-BEslsuGz.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-BwP8QHTI.js";import"./index-CYANIyVc.js";import"./index-fUCaa9pg.js";import"./index-CGrAONsN.js";/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xo=[["path",{d:"M18 6 6 18",key:"1bl5f8"}],["path",{d:"m6 6 12 12",key:"d8bk6v"}]],Zo=Jo("x",Xo);var k="Dialog",[To]=ko(k),[Qo,f]=To(k),No=o=>{const{__scopeDialog:a,children:t,open:n,defaultOpen:r,onOpenChange:i,modal:d=!0}=o,g=l.useRef(null),v=l.useRef(null),[H,U]=Wo({prop:n,defaultProp:r??!1,onChange:i,caller:k});return e.jsx(Qo,{scope:a,triggerRef:g,contentRef:v,contentId:V(),titleId:V(),descriptionId:V(),open:H,onOpenChange:U,onOpenToggle:l.useCallback(()=>U(qo=>!qo),[U]),modal:d,children:t})};No.displayName=k;var wo="DialogTrigger",Bo=l.forwardRef((o,a)=>{const{__scopeDialog:t,...n}=o,r=f(wo,t),i=$(a,r.triggerRef);return e.jsx(q.button,{type:"button","aria-haspopup":"dialog","aria-expanded":r.open,"aria-controls":r.contentId,"data-state":K(r.open),...n,ref:i,onClick:R(o.onClick,r.onOpenToggle)})});Bo.displayName=wo;var z="DialogPortal",[ea,bo]=To(z,{forceMount:void 0}),Fo=o=>{const{__scopeDialog:a,forceMount:t,children:n,container:r}=o,i=f(z,a);return e.jsx(ea,{scope:a,forceMount:t,children:l.Children.map(n,d=>e.jsx(Y,{present:t||i.open,children:e.jsx(Vo,{asChild:!0,container:r,children:d})}))})};Fo.displayName=z;var M="DialogOverlay",_o=l.forwardRef((o,a)=>{const t=bo(M,o.__scopeDialog),{forceMount:n=t.forceMount,...r}=o,i=f(M,o.__scopeDialog);return i.modal?e.jsx(Y,{present:n||i.open,children:e.jsx(aa,{...r,ref:a})}):null});_o.displayName=M;var oa=Mo("DialogOverlay.RemoveScroll"),aa=l.forwardRef((o,a)=>{const{__scopeDialog:t,...n}=o,r=f(M,t);return e.jsx(zo,{as:oa,allowPinchZoom:!0,shards:[r.contentRef],children:e.jsx(q.div,{"data-state":K(r.open),...n,ref:a,style:{pointerEvents:"auto",...n.style}})})}),I="DialogContent",So=l.forwardRef((o,a)=>{const t=bo(I,o.__scopeDialog),{forceMount:n=t.forceMount,...r}=o,i=f(I,o.__scopeDialog);return e.jsx(Y,{present:n||i.open,children:i.modal?e.jsx(ia,{...r,ref:a}):e.jsx(ta,{...r,ref:a})})});So.displayName=I;var ia=l.forwardRef((o,a)=>{const t=f(I,o.__scopeDialog),n=l.useRef(null),r=$(a,t.contentRef,n);return l.useEffect(()=>{const i=n.current;if(i)return Yo(i)},[]),e.jsx(Ao,{...o,ref:r,trapFocus:t.open,disableOutsidePointerEvents:!0,onCloseAutoFocus:R(o.onCloseAutoFocus,i=>{var d;i.preventDefault(),(d=t.triggerRef.current)==null||d.focus()}),onPointerDownOutside:R(o.onPointerDownOutside,i=>{const d=i.detail.originalEvent,g=d.button===0&&d.ctrlKey===!0;(d.button===2||g)&&i.preventDefault()}),onFocusOutside:R(o.onFocusOutside,i=>i.preventDefault())})}),ta=l.forwardRef((o,a)=>{const t=f(I,o.__scopeDialog),n=l.useRef(!1),r=l.useRef(!1);return e.jsx(Ao,{...o,ref:a,trapFocus:!1,disableOutsidePointerEvents:!1,onCloseAutoFocus:i=>{var d,g;(d=o.onCloseAutoFocus)==null||d.call(o,i),i.defaultPrevented||(n.current||(g=t.triggerRef.current)==null||g.focus(),i.preventDefault()),n.current=!1,r.current=!1},onInteractOutside:i=>{var v,H;(v=o.onInteractOutside)==null||v.call(o,i),i.defaultPrevented||(n.current=!0,i.detail.originalEvent.type==="pointerdown"&&(r.current=!0));const d=i.target;((H=t.triggerRef.current)==null?void 0:H.contains(d))&&i.preventDefault(),i.detail.originalEvent.type==="focusin"&&r.current&&i.preventDefault()}})}),Ao=l.forwardRef((o,a)=>{const{__scopeDialog:t,trapFocus:n,onOpenAutoFocus:r,onCloseAutoFocus:i,...d}=o,g=f(I,t),v=l.useRef(null),H=$(a,v);return Go(),e.jsxs(e.Fragment,{children:[e.jsx(Ko,{asChild:!0,loop:!0,trapped:n,onMountAutoFocus:r,onUnmountAutoFocus:i,children:e.jsx($o,{role:"dialog",id:g.contentId,"aria-describedby":g.descriptionId,"aria-labelledby":g.titleId,"data-state":K(g.open),...d,ref:H,onDismiss:()=>g.onOpenChange(!1)})}),e.jsxs(e.Fragment,{children:[e.jsx(ra,{titleId:g.titleId}),e.jsx(sa,{contentRef:v,descriptionId:g.descriptionId})]})]})}),G="DialogTitle",Po=l.forwardRef((o,a)=>{const{__scopeDialog:t,...n}=o,r=f(G,t);return e.jsx(q.h2,{id:r.titleId,...n,ref:a})});Po.displayName=G;var Io="DialogDescription",Ho=l.forwardRef((o,a)=>{const{__scopeDialog:t,...n}=o,r=f(Io,t);return e.jsx(q.p,{id:r.descriptionId,...n,ref:a})});Ho.displayName=Io;var Oo="DialogClose",Eo=l.forwardRef((o,a)=>{const{__scopeDialog:t,...n}=o,r=f(Oo,t);return e.jsx(q.button,{type:"button",...n,ref:a,onClick:R(o.onClick,()=>r.onOpenChange(!1))})});Eo.displayName=Oo;function K(o){return o?"open":"closed"}var Lo="DialogTitleWarning",[La,Ro]=Uo(Lo,{contentName:I,titleName:G,docsSlug:"dialog"}),ra=({titleId:o})=>{const a=Ro(Lo),t=`\`${a.contentName}\` requires a \`${a.titleName}\` for the component to be accessible for screen reader users.

If you want to hide the \`${a.titleName}\`, you can wrap it with our VisuallyHidden component.

For more information, see https://radix-ui.com/primitives/docs/components/${a.docsSlug}`;return l.useEffect(()=>{o&&(document.getElementById(o)||console.error(t))},[t,o]),null},na="DialogDescriptionWarning",sa=({contentRef:o,descriptionId:a})=>{const n=`Warning: Missing \`Description\` or \`aria-describedby={undefined}\` for {${Ro(na).contentName}}.`;return l.useEffect(()=>{var i;const r=(i=o.current)==null?void 0:i.getAttribute("aria-describedby");a&&r&&(document.getElementById(a)||console.warn(n))},[n,o,a]),null},la=No,da=Bo,ca=Fo,ga=_o,ua=So,pa=Po,ma=Ho,Da=Eo;function c({...o}){return e.jsx(la,{"data-slot":"dialog",...o})}function u({...o}){return e.jsx(da,{"data-slot":"dialog-trigger",...o})}function J({...o}){return e.jsx(ca,{"data-slot":"dialog-portal",...o})}function X({className:o,...a}){return e.jsx(ga,{"data-slot":"dialog-overlay",className:L("data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-[9999] bg-black/50",o),...a})}function p({className:o,children:a,...t}){return e.jsxs(J,{"data-slot":"dialog-portal",children:[e.jsx(X,{}),e.jsxs(ua,{"data-slot":"dialog-content",className:L("bg-background data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 fixed top-[50%] left-[50%] z-[10000] grid w-full max-w-[calc(100%-2rem)] translate-x-[-50%] translate-y-[-50%] gap-4 rounded-lg border p-6 shadow-lg duration-200 sm:max-w-lg",o),...t,children:[a,e.jsxs(Da,{className:"ring-offset-background focus:ring-ring data-[state=open]:bg-accent data-[state=open]:text-muted-foreground absolute top-4 right-4 rounded-xs opacity-70 transition-opacity hover:opacity-100 focus:ring-2 focus:ring-offset-2 focus:outline-hidden disabled:pointer-events-none [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",children:[e.jsx(Zo,{}),e.jsx("span",{className:"sr-only",children:"Close"})]})]})]})}function m({className:o,...a}){return e.jsx("div",{"data-slot":"dialog-header",className:L("flex flex-col gap-2 text-center sm:text-left",o),...a})}function h({className:o,...a}){return e.jsx("div",{"data-slot":"dialog-footer",className:L("flex flex-col-reverse gap-2 sm:flex-row sm:justify-end",o),...a})}function D({className:o,...a}){return e.jsx(pa,{"data-slot":"dialog-title",className:L("text-lg leading-none font-semibold",o),...a})}function x({className:o,...a}){return e.jsx(ma,{"data-slot":"dialog-description",className:L("text-muted-foreground text-sm",o),...a})}c.__docgenInfo={description:"",methods:[],displayName:"Dialog"};p.__docgenInfo={description:"",methods:[],displayName:"DialogContent"};x.__docgenInfo={description:"",methods:[],displayName:"DialogDescription"};h.__docgenInfo={description:"",methods:[],displayName:"DialogFooter"};m.__docgenInfo={description:"",methods:[],displayName:"DialogHeader"};X.__docgenInfo={description:"",methods:[],displayName:"DialogOverlay"};J.__docgenInfo={description:"",methods:[],displayName:"DialogPortal"};D.__docgenInfo={description:"",methods:[],displayName:"DialogTitle"};u.__docgenInfo={description:"",methods:[],displayName:"DialogTrigger"};c.__docgenInfo={description:"",methods:[],displayName:"Dialog"};p.__docgenInfo={description:"",methods:[],displayName:"DialogContent"};x.__docgenInfo={description:"",methods:[],displayName:"DialogDescription"};h.__docgenInfo={description:"",methods:[],displayName:"DialogFooter"};m.__docgenInfo={description:"",methods:[],displayName:"DialogHeader"};X.__docgenInfo={description:"",methods:[],displayName:"DialogOverlay"};J.__docgenInfo={description:"",methods:[],displayName:"DialogPortal"};D.__docgenInfo={description:"",methods:[],displayName:"DialogTitle"};u.__docgenInfo={description:"",methods:[],displayName:"DialogTrigger"};const Ra={title:"UI/Dialog",component:c,parameters:{layout:"centered",docs:{description:{component:`
The Dialog component creates a modal overlay that captures user focus and requires interaction before returning to the main content. It's perfect for forms, confirmations, and important messages.

### Sub-components
- **Dialog**: Main container component
- **DialogTrigger**: Button or element that opens the dialog
- **DialogContent**: Content container with backdrop
- **DialogHeader**: Header section for title and description
- **DialogTitle**: Dialog title (required for accessibility)
- **DialogDescription**: Optional description text
- **DialogFooter**: Footer section for actions

### Usage Guidelines
- Use for important actions that require user attention
- Always include a DialogTitle for accessibility
- Provide clear action buttons
- Use for forms, confirmations, or detailed information
- Keep content focused and concise
- Provide a way to close (X button or Cancel action)

### Accessibility
- Focus trap keeps keyboard navigation within dialog
- Escape key closes the dialog
- Proper ARIA attributes (role="dialog", aria-labelledby)
- Focus returns to trigger element on close
- Screen reader announcements
- Backdrop click to close
        `}}},tags:["autodocs"]},y={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{children:"Open Dialog"})}),e.jsxs(p,{children:[e.jsxs(m,{children:[e.jsx(D,{children:"Dialog Title"}),e.jsx(x,{children:"This is a dialog description. You can put any content here."})]}),e.jsx("div",{className:"py-4",children:e.jsx("p",{children:"Dialog content goes here."})}),e.jsx(h,{children:e.jsx(s,{children:"Close"})})]})]})},j={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{children:"Edit Profile"})}),e.jsxs(p,{className:"sm:max-w-[425px]",children:[e.jsxs(m,{children:[e.jsx(D,{children:"Edit profile"}),e.jsx(x,{children:"Make changes to your profile here. Click save when you're done."})]}),e.jsxs("div",{className:"grid gap-4 py-4",children:[e.jsxs("div",{className:"grid grid-cols-4 items-center gap-4",children:[e.jsx(E,{htmlFor:"name",className:"text-right",children:"Name"}),e.jsx(O,{id:"name",defaultValue:"Pedro Duarte",className:"col-span-3"})]}),e.jsxs("div",{className:"grid grid-cols-4 items-center gap-4",children:[e.jsx(E,{htmlFor:"username",className:"text-right",children:"Username"}),e.jsx(O,{id:"username",defaultValue:"@peduarte",className:"col-span-3"})]})]}),e.jsx(h,{children:e.jsx(s,{type:"submit",children:"Save changes"})})]})]})},C={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{variant:"destructive",children:"Delete Account"})}),e.jsxs(p,{children:[e.jsxs(m,{children:[e.jsx(D,{children:"Are you absolutely sure?"}),e.jsx(x,{children:"This action cannot be undone. This will permanently delete your account and remove your data from our servers."})]}),e.jsxs(h,{children:[e.jsx(s,{variant:"outline",children:"Cancel"}),e.jsx(s,{variant:"destructive",children:"Delete"})]})]})]})},T={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{children:"Open"})}),e.jsxs(p,{children:[e.jsx(m,{children:e.jsx(D,{children:"Simple Dialog"})}),e.jsx("div",{className:"py-4",children:e.jsx("p",{children:"This dialog has no description."})}),e.jsx(h,{children:e.jsx(s,{children:"OK"})})]})]})},N={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{children:"View Terms"})}),e.jsxs(p,{className:"max-h-[80vh] overflow-y-auto",children:[e.jsxs(m,{children:[e.jsx(D,{children:"Terms and Conditions"}),e.jsx(x,{children:"Please read our terms and conditions carefully."})]}),e.jsxs("div",{className:"py-4 space-y-4",children:[e.jsx("p",{children:"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."}),e.jsx("p",{children:"Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."}),e.jsx("p",{children:"Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."}),e.jsx("p",{children:"Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."}),e.jsx("p",{children:"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."}),e.jsx("p",{children:"Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."})]}),e.jsx(h,{children:e.jsx(s,{children:"Accept"})})]})]})},w={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{children:"Save Changes"})}),e.jsxs(p,{children:[e.jsxs(m,{children:[e.jsx(D,{children:"Unsaved Changes"}),e.jsx(x,{children:"You have unsaved changes. What would you like to do?"})]}),e.jsxs(h,{className:"sm:justify-between",children:[e.jsx(s,{variant:"outline",children:"Cancel"}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx(s,{variant:"secondary",children:"Don't Save"}),e.jsx(s,{children:"Save"})]})]})]})]}),parameters:{docs:{description:{story:"Dialog with multiple action buttons."}}}},B={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{children:"Open"})}),e.jsxs(p,{children:[e.jsx(m,{children:e.jsx(D,{children:"A"})}),e.jsx("div",{className:"py-4",children:e.jsx("p",{children:"B"})})]})]}),parameters:{docs:{description:{story:"Dialog with minimal single-character content."}}}},b={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{children:"Open"})}),e.jsxs(p,{children:[e.jsxs(m,{children:[e.jsx(D,{children:"This is a very long dialog title that might wrap to multiple lines depending on the dialog width and screen size"}),e.jsx(x,{children:"Testing title wrapping behavior in dialogs."})]}),e.jsx("div",{className:"py-4",children:e.jsx("p",{children:"Dialog content."})}),e.jsx(h,{children:e.jsx(s,{children:"OK"})})]})]}),parameters:{docs:{description:{story:"Dialog with very long title to test text wrapping."}}}},F={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{children:"View Status"})}),e.jsxs(p,{children:[e.jsxs(m,{children:[e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(D,{children:"Project Status"}),e.jsx(W,{children:"Active"})]}),e.jsx(x,{children:"Current status and metrics for your project."})]}),e.jsxs("div",{className:"py-4 space-y-3",children:[e.jsxs("div",{className:"flex justify-between items-center",children:[e.jsx("span",{children:"Build Status:"}),e.jsx(W,{children:"Success"})]}),e.jsxs("div",{className:"flex justify-between items-center",children:[e.jsx("span",{children:"Tests:"}),e.jsx(W,{variant:"secondary",children:"Passing"})]}),e.jsxs("div",{className:"flex justify-between items-center",children:[e.jsx("span",{children:"Deployment:"}),e.jsx(W,{variant:"destructive",children:"Failed"})]})]}),e.jsx(h,{children:e.jsx(s,{children:"Close"})})]})]}),parameters:{docs:{description:{story:"Dialog with Badge components for status display."}}}},_={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{children:"Open Wide Dialog"})}),e.jsxs(p,{className:"sm:max-w-[800px]",children:[e.jsxs(m,{children:[e.jsx(D,{children:"Wide Dialog"}),e.jsx(x,{children:"This dialog has a wider maximum width for displaying more content."})]}),e.jsx("div",{className:"py-4",children:e.jsx("p",{children:"Content can span across a wider area, useful for tables or detailed forms."})}),e.jsx(h,{children:e.jsx(s,{children:"Close"})})]})]}),parameters:{docs:{description:{story:"Dialog with wider maximum width for complex content."}}}},S={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{children:"Process Data"})}),e.jsxs(p,{children:[e.jsxs(m,{children:[e.jsx(D,{children:"Processing..."}),e.jsx(x,{children:"Please wait while we process your request."})]}),e.jsx("div",{className:"py-8 flex justify-center",children:e.jsx("div",{className:"animate-spin rounded-full h-12 w-12 border-b-2 border-primary"})}),e.jsx(h,{children:e.jsx(s,{disabled:!0,children:"Cancel"})})]})]}),parameters:{docs:{description:{story:"Dialog showing loading state with spinner."}}}},A={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{children:"Create Account"})}),e.jsxs(p,{className:"sm:max-w-[500px]",children:[e.jsxs(m,{children:[e.jsx(D,{children:"Create New Account"}),e.jsx(x,{children:"Fill in the form below to create a new account."})]}),e.jsxs("div",{className:"grid gap-4 py-4",children:[e.jsxs("div",{className:"grid gap-2",children:[e.jsx(E,{htmlFor:"fullname",children:"Full Name"}),e.jsx(O,{id:"fullname",placeholder:"John Doe"})]}),e.jsxs("div",{className:"grid gap-2",children:[e.jsx(E,{htmlFor:"email-create",children:"Email"}),e.jsx(O,{id:"email-create",type:"email",placeholder:"john@example.com"})]}),e.jsxs("div",{className:"grid gap-2",children:[e.jsx(E,{htmlFor:"password-create",children:"Password"}),e.jsx(O,{id:"password-create",type:"password",placeholder:"••••••••"})]}),e.jsxs("div",{className:"grid gap-2",children:[e.jsx(E,{htmlFor:"confirm-password",children:"Confirm Password"}),e.jsx(O,{id:"confirm-password",type:"password",placeholder:"••••••••"})]})]}),e.jsxs(h,{children:[e.jsx(s,{variant:"outline",children:"Cancel"}),e.jsx(s,{type:"submit",children:"Create Account"})]})]})]}),parameters:{docs:{description:{story:"Dialog with complex multi-field form."}}}},P={render:()=>e.jsxs(c,{children:[e.jsx(u,{asChild:!0,children:e.jsx(s,{variant:"destructive",children:"Delete All"})}),e.jsxs(p,{children:[e.jsxs(m,{children:[e.jsx(D,{className:"text-destructive",children:"⚠️ Warning"}),e.jsx(x,{children:"This action will permanently delete all your data. This cannot be undone."})]}),e.jsxs("div",{className:"py-4 bg-destructive/10 rounded-md p-4",children:[e.jsx("p",{className:"text-sm font-medium",children:"Items to be deleted:"}),e.jsxs("ul",{className:"text-sm mt-2 space-y-1",children:[e.jsx("li",{children:"• All projects (15)"}),e.jsx("li",{children:"• All files (234)"}),e.jsx("li",{children:"• All settings"})]})]}),e.jsxs(h,{children:[e.jsx(s,{variant:"outline",children:"Cancel"}),e.jsx(s,{variant:"destructive",children:"Yes, Delete Everything"})]})]})]}),parameters:{docs:{description:{story:"Alert-style dialog for dangerous actions with warning styling."}}}};var Z,Q,ee;y.parameters={...y.parameters,docs:{...(Z=y.parameters)==null?void 0:Z.docs,source:{originalSource:`{
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
}`,...(ee=(Q=y.parameters)==null?void 0:Q.docs)==null?void 0:ee.source}}};var oe,ae,ie;j.parameters={...j.parameters,docs:{...(oe=j.parameters)==null?void 0:oe.docs,source:{originalSource:`{
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
}`,...(ie=(ae=j.parameters)==null?void 0:ae.docs)==null?void 0:ie.source}}};var te,re,ne;C.parameters={...C.parameters,docs:{...(te=C.parameters)==null?void 0:te.docs,source:{originalSource:`{
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
}`,...(ne=(re=C.parameters)==null?void 0:re.docs)==null?void 0:ne.source}}};var se,le,de;T.parameters={...T.parameters,docs:{...(se=T.parameters)==null?void 0:se.docs,source:{originalSource:`{
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
}`,...(de=(le=T.parameters)==null?void 0:le.docs)==null?void 0:de.source}}};var ce,ge,ue;N.parameters={...N.parameters,docs:{...(ce=N.parameters)==null?void 0:ce.docs,source:{originalSource:`{
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
}`,...(ue=(ge=N.parameters)==null?void 0:ge.docs)==null?void 0:ue.source}}};var pe,me,De;w.parameters={...w.parameters,docs:{...(pe=w.parameters)==null?void 0:pe.docs,source:{originalSource:`{
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
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with multiple action buttons.'
      }
    }
  }
}`,...(De=(me=w.parameters)==null?void 0:me.docs)==null?void 0:De.source}}};var he,xe,fe;B.parameters={...B.parameters,docs:{...(he=B.parameters)==null?void 0:he.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Open</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>A</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <p>B</p>
        </div>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with minimal single-character content.'
      }
    }
  }
}`,...(fe=(xe=B.parameters)==null?void 0:xe.docs)==null?void 0:fe.source}}};var ve,ye,je;b.parameters={...b.parameters,docs:{...(ve=b.parameters)==null?void 0:ve.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Open</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            This is a very long dialog title that might wrap to multiple lines depending on the dialog width and screen size
          </DialogTitle>
          <DialogDescription>
            Testing title wrapping behavior in dialogs.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p>Dialog content.</p>
        </div>
        <DialogFooter>
          <Button>OK</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with very long title to test text wrapping.'
      }
    }
  }
}`,...(je=(ye=b.parameters)==null?void 0:ye.docs)==null?void 0:je.source}}};var Ce,Te,Ne;F.parameters={...F.parameters,docs:{...(Ce=F.parameters)==null?void 0:Ce.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>View Status</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center gap-2">
            <DialogTitle>Project Status</DialogTitle>
            <Badge>Active</Badge>
          </div>
          <DialogDescription>
            Current status and metrics for your project.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 space-y-3">
          <div className="flex justify-between items-center">
            <span>Build Status:</span>
            <Badge>Success</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span>Tests:</span>
            <Badge variant="secondary">Passing</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span>Deployment:</span>
            <Badge variant="destructive">Failed</Badge>
          </div>
        </div>
        <DialogFooter>
          <Button>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with Badge components for status display.'
      }
    }
  }
}`,...(Ne=(Te=F.parameters)==null?void 0:Te.docs)==null?void 0:Ne.source}}};var we,Be,be;_.parameters={..._.parameters,docs:{...(we=_.parameters)==null?void 0:we.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Open Wide Dialog</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[800px]">
        <DialogHeader>
          <DialogTitle>Wide Dialog</DialogTitle>
          <DialogDescription>
            This dialog has a wider maximum width for displaying more content.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p>Content can span across a wider area, useful for tables or detailed forms.</p>
        </div>
        <DialogFooter>
          <Button>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with wider maximum width for complex content.'
      }
    }
  }
}`,...(be=(Be=_.parameters)==null?void 0:Be.docs)==null?void 0:be.source}}};var Fe,_e,Se;S.parameters={...S.parameters,docs:{...(Fe=S.parameters)==null?void 0:Fe.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Process Data</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Processing...</DialogTitle>
          <DialogDescription>
            Please wait while we process your request.
          </DialogDescription>
        </DialogHeader>
        <div className="py-8 flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
        <DialogFooter>
          <Button disabled>Cancel</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog showing loading state with spinner.'
      }
    }
  }
}`,...(Se=(_e=S.parameters)==null?void 0:_e.docs)==null?void 0:Se.source}}};var Ae,Pe,Ie;A.parameters={...A.parameters,docs:{...(Ae=A.parameters)==null?void 0:Ae.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Create Account</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Account</DialogTitle>
          <DialogDescription>
            Fill in the form below to create a new account.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="fullname">Full Name</Label>
            <Input id="fullname" placeholder="John Doe" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email-create">Email</Label>
            <Input id="email-create" type="email" placeholder="john@example.com" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="password-create">Password</Label>
            <Input id="password-create" type="password" placeholder="••••••••" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="confirm-password">Confirm Password</Label>
            <Input id="confirm-password" type="password" placeholder="••••••••" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button type="submit">Create Account</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with complex multi-field form.'
      }
    }
  }
}`,...(Ie=(Pe=A.parameters)==null?void 0:Pe.docs)==null?void 0:Ie.source}}};var He,Oe,Ee;P.parameters={...P.parameters,docs:{...(He=P.parameters)==null?void 0:He.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive">Delete All</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="text-destructive">⚠️ Warning</DialogTitle>
          <DialogDescription>
            This action will permanently delete all your data. This cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 bg-destructive/10 rounded-md p-4">
          <p className="text-sm font-medium">Items to be deleted:</p>
          <ul className="text-sm mt-2 space-y-1">
            <li>• All projects (15)</li>
            <li>• All files (234)</li>
            <li>• All settings</li>
          </ul>
        </div>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive">Yes, Delete Everything</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Alert-style dialog for dangerous actions with warning styling.'
      }
    }
  }
}`,...(Ee=(Oe=P.parameters)==null?void 0:Oe.docs)==null?void 0:Ee.source}}};var Le,Re,qe;y.parameters={...y.parameters,docs:{...(Le=y.parameters)==null?void 0:Le.docs,source:{originalSource:`{
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
}`,...(qe=(Re=y.parameters)==null?void 0:Re.docs)==null?void 0:qe.source}}};var We,Me,ke;j.parameters={...j.parameters,docs:{...(We=j.parameters)==null?void 0:We.docs,source:{originalSource:`{
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
}`,...(ke=(Me=j.parameters)==null?void 0:Me.docs)==null?void 0:ke.source}}};var Ue,Ve,$e;C.parameters={...C.parameters,docs:{...(Ue=C.parameters)==null?void 0:Ue.docs,source:{originalSource:`{
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
}`,...($e=(Ve=C.parameters)==null?void 0:Ve.docs)==null?void 0:$e.source}}};var Ye,ze,Ge;T.parameters={...T.parameters,docs:{...(Ye=T.parameters)==null?void 0:Ye.docs,source:{originalSource:`{
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
}`,...(Ge=(ze=T.parameters)==null?void 0:ze.docs)==null?void 0:Ge.source}}};var Ke,Je,Xe;N.parameters={...N.parameters,docs:{...(Ke=N.parameters)==null?void 0:Ke.docs,source:{originalSource:`{
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
}`,...(Xe=(Je=N.parameters)==null?void 0:Je.docs)==null?void 0:Xe.source}}};var Ze,Qe,eo;w.parameters={...w.parameters,docs:{...(Ze=w.parameters)==null?void 0:Ze.docs,source:{originalSource:`{
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
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with multiple action buttons.'
      }
    }
  }
}`,...(eo=(Qe=w.parameters)==null?void 0:Qe.docs)==null?void 0:eo.source}}};var oo,ao,io;B.parameters={...B.parameters,docs:{...(oo=B.parameters)==null?void 0:oo.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Open</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>A</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <p>B</p>
        </div>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with minimal single-character content.'
      }
    }
  }
}`,...(io=(ao=B.parameters)==null?void 0:ao.docs)==null?void 0:io.source}}};var to,ro,no;b.parameters={...b.parameters,docs:{...(to=b.parameters)==null?void 0:to.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Open</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            This is a very long dialog title that might wrap to multiple lines depending on the dialog width and screen size
          </DialogTitle>
          <DialogDescription>
            Testing title wrapping behavior in dialogs.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p>Dialog content.</p>
        </div>
        <DialogFooter>
          <Button>OK</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with very long title to test text wrapping.'
      }
    }
  }
}`,...(no=(ro=b.parameters)==null?void 0:ro.docs)==null?void 0:no.source}}};var so,lo,co;F.parameters={...F.parameters,docs:{...(so=F.parameters)==null?void 0:so.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>View Status</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center gap-2">
            <DialogTitle>Project Status</DialogTitle>
            <Badge>Active</Badge>
          </div>
          <DialogDescription>
            Current status and metrics for your project.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 space-y-3">
          <div className="flex justify-between items-center">
            <span>Build Status:</span>
            <Badge>Success</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span>Tests:</span>
            <Badge variant="secondary">Passing</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span>Deployment:</span>
            <Badge variant="destructive">Failed</Badge>
          </div>
        </div>
        <DialogFooter>
          <Button>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with Badge components for status display.'
      }
    }
  }
}`,...(co=(lo=F.parameters)==null?void 0:lo.docs)==null?void 0:co.source}}};var go,uo,po;_.parameters={..._.parameters,docs:{...(go=_.parameters)==null?void 0:go.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Open Wide Dialog</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[800px]">
        <DialogHeader>
          <DialogTitle>Wide Dialog</DialogTitle>
          <DialogDescription>
            This dialog has a wider maximum width for displaying more content.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p>Content can span across a wider area, useful for tables or detailed forms.</p>
        </div>
        <DialogFooter>
          <Button>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with wider maximum width for complex content.'
      }
    }
  }
}`,...(po=(uo=_.parameters)==null?void 0:uo.docs)==null?void 0:po.source}}};var mo,Do,ho;S.parameters={...S.parameters,docs:{...(mo=S.parameters)==null?void 0:mo.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Process Data</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Processing...</DialogTitle>
          <DialogDescription>
            Please wait while we process your request.
          </DialogDescription>
        </DialogHeader>
        <div className="py-8 flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
        <DialogFooter>
          <Button disabled>Cancel</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog showing loading state with spinner.'
      }
    }
  }
}`,...(ho=(Do=S.parameters)==null?void 0:Do.docs)==null?void 0:ho.source}}};var xo,fo,vo;A.parameters={...A.parameters,docs:{...(xo=A.parameters)==null?void 0:xo.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button>Create Account</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Account</DialogTitle>
          <DialogDescription>
            Fill in the form below to create a new account.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="fullname">Full Name</Label>
            <Input id="fullname" placeholder="John Doe" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email-create">Email</Label>
            <Input id="email-create" type="email" placeholder="john@example.com" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="password-create">Password</Label>
            <Input id="password-create" type="password" placeholder="••••••••" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="confirm-password">Confirm Password</Label>
            <Input id="confirm-password" type="password" placeholder="••••••••" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button type="submit">Create Account</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Dialog with complex multi-field form.'
      }
    }
  }
}`,...(vo=(fo=A.parameters)==null?void 0:fo.docs)==null?void 0:vo.source}}};var yo,jo,Co;P.parameters={...P.parameters,docs:{...(yo=P.parameters)==null?void 0:yo.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive">Delete All</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="text-destructive">⚠️ Warning</DialogTitle>
          <DialogDescription>
            This action will permanently delete all your data. This cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 bg-destructive/10 rounded-md p-4">
          <p className="text-sm font-medium">Items to be deleted:</p>
          <ul className="text-sm mt-2 space-y-1">
            <li>• All projects (15)</li>
            <li>• All files (234)</li>
            <li>• All settings</li>
          </ul>
        </div>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive">Yes, Delete Everything</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
  parameters: {
    docs: {
      description: {
        story: 'Alert-style dialog for dangerous actions with warning styling.'
      }
    }
  }
}`,...(Co=(jo=P.parameters)==null?void 0:jo.docs)==null?void 0:Co.source}}};const qa=["Default","WithForm","Confirmation","WithoutDescription","LongContent","MultipleButtons","MinimalContent","VeryLongTitle","WithBadges","WideDialog","LoadingState","NestedForm","AlertDialog"];export{P as AlertDialog,C as Confirmation,y as Default,S as LoadingState,N as LongContent,B as MinimalContent,w as MultipleButtons,A as NestedForm,b as VeryLongTitle,_ as WideDialog,F as WithBadges,j as WithForm,T as WithoutDescription,qa as __namedExportsOrder,Ra as default};
