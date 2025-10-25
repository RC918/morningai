import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as f,R as u}from"./storybook-vendor-CPzy2iGn.js";import{c as ye,u as qe}from"./index-CfloHgh8.js";import{c as Le,u as ze}from"./index-kwXZyLdX.js";import{u as Ie}from"./index-CXs_xfTS.js";import{u as H,c as we}from"./index-Gg2jh08l.js";import{P}from"./index-DRUeUdNs.js";import{P as Ke}from"./index-DY-33XIg.js";import{u as je}from"./index-CNEstPV4.js";import{c as q}from"./utils-D-KgF5mV.js";import{C as Ye}from"./chevron-down-Bao7sDMC.js";import"./react-vendor-Bzgz95E1.js";import"./index-CAPShSkS.js";import"./createLucideIcon-DgPn5ReF.js";var E="Collapsible",[Je,Ne]=ye(E),[Qe,L]=Je(E),Te=f.forwardRef((o,t)=>{const{__scopeCollapsible:i,open:n,defaultOpen:c,disabled:r,onOpenChange:s,...l}=o,[d,m]=H({prop:n,defaultProp:c??!1,onChange:s,caller:E});return e.jsx(Qe,{scope:i,disabled:r,contentId:je(),open:d,onOpenToggle:f.useCallback(()=>m(h=>!h),[m]),children:e.jsx(P.div,{"data-state":K(d),"data-disabled":r?"":void 0,...l,ref:t})})});Te.displayName=E;var Re="CollapsibleTrigger",Se=f.forwardRef((o,t)=>{const{__scopeCollapsible:i,...n}=o,c=L(Re,i);return e.jsx(P.button,{type:"button","aria-controls":c.contentId,"aria-expanded":c.open||!1,"data-state":K(c.open),"data-disabled":c.disabled?"":void 0,disabled:c.disabled,...n,ref:t,onClick:we(o.onClick,c.onOpenToggle)})});Se.displayName=Re;var z="CollapsibleContent",_e=f.forwardRef((o,t)=>{const{forceMount:i,...n}=o,c=L(z,o.__scopeCollapsible);return e.jsx(Ke,{present:i||c.open,children:({present:r})=>e.jsx(Ue,{...n,ref:t,present:r})})});_e.displayName=z;var Ue=f.forwardRef((o,t)=>{const{__scopeCollapsible:i,present:n,children:c,...r}=o,s=L(z,i),[l,d]=f.useState(n),m=f.useRef(null),h=Ie(t,m),x=f.useRef(0),S=x.current,w=f.useRef(0),k=w.current,j=s.open||l,N=f.useRef(j),T=f.useRef(void 0);return f.useEffect(()=>{const a=requestAnimationFrame(()=>N.current=!1);return()=>cancelAnimationFrame(a)},[]),qe(()=>{const a=m.current;if(a){T.current=T.current||{transitionDuration:a.style.transitionDuration,animationName:a.style.animationName},a.style.transitionDuration="0s",a.style.animationName="none";const _=a.getBoundingClientRect();x.current=_.height,w.current=_.width,N.current||(a.style.transitionDuration=T.current.transitionDuration,a.style.animationName=T.current.animationName),d(n)}},[s.open,n]),e.jsx(P.div,{"data-state":K(s.open),"data-disabled":s.disabled?"":void 0,id:s.contentId,hidden:!j,...r,ref:h,style:{"--radix-collapsible-content-height":S?`${S}px`:void 0,"--radix-collapsible-content-width":k?`${k}px`:void 0,...o.style},children:j&&c})});function K(o){return o?"open":"closed"}var Be=Te,Xe=Se,Ze=_e,v="Accordion",eo=["Home","End","ArrowDown","ArrowUp","ArrowLeft","ArrowRight"],[Y,oo,io]=Le(v),[O]=ye(v,[io,Ne]),J=Ne(),Pe=u.forwardRef((o,t)=>{const{type:i,...n}=o,c=n,r=n;return e.jsx(Y.Provider,{scope:o.__scopeAccordion,children:i==="multiple"?e.jsx(co,{...r,ref:t}):e.jsx(no,{...c,ref:t})})});Pe.displayName=v;var[ke,ro]=O(v),[Me,to]=O(v,{collapsible:!1}),no=u.forwardRef((o,t)=>{const{value:i,defaultValue:n,onValueChange:c=()=>{},collapsible:r=!1,...s}=o,[l,d]=H({prop:i,defaultProp:n??"",onChange:c,caller:v});return e.jsx(ke,{scope:o.__scopeAccordion,value:u.useMemo(()=>l?[l]:[],[l]),onItemOpen:d,onItemClose:u.useCallback(()=>r&&d(""),[r,d]),children:e.jsx(Me,{scope:o.__scopeAccordion,collapsible:r,children:e.jsx(Ee,{...s,ref:t})})})}),co=u.forwardRef((o,t)=>{const{value:i,defaultValue:n,onValueChange:c=()=>{},...r}=o,[s,l]=H({prop:i,defaultProp:n??[],onChange:c,caller:v}),d=u.useCallback(h=>l((x=[])=>[...x,h]),[l]),m=u.useCallback(h=>l((x=[])=>x.filter(S=>S!==h)),[l]);return e.jsx(ke,{scope:o.__scopeAccordion,value:s,onItemOpen:d,onItemClose:m,children:e.jsx(Me,{scope:o.__scopeAccordion,collapsible:!0,children:e.jsx(Ee,{...r,ref:t})})})}),[so,D]=O(v),Ee=u.forwardRef((o,t)=>{const{__scopeAccordion:i,disabled:n,dir:c,orientation:r="vertical",...s}=o,l=u.useRef(null),d=Ie(l,t),m=oo(i),x=ze(c)==="ltr",S=we(o.onKeyDown,w=>{var U;if(!eo.includes(w.key))return;const k=w.target,j=m().filter(W=>{var B;return!((B=W.ref.current)!=null&&B.disabled)}),N=j.findIndex(W=>W.ref.current===k),T=j.length;if(N===-1)return;w.preventDefault();let a=N;const _=0,F=T-1,$=()=>{a=N+1,a>F&&(a=_)},V=()=>{a=N-1,a<_&&(a=F)};switch(w.key){case"Home":a=_;break;case"End":a=F;break;case"ArrowRight":r==="horizontal"&&(x?$():V());break;case"ArrowDown":r==="vertical"&&$();break;case"ArrowLeft":r==="horizontal"&&(x?V():$());break;case"ArrowUp":r==="vertical"&&V();break}const He=a%T;(U=j[He].ref.current)==null||U.focus()});return e.jsx(so,{scope:i,disabled:n,direction:c,orientation:r,children:e.jsx(Y.Slot,{scope:i,children:e.jsx(P.div,{...s,"data-orientation":r,ref:d,onKeyDown:n?void 0:S})})})}),M="AccordionItem",[ao,Q]=O(M),Oe=u.forwardRef((o,t)=>{const{__scopeAccordion:i,value:n,...c}=o,r=D(M,i),s=ro(M,i),l=J(i),d=je(),m=n&&s.value.includes(n)||!1,h=r.disabled||o.disabled;return e.jsx(ao,{scope:i,open:m,disabled:h,triggerId:d,children:e.jsx(Be,{"data-orientation":r.orientation,"data-state":Ge(m),...l,...c,ref:t,disabled:h,open:m,onOpenChange:x=>{x?s.onItemOpen(n):s.onItemClose(n)}})})});Oe.displayName=M;var De="AccordionHeader",Fe=u.forwardRef((o,t)=>{const{__scopeAccordion:i,...n}=o,c=D(v,i),r=Q(De,i);return e.jsx(P.h3,{"data-orientation":c.orientation,"data-state":Ge(r.open),"data-disabled":r.disabled?"":void 0,...n,ref:t})});Fe.displayName=De;var G="AccordionTrigger",$e=u.forwardRef((o,t)=>{const{__scopeAccordion:i,...n}=o,c=D(v,i),r=Q(G,i),s=to(G,i),l=J(i);return e.jsx(Y.ItemSlot,{scope:i,children:e.jsx(Xe,{"aria-disabled":r.open&&!s.collapsible||void 0,"data-orientation":c.orientation,id:r.triggerId,...l,...n,ref:t})})});$e.displayName=G;var Ve="AccordionContent",We=u.forwardRef((o,t)=>{const{__scopeAccordion:i,...n}=o,c=D(v,i),r=Q(Ve,i),s=J(i);return e.jsx(Ze,{role:"region","aria-labelledby":r.triggerId,"data-orientation":c.orientation,...s,...n,ref:t,style:{"--radix-accordion-content-height":"var(--radix-collapsible-content-height)","--radix-accordion-content-width":"var(--radix-collapsible-content-width)",...o.style}})});We.displayName=Ve;function Ge(o){return o?"open":"closed"}var lo=Pe,mo=Oe,uo=Fe,po=$e,go=We;function R({...o}){return e.jsx(lo,{"data-slot":"accordion",...o})}function p({className:o,...t}){return e.jsx(mo,{"data-slot":"accordion-item",className:q("border-b last:border-b-0",o),...t})}function g({className:o,children:t,...i}){return e.jsx(uo,{className:"flex",children:e.jsxs(po,{"data-slot":"accordion-trigger",className:q("focus-visible:border-ring focus-visible:ring-ring/50 flex flex-1 items-start justify-between gap-4 rounded-md py-4 text-left text-sm font-medium transition-all outline-none hover:underline focus-visible:ring-[3px] disabled:pointer-events-none disabled:opacity-50 [&[data-state=open]>svg]:rotate-180",o),...i,children:[t,e.jsx(Ye,{className:"text-muted-foreground pointer-events-none size-4 shrink-0 translate-y-0.5 transition-transform duration-200"})]})})}function A({className:o,children:t,...i}){return e.jsx(go,{"data-slot":"accordion-content",className:"data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down overflow-hidden text-sm",...i,children:e.jsx("div",{className:q("pt-0 pb-4",o),children:t})})}R.__docgenInfo={description:"",methods:[],displayName:"Accordion"};p.__docgenInfo={description:"",methods:[],displayName:"AccordionItem"};g.__docgenInfo={description:"",methods:[],displayName:"AccordionTrigger"};A.__docgenInfo={description:"",methods:[],displayName:"AccordionContent"};R.__docgenInfo={description:"",methods:[],displayName:"Accordion"};p.__docgenInfo={description:"",methods:[],displayName:"AccordionItem"};g.__docgenInfo={description:"",methods:[],displayName:"AccordionTrigger"};A.__docgenInfo={description:"",methods:[],displayName:"AccordionContent"};const So={title:"UI/Accordion",component:R,parameters:{layout:"padded"},tags:["autodocs"]},C={render:()=>e.jsxs(R,{type:"single",collapsible:!0,className:"w-full max-w-md",children:[e.jsxs(p,{value:"item-1",children:[e.jsx(g,{children:"What is Morning AI?"}),e.jsx(A,{children:"Morning AI is an intelligent automation platform that helps businesses streamline their workflows and make data-driven decisions."})]}),e.jsxs(p,{value:"item-2",children:[e.jsx(g,{children:"How does it work?"}),e.jsx(A,{children:"Our platform uses advanced AI algorithms to analyze your data, identify patterns, and provide actionable insights. It integrates seamlessly with your existing tools and workflows."})]}),e.jsxs(p,{value:"item-3",children:[e.jsx(g,{children:"Is it secure?"}),e.jsx(A,{children:"Yes, security is our top priority. We use industry-standard encryption, regular security audits, and comply with major data protection regulations including GDPR and SOC 2."})]})]}),parameters:{docs:{description:{story:"Single accordion - only one item can be open at a time."}}}},b={render:()=>e.jsxs(R,{type:"multiple",className:"w-full max-w-md",children:[e.jsxs(p,{value:"item-1",children:[e.jsx(g,{children:"Features"}),e.jsx(A,{children:e.jsxs("ul",{className:"list-disc pl-4 space-y-1",children:[e.jsx("li",{children:"Real-time analytics"}),e.jsx("li",{children:"Automated workflows"}),e.jsx("li",{children:"Custom integrations"}),e.jsx("li",{children:"24/7 support"})]})})]}),e.jsxs(p,{value:"item-2",children:[e.jsx(g,{children:"Pricing"}),e.jsxs(A,{children:[e.jsx("p",{children:"We offer flexible pricing plans to suit businesses of all sizes:"}),e.jsxs("ul",{className:"list-disc pl-4 mt-2 space-y-1",children:[e.jsx("li",{children:"Starter: $29/month"}),e.jsx("li",{children:"Professional: $99/month"}),e.jsx("li",{children:"Enterprise: Custom pricing"})]})]})]}),e.jsxs(p,{value:"item-3",children:[e.jsx(g,{children:"Support"}),e.jsx(A,{children:"Our support team is available 24/7 via email, chat, and phone. We also provide comprehensive documentation and video tutorials."})]})]}),parameters:{docs:{description:{story:"Multiple accordion - multiple items can be open simultaneously."}}}},y={render:()=>e.jsxs(R,{type:"single",collapsible:!0,defaultValue:"item-2",className:"w-full max-w-md",children:[e.jsxs(p,{value:"item-1",children:[e.jsx(g,{children:"Getting Started"}),e.jsx(A,{children:"Follow our quick start guide to set up your account and configure your first workflow."})]}),e.jsxs(p,{value:"item-2",children:[e.jsx(g,{children:"Quick Start Guide"}),e.jsx(A,{children:e.jsxs("ol",{className:"list-decimal pl-4 space-y-2",children:[e.jsx("li",{children:"Create your account"}),e.jsx("li",{children:"Connect your data sources"}),e.jsx("li",{children:"Configure your first workflow"}),e.jsx("li",{children:"Monitor results in real-time"})]})})]}),e.jsxs(p,{value:"item-3",children:[e.jsx(g,{children:"Advanced Features"}),e.jsx(A,{children:"Explore advanced features like custom integrations, API access, and enterprise-grade security options."})]})]}),parameters:{docs:{description:{story:"Accordion with a default open item using defaultValue prop."}}}},I={render:()=>e.jsxs(R,{type:"single",collapsible:!0,className:"w-full max-w-md",children:[e.jsxs(p,{value:"item-1",children:[e.jsx(g,{children:"System Requirements"}),e.jsx(A,{children:e.jsxs("div",{className:"space-y-3",children:[e.jsxs("div",{children:[e.jsx("h4",{className:"font-medium mb-1",children:"Minimum Requirements"}),e.jsxs("ul",{className:"list-disc pl-4 text-sm",children:[e.jsx("li",{children:"Modern web browser (Chrome, Firefox, Safari, Edge)"}),e.jsx("li",{children:"Internet connection (1 Mbps minimum)"}),e.jsx("li",{children:"JavaScript enabled"})]})]}),e.jsxs("div",{children:[e.jsx("h4",{className:"font-medium mb-1",children:"Recommended"}),e.jsxs("ul",{className:"list-disc pl-4 text-sm",children:[e.jsx("li",{children:"Latest browser version"}),e.jsx("li",{children:"High-speed internet (10+ Mbps)"}),e.jsx("li",{children:"Desktop or tablet device"})]})]})]})})]}),e.jsxs(p,{value:"item-2",children:[e.jsx(g,{children:"API Documentation"}),e.jsxs(A,{children:[e.jsx("p",{className:"mb-2",children:"Access our comprehensive API documentation:"}),e.jsx("div",{className:"bg-muted p-3 rounded-md text-sm font-mono",children:"https://api.morningai.com/docs"}),e.jsx("p",{className:"mt-2 text-sm",children:"Includes authentication guides, endpoint references, and code examples in multiple languages."})]})]})]}),parameters:{docs:{description:{story:"Accordion with rich content including headings, lists, and code blocks."}}}};var X,Z,ee;C.parameters={...C.parameters,docs:{...(X=C.parameters)==null?void 0:X.docs,source:{originalSource:`{
  render: () => <Accordion type="single" collapsible className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>What is Morning AI?</AccordionTrigger>
        <AccordionContent>
          Morning AI is an intelligent automation platform that helps businesses streamline their workflows and make data-driven decisions.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>How does it work?</AccordionTrigger>
        <AccordionContent>
          Our platform uses advanced AI algorithms to analyze your data, identify patterns, and provide actionable insights. It integrates seamlessly with your existing tools and workflows.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Is it secure?</AccordionTrigger>
        <AccordionContent>
          Yes, security is our top priority. We use industry-standard encryption, regular security audits, and comply with major data protection regulations including GDPR and SOC 2.
        </AccordionContent>
      </AccordionItem>
    </Accordion>,
  parameters: {
    docs: {
      description: {
        story: 'Single accordion - only one item can be open at a time.'
      }
    }
  }
}`,...(ee=(Z=C.parameters)==null?void 0:Z.docs)==null?void 0:ee.source}}};var oe,ie,re;b.parameters={...b.parameters,docs:{...(oe=b.parameters)==null?void 0:oe.docs,source:{originalSource:`{
  render: () => <Accordion type="multiple" className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>Features</AccordionTrigger>
        <AccordionContent>
          <ul className="list-disc pl-4 space-y-1">
            <li>Real-time analytics</li>
            <li>Automated workflows</li>
            <li>Custom integrations</li>
            <li>24/7 support</li>
          </ul>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>Pricing</AccordionTrigger>
        <AccordionContent>
          <p>We offer flexible pricing plans to suit businesses of all sizes:</p>
          <ul className="list-disc pl-4 mt-2 space-y-1">
            <li>Starter: $29/month</li>
            <li>Professional: $99/month</li>
            <li>Enterprise: Custom pricing</li>
          </ul>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Support</AccordionTrigger>
        <AccordionContent>
          Our support team is available 24/7 via email, chat, and phone. We also provide comprehensive documentation and video tutorials.
        </AccordionContent>
      </AccordionItem>
    </Accordion>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple accordion - multiple items can be open simultaneously.'
      }
    }
  }
}`,...(re=(ie=b.parameters)==null?void 0:ie.docs)==null?void 0:re.source}}};var te,ne,ce;y.parameters={...y.parameters,docs:{...(te=y.parameters)==null?void 0:te.docs,source:{originalSource:`{
  render: () => <Accordion type="single" collapsible defaultValue="item-2" className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>Getting Started</AccordionTrigger>
        <AccordionContent>
          Follow our quick start guide to set up your account and configure your first workflow.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>Quick Start Guide</AccordionTrigger>
        <AccordionContent>
          <ol className="list-decimal pl-4 space-y-2">
            <li>Create your account</li>
            <li>Connect your data sources</li>
            <li>Configure your first workflow</li>
            <li>Monitor results in real-time</li>
          </ol>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Advanced Features</AccordionTrigger>
        <AccordionContent>
          Explore advanced features like custom integrations, API access, and enterprise-grade security options.
        </AccordionContent>
      </AccordionItem>
    </Accordion>,
  parameters: {
    docs: {
      description: {
        story: 'Accordion with a default open item using defaultValue prop.'
      }
    }
  }
}`,...(ce=(ne=y.parameters)==null?void 0:ne.docs)==null?void 0:ce.source}}};var se,ae,le;I.parameters={...I.parameters,docs:{...(se=I.parameters)==null?void 0:se.docs,source:{originalSource:`{
  render: () => <Accordion type="single" collapsible className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>System Requirements</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">Minimum Requirements</h4>
              <ul className="list-disc pl-4 text-sm">
                <li>Modern web browser (Chrome, Firefox, Safari, Edge)</li>
                <li>Internet connection (1 Mbps minimum)</li>
                <li>JavaScript enabled</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Recommended</h4>
              <ul className="list-disc pl-4 text-sm">
                <li>Latest browser version</li>
                <li>High-speed internet (10+ Mbps)</li>
                <li>Desktop or tablet device</li>
              </ul>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>API Documentation</AccordionTrigger>
        <AccordionContent>
          <p className="mb-2">Access our comprehensive API documentation:</p>
          <div className="bg-muted p-3 rounded-md text-sm font-mono">
            https://api.morningai.com/docs
          </div>
          <p className="mt-2 text-sm">
            Includes authentication guides, endpoint references, and code examples in multiple languages.
          </p>
        </AccordionContent>
      </AccordionItem>
    </Accordion>,
  parameters: {
    docs: {
      description: {
        story: 'Accordion with rich content including headings, lists, and code blocks.'
      }
    }
  }
}`,...(le=(ae=I.parameters)==null?void 0:ae.docs)==null?void 0:le.source}}};var de,me,ue;C.parameters={...C.parameters,docs:{...(de=C.parameters)==null?void 0:de.docs,source:{originalSource:`{
  render: () => <Accordion type="single" collapsible className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>What is Morning AI?</AccordionTrigger>
        <AccordionContent>
          Morning AI is an intelligent automation platform that helps businesses streamline their workflows and make data-driven decisions.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>How does it work?</AccordionTrigger>
        <AccordionContent>
          Our platform uses advanced AI algorithms to analyze your data, identify patterns, and provide actionable insights. It integrates seamlessly with your existing tools and workflows.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Is it secure?</AccordionTrigger>
        <AccordionContent>
          Yes, security is our top priority. We use industry-standard encryption, regular security audits, and comply with major data protection regulations including GDPR and SOC 2.
        </AccordionContent>
      </AccordionItem>
    </Accordion>,
  parameters: {
    docs: {
      description: {
        story: 'Single accordion - only one item can be open at a time.'
      }
    }
  }
}`,...(ue=(me=C.parameters)==null?void 0:me.docs)==null?void 0:ue.source}}};var pe,ge,Ae;b.parameters={...b.parameters,docs:{...(pe=b.parameters)==null?void 0:pe.docs,source:{originalSource:`{
  render: () => <Accordion type="multiple" className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>Features</AccordionTrigger>
        <AccordionContent>
          <ul className="list-disc pl-4 space-y-1">
            <li>Real-time analytics</li>
            <li>Automated workflows</li>
            <li>Custom integrations</li>
            <li>24/7 support</li>
          </ul>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>Pricing</AccordionTrigger>
        <AccordionContent>
          <p>We offer flexible pricing plans to suit businesses of all sizes:</p>
          <ul className="list-disc pl-4 mt-2 space-y-1">
            <li>Starter: $29/month</li>
            <li>Professional: $99/month</li>
            <li>Enterprise: Custom pricing</li>
          </ul>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Support</AccordionTrigger>
        <AccordionContent>
          Our support team is available 24/7 via email, chat, and phone. We also provide comprehensive documentation and video tutorials.
        </AccordionContent>
      </AccordionItem>
    </Accordion>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple accordion - multiple items can be open simultaneously.'
      }
    }
  }
}`,...(Ae=(ge=b.parameters)==null?void 0:ge.docs)==null?void 0:Ae.source}}};var fe,he,xe;y.parameters={...y.parameters,docs:{...(fe=y.parameters)==null?void 0:fe.docs,source:{originalSource:`{
  render: () => <Accordion type="single" collapsible defaultValue="item-2" className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>Getting Started</AccordionTrigger>
        <AccordionContent>
          Follow our quick start guide to set up your account and configure your first workflow.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>Quick Start Guide</AccordionTrigger>
        <AccordionContent>
          <ol className="list-decimal pl-4 space-y-2">
            <li>Create your account</li>
            <li>Connect your data sources</li>
            <li>Configure your first workflow</li>
            <li>Monitor results in real-time</li>
          </ol>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Advanced Features</AccordionTrigger>
        <AccordionContent>
          Explore advanced features like custom integrations, API access, and enterprise-grade security options.
        </AccordionContent>
      </AccordionItem>
    </Accordion>,
  parameters: {
    docs: {
      description: {
        story: 'Accordion with a default open item using defaultValue prop.'
      }
    }
  }
}`,...(xe=(he=y.parameters)==null?void 0:he.docs)==null?void 0:xe.source}}};var ve,Ce,be;I.parameters={...I.parameters,docs:{...(ve=I.parameters)==null?void 0:ve.docs,source:{originalSource:`{
  render: () => <Accordion type="single" collapsible className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>System Requirements</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">Minimum Requirements</h4>
              <ul className="list-disc pl-4 text-sm">
                <li>Modern web browser (Chrome, Firefox, Safari, Edge)</li>
                <li>Internet connection (1 Mbps minimum)</li>
                <li>JavaScript enabled</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Recommended</h4>
              <ul className="list-disc pl-4 text-sm">
                <li>Latest browser version</li>
                <li>High-speed internet (10+ Mbps)</li>
                <li>Desktop or tablet device</li>
              </ul>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>API Documentation</AccordionTrigger>
        <AccordionContent>
          <p className="mb-2">Access our comprehensive API documentation:</p>
          <div className="bg-muted p-3 rounded-md text-sm font-mono">
            https://api.morningai.com/docs
          </div>
          <p className="mt-2 text-sm">
            Includes authentication guides, endpoint references, and code examples in multiple languages.
          </p>
        </AccordionContent>
      </AccordionItem>
    </Accordion>,
  parameters: {
    docs: {
      description: {
        story: 'Accordion with rich content including headings, lists, and code blocks.'
      }
    }
  }
}`,...(be=(Ce=I.parameters)==null?void 0:Ce.docs)==null?void 0:be.source}}};const _o=["Single","Multiple","DefaultOpen","WithRichContent"];export{y as DefaultOpen,b as Multiple,C as Single,I as WithRichContent,_o as __namedExportsOrder,So as default};
