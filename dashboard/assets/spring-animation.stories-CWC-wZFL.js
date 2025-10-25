import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as l}from"./storybook-vendor-CPzy2iGn.js";import{m as i,g as n,s as Te,a as f,b as Oe,t as c,c as Fe,d as Ee,e as Me,f as k,h as Re}from"./spring-animation-BTWXT2NA.js";import{A as N}from"./index-ppjL1wy9.js";import"./react-vendor-Bzgz95E1.js";const Ue={title:"Design System/Spring Animation System",parameters:{layout:"padded",docs:{description:{component:"Apple-level spring animation system with haptic feedback simulation and contextual animations."}}}},m={render:()=>{const[a,s]=l.useState(null),r=[{name:"gentle",label:"Gentle",description:"溫和的彈性動畫",color:"bg-blue-100 dark:bg-blue-900"},{name:"default",label:"Default",description:"標準 iOS 動畫（推薦）",color:"bg-green-100 dark:bg-green-900"},{name:"bouncy",label:"Bouncy",description:"活潑、有趣的彈性",color:"bg-purple-100 dark:bg-purple-900"},{name:"snappy",label:"Snappy",description:"快速、響應式",color:"bg-orange-100 dark:bg-orange-900"},{name:"smooth",label:"Smooth",description:"優雅、流暢",color:"bg-pink-100 dark:bg-pink-900"},{name:"wobbly",label:"Wobbly",description:"誇張的彈性效果",color:"bg-yellow-100 dark:bg-yellow-900"}];return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"6 種彈性預設"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"點擊查看不同彈性動畫的效果"})]}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-3 gap-6",children:r.map(t=>e.jsxs(i.button,{onClick:()=>s(t.name),whileHover:{scale:1.05},whileTap:{scale:.95},transition:n(t.name),className:`${t.color} p-6 rounded-xl shadow-md text-left relative overflow-hidden`,children:[e.jsxs("div",{className:"relative z-10",children:[e.jsx("h3",{className:"text-lg font-semibold mb-1",children:t.label}),e.jsx("p",{className:"text-sm text-gray-600 dark:text-gray-300",children:t.description})]}),e.jsx(N,{children:a===t.name&&e.jsx(i.div,{initial:{scale:0,opacity:0},animate:{scale:1,opacity:1},exit:{scale:0,opacity:0},transition:n(t.name),className:"absolute inset-0 bg-white/20 dark:bg-black/20"})})]},t.name))}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"技術參數"}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-3 gap-4",children:Object.entries(Te).map(([t,o])=>e.jsxs("div",{className:"p-4 bg-gray-50 dark:bg-gray-700 rounded-lg",children:[e.jsx("h4",{className:"font-semibold capitalize mb-2",children:t}),e.jsxs("div",{className:"text-sm space-y-1 text-gray-600 dark:text-gray-300",children:[e.jsxs("div",{children:["Stiffness: ",o.stiffness]}),e.jsxs("div",{children:["Damping: ",o.damping]}),e.jsxs("div",{children:["Mass: ",o.mass]}),e.jsxs("div",{children:["Duration: ",o.duration,"s"]})]})]},t))})]})]})}},g={render:()=>{var t,o;const[a,s]=l.useState(null),r=[{name:"fade",label:"Fade",description:"淡入淡出"},{name:"scale",label:"Scale",description:"縮放"},{name:"pop",label:"Pop",description:"彈出"},{name:"bounce",label:"Bounce",description:"彈跳"},{name:"slideUp",label:"Slide Up",description:"向上滑動"},{name:"slideDown",label:"Slide Down",description:"向下滑動"},{name:"slideLeft",label:"Slide Left",description:"向左滑動"},{name:"slideRight",label:"Slide Right",description:"向右滑動"},{name:"shake",label:"Shake",description:"搖晃"},{name:"pulse",label:"Pulse",description:"脈衝"}];return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"動畫變體"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"點擊按鈕查看不同的動畫效果"})]}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-5 gap-4",children:r.map(d=>e.jsx("button",{onClick:()=>s(d.name),className:"px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors",children:d.label},d.name))}),e.jsx("div",{className:"bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[300px] flex items-center justify-center",children:e.jsx(N,{mode:"wait",children:a&&e.jsxs(i.div,{variants:f(a,"default"),initial:"initial",animate:"animate",exit:"exit",className:"bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl",children:[e.jsx("h3",{className:"text-2xl font-bold mb-2",children:(t=r.find(d=>d.name===a))==null?void 0:t.label}),e.jsx("p",{className:"text-blue-100",children:(o=r.find(d=>d.name===a))==null?void 0:o.description})]},a)})})]})}},p={render:()=>{const a=[{type:"light",label:"Light",description:"輕微",color:"bg-gray-500"},{type:"medium",label:"Medium",description:"中等",color:"bg-blue-500"},{type:"heavy",label:"Heavy",description:"重度",color:"bg-purple-500"},{type:"success",label:"Success",description:"成功",color:"bg-green-500"},{type:"warning",label:"Warning",description:"警告",color:"bg-yellow-500"},{type:"error",label:"Error",description:"錯誤",color:"bg-red-500"},{type:"selection",label:"Selection",description:"選擇",color:"bg-indigo-500"}];return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"觸覺反饋模擬"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"點擊按鈕體驗不同強度的觸覺反饋"})]}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-6",children:a.map(s=>e.jsxs(i.button,{onClick:r=>c(r.currentTarget,s.type),whileHover:{scale:1.05},whileTap:Oe(s.type),className:`${s.color} text-white p-6 rounded-xl shadow-md`,children:[e.jsx("h3",{className:"text-lg font-semibold mb-1",children:s.label}),e.jsx("p",{className:"text-sm opacity-90",children:s.description})]},s.type))}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"CSS 類名範例"}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-4",children:a.map(s=>e.jsxs("button",{className:`haptic-${s.type} ${s.color} text-white px-4 py-3 rounded-lg`,children:[".haptic-",s.type]},`css-${s.type}`))})]})]})}},x={render:()=>e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"按鈕互動"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"Apple 風格的按鈕按壓效果"})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"Framer Motion 按鈕"}),e.jsxs("div",{className:"flex flex-wrap gap-4",children:[e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("snappy"),onClick:a=>c(a.currentTarget,"medium"),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"Primary Button"}),e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("bouncy"),onClick:a=>c(a.currentTarget,"success"),className:"px-6 py-3 bg-green-600 text-white rounded-lg shadow-md",children:"Success Button"}),e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("default"),onClick:a=>c(a.currentTarget,"warning"),className:"px-6 py-3 bg-yellow-600 text-white rounded-lg shadow-md",children:"Warning Button"}),e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("wobbly"),onClick:a=>c(a.currentTarget,"error"),className:"px-6 py-3 bg-red-600 text-white rounded-lg shadow-md",children:"Error Button"})]})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"CSS 類名按鈕"}),e.jsxs("div",{className:"flex flex-wrap gap-4",children:[e.jsx("button",{className:"btn-spring-press px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"Standard Press"}),e.jsx("button",{className:"btn-spring-press-heavy px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md",children:"Heavy Press"}),e.jsx("button",{className:"spring-hover-lift px-6 py-3 bg-indigo-600 text-white rounded-lg shadow-md",children:"Hover Lift"}),e.jsx("button",{className:"spring-hover-scale px-6 py-3 bg-pink-600 text-white rounded-lg shadow-md",children:"Hover Scale"})]})]})]})},b={render:()=>{const[a,s]=l.useState(!1);return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"模態對話框動畫"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"iOS 風格的 Sheet 動畫"})]}),e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("snappy"),onClick:()=>s(!0),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"打開 Modal"}),e.jsx(N,{children:a&&e.jsxs(e.Fragment,{children:[e.jsx(i.div,{initial:{opacity:0},animate:{opacity:1},exit:{opacity:0},onClick:()=>s(!1),className:"fixed inset-0 bg-black/40 z-40"}),e.jsxs(i.div,{variants:f("slideUp","default"),initial:"initial",animate:"animate",exit:"exit",className:"fixed inset-x-4 bottom-4 bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-2xl z-50 max-w-md mx-auto",children:[e.jsx("h3",{className:"text-xl font-bold mb-4",children:"iOS 風格 Sheet"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400 mb-6",children:"這是一個使用彈性動畫的模態對話框，模擬 iOS 的 Sheet 效果。"}),e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("snappy"),onClick:()=>s(!1),className:"w-full px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"關閉"})]})]})})]})}},h={render:()=>{const[a,s]=l.useState(!0),r=[{id:1,title:"項目 1",description:"這是第一個項目"},{id:2,title:"項目 2",description:"這是第二個項目"},{id:3,title:"項目 3",description:"這是第三個項目"},{id:4,title:"項目 4",description:"這是第四個項目"},{id:5,title:"項目 5",description:"這是第五個項目"}];return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"列表交錯動畫"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"子元素依序出現的動畫效果"})]}),e.jsxs(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("snappy"),onClick:()=>s(!a),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:[a?"隱藏":"顯示","列表"]}),e.jsx(N,{children:a&&e.jsx(i.div,{variants:{animate:{transition:Fe("default",.08)}},initial:"initial",animate:"animate",exit:"exit",className:"space-y-4",children:r.map(t=>e.jsxs(i.div,{variants:f("slideUp","default"),className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-2",children:t.title}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:t.description})]},t.id))})}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"CSS 交錯動畫"}),e.jsx("div",{className:"stagger-children space-y-4",children:r.map(t=>e.jsxs("div",{className:"bg-gray-50 dark:bg-gray-700 p-4 rounded-lg",children:[e.jsx("h4",{className:"font-semibold",children:t.title}),e.jsx("p",{className:"text-sm text-gray-600 dark:text-gray-300",children:t.description})]},t.id))})]})]})}},u={render:()=>{const[a,s]=l.useState(!1),[r,t]=l.useState(!1),o=l.useRef(null),d=l.useRef(null);return l.useEffect(()=>{a&&o.current&&c(o.current,"success")},[a]),l.useEffect(()=>{r&&d.current&&c(d.current,"error")},[r]),e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"成功/錯誤反饋"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"帶有觸覺反饋的狀態提示"})]}),e.jsxs("div",{className:"flex gap-4",children:[e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("snappy"),onClick:()=>{s(!0),setTimeout(()=>s(!1),3e3)},className:"px-6 py-3 bg-green-600 text-white rounded-lg shadow-md",children:"顯示成功"}),e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("snappy"),onClick:()=>{t(!0),setTimeout(()=>t(!1),3e3)},className:"px-6 py-3 bg-red-600 text-white rounded-lg shadow-md",children:"顯示錯誤"})]}),e.jsxs("div",{className:"space-y-4",children:[e.jsx(N,{children:a&&e.jsxs(i.div,{ref:o,variants:f("bounce","bouncy"),initial:"initial",animate:"animate",exit:"exit",className:"bg-green-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3",children:[e.jsx("div",{className:"text-2xl",children:"✓"}),e.jsxs("div",{children:[e.jsx("h3",{className:"font-semibold",children:"操作成功！"}),e.jsx("p",{className:"text-sm opacity-90",children:"您的更改已保存"})]})]})}),e.jsx(N,{children:r&&e.jsxs(i.div,{ref:d,variants:f("shake","wobbly"),initial:"initial",animate:"animate",exit:"exit",className:"bg-red-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3",children:[e.jsx("div",{className:"text-2xl",children:"✗"}),e.jsxs("div",{children:[e.jsx("h3",{className:"font-semibold",children:"操作失敗！"}),e.jsx("p",{className:"text-sm opacity-90",children:"請稍後再試"})]})]})})]})]})}},y={render:()=>{const[a,s]=l.useState(Ee()),[r,t]=l.useState(0);return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"上下文感知動畫"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"根據用戶環境自動調整動畫"})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"當前上下文"}),e.jsxs("div",{className:"grid grid-cols-2 gap-4 text-sm",children:[e.jsxs("div",{children:[e.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"設備類型："}),e.jsx("span",{className:"font-semibold ml-2",children:a.isMobile?"移動設備":"桌面設備"})]}),e.jsxs("div",{children:[e.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"低電量模式："}),e.jsx("span",{className:"font-semibold ml-2",children:a.isLowPower?"是":"否"})]}),e.jsxs("div",{children:[e.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"網絡速度："}),e.jsx("span",{className:"font-semibold ml-2",children:a.connectionSpeed})]}),e.jsxs("div",{children:[e.jsx("span",{className:"text-gray-600 dark:text-gray-400",children:"用戶偏好："}),e.jsx("span",{className:"font-semibold ml-2",children:a.userPreference})]})]})]}),e.jsx("div",{className:"bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[200px] flex items-center justify-center",children:e.jsxs(i.div,{...Me("slideUp",a),initial:"initial",animate:"animate",className:"bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl",children:[e.jsx("h3",{className:"text-2xl font-bold",children:"上下文感知動畫"}),e.jsx("p",{className:"text-blue-100 mt-2",children:"根據您的環境自動調整"})]},r)}),e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("snappy"),onClick:()=>t(o=>o+1),className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md",children:"重新播放動畫"})]})}},v={render:()=>{const[a,s]=l.useState(k()),[r,t]=l.useState(!1),o=()=>{t(!0),Re(),setTimeout(()=>{t(!1),s(k())},1e3)};return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"性能監控"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"追蹤動畫性能指標"})]}),e.jsxs("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-4",children:[e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("div",{className:"text-3xl font-bold text-blue-600",children:a.totalAnimations}),e.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"總動畫數"})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("div",{className:"text-3xl font-bold text-green-600",children:a.activeAnimations}),e.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"活躍動畫"})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("div",{className:"text-3xl font-bold text-yellow-600",children:a.droppedFrames}),e.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"掉幀數"})]}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("div",{className:"text-3xl font-bold text-purple-600",children:a.averageFPS.toFixed(1)}),e.jsx("div",{className:"text-sm text-gray-600 dark:text-gray-400 mt-1",children:"平均 FPS"})]})]}),e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("snappy"),onClick:o,disabled:r,className:"px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md disabled:opacity-50",children:r?"動畫中...":"開始動畫"}),e.jsxs("div",{className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md",children:[e.jsx("h3",{className:"text-lg font-semibold mb-4",children:"性能建議"}),e.jsxs("div",{className:"space-y-2 text-sm",children:[a.averageFPS<55&&e.jsx("div",{className:"text-red-600 dark:text-red-400",children:"⚠️ 平均 FPS 低於 55，建議降級到更簡單的動畫"}),a.activeAnimations>5&&e.jsx("div",{className:"text-yellow-600 dark:text-yellow-400",children:"⚠️ 同時活躍動畫過多，可能影響性能"}),a.droppedFrames>10&&e.jsx("div",{className:"text-orange-600 dark:text-orange-400",children:"⚠️ 掉幀數較多，建議優化動畫"}),a.averageFPS>=55&&a.activeAnimations<=5&&a.droppedFrames<=10&&e.jsx("div",{className:"text-green-600 dark:text-green-400",children:"✓ 性能良好，動畫流暢"})]})]})]})}},w={render:()=>{const[a,s]=l.useState(!1);return e.jsxs("div",{className:"space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl",children:[e.jsxs("div",{children:[e.jsx("h2",{className:"text-2xl font-bold mb-2",children:"完整演示"}),e.jsx("p",{className:"text-gray-600 dark:text-gray-400",children:"綜合展示彈性動畫系統的各種功能"})]}),e.jsxs(i.div,{layout:!0,onClick:()=>s(!a),className:"bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md cursor-pointer",whileHover:{scale:1.02},transition:n("default"),children:[e.jsx(i.h3,{layout:"position",className:"text-xl font-bold mb-2",children:"互動卡片"}),e.jsx(i.p,{layout:"position",className:"text-gray-600 dark:text-gray-400",children:"點擊展開查看更多內容"}),e.jsx(N,{children:a&&e.jsxs(i.div,{initial:{opacity:0,height:0},animate:{opacity:1,height:"auto"},exit:{opacity:0,height:0},transition:n("default"),className:"mt-4 pt-4 border-t border-gray-200 dark:border-gray-700",children:[e.jsx("p",{className:"text-gray-600 dark:text-gray-400 mb-4",children:"這是展開的內容區域，使用了彈性動畫來創造流暢的展開效果。"}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("snappy"),onClick:r=>{r.stopPropagation(),c(r.currentTarget,"success")},className:"px-4 py-2 bg-green-600 text-white rounded-lg text-sm",children:"確認"}),e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("snappy"),onClick:r=>{r.stopPropagation(),s(!1)},className:"px-4 py-2 bg-gray-600 text-white rounded-lg text-sm",children:"取消"})]})]})})]}),e.jsx("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-4",children:["Primary","Success","Warning","Error"].map((r,t)=>e.jsx(i.button,{whileHover:{scale:1.05},whileTap:{scale:.95},transition:n("snappy"),onClick:o=>{const d=["medium","success","warning","error"][t];c(o.currentTarget,d)},className:`px-6 py-3 text-white rounded-lg shadow-md ${["bg-blue-600","bg-green-600","bg-yellow-600","bg-red-600"][t]}`,children:r},r))})]})}};var S,j,C;m.parameters={...m.parameters,docs:{...(S=m.parameters)==null?void 0:S.docs,source:{originalSource:`{
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
}`,...(C=(j=m.parameters)==null?void 0:j.docs)==null?void 0:C.source}}};var A,P,H;g.parameters={...g.parameters,docs:{...(A=g.parameters)==null?void 0:A.docs,source:{originalSource:`{
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
}`,...(H=(P=g.parameters)==null?void 0:P.docs)==null?void 0:H.source}}};var T,O,F;p.parameters={...p.parameters,docs:{...(T=p.parameters)==null?void 0:T.docs,source:{originalSource:`{
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
}`,...(F=(O=p.parameters)==null?void 0:O.docs)==null?void 0:F.source}}};var E,M,R;x.parameters={...x.parameters,docs:{...(E=x.parameters)==null?void 0:E.docs,source:{originalSource:`{
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
}`,...(R=(M=x.parameters)==null?void 0:M.docs)==null?void 0:R.source}}};var V,I,D;b.parameters={...b.parameters,docs:{...(V=b.parameters)==null?void 0:V.docs,source:{originalSource:`{
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
}`,...(D=(I=b.parameters)==null?void 0:I.docs)==null?void 0:D.source}}};var L,B,U;h.parameters={...h.parameters,docs:{...(L=h.parameters)==null?void 0:L.docs,source:{originalSource:`{
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
}`,...(U=(B=h.parameters)==null?void 0:B.docs)==null?void 0:U.source}}};var $,z,W;u.parameters={...u.parameters,docs:{...($=u.parameters)==null?void 0:$.docs,source:{originalSource:`{
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
}`,...(W=(z=u.parameters)==null?void 0:z.docs)==null?void 0:W.source}}};var K,G,_;y.parameters={...y.parameters,docs:{...(K=y.parameters)==null?void 0:K.docs,source:{originalSource:`{
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
}`,...(_=(G=y.parameters)==null?void 0:G.docs)==null?void 0:_.source}}};var q,J,Q;v.parameters={...v.parameters,docs:{...(q=v.parameters)==null?void 0:q.docs,source:{originalSource:`{
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
}`,...(Q=(J=v.parameters)==null?void 0:J.docs)==null?void 0:Q.source}}};var X,Y,Z;w.parameters={...w.parameters,docs:{...(X=w.parameters)==null?void 0:X.docs,source:{originalSource:`{
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
}`,...(Z=(Y=w.parameters)==null?void 0:Y.docs)==null?void 0:Z.source}}};var ee,ae,te;m.parameters={...m.parameters,docs:{...(ee=m.parameters)==null?void 0:ee.docs,source:{originalSource:`{
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
}`,...(te=(ae=m.parameters)==null?void 0:ae.docs)==null?void 0:te.source}}};var se,ie,re;g.parameters={...g.parameters,docs:{...(se=g.parameters)==null?void 0:se.docs,source:{originalSource:`{
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
}`,...(re=(ie=g.parameters)==null?void 0:ie.docs)==null?void 0:re.source}}};var ne,oe,le;p.parameters={...p.parameters,docs:{...(ne=p.parameters)==null?void 0:ne.docs,source:{originalSource:`{
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
}`,...(le=(oe=p.parameters)==null?void 0:oe.docs)==null?void 0:le.source}}};var de,ce,me;x.parameters={...x.parameters,docs:{...(de=x.parameters)==null?void 0:de.docs,source:{originalSource:`{
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
}`,...(me=(ce=x.parameters)==null?void 0:ce.docs)==null?void 0:me.source}}};var ge,pe,xe;b.parameters={...b.parameters,docs:{...(ge=b.parameters)==null?void 0:ge.docs,source:{originalSource:`{
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
}`,...(xe=(pe=b.parameters)==null?void 0:pe.docs)==null?void 0:xe.source}}};var be,he,ue;h.parameters={...h.parameters,docs:{...(be=h.parameters)==null?void 0:be.docs,source:{originalSource:`{
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
}`,...(ue=(he=h.parameters)==null?void 0:he.docs)==null?void 0:ue.source}}};var ye,ve,we;u.parameters={...u.parameters,docs:{...(ye=u.parameters)==null?void 0:ye.docs,source:{originalSource:`{
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
}`,...(we=(ve=u.parameters)==null?void 0:ve.docs)==null?void 0:we.source}}};var Ne,fe,ke;y.parameters={...y.parameters,docs:{...(Ne=y.parameters)==null?void 0:Ne.docs,source:{originalSource:`{
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
}`,...(ke=(fe=y.parameters)==null?void 0:fe.docs)==null?void 0:ke.source}}};var Se,je,Ce;v.parameters={...v.parameters,docs:{...(Se=v.parameters)==null?void 0:Se.docs,source:{originalSource:`{
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
}`,...(Ce=(je=v.parameters)==null?void 0:je.docs)==null?void 0:Ce.source}}};var Ae,Pe,He;w.parameters={...w.parameters,docs:{...(Ae=w.parameters)==null?void 0:Ae.docs,source:{originalSource:`{
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
}`,...(He=(Pe=w.parameters)==null?void 0:Pe.docs)==null?void 0:He.source}}};const $e=["SpringPresets","AnimationVariants","HapticFeedback","ButtonInteractions","ModalAnimations","ListStaggerAnimation","FeedbackAnimations","ContextualAnimations","PerformanceMonitoring","CompleteDemo"];export{g as AnimationVariants,x as ButtonInteractions,w as CompleteDemo,y as ContextualAnimations,u as FeedbackAnimations,p as HapticFeedback,h as ListStaggerAnimation,b as ModalAnimations,v as PerformanceMonitoring,m as SpringPresets,$e as __namedExportsOrder,Ue as default};
