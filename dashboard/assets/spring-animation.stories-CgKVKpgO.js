import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as n}from"./storybook-vendor-CPzy2iGn.js";import{M as at,i as st,u as Ze,P as it,a as rt,b as nt,L as ot,m as l,g as d,s as lt,c as I,d as dt,t as y,e as ct,f as mt,h as pt,j as W,k as gt}from"./spring-animation-a9xV3pFo.js";import"./react-vendor-Bzgz95E1.js";function K(t,i){if(typeof t=="function")return t(i);t!=null&&(t.current=i)}function xt(...t){return i=>{let a=!1;const s=t.map(o=>{const r=K(o,i);return!a&&typeof r=="function"&&(a=!0),r});if(a)return()=>{for(let o=0;o<s.length;o++){const r=s[o];typeof r=="function"?r():K(t[o],null)}}}}function ht(...t){return n.useCallback(xt(...t),t)}class bt extends n.Component{getSnapshotBeforeUpdate(i){const a=this.props.childRef.current;if(a&&i.isPresent&&!this.props.isPresent){const s=a.offsetParent,o=st(s)&&s.offsetWidth||0,r=this.props.sizeRef.current;r.height=a.offsetHeight||0,r.width=a.offsetWidth||0,r.top=a.offsetTop,r.left=a.offsetLeft,r.right=o-r.width-r.left}return null}componentDidUpdate(){}render(){return this.props.children}}function ut({children:t,isPresent:i,anchorX:a,root:s}){const o=n.useId(),r=n.useRef(null),u=n.useRef({width:0,height:0,top:0,left:0,right:0}),{nonce:R}=n.useContext(at),F=ht(r,t==null?void 0:t.ref);return n.useInsertionEffect(()=>{const{width:c,height:v,top:m,left:x,right:h}=u.current;if(i||!r.current||!c||!v)return;const w=a==="left"?`left: ${x}`:`right: ${h}`;r.current.dataset.motionPopId=o;const g=document.createElement("style");R&&(g.nonce=R);const V=s??document.head;return V.appendChild(g),g.sheet&&g.sheet.insertRule(`
          [data-motion-pop-id="${o}"] {
            position: absolute !important;
            width: ${c}px !important;
            height: ${v}px !important;
            ${w}px !important;
            top: ${m}px !important;
          }
        `),()=>{V.contains(g)&&V.removeChild(g)}},[i]),e.jsx(bt,{isPresent:i,childRef:r,sizeRef:u,children:n.cloneElement(t,{ref:F})})}const yt=({children:t,initial:i,isPresent:a,onExitComplete:s,custom:o,presenceAffectsLayout:r,mode:u,anchorX:R,root:F})=>{const c=Ze(vt),v=n.useId();let m=!0,x=n.useMemo(()=>(m=!1,{id:v,initial:i,isPresent:a,custom:o,onExitComplete:h=>{c.set(h,!0);for(const w of c.values())if(!w)return;s&&s()},register:h=>(c.set(h,!1),()=>c.delete(h))}),[a,c,s]);return r&&m&&(x={...x}),n.useMemo(()=>{c.forEach((h,w)=>c.set(w,!1))},[a]),n.useEffect(()=>{!a&&!c.size&&s&&s()},[a]),u==="popLayout"&&(t=e.jsx(ut,{isPresent:a,anchorX:R,root:F,children:t})),e.jsx(it.Provider,{value:x,children:t})};function vt(){return new Map}const L=t=>t.key||"";function G(t){const i=[];return n.Children.forEach(t,a=>{n.isValidElement(a)&&i.push(a)}),i}const M=({children:t,custom:i,initial:a=!0,onExitComplete:s,presenceAffectsLayout:o=!0,mode:r="sync",propagate:u=!1,anchorX:R="left",root:F})=>{const[c,v]=rt(u),m=n.useMemo(()=>G(t),[t]),x=u&&!c?[]:m.map(L),h=n.useRef(!0),w=n.useRef(m),g=Ze(()=>new Map),[V,et]=n.useState(m),[E,U]=n.useState(m);nt(()=>{h.current=!1,w.current=m;for(let b=0;b<E.length;b++){const p=L(E[b]);x.includes(p)?g.delete(p):g.get(p)!==!0&&g.set(p,!1)}},[E,x.length,x.join("-")]);const $=[];if(m!==V){let b=[...m];for(let p=0;p<E.length;p++){const O=E[p],B=L(O);x.includes(B)||(b.splice(p,0,O),$.push(O))}return r==="wait"&&$.length&&(b=$),U(G(b)),et(m),null}const{forceRender:D}=n.useContext(ot);return e.jsx(e.Fragment,{children:E.map(b=>{const p=L(b),O=u&&!c?!1:m===E||x.includes(p),B=()=>{if(g.has(p))g.set(p,!0);else return;let z=!0;g.forEach(tt=>{tt||(z=!1)}),z&&(D==null||D(),U(w.current),u&&(v==null||v()),s&&s())};return e.jsx(yt,{isPresent:O,initial:!h.current||a?void 0:!1,custom:i,presenceAffectsLayout:o,mode:r,root:F,onExitComplete:O?void 0:B,anchorX:R,children:b},p)})})},St={title:"Design System/Spring Animation System",parameters:{layout:"padded",docs:{description:{component:"Apple-level spring animation system with haptic feedback simulation and contextual animations."}}}},f={render:()=>{const[t,i]=n.useState(null),a=[{name:"gentle",label:"Gentle",description:"溫和的彈性動畫",color:"bg-blue-100 dark:bg-blue-900"},{name:"default",label:"Default",description:"標準 iOS 動畫（推薦）",color:"bg-green-100 dark:bg-green-900"},{name:"bouncy",label:"Bouncy",description:"活潑、有趣的彈性",color:"bg-purple-100 dark:bg-purple-900"},{name:"snappy",label:"Snappy",description:"快速、響應式",color:"bg-orange-100 dark:bg-orange-900"},{name:"smooth",label:"Smooth",description:"優雅、流暢",color:"bg-pink-100 dark:bg-pink-900"},{name:"wobbly",label:"Wobbly",description:"誇張的彈性效果",color:"bg-yellow-100 dark:bg-yellow-900"}];return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"6 種彈性預設"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"點擊查看不同彈性動畫的效果"})]}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-3 gap-6",children:a.map(s=>e.jsxs(l.button,{onClick:()=>i(s.name),whileHover:{scale:1.05},whileTap:{scale:.95},transition:d(s.name),className:`${s.color} p-6 rounded-xl shadow-md text-left relative overflow-hidden`,children:[e.jsxs("div",{className:"relative z-10",children:[e.jsx("h3",{className:"text-lg font-semibold mb-1",children:s.label}),e.jsx("p",{className:"text-sm text-gray-600 dark:text-gray-300",children:s.description})]}),e.jsx(M,{children:t===s.name&&e.jsx(l.div,{initial:{scale:0,opacity:0},animate:{scale:1,opacity:1},exit:{scale:0,opacity:0},transition:d(s.name),className:"absolute inset-0 bg-white/20 dark:bg-black/20"})})]},s.name))}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"技術參數"}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-3 gap-4",children:Object.entries(lt).map(([s,o])=>e.jsxs("div",{className:"p-4 bg-gray-50 dark:bg-gray-700 rounded-lg",children:[e.jsx("h4",{className:"font-semibold capitalize mb-2",children:s}),e.jsxs("div",{className:"text-sm space-y-1 text-gray-600 dark:text-gray-300",children:[e.jsxs("div",{children:["Stiffness: ",o.stiffness]}),e.jsxs("div",{children:["Damping: ",o.damping]}),e.jsxs("div",{children:["Mass: ",o.mass]}),e.jsxs("div",{children:["Duration: ",o.duration,"s"]})]})]},s))})]})]})}},N={render:()=>{var s,o;const[t,i]=n.useState(null),a=[{name:"fade",label:"Fade",description:"淡入淡出"},{name:"scale",label:"Scale",description:"縮放"},{name:"pop",label:"Pop",description:"彈出"},{name:"bounce",label:"Bounce",description:"彈跳"},{name:"slideUp",label:"Slide Up",description:"向上滑動"},{name:"slideDown",label:"Slide Down",description:"向下滑動"},{name:"slideLeft",label:"Slide Left",description:"向左滑動"},{name:"slideRight",label:"Slide Right",description:"向右滑動"},{name:"shake",label:"Shake",description:"搖晃"},{name:"pulse",label:"Pulse",description:"脈衝"}];return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"動畫變體"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"點擊按鈕查看不同的動畫效果"})]}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-5 gap-4",children:a.map(r=>e.jsx("button",{onClick:()=>i(r.name),className:"px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors",children:r.label},r.name))}),e.jsx("div",{className:"bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[300px] flex items-center justify-center",children:e.jsx(M,{mode:"wait",children:t&&e.jsxs(l.div,{variants:I(t,"default"),initial:"initial",animate:"animate",exit:"exit",className:"bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl",children:[e.jsx("h3",{className:"text-2xl font-bold mb-2",children:(s=a.find(r=>r.name===t))==null?void 0:s.label}),e.jsx("p",{className:"text-blue-100",children:(o=a.find(r=>r.name===t))==null?void 0:o.description})]},t)})})]})}},k={render:()=>{const t=[{type:"light",label:"Light",description:"輕微",color:"bg-gray-500"},{type:"medium",label:"Medium",description:"中等",color:"bg-blue-500"},{type:"heavy",label:"Heavy",description:"重度",color:"bg-purple-500"},{type:"success",label:"Success",description:"成功",color:"bg-green-500"},{type:"warning",label:"Warning",description:"警告",color:"bg-yellow-500"},{type:"error",label:"Error",description:"錯誤",color:"bg-red-500"},{type:"selection",label:"Selection",description:"選擇",color:"bg-indigo-500"}];return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"觸覺反饋模擬"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"點擊按鈕體驗不同強度的觸覺反饋"})]}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-6",children:t.map(i=>e.jsxs(l.button,{onClick:a=>y(a.currentTarget,i.type),whileHover:{scale:1.05},whileTap:dt(i.type),className:`${i.color} text-white p-6 rounded-xl shadow-md`,children:[e.jsx("h3",{className:"text-lg font-semibold mb-1",children:i.label}),e.jsx("p",{className:"text-sm opacity-90",children:i.description})]},i.type))}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"CSS 類名範例"}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-4",children:t.map(i=>e.jsxs("button",{className:`haptic-${i.type} ${i.color} text-white px-4 py-3 rounded-lg`,children:[".haptic-",i.type]},`css-${i.type}`))})]})]})}},S={render:()=>e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"按鈕互動"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"Apple 風格的按鈕按壓效果"})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Framer Motion 按鈕"}),e.jsxs("div",{className:"flex flex-wrap gap-4",children:[e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("snappy"),onClick:t=>y(t.currentTarget,"medium"),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"Primary Button"}),e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("bouncy"),onClick:t=>y(t.currentTarget,"success"),className:"px-6 py-3 bg-green-600 text-white rounded-lg shadow-md",children:"Success Button"}),e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("default"),onClick:t=>y(t.currentTarget,"warning"),className:"px-6 py-3 bg-yellow-600 text-white rounded-lg shadow-md",children:"Warning Button"}),e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("wobbly"),onClick:t=>y(t.currentTarget,"error"),className:"px-6 py-3 bg-red-600 text-white rounded-lg shadow-md",children:"Error Button"})]})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"CSS 類名按鈕"}),e.jsxs("div",{className:"flex flex-wrap gap-4",children:[e.jsx("button",{className:"btn-spring-press px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"Standard Press"}),e.jsx("button",{className:"btn-spring-press-heavy px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md",children:"Heavy Press"}),e.jsx("button",{className:"spring-hover-lift px-6 py-3 bg-indigo-600 text-white rounded-lg shadow-md",children:"Hover Lift"}),e.jsx("button",{className:"spring-hover-scale px-6 py-3 bg-pink-600 text-white rounded-lg shadow-md",children:"Hover Scale"})]})]})]})},j={render:()=>{const[t,i]=n.useState(!1);return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"模態對話框動畫"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"iOS 風格的 Sheet 動畫"})]}),e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("snappy"),onClick:()=>i(!0),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"打開 Modal"}),e.jsx(M,{children:t&&e.jsxs(e.Fragment,{children:[e.jsx(l.div,{initial:{opacity:0},animate:{opacity:1},exit:{opacity:0},onClick:()=>i(!1),className:"fixed inset-0 bg-black/40 z-40"}),e.jsxs(l.div,{variants:I("slideUp","default"),initial:"initial",animate:"animate",exit:"exit",className:"fixed inset-x-4 bottom-4 bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-2xl z-50 max-w-md mx-auto",children:[e.jsx("h3",{className:"text-xl font-bold mb-4",children:"iOS 風格 Sheet"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400 mb-6",children:"這是一個使用彈性動畫的模態對話框，模擬 iOS 的 Sheet 效果。"}),e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("snappy"),onClick:()=>i(!1),className:"w-full px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"關閉"})]})]})})]})}},C={render:()=>{const[t,i]=n.useState(!0),a=[{id:1,title:"項目 1",description:"這是第一個項目"},{id:2,title:"項目 2",description:"這是第二個項目"},{id:3,title:"項目 3",description:"這是第三個項目"},{id:4,title:"項目 4",description:"這是第四個項目"},{id:5,title:"項目 5",description:"這是第五個項目"}];return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"列表交錯動畫"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"子元素依序出現的動畫效果"})]}),e.jsxs(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("snappy"),onClick:()=>i(!t),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:[t?"隱藏":"顯示","列表"]}),e.jsx(M,{children:t&&e.jsx(l.div,{variants:{animate:{transition:ct("default",.08)}},initial:"initial",animate:"animate",exit:"exit",className:"space-y-4",children:a.map(s=>e.jsxs(l.div,{variants:I("slideUp","default"),className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-2",children:s.title}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:s.description})]},s.id))})}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"CSS 交錯動畫"}),e.jsx("div",{className:"stagger-children space-y-4",children:a.map(s=>e.jsxs("div",{className:"bg-gray-50 dark:bg-gray-700 p-4 rounded-lg",children:[e.jsx("h4",{className:"font-semibold",children:s.title}),e.jsx("p",{className:"text-sm text-gray-600 dark:text-gray-300",children:s.description})]},s.id))})]})]})}},P={render:()=>{const[t,i]=n.useState(!1),[a,s]=n.useState(!1),o=n.useRef(null),r=n.useRef(null);return n.useEffect(()=>{t&&o.current&&y(o.current,"success")},[t]),n.useEffect(()=>{a&&r.current&&y(r.current,"error")},[a]),e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"成功/錯誤反饋"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"帶有觸覺反饋的狀態提示"})]}),e.jsxs("div",{className:"flex gap-4",children:[e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("snappy"),onClick:()=>{i(!0),setTimeout(()=>i(!1),3e3)},className:"px-6 py-3 bg-green-600 text-white rounded-lg shadow-md",children:"顯示成功"}),e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("snappy"),onClick:()=>{s(!0),setTimeout(()=>s(!1),3e3)},className:"px-6 py-3 bg-red-600 text-white rounded-lg shadow-md",children:"顯示錯誤"})]}),e.jsxs("div",{className:"space-y-4",children:[e.jsx(M,{children:t&&e.jsxs(l.div,{ref:o,variants:I("bounce","bouncy"),initial:"initial",animate:"animate",exit:"exit",className:"bg-green-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3",children:[e.jsx("div",{className:"text-2xl",children:"✓"}),e.jsxs("div",{children:[e.jsx("h3",{className:"font-semibold",children:"操作成功！"}),e.jsx("p",{className:"text-sm opacity-90",children:"您的更改已保存"})]})]})}),e.jsx(M,{children:a&&e.jsxs(l.div,{ref:r,variants:I("shake","wobbly"),initial:"initial",animate:"animate",exit:"exit",className:"bg-red-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3",children:[e.jsx("div",{className:"text-2xl",children:"✗"}),e.jsxs("div",{children:[e.jsx("h3",{className:"font-semibold",children:"操作失敗！"}),e.jsx("p",{className:"text-sm opacity-90",children:"請稍後再試"})]})]})})]})]})}},A={render:()=>{const[t,i]=n.useState(mt()),[a,s]=n.useState(0);return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"上下文感知動畫"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"根據用戶環境自動調整動畫"})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"當前上下文"}),e.jsxs("div",{className:"grid grid-cols-2 gap-4 text-sm",children:[e.jsxs("div",{children:[e.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"設備類型："}),e.jsx("span",{className:"font-semibold ml-2",children:t.isMobile?"移動設備":"桌面設備"})]}),e.jsxs("div",{children:[e.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"低電量模式："}),e.jsx("span",{className:"font-semibold ml-2",children:t.isLowPower?"是":"否"})]}),e.jsxs("div",{children:[e.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"網絡速度："}),e.jsx("span",{className:"font-semibold ml-2",children:t.connectionSpeed})]}),e.jsxs("div",{children:[e.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"用戶偏好："}),e.jsx("span",{className:"font-semibold ml-2",children:t.userPreference})]})]})]}),e.jsx("div",{className:"bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[200px] flex items-center justify-center",children:e.jsxs(l.div,{...pt("slideUp",t),initial:"initial",animate:"animate",className:"bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl",children:[e.jsx("h3",{className:"text-2xl font-bold",children:"上下文感知動畫"}),e.jsx("p",{className:"text-blue-100 mt-2",children:"根據您的環境自動調整"})]},a)}),e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("snappy"),onClick:()=>s(o=>o+1),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"重新播放動畫"})]})}},H={render:()=>{const[t,i]=n.useState(W()),[a,s]=n.useState(!1),o=()=>{s(!0),gt(),setTimeout(()=>{s(!1),i(W())},1e3)};return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"性能監控"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"追蹤動畫性能指標"})]}),e.jsxs("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-4",children:[e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("div",{className:"text-3xl font-bold text-blue-600",children:t.totalAnimations}),e.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"總動畫數"})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("div",{className:"text-3xl font-bold text-green-600",children:t.activeAnimations}),e.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"活躍動畫"})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("div",{className:"text-3xl font-bold text-yellow-600",children:t.droppedFrames}),e.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"掉幀數"})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("div",{className:"text-3xl font-bold text-purple-600",children:t.averageFPS.toFixed(1)}),e.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"平均 FPS"})]})]}),e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("snappy"),onClick:o,disabled:a,className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md disabled:opacity-50",children:a?"動畫中...":"開始動畫"}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"性能建議"}),e.jsxs("div",{className:"space-y-2 text-sm",children:[t.averageFPS<55&&e.jsx("div",{className:"text-red-600 dark:text-red-400",children:"⚠️ 平均 FPS 低於 55，建議降級到更簡單的動畫"}),t.activeAnimations>5&&e.jsx("div",{className:"text-yellow-600 dark:text-yellow-400",children:"⚠️ 同時活躍動畫過多，可能影響性能"}),t.droppedFrames>10&&e.jsx("div",{className:"text-orange-600 dark:text-orange-400",children:"⚠️ 掉幀數較多，建議優化動畫"}),t.averageFPS>=55&&t.activeAnimations<=5&&t.droppedFrames<=10&&e.jsx("div",{className:"text-green-600 dark:text-green-400",children:"✓ 性能良好，動畫流暢"})]})]})]})}},T={render:()=>{const[t,i]=n.useState(!1);return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"完整演示"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"綜合展示彈性動畫系統的各種功能"})]}),e.jsxs(l.div,{layout:!0,onClick:()=>i(!t),className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md cursor-pointer",whileHover:{scale:1.02},transition:d("default"),children:[e.jsx(l.h3,{layout:"position",className:"text-xl font-bold mb-2",children:"互動卡片"}),e.jsx(l.p,{layout:"position",className:"text-gray-600 dark:text-gray-400",children:"點擊展開查看更多內容"}),e.jsx(M,{children:t&&e.jsxs(l.div,{initial:{opacity:0,height:0},animate:{opacity:1,height:"auto"},exit:{opacity:0,height:0},transition:d("default"),className:"mt-4 pt-4 border-t border-gray-200 dark:border-gray-700",children:[e.jsx("p",{className:"text-gray-600 dark:text-gray-400 mb-4",children:"這是展開的內容區域，使用了彈性動畫來創造流暢的展開效果。"}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("snappy"),onClick:a=>{a.stopPropagation(),y(a.currentTarget,"success")},className:"px-4 py-2 bg-green-600 text-white rounded-lg text-sm",children:"確認"}),e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("snappy"),onClick:a=>{a.stopPropagation(),i(!1)},className:"px-4 py-2 bg-gray-600 text-white rounded-lg text-sm",children:"取消"})]})]})})]}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-4",children:["Primary","Success","Warning","Error"].map((a,s)=>e.jsx(l.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:d("snappy"),onClick:o=>{const r=["medium","success","warning","error"][s];y(o.currentTarget,r)},className:`px-6 py-3 text-white rounded-lg shadow-md ${["bg-blue-600","bg-green-600","bg-yellow-600","bg-red-600"][s]}`,children:a},a))})]})}};var _,X,q;f.parameters={...f.parameters,docs:{...(_=f.parameters)==null?void 0:_.docs,source:{originalSource:`{
  render: () => {
    const [activePreset, setActivePreset] = useState<string | null>(null);
    const presets = [{
      name: 'gentle',
      label: 'Gentle',
      description: '溫和的彈性動畫',
      color: 'bg-blue-100 dark:bg-blue-900'
    }, {
      name: 'default',
      label: 'Default',
      description: '標準 iOS 動畫（推薦）',
      color: 'bg-green-100 dark:bg-green-900'
    }, {
      name: 'bouncy',
      label: 'Bouncy',
      description: '活潑、有趣的彈性',
      color: 'bg-purple-100 dark:bg-purple-900'
    }, {
      name: 'snappy',
      label: 'Snappy',
      description: '快速、響應式',
      color: 'bg-orange-100 dark:bg-orange-900'
    }, {
      name: 'smooth',
      label: 'Smooth',
      description: '優雅、流暢',
      color: 'bg-pink-100 dark:bg-pink-900'
    }, {
      name: 'wobbly',
      label: 'Wobbly',
      description: '誇張的彈性效果',
      color: 'bg-yellow-100 dark:bg-yellow-900'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">6 種彈性預設</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊查看不同彈性動畫的效果</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          {presets.map(preset => <motion.button key={preset.name} onClick={() => setActivePreset(preset.name)} whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig(preset.name as keyof typeof springPresets)} className={\`\${preset.color} p-6 rounded-xl shadow-md text-left relative overflow-hidden\`}>
              <div className="relative z-10">
                <h3 className="text-lg font-semibold mb-1">{preset.label}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">{preset.description}</p>
              </div>
              
              <AnimatePresence>
                {activePreset === preset.name && <motion.div initial={{
              scale: 0,
              opacity: 0
            }} animate={{
              scale: 1,
              opacity: 1
            }} exit={{
              scale: 0,
              opacity: 0
            }} transition={getSpringConfig(preset.name as keyof typeof springPresets)} className="absolute inset-0 bg-white/20 dark:bg-black/20" />}
              </AnimatePresence>
            </motion.button>)}
        </div>
        
        {/* 技術參數展示 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">技術參數</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(springPresets).map(([name, config]) => <div key={name} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h4 className="font-semibold capitalize mb-2">{name}</h4>
                <div className="text-sm space-y-1 text-gray-600 dark:text-gray-300">
                  <div>Stiffness: {config.stiffness}</div>
                  <div>Damping: {config.damping}</div>
                  <div>Mass: {config.mass}</div>
                  <div>Duration: {config.duration}s</div>
                </div>
              </div>)}
          </div>
        </div>
      </div>;
  }
}`,...(q=(X=f.parameters)==null?void 0:X.docs)==null?void 0:q.source}}};var J,Q,Y;N.parameters={...N.parameters,docs:{...(J=N.parameters)==null?void 0:J.docs,source:{originalSource:`{
  render: () => {
    const [activeVariant, setActiveVariant] = useState<string | null>(null);
    const variants = [{
      name: 'fade',
      label: 'Fade',
      description: '淡入淡出'
    }, {
      name: 'scale',
      label: 'Scale',
      description: '縮放'
    }, {
      name: 'pop',
      label: 'Pop',
      description: '彈出'
    }, {
      name: 'bounce',
      label: 'Bounce',
      description: '彈跳'
    }, {
      name: 'slideUp',
      label: 'Slide Up',
      description: '向上滑動'
    }, {
      name: 'slideDown',
      label: 'Slide Down',
      description: '向下滑動'
    }, {
      name: 'slideLeft',
      label: 'Slide Left',
      description: '向左滑動'
    }, {
      name: 'slideRight',
      label: 'Slide Right',
      description: '向右滑動'
    }, {
      name: 'shake',
      label: 'Shake',
      description: '搖晃'
    }, {
      name: 'pulse',
      label: 'Pulse',
      description: '脈衝'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">動畫變體</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊按鈕查看不同的動畫效果</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {variants.map(variant => <button key={variant.name} onClick={() => setActiveVariant(variant.name)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              {variant.label}
            </button>)}
        </div>
        
        {/* 動畫展示區域 */}
        <div className="bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[300px] flex items-center justify-center">
          <AnimatePresence mode="wait">
            {activeVariant && <motion.div key={activeVariant} variants={getSpringVariants(activeVariant, 'default')} initial="initial" animate="animate" exit="exit" className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl">
                <h3 className="text-2xl font-bold mb-2">
                  {variants.find(v => v.name === activeVariant)?.label}
                </h3>
                <p className="text-blue-100">
                  {variants.find(v => v.name === activeVariant)?.description}
                </p>
              </motion.div>}
          </AnimatePresence>
        </div>
      </div>;
  }
}`,...(Y=(Q=N.parameters)==null?void 0:Q.docs)==null?void 0:Y.source}}};var Z,ee,te;k.parameters={...k.parameters,docs:{...(Z=k.parameters)==null?void 0:Z.docs,source:{originalSource:`{
  render: () => {
    const haptics = [{
      type: 'light',
      label: 'Light',
      description: '輕微',
      color: 'bg-gray-500'
    }, {
      type: 'medium',
      label: 'Medium',
      description: '中等',
      color: 'bg-blue-500'
    }, {
      type: 'heavy',
      label: 'Heavy',
      description: '重度',
      color: 'bg-purple-500'
    }, {
      type: 'success',
      label: 'Success',
      description: '成功',
      color: 'bg-green-500'
    }, {
      type: 'warning',
      label: 'Warning',
      description: '警告',
      color: 'bg-yellow-500'
    }, {
      type: 'error',
      label: 'Error',
      description: '錯誤',
      color: 'bg-red-500'
    }, {
      type: 'selection',
      label: 'Selection',
      description: '選擇',
      color: 'bg-indigo-500'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">觸覺反饋模擬</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊按鈕體驗不同強度的觸覺反饋</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {haptics.map(haptic => <motion.button key={haptic.type} onClick={e => triggerHaptic(e.currentTarget, haptic.type as any)} whileHover={{
          scale: 1.05
        }} whileTap={getHapticAnimation(haptic.type as any)} className={\`\${haptic.color} text-white p-6 rounded-xl shadow-md\`}>
              <h3 className="text-lg font-semibold mb-1">{haptic.label}</h3>
              <p className="text-sm opacity-90">{haptic.description}</p>
            </motion.button>)}
        </div>
        
        {/* CSS 類名範例 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 類名範例</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {haptics.map(haptic => <button key={\`css-\${haptic.type}\`} className={\`haptic-\${haptic.type} \${haptic.color} text-white px-4 py-3 rounded-lg\`}>
                .haptic-{haptic.type}
              </button>)}
          </div>
        </div>
      </div>;
  }
}`,...(te=(ee=k.parameters)==null?void 0:ee.docs)==null?void 0:te.source}}};var ae,se,ie;S.parameters={...S.parameters,docs:{...(ae=S.parameters)==null?void 0:ae.docs,source:{originalSource:`{
  render: () => {
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">按鈕互動</h2>
          <p className="text-gray-600 dark:text-gray-400">Apple 風格的按鈕按壓效果</p>
        </div>
        
        {/* Framer Motion 按鈕 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">Framer Motion 按鈕</h3>
          <div className="flex flex-wrap gap-4">
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('snappy')} onClick={e => triggerHaptic(e.currentTarget, 'medium')} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
              Primary Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('bouncy')} onClick={e => triggerHaptic(e.currentTarget, 'success')} className="px-6 py-3 bg-green-600 text-white rounded-lg shadow-md">
              Success Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('default')} onClick={e => triggerHaptic(e.currentTarget, 'warning')} className="px-6 py-3 bg-yellow-600 text-white rounded-lg shadow-md">
              Warning Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('wobbly')} onClick={e => triggerHaptic(e.currentTarget, 'error')} className="px-6 py-3 bg-red-600 text-white rounded-lg shadow-md">
              Error Button
            </motion.button>
          </div>
        </div>
        
        {/* CSS 類名按鈕 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 類名按鈕</h3>
          <div className="flex flex-wrap gap-4">
            <button className="btn-spring-press px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
              Standard Press
            </button>
            
            <button className="btn-spring-press-heavy px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md">
              Heavy Press
            </button>
            
            <button className="spring-hover-lift px-6 py-3 bg-indigo-600 text-white rounded-lg shadow-md">
              Hover Lift
            </button>
            
            <button className="spring-hover-scale px-6 py-3 bg-pink-600 text-white rounded-lg shadow-md">
              Hover Scale
            </button>
          </div>
        </div>
      </div>;
  }
}`,...(ie=(se=S.parameters)==null?void 0:se.docs)==null?void 0:ie.source}}};var re,ne,oe;j.parameters={...j.parameters,docs:{...(re=j.parameters)==null?void 0:re.docs,source:{originalSource:`{
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">模態對話框動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">iOS 風格的 Sheet 動畫</p>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setIsOpen(true)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          打開 Modal
        </motion.button>
        
        <AnimatePresence>
          {isOpen && <>
              {/* 背景遮罩 */}
              <motion.div initial={{
            opacity: 0
          }} animate={{
            opacity: 1
          }} exit={{
            opacity: 0
          }} onClick={() => setIsOpen(false)} className="fixed inset-0 bg-black/40 z-40" />
              
              {/* 對話框 */}
              <motion.div variants={getSpringVariants('slideUp', 'default')} initial="initial" animate="animate" exit="exit" className="fixed inset-x-4 bottom-4 bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-2xl z-50 max-w-md mx-auto">
                <h3 className="text-xl font-bold mb-4">iOS 風格 Sheet</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  這是一個使用彈性動畫的模態對話框，模擬 iOS 的 Sheet 效果。
                </p>
                <motion.button whileHover={{
              scale: 1.05
            }} whileTap={{
              scale: 0.95
            }} transition={getSpringConfig('snappy')} onClick={() => setIsOpen(false)} className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
                  關閉
                </motion.button>
              </motion.div>
            </>}
        </AnimatePresence>
      </div>;
  }
}`,...(oe=(ne=j.parameters)==null?void 0:ne.docs)==null?void 0:oe.source}}};var le,de,ce;C.parameters={...C.parameters,docs:{...(le=C.parameters)==null?void 0:le.docs,source:{originalSource:`{
  render: () => {
    const [show, setShow] = useState(true);
    const items = [{
      id: 1,
      title: '項目 1',
      description: '這是第一個項目'
    }, {
      id: 2,
      title: '項目 2',
      description: '這是第二個項目'
    }, {
      id: 3,
      title: '項目 3',
      description: '這是第三個項目'
    }, {
      id: 4,
      title: '項目 4',
      description: '這是第四個項目'
    }, {
      id: 5,
      title: '項目 5',
      description: '這是第五個項目'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">列表交錯動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">子元素依序出現的動畫效果</p>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setShow(!show)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          {show ? '隱藏' : '顯示'}列表
        </motion.button>
        
        <AnimatePresence>
          {show && <motion.div variants={{
          animate: {
            transition: getStaggerConfig('default', 0.08)
          }
        }} initial="initial" animate="animate" exit="exit" className="space-y-4">
              {items.map(item => <motion.div key={item.id} variants={getSpringVariants('slideUp', 'default')} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
                  <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                  <p className="text-gray-600 dark:text-gray-400">{item.description}</p>
                </motion.div>)}
            </motion.div>}
        </AnimatePresence>
        
        {/* CSS 交錯動畫 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 交錯動畫</h3>
          <div className="stagger-children space-y-4">
            {items.map(item => <div key={item.id} className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 className="font-semibold">{item.title}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">{item.description}</p>
              </div>)}
          </div>
        </div>
      </div>;
  }
}`,...(ce=(de=C.parameters)==null?void 0:de.docs)==null?void 0:ce.source}}};var me,pe,ge;P.parameters={...P.parameters,docs:{...(me=P.parameters)==null?void 0:me.docs,source:{originalSource:`{
  render: () => {
    const [showSuccess, setShowSuccess] = useState(false);
    const [showError, setShowError] = useState(false);
    const successRef = useRef<HTMLDivElement>(null);
    const errorRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
      if (showSuccess && successRef.current) {
        triggerHaptic(successRef.current, 'success');
      }
    }, [showSuccess]);
    useEffect(() => {
      if (showError && errorRef.current) {
        triggerHaptic(errorRef.current, 'error');
      }
    }, [showError]);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">成功/錯誤反饋</h2>
          <p className="text-gray-600 dark:text-gray-400">帶有觸覺反饋的狀態提示</p>
        </div>
        
        <div className="flex gap-4">
          <motion.button whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={() => {
          setShowSuccess(true);
          setTimeout(() => setShowSuccess(false), 3000);
        }} className="px-6 py-3 bg-green-600 text-white rounded-lg shadow-md">
            顯示成功
          </motion.button>
          
          <motion.button whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={() => {
          setShowError(true);
          setTimeout(() => setShowError(false), 3000);
        }} className="px-6 py-3 bg-red-600 text-white rounded-lg shadow-md">
            顯示錯誤
          </motion.button>
        </div>
        
        <div className="space-y-4">
          <AnimatePresence>
            {showSuccess && <motion.div ref={successRef} variants={getSpringVariants('bounce', 'bouncy')} initial="initial" animate="animate" exit="exit" className="bg-green-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3">
                <div className="text-2xl">✓</div>
                <div>
                  <h3 className="font-semibold">操作成功！</h3>
                  <p className="text-sm opacity-90">您的更改已保存</p>
                </div>
              </motion.div>}
          </AnimatePresence>
          
          <AnimatePresence>
            {showError && <motion.div ref={errorRef} variants={getSpringVariants('shake', 'wobbly')} initial="initial" animate="animate" exit="exit" className="bg-red-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3">
                <div className="text-2xl">✗</div>
                <div>
                  <h3 className="font-semibold">操作失敗！</h3>
                  <p className="text-sm opacity-90">請稍後再試</p>
                </div>
              </motion.div>}
          </AnimatePresence>
        </div>
      </div>;
  }
}`,...(ge=(pe=P.parameters)==null?void 0:pe.docs)==null?void 0:ge.source}}};var xe,he,be;A.parameters={...A.parameters,docs:{...(xe=A.parameters)==null?void 0:xe.docs,source:{originalSource:`{
  render: () => {
    const [context, setContext] = useState(getUserContext());
    const [animationKey, setAnimationKey] = useState(0);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">上下文感知動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">根據用戶環境自動調整動畫</p>
        </div>
        
        {/* 當前上下文 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">當前上下文</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">設備類型：</span>
              <span className="font-semibold ml-2">{context.isMobile ? '移動設備' : '桌面設備'}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">低電量模式：</span>
              <span className="font-semibold ml-2">{context.isLowPower ? '是' : '否'}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">網絡速度：</span>
              <span className="font-semibold ml-2">{context.connectionSpeed}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">用戶偏好：</span>
              <span className="font-semibold ml-2">{context.userPreference}</span>
            </div>
          </div>
        </div>
        
        {/* 動畫展示 */}
        <div className="bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[200px] flex items-center justify-center">
          <motion.div key={animationKey} {...getContextualAnimation('slideUp', context)} initial="initial" animate="animate" className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl">
            <h3 className="text-2xl font-bold">上下文感知動畫</h3>
            <p className="text-blue-100 mt-2">根據您的環境自動調整</p>
          </motion.div>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setAnimationKey(k => k + 1)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          重新播放動畫
        </motion.button>
      </div>;
  }
}`,...(be=(he=A.parameters)==null?void 0:he.docs)==null?void 0:be.source}}};var ue,ye,ve;H.parameters={...H.parameters,docs:{...(ue=H.parameters)==null?void 0:ue.docs,source:{originalSource:`{
  render: () => {
    const [metrics, setMetrics] = useState(getAnimationMetrics());
    const [isAnimating, setIsAnimating] = useState(false);
    const startAnimation = () => {
      setIsAnimating(true);
      trackAnimation('demo-animation');
      setTimeout(() => {
        setIsAnimating(false);
        setMetrics(getAnimationMetrics());
      }, 1000);
    };
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">性能監控</h2>
          <p className="text-gray-600 dark:text-gray-400">追蹤動畫性能指標</p>
        </div>
        
        {/* 性能指標 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-blue-600">{metrics.totalAnimations}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">總動畫數</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-green-600">{metrics.activeAnimations}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">活躍動畫</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-yellow-600">{metrics.droppedFrames}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">掉幀數</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-purple-600">{metrics.averageFPS.toFixed(1)}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">平均 FPS</div>
          </div>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={startAnimation} disabled={isAnimating} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md disabled:opacity-50">
          {isAnimating ? '動畫中...' : '開始動畫'}
        </motion.button>
        
        {/* 性能建議 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">性能建議</h3>
          <div className="space-y-2 text-sm">
            {metrics.averageFPS < 55 && <div className="text-red-600 dark:text-red-400">
                ⚠️ 平均 FPS 低於 55，建議降級到更簡單的動畫
              </div>}
            {metrics.activeAnimations > 5 && <div className="text-yellow-600 dark:text-yellow-400">
                ⚠️ 同時活躍動畫過多，可能影響性能
              </div>}
            {metrics.droppedFrames > 10 && <div className="text-orange-600 dark:text-orange-400">
                ⚠️ 掉幀數較多，建議優化動畫
              </div>}
            {metrics.averageFPS >= 55 && metrics.activeAnimations <= 5 && metrics.droppedFrames <= 10 && <div className="text-green-600 dark:text-green-400">
                ✓ 性能良好，動畫流暢
              </div>}
          </div>
        </div>
      </div>;
  }
}`,...(ve=(ye=H.parameters)==null?void 0:ye.docs)==null?void 0:ve.source}}};var we,fe,Ne;T.parameters={...T.parameters,docs:{...(we=T.parameters)==null?void 0:we.docs,source:{originalSource:`{
  render: () => {
    const [isCardOpen, setIsCardOpen] = useState(false);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">完整演示</h2>
          <p className="text-gray-600 dark:text-gray-400">綜合展示彈性動畫系統的各種功能</p>
        </div>
        
        {/* 互動卡片 */}
        <motion.div layout onClick={() => setIsCardOpen(!isCardOpen)} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md cursor-pointer" whileHover={{
        scale: 1.02
      }} transition={getSpringConfig('default')}>
          <motion.h3 layout="position" className="text-xl font-bold mb-2">
            互動卡片
          </motion.h3>
          <motion.p layout="position" className="text-gray-600 dark:text-gray-400">
            點擊展開查看更多內容
          </motion.p>
          
          <AnimatePresence>
            {isCardOpen && <motion.div initial={{
            opacity: 0,
            height: 0
          }} animate={{
            opacity: 1,
            height: 'auto'
          }} exit={{
            opacity: 0,
            height: 0
          }} transition={getSpringConfig('default')} className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  這是展開的內容區域，使用了彈性動畫來創造流暢的展開效果。
                </p>
                <div className="flex gap-2">
                  <motion.button whileHover={{
                scale: 1.05
              }} whileTap={{
                scale: 0.95
              }} transition={getSpringConfig('snappy')} onClick={e => {
                e.stopPropagation();
                triggerHaptic(e.currentTarget, 'success');
              }} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm">
                    確認
                  </motion.button>
                  <motion.button whileHover={{
                scale: 1.05
              }} whileTap={{
                scale: 0.95
              }} transition={getSpringConfig('snappy')} onClick={e => {
                e.stopPropagation();
                setIsCardOpen(false);
              }} className="px-4 py-2 bg-gray-600 text-white rounded-lg text-sm">
                    取消
                  </motion.button>
                </div>
              </motion.div>}
          </AnimatePresence>
        </motion.div>
        
        {/* 功能按鈕組 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {['Primary', 'Success', 'Warning', 'Error'].map((type, i) => <motion.button key={type} whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={e => {
          const hapticType = ['medium', 'success', 'warning', 'error'][i];
          triggerHaptic(e.currentTarget, hapticType as any);
        }} className={\`px-6 py-3 text-white rounded-lg shadow-md \${['bg-blue-600', 'bg-green-600', 'bg-yellow-600', 'bg-red-600'][i]}\`}>
              {type}
            </motion.button>)}
        </div>
      </div>;
  }
}`,...(Ne=(fe=T.parameters)==null?void 0:fe.docs)==null?void 0:Ne.source}}};var ke,Se,je;f.parameters={...f.parameters,docs:{...(ke=f.parameters)==null?void 0:ke.docs,source:{originalSource:`{
  render: () => {
    const [activePreset, setActivePreset] = useState<string | null>(null);
    const presets = [{
      name: 'gentle',
      label: 'Gentle',
      description: '溫和的彈性動畫',
      color: 'bg-blue-100 dark:bg-blue-900'
    }, {
      name: 'default',
      label: 'Default',
      description: '標準 iOS 動畫（推薦）',
      color: 'bg-green-100 dark:bg-green-900'
    }, {
      name: 'bouncy',
      label: 'Bouncy',
      description: '活潑、有趣的彈性',
      color: 'bg-purple-100 dark:bg-purple-900'
    }, {
      name: 'snappy',
      label: 'Snappy',
      description: '快速、響應式',
      color: 'bg-orange-100 dark:bg-orange-900'
    }, {
      name: 'smooth',
      label: 'Smooth',
      description: '優雅、流暢',
      color: 'bg-pink-100 dark:bg-pink-900'
    }, {
      name: 'wobbly',
      label: 'Wobbly',
      description: '誇張的彈性效果',
      color: 'bg-yellow-100 dark:bg-yellow-900'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">6 種彈性預設</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊查看不同彈性動畫的效果</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          {presets.map(preset => <motion.button key={preset.name} onClick={() => setActivePreset(preset.name)} whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig(preset.name as keyof typeof springPresets)} className={\`\${preset.color} p-6 rounded-xl shadow-md text-left relative overflow-hidden\`}>
              <div className="relative z-10">
                <h3 className="text-lg font-semibold mb-1">{preset.label}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">{preset.description}</p>
              </div>
              
              <AnimatePresence>
                {activePreset === preset.name && <motion.div initial={{
              scale: 0,
              opacity: 0
            }} animate={{
              scale: 1,
              opacity: 1
            }} exit={{
              scale: 0,
              opacity: 0
            }} transition={getSpringConfig(preset.name as keyof typeof springPresets)} className="absolute inset-0 bg-white/20 dark:bg-black/20" />}
              </AnimatePresence>
            </motion.button>)}
        </div>
        
        {/* 技術參數展示 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">技術參數</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(springPresets).map(([name, config]) => <div key={name} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h4 className="font-semibold capitalize mb-2">{name}</h4>
                <div className="text-sm space-y-1 text-gray-600 dark:text-gray-300">
                  <div>Stiffness: {config.stiffness}</div>
                  <div>Damping: {config.damping}</div>
                  <div>Mass: {config.mass}</div>
                  <div>Duration: {config.duration}s</div>
                </div>
              </div>)}
          </div>
        </div>
      </div>;
  }
}`,...(je=(Se=f.parameters)==null?void 0:Se.docs)==null?void 0:je.source}}};var Ce,Pe,Ae;N.parameters={...N.parameters,docs:{...(Ce=N.parameters)==null?void 0:Ce.docs,source:{originalSource:`{
  render: () => {
    const [activeVariant, setActiveVariant] = useState<string | null>(null);
    const variants = [{
      name: 'fade',
      label: 'Fade',
      description: '淡入淡出'
    }, {
      name: 'scale',
      label: 'Scale',
      description: '縮放'
    }, {
      name: 'pop',
      label: 'Pop',
      description: '彈出'
    }, {
      name: 'bounce',
      label: 'Bounce',
      description: '彈跳'
    }, {
      name: 'slideUp',
      label: 'Slide Up',
      description: '向上滑動'
    }, {
      name: 'slideDown',
      label: 'Slide Down',
      description: '向下滑動'
    }, {
      name: 'slideLeft',
      label: 'Slide Left',
      description: '向左滑動'
    }, {
      name: 'slideRight',
      label: 'Slide Right',
      description: '向右滑動'
    }, {
      name: 'shake',
      label: 'Shake',
      description: '搖晃'
    }, {
      name: 'pulse',
      label: 'Pulse',
      description: '脈衝'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">動畫變體</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊按鈕查看不同的動畫效果</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {variants.map(variant => <button key={variant.name} onClick={() => setActiveVariant(variant.name)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              {variant.label}
            </button>)}
        </div>
        
        {/* 動畫展示區域 */}
        <div className="bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[300px] flex items-center justify-center">
          <AnimatePresence mode="wait">
            {activeVariant && <motion.div key={activeVariant} variants={getSpringVariants(activeVariant, 'default')} initial="initial" animate="animate" exit="exit" className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl">
                <h3 className="text-2xl font-bold mb-2">
                  {variants.find(v => v.name === activeVariant)?.label}
                </h3>
                <p className="text-blue-100">
                  {variants.find(v => v.name === activeVariant)?.description}
                </p>
              </motion.div>}
          </AnimatePresence>
        </div>
      </div>;
  }
}`,...(Ae=(Pe=N.parameters)==null?void 0:Pe.docs)==null?void 0:Ae.source}}};var He,Te,Ee;k.parameters={...k.parameters,docs:{...(He=k.parameters)==null?void 0:He.docs,source:{originalSource:`{
  render: () => {
    const haptics = [{
      type: 'light',
      label: 'Light',
      description: '輕微',
      color: 'bg-gray-500'
    }, {
      type: 'medium',
      label: 'Medium',
      description: '中等',
      color: 'bg-blue-500'
    }, {
      type: 'heavy',
      label: 'Heavy',
      description: '重度',
      color: 'bg-purple-500'
    }, {
      type: 'success',
      label: 'Success',
      description: '成功',
      color: 'bg-green-500'
    }, {
      type: 'warning',
      label: 'Warning',
      description: '警告',
      color: 'bg-yellow-500'
    }, {
      type: 'error',
      label: 'Error',
      description: '錯誤',
      color: 'bg-red-500'
    }, {
      type: 'selection',
      label: 'Selection',
      description: '選擇',
      color: 'bg-indigo-500'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">觸覺反饋模擬</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊按鈕體驗不同強度的觸覺反饋</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {haptics.map(haptic => <motion.button key={haptic.type} onClick={e => triggerHaptic(e.currentTarget, haptic.type as any)} whileHover={{
          scale: 1.05
        }} whileTap={getHapticAnimation(haptic.type as any)} className={\`\${haptic.color} text-white p-6 rounded-xl shadow-md\`}>
              <h3 className="text-lg font-semibold mb-1">{haptic.label}</h3>
              <p className="text-sm opacity-90">{haptic.description}</p>
            </motion.button>)}
        </div>
        
        {/* CSS 類名範例 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 類名範例</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {haptics.map(haptic => <button key={\`css-\${haptic.type}\`} className={\`haptic-\${haptic.type} \${haptic.color} text-white px-4 py-3 rounded-lg\`}>
                .haptic-{haptic.type}
              </button>)}
          </div>
        </div>
      </div>;
  }
}`,...(Ee=(Te=k.parameters)==null?void 0:Te.docs)==null?void 0:Ee.source}}};var Me,Re,Oe;S.parameters={...S.parameters,docs:{...(Me=S.parameters)==null?void 0:Me.docs,source:{originalSource:`{
  render: () => {
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">按鈕互動</h2>
          <p className="text-gray-600 dark:text-gray-400">Apple 風格的按鈕按壓效果</p>
        </div>
        
        {/* Framer Motion 按鈕 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">Framer Motion 按鈕</h3>
          <div className="flex flex-wrap gap-4">
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('snappy')} onClick={e => triggerHaptic(e.currentTarget, 'medium')} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
              Primary Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('bouncy')} onClick={e => triggerHaptic(e.currentTarget, 'success')} className="px-6 py-3 bg-green-600 text-white rounded-lg shadow-md">
              Success Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('default')} onClick={e => triggerHaptic(e.currentTarget, 'warning')} className="px-6 py-3 bg-yellow-600 text-white rounded-lg shadow-md">
              Warning Button
            </motion.button>
            
            <motion.button whileHover={{
            scale: 1.05
          }} whileTap={{
            scale: 0.95
          }} transition={getSpringConfig('wobbly')} onClick={e => triggerHaptic(e.currentTarget, 'error')} className="px-6 py-3 bg-red-600 text-white rounded-lg shadow-md">
              Error Button
            </motion.button>
          </div>
        </div>
        
        {/* CSS 類名按鈕 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 類名按鈕</h3>
          <div className="flex flex-wrap gap-4">
            <button className="btn-spring-press px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
              Standard Press
            </button>
            
            <button className="btn-spring-press-heavy px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md">
              Heavy Press
            </button>
            
            <button className="spring-hover-lift px-6 py-3 bg-indigo-600 text-white rounded-lg shadow-md">
              Hover Lift
            </button>
            
            <button className="spring-hover-scale px-6 py-3 bg-pink-600 text-white rounded-lg shadow-md">
              Hover Scale
            </button>
          </div>
        </div>
      </div>;
  }
}`,...(Oe=(Re=S.parameters)==null?void 0:Re.docs)==null?void 0:Oe.source}}};var Fe,Ve,Ie;j.parameters={...j.parameters,docs:{...(Fe=j.parameters)==null?void 0:Fe.docs,source:{originalSource:`{
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">模態對話框動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">iOS 風格的 Sheet 動畫</p>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setIsOpen(true)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          打開 Modal
        </motion.button>
        
        <AnimatePresence>
          {isOpen && <>
              {/* 背景遮罩 */}
              <motion.div initial={{
            opacity: 0
          }} animate={{
            opacity: 1
          }} exit={{
            opacity: 0
          }} onClick={() => setIsOpen(false)} className="fixed inset-0 bg-black/40 z-40" />
              
              {/* 對話框 */}
              <motion.div variants={getSpringVariants('slideUp', 'default')} initial="initial" animate="animate" exit="exit" className="fixed inset-x-4 bottom-4 bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-2xl z-50 max-w-md mx-auto">
                <h3 className="text-xl font-bold mb-4">iOS 風格 Sheet</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  這是一個使用彈性動畫的模態對話框，模擬 iOS 的 Sheet 效果。
                </p>
                <motion.button whileHover={{
              scale: 1.05
            }} whileTap={{
              scale: 0.95
            }} transition={getSpringConfig('snappy')} onClick={() => setIsOpen(false)} className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
                  關閉
                </motion.button>
              </motion.div>
            </>}
        </AnimatePresence>
      </div>;
  }
}`,...(Ie=(Ve=j.parameters)==null?void 0:Ve.docs)==null?void 0:Ie.source}}};var Le,$e,De;C.parameters={...C.parameters,docs:{...(Le=C.parameters)==null?void 0:Le.docs,source:{originalSource:`{
  render: () => {
    const [show, setShow] = useState(true);
    const items = [{
      id: 1,
      title: '項目 1',
      description: '這是第一個項目'
    }, {
      id: 2,
      title: '項目 2',
      description: '這是第二個項目'
    }, {
      id: 3,
      title: '項目 3',
      description: '這是第三個項目'
    }, {
      id: 4,
      title: '項目 4',
      description: '這是第四個項目'
    }, {
      id: 5,
      title: '項目 5',
      description: '這是第五個項目'
    }];
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">列表交錯動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">子元素依序出現的動畫效果</p>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setShow(!show)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          {show ? '隱藏' : '顯示'}列表
        </motion.button>
        
        <AnimatePresence>
          {show && <motion.div variants={{
          animate: {
            transition: getStaggerConfig('default', 0.08)
          }
        }} initial="initial" animate="animate" exit="exit" className="space-y-4">
              {items.map(item => <motion.div key={item.id} variants={getSpringVariants('slideUp', 'default')} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
                  <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                  <p className="text-gray-600 dark:text-gray-400">{item.description}</p>
                </motion.div>)}
            </motion.div>}
        </AnimatePresence>
        
        {/* CSS 交錯動畫 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 交錯動畫</h3>
          <div className="stagger-children space-y-4">
            {items.map(item => <div key={item.id} className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 className="font-semibold">{item.title}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">{item.description}</p>
              </div>)}
          </div>
        </div>
      </div>;
  }
}`,...(De=($e=C.parameters)==null?void 0:$e.docs)==null?void 0:De.source}}};var Be,Ue,ze;P.parameters={...P.parameters,docs:{...(Be=P.parameters)==null?void 0:Be.docs,source:{originalSource:`{
  render: () => {
    const [showSuccess, setShowSuccess] = useState(false);
    const [showError, setShowError] = useState(false);
    const successRef = useRef<HTMLDivElement>(null);
    const errorRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
      if (showSuccess && successRef.current) {
        triggerHaptic(successRef.current, 'success');
      }
    }, [showSuccess]);
    useEffect(() => {
      if (showError && errorRef.current) {
        triggerHaptic(errorRef.current, 'error');
      }
    }, [showError]);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">成功/錯誤反饋</h2>
          <p className="text-gray-600 dark:text-gray-400">帶有觸覺反饋的狀態提示</p>
        </div>
        
        <div className="flex gap-4">
          <motion.button whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={() => {
          setShowSuccess(true);
          setTimeout(() => setShowSuccess(false), 3000);
        }} className="px-6 py-3 bg-green-600 text-white rounded-lg shadow-md">
            顯示成功
          </motion.button>
          
          <motion.button whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={() => {
          setShowError(true);
          setTimeout(() => setShowError(false), 3000);
        }} className="px-6 py-3 bg-red-600 text-white rounded-lg shadow-md">
            顯示錯誤
          </motion.button>
        </div>
        
        <div className="space-y-4">
          <AnimatePresence>
            {showSuccess && <motion.div ref={successRef} variants={getSpringVariants('bounce', 'bouncy')} initial="initial" animate="animate" exit="exit" className="bg-green-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3">
                <div className="text-2xl">✓</div>
                <div>
                  <h3 className="font-semibold">操作成功！</h3>
                  <p className="text-sm opacity-90">您的更改已保存</p>
                </div>
              </motion.div>}
          </AnimatePresence>
          
          <AnimatePresence>
            {showError && <motion.div ref={errorRef} variants={getSpringVariants('shake', 'wobbly')} initial="initial" animate="animate" exit="exit" className="bg-red-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3">
                <div className="text-2xl">✗</div>
                <div>
                  <h3 className="font-semibold">操作失敗！</h3>
                  <p className="text-sm opacity-90">請稍後再試</p>
                </div>
              </motion.div>}
          </AnimatePresence>
        </div>
      </div>;
  }
}`,...(ze=(Ue=P.parameters)==null?void 0:Ue.docs)==null?void 0:ze.source}}};var We,Ke,Ge;A.parameters={...A.parameters,docs:{...(We=A.parameters)==null?void 0:We.docs,source:{originalSource:`{
  render: () => {
    const [context, setContext] = useState(getUserContext());
    const [animationKey, setAnimationKey] = useState(0);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">上下文感知動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">根據用戶環境自動調整動畫</p>
        </div>
        
        {/* 當前上下文 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">當前上下文</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">設備類型：</span>
              <span className="font-semibold ml-2">{context.isMobile ? '移動設備' : '桌面設備'}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">低電量模式：</span>
              <span className="font-semibold ml-2">{context.isLowPower ? '是' : '否'}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">網絡速度：</span>
              <span className="font-semibold ml-2">{context.connectionSpeed}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">用戶偏好：</span>
              <span className="font-semibold ml-2">{context.userPreference}</span>
            </div>
          </div>
        </div>
        
        {/* 動畫展示 */}
        <div className="bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[200px] flex items-center justify-center">
          <motion.div key={animationKey} {...getContextualAnimation('slideUp', context)} initial="initial" animate="animate" className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl">
            <h3 className="text-2xl font-bold">上下文感知動畫</h3>
            <p className="text-blue-100 mt-2">根據您的環境自動調整</p>
          </motion.div>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={() => setAnimationKey(k => k + 1)} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
          重新播放動畫
        </motion.button>
      </div>;
  }
}`,...(Ge=(Ke=A.parameters)==null?void 0:Ke.docs)==null?void 0:Ge.source}}};var _e,Xe,qe;H.parameters={...H.parameters,docs:{...(_e=H.parameters)==null?void 0:_e.docs,source:{originalSource:`{
  render: () => {
    const [metrics, setMetrics] = useState(getAnimationMetrics());
    const [isAnimating, setIsAnimating] = useState(false);
    const startAnimation = () => {
      setIsAnimating(true);
      trackAnimation('demo-animation');
      setTimeout(() => {
        setIsAnimating(false);
        setMetrics(getAnimationMetrics());
      }, 1000);
    };
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">性能監控</h2>
          <p className="text-gray-600 dark:text-gray-400">追蹤動畫性能指標</p>
        </div>
        
        {/* 性能指標 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-blue-600">{metrics.totalAnimations}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">總動畫數</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-green-600">{metrics.activeAnimations}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">活躍動畫</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-yellow-600">{metrics.droppedFrames}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">掉幀數</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-purple-600">{metrics.averageFPS.toFixed(1)}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">平均 FPS</div>
          </div>
        </div>
        
        <motion.button whileHover={{
        scale: 1.05
      }} whileTap={{
        scale: 0.95
      }} transition={getSpringConfig('snappy')} onClick={startAnimation} disabled={isAnimating} className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md disabled:opacity-50">
          {isAnimating ? '動畫中...' : '開始動畫'}
        </motion.button>
        
        {/* 性能建議 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">性能建議</h3>
          <div className="space-y-2 text-sm">
            {metrics.averageFPS < 55 && <div className="text-red-600 dark:text-red-400">
                ⚠️ 平均 FPS 低於 55，建議降級到更簡單的動畫
              </div>}
            {metrics.activeAnimations > 5 && <div className="text-yellow-600 dark:text-yellow-400">
                ⚠️ 同時活躍動畫過多，可能影響性能
              </div>}
            {metrics.droppedFrames > 10 && <div className="text-orange-600 dark:text-orange-400">
                ⚠️ 掉幀數較多，建議優化動畫
              </div>}
            {metrics.averageFPS >= 55 && metrics.activeAnimations <= 5 && metrics.droppedFrames <= 10 && <div className="text-green-600 dark:text-green-400">
                ✓ 性能良好，動畫流暢
              </div>}
          </div>
        </div>
      </div>;
  }
}`,...(qe=(Xe=H.parameters)==null?void 0:Xe.docs)==null?void 0:qe.source}}};var Je,Qe,Ye;T.parameters={...T.parameters,docs:{...(Je=T.parameters)==null?void 0:Je.docs,source:{originalSource:`{
  render: () => {
    const [isCardOpen, setIsCardOpen] = useState(false);
    return <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">完整演示</h2>
          <p className="text-gray-600 dark:text-gray-400">綜合展示彈性動畫系統的各種功能</p>
        </div>
        
        {/* 互動卡片 */}
        <motion.div layout onClick={() => setIsCardOpen(!isCardOpen)} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md cursor-pointer" whileHover={{
        scale: 1.02
      }} transition={getSpringConfig('default')}>
          <motion.h3 layout="position" className="text-xl font-bold mb-2">
            互動卡片
          </motion.h3>
          <motion.p layout="position" className="text-gray-600 dark:text-gray-400">
            點擊展開查看更多內容
          </motion.p>
          
          <AnimatePresence>
            {isCardOpen && <motion.div initial={{
            opacity: 0,
            height: 0
          }} animate={{
            opacity: 1,
            height: 'auto'
          }} exit={{
            opacity: 0,
            height: 0
          }} transition={getSpringConfig('default')} className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  這是展開的內容區域，使用了彈性動畫來創造流暢的展開效果。
                </p>
                <div className="flex gap-2">
                  <motion.button whileHover={{
                scale: 1.05
              }} whileTap={{
                scale: 0.95
              }} transition={getSpringConfig('snappy')} onClick={e => {
                e.stopPropagation();
                triggerHaptic(e.currentTarget, 'success');
              }} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm">
                    確認
                  </motion.button>
                  <motion.button whileHover={{
                scale: 1.05
              }} whileTap={{
                scale: 0.95
              }} transition={getSpringConfig('snappy')} onClick={e => {
                e.stopPropagation();
                setIsCardOpen(false);
              }} className="px-4 py-2 bg-gray-600 text-white rounded-lg text-sm">
                    取消
                  </motion.button>
                </div>
              </motion.div>}
          </AnimatePresence>
        </motion.div>
        
        {/* 功能按鈕組 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {['Primary', 'Success', 'Warning', 'Error'].map((type, i) => <motion.button key={type} whileHover={{
          scale: 1.05
        }} whileTap={{
          scale: 0.95
        }} transition={getSpringConfig('snappy')} onClick={e => {
          const hapticType = ['medium', 'success', 'warning', 'error'][i];
          triggerHaptic(e.currentTarget, hapticType as any);
        }} className={\`px-6 py-3 text-white rounded-lg shadow-md \${['bg-blue-600', 'bg-green-600', 'bg-yellow-600', 'bg-red-600'][i]}\`}>
              {type}
            </motion.button>)}
        </div>
      </div>;
  }
}`,...(Ye=(Qe=T.parameters)==null?void 0:Qe.docs)==null?void 0:Ye.source}}};const jt=["SpringPresets","AnimationVariants","HapticFeedback","ButtonInteractions","ModalAnimations","ListStaggerAnimation","FeedbackAnimations","ContextualAnimations","PerformanceMonitoring","CompleteDemo"];export{N as AnimationVariants,S as ButtonInteractions,T as CompleteDemo,A as ContextualAnimations,P as FeedbackAnimations,k as HapticFeedback,C as ListStaggerAnimation,j as ModalAnimations,H as PerformanceMonitoring,f as SpringPresets,jt as __namedExportsOrder,St as default};
