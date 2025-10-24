import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as d}from"./index-Dz3UJJSw.js";import{B as I}from"./button-6x4QkhmZ.js";import{c as N}from"./createLucideIcon-ClV4rtrr.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-DRuEWG1E.js";import"./index-CGrAONsN.js";import"./utils-D-KgF5mV.js";/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M=[["path",{d:"M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z",key:"a7tn18"}]],E=N("moon",M);/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const q=[["circle",{cx:"12",cy:"12",r:"4",key:"4exip2"}],["path",{d:"M12 2v2",key:"tus03m"}],["path",{d:"M12 20v2",key:"1lh1kg"}],["path",{d:"m4.93 4.93 1.41 1.41",key:"149t6j"}],["path",{d:"m17.66 17.66 1.41 1.41",key:"ptbguv"}],["path",{d:"M2 12h2",key:"1t8f8n"}],["path",{d:"M20 12h2",key:"1q8mjw"}],["path",{d:"m6.34 17.66-1.41 1.41",key:"1m8zz5"}],["path",{d:"m19.07 4.93-1.41 1.41",key:"1shlcs"}]],D=N("sun",q),j=d.createContext({theme:"light",setTheme:()=>null,toggleTheme:()=>null}),P=()=>{const s=d.useContext(j);if(s===void 0)throw new Error("useTheme must be used within a ThemeProvider");return s},l=({children:s,defaultTheme:n="system",storageKey:c="ui-theme",..._})=>{const[r,i]=d.useState(()=>typeof window<"u"&&localStorage.getItem(c)||n);d.useEffect(()=>{const t=window.document.documentElement;if(t.classList.remove("light","dark"),r==="system"){const C=window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";t.classList.add(C);return}t.classList.add(r)},[r]);const S={theme:r,setTheme:t=>{localStorage.setItem(c,t),i(t)},toggleTheme:()=>{const t=r==="light"?"dark":"light";localStorage.setItem(c,t),i(t)}};return e.jsx(j.Provider,{..._,value:S,children:s})};l.__docgenInfo={description:"",methods:[],displayName:"ThemeProvider",props:{defaultTheme:{defaultValue:{value:"'system'",computed:!1},required:!1},storageKey:{defaultValue:{value:"'ui-theme'",computed:!1},required:!1}}};l.__docgenInfo={description:"",methods:[],displayName:"ThemeProvider",props:{defaultTheme:{defaultValue:{value:"'system'",computed:!1},required:!1},storageKey:{defaultValue:{value:"'ui-theme'",computed:!1},required:!1}}};function m(){const{theme:s,toggleTheme:n}=P();return e.jsxs(I,{variant:"ghost",size:"icon",onClick:n,"aria-label":`Switch to ${s==="light"?"dark":"light"} mode`,children:[e.jsx(D,{className:"h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0"}),e.jsx(E,{className:"absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100"}),e.jsx("span",{className:"sr-only",children:"Toggle theme"})]})}m.__docgenInfo={description:"",methods:[],displayName:"ThemeToggle"};m.__docgenInfo={description:"",methods:[],displayName:"ThemeToggle"};const R={title:"UI/Theme Toggle",component:m,parameters:{layout:"centered"},tags:["autodocs"],decorators:[s=>e.jsx(l,{defaultTheme:"light",storageKey:"storybook-theme",children:e.jsx("div",{className:"p-8 bg-background text-foreground rounded-lg border",children:e.jsx(s,{})})})]},a={args:{},parameters:{docs:{description:{story:"Default theme toggle button that switches between light and dark modes."}}}},o={render:()=>e.jsxs("div",{className:"space-y-4",children:[e.jsxs("div",{className:"flex items-center gap-4",children:[e.jsx(m,{}),e.jsx("span",{className:"text-sm text-muted-foreground",children:"Click to toggle between light and dark mode"})]}),e.jsxs("div",{className:"p-4 bg-card rounded-lg border",children:[e.jsx("h3",{className:"font-semibold mb-2",children:"Sample Content"}),e.jsx("p",{className:"text-sm text-muted-foreground",children:"This content will change appearance based on the selected theme."})]})]}),parameters:{docs:{description:{story:"Theme toggle with sample content showing how colors adapt to the theme."}}}};var h,p,g;a.parameters={...a.parameters,docs:{...(h=a.parameters)==null?void 0:h.docs,source:{originalSource:`{
  args: {},
  parameters: {
    docs: {
      description: {
        story: 'Default theme toggle button that switches between light and dark modes.'
      }
    }
  }
}`,...(g=(p=a.parameters)==null?void 0:p.docs)==null?void 0:g.source}}};var u,f,x;o.parameters={...o.parameters,docs:{...(u=o.parameters)==null?void 0:u.docs,source:{originalSource:`{
  render: () => <div className="space-y-4">
      <div className="flex items-center gap-4">
        <ThemeToggle />
        <span className="text-sm text-muted-foreground">
          Click to toggle between light and dark mode
        </span>
      </div>
      <div className="p-4 bg-card rounded-lg border">
        <h3 className="font-semibold mb-2">Sample Content</h3>
        <p className="text-sm text-muted-foreground">
          This content will change appearance based on the selected theme.
        </p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Theme toggle with sample content showing how colors adapt to the theme.'
      }
    }
  }
}`,...(x=(f=o.parameters)==null?void 0:f.docs)==null?void 0:x.source}}};var T,w,y;a.parameters={...a.parameters,docs:{...(T=a.parameters)==null?void 0:T.docs,source:{originalSource:`{
  args: {},
  parameters: {
    docs: {
      description: {
        story: 'Default theme toggle button that switches between light and dark modes.'
      }
    }
  }
}`,...(y=(w=a.parameters)==null?void 0:w.docs)==null?void 0:y.source}}};var b,k,v;o.parameters={...o.parameters,docs:{...(b=o.parameters)==null?void 0:b.docs,source:{originalSource:`{
  render: () => <div className="space-y-4">
      <div className="flex items-center gap-4">
        <ThemeToggle />
        <span className="text-sm text-muted-foreground">
          Click to toggle between light and dark mode
        </span>
      </div>
      <div className="p-4 bg-card rounded-lg border">
        <h3 className="font-semibold mb-2">Sample Content</h3>
        <p className="text-sm text-muted-foreground">
          This content will change appearance based on the selected theme.
        </p>
      </div>
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Theme toggle with sample content showing how colors adapt to the theme.'
      }
    }
  }
}`,...(v=(k=o.parameters)==null?void 0:k.docs)==null?void 0:v.source}}};const U=["Default","WithContext"];export{a as Default,o as WithContext,U as __namedExportsOrder,R as default};
