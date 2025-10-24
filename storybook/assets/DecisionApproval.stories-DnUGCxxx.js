import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as u}from"./index-DbOFzPHX.js";import{b as ne,c as de,u as me,C as x,d as h,e as pe,f as xe,g as he,B as j,M as ue}from"./chunk-NISHYRIK-CfUWBg2t.js";import{B as ge}from"./badge-BJa9me8x.js";import{L as ve}from"./label-B7R9sVpP.js";import{s as ye,T as je,D as fe,a as we,b as be,c as _e,d as Ne,e as De}from"./safeInterval-DRa5QIBP.js";import{T as Ce,D as Te,P as Se}from"./progress-C8KhyBp9.js";import{a as ke,C as k}from"./clock-p0E8112v.js";import{w as A,e as g}from"./index-BQxpGEEd.js";import"./_commonjsHelpers-Cpj98o6Y.js";import"./Combination-CEeXFs5e.js";import"./index-DQTZIOkN.js";import"./index-BQeLGKNK.js";/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ae=[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["path",{d:"m15 9-6 6",key:"1uzhvr"}],["path",{d:"m9 9 6 6",key:"z0biqf"}]],I=ne("circle-x",Ae);/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ee=[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["path",{d:"M12 16v-4",key:"1dtifu"}],["path",{d:"M12 8h.01",key:"e9boi3"}]],Be=ne("info",Ee);function re({className:r,...n}){return e.jsx("textarea",{"data-slot":"textarea",className:de("border-input placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 flex field-sizing-content min-h-16 w-full rounded-md border bg-transparent px-3 py-2 text-base shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",r),...n})}re.__docgenInfo={description:"",methods:[],displayName:"Textarea"};const Ie=()=>{const[r,n]=u.useState([]);return{toast:u.useCallback(({title:i,description:c,variant:m="default"})=>{const v=Math.random().toString(36).substr(2,9),y={id:v,title:i,description:c,variant:m,timestamp:Date.now()};return n(d=>[...d,y]),setTimeout(()=>{n(d=>d.filter(p=>p.id!==v))},5e3),{id:v,dismiss:()=>n(d=>d.filter(p=>p.id!==v))}},[]),toasts:r,dismiss:i=>n(c=>c.filter(m=>m.id!==i))}},ie=()=>{const{toast:r}=Ie(),{trackPathStart:n,trackPathComplete:l,trackPathFail:i}=me(),[c,m]=u.useState([{id:"decision_001",timestamp:"2024-01-01T14:30:00Z",strategy:{name:"CPU優化策略",description:"當CPU使用率超過85%時自動擴容並優化緩存配置",actions:[{type:"scale_up",description:"增加2個計算實例",estimated_time:"3分鐘"},{type:"optimize_cache",description:"調整緩存TTL為300秒",estimated_time:"30秒"}]},trigger:{type:"high_cpu_usage",value:92,threshold:85,duration:"5分鐘"},predicted_impact:{cpu_reduction:25,response_time_improvement:30,cost_increase:18.5,confidence:.87},risk_assessment:{level:"low",factors:["已測試策略","可回滾","低影響範圍"]},priority:"high",auto_approve_in:300},{id:"decision_002",timestamp:"2024-01-01T14:25:00Z",strategy:{name:"數據庫連接池優化",description:"調整數據庫連接池大小以應對高並發",actions:[{type:"adjust_connection_pool",description:"將連接池從50增加到80",estimated_time:"1分鐘"}]},trigger:{type:"database_connection_exhaustion",value:48,threshold:45,duration:"2分鐘"},predicted_impact:{database_performance:20,response_time_improvement:15,cost_increase:5.2,confidence:.92},risk_assessment:{level:"very_low",factors:["常規操作","即時生效","可動態調整"]},priority:"medium",auto_approve_in:600},{id:"decision_003",timestamp:"2024-01-01T14:20:00Z",strategy:{name:"緊急故障轉移",description:"檢測到主服務異常，建議切換到備用服務",actions:[{type:"failover",description:"切換到備用數據中心",estimated_time:"2分鐘"},{type:"notify_team",description:"通知運維團隊",estimated_time:"即時"}]},trigger:{type:"service_failure",value:"primary_service_down",threshold:"availability_below_99",duration:"30秒"},predicted_impact:{availability_restoration:99.9,user_impact_reduction:80,cost_increase:50,confidence:.95},risk_assessment:{level:"medium",factors:["緊急操作","影響用戶","需要監控"]},priority:"critical",auto_approve_in:120}]),[v,y]=u.useState(null),[d,p]=u.useState("");u.useEffect(()=>ye(()=>{m(s=>s.map(a=>({...a,auto_approve_in:Math.max(0,a.auto_approve_in-1)})))},1e3,120),[]);const E=async(t,s="")=>{const a=n("decision_approve");try{await new Promise(o=>setTimeout(o,1e3)),m(o=>o.filter(S=>S.id!==t)),l(a),r({title:"決策已批准",description:"策略將立即執行",variant:"default"}),window.dispatchEvent(new CustomEvent("first-value-operation",{detail:{operation:"decision_approve"}})),y(null),p("")}catch(o){i(a,o),r({title:"批准失敗",description:"請稍後重試",variant:"destructive"})}},B=async(t,s)=>{if(!s.trim()){r({title:"請提供拒絕理由",description:"拒絕決策時必須說明原因",variant:"destructive"});return}const a=n("decision_reject");try{await new Promise(o=>setTimeout(o,1e3)),m(o=>o.filter(S=>S.id!==t)),l(a),r({title:"決策已拒絕",description:"系統將尋找替代方案",variant:"default"}),window.dispatchEvent(new CustomEvent("first-value-operation",{detail:{operation:"decision_reject"}})),y(null),p("")}catch(o){i(a,o),r({title:"拒絕失敗",description:"請稍後重試",variant:"destructive"})}},ce=t=>{switch(t){case"critical":return"bg-red-100 text-red-800 border-red-200";case"high":return"bg-orange-100 text-orange-800 border-orange-200";case"medium":return"bg-yellow-100 text-yellow-800 border-yellow-200";case"low":return"bg-green-100 text-green-800 border-green-200";default:return"bg-gray-100 text-gray-800 border-gray-200"}},oe=t=>{switch(t){case"very_low":return"text-green-600";case"low":return"text-green-500";case"medium":return"text-yellow-500";case"high":return"text-red-500";case"very_high":return"text-red-600";default:return"text-gray-500"}},le=t=>{const s=Math.floor(t/60),a=t%60;return`${s}:${a.toString().padStart(2,"0")}`};return e.jsxs("div",{className:"p-6 space-y-6",children:[e.jsxs("div",{children:[e.jsx("h1",{className:"text-3xl font-bold text-gray-900",children:"決策審批中心"}),e.jsx("p",{className:"text-gray-600 mt-2",children:"審核AI系統提出的決策建議，確保系統安全穩定運行"})]}),e.jsxs("div",{className:"grid grid-cols-1 md:grid-cols-4 gap-4",children:[e.jsx(x,{children:e.jsx(h,{className:"p-4",children:e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsxs("div",{children:[e.jsx("p",{className:"text-sm text-gray-600",children:"待審批"}),e.jsx("p",{className:"text-2xl font-bold",children:c.length})]}),e.jsx(ke,{className:"w-8 h-8 text-orange-500"})]})})}),e.jsx(x,{children:e.jsx(h,{className:"p-4",children:e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsxs("div",{children:[e.jsx("p",{className:"text-sm text-gray-600",children:"緊急決策"}),e.jsx("p",{className:"text-2xl font-bold text-red-600",children:c.filter(t=>t.priority==="critical").length})]}),e.jsx(je,{className:"w-8 h-8 text-red-500"})]})})}),e.jsx(x,{children:e.jsx(h,{className:"p-4",children:e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsxs("div",{children:[e.jsx("p",{className:"text-sm text-gray-600",children:"平均信心度"}),e.jsxs("p",{className:"text-2xl font-bold text-green-600",children:[Math.round(c.reduce((t,s)=>t+s.predicted_impact.confidence,0)/c.length*100),"%"]})]}),e.jsx(Ce,{className:"w-8 h-8 text-green-500"})]})})}),e.jsx(x,{children:e.jsx(h,{className:"p-4",children:e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsxs("div",{children:[e.jsx("p",{className:"text-sm text-gray-600",children:"預計成本"}),e.jsxs("p",{className:"text-2xl font-bold text-blue-600",children:["$",c.reduce((t,s)=>t+s.predicted_impact.cost_increase,0).toFixed(2)]})]}),e.jsx(Te,{className:"w-8 h-8 text-blue-500"})]})})})]}),e.jsx("div",{className:"space-y-4",children:c.length===0?e.jsx(x,{children:e.jsxs(h,{className:"p-8 text-center",children:[e.jsx(k,{className:"w-16 h-16 text-green-500 mx-auto mb-4"}),e.jsx("h3",{className:"text-lg font-medium text-gray-900 mb-2",children:"沒有待審批的決策"}),e.jsx("p",{className:"text-gray-600",children:"所有決策都已處理完畢，系統運行正常"})]})}):c.map(t=>e.jsxs(x,{className:"border-l-4 border-l-orange-400",children:[e.jsx(pe,{children:e.jsxs("div",{className:"flex items-start justify-between",children:[e.jsxs("div",{className:"flex-1",children:[e.jsxs("div",{className:"flex items-center space-x-2 mb-2",children:[e.jsx(xe,{className:"text-lg",children:t.strategy.name}),e.jsx(ge,{className:ce(t.priority),children:t.priority==="critical"?"緊急":t.priority==="high"?"高":t.priority==="medium"?"中":"低"})]}),e.jsx(he,{children:t.strategy.description}),e.jsxs("p",{className:"text-sm text-gray-500 mt-2",children:["觸發時間: ",new Date(t.timestamp).toLocaleString()]})]}),e.jsxs("div",{className:"text-right",children:[e.jsx("div",{className:"text-sm text-gray-600 mb-2",children:"自動批准倒計時"}),e.jsx("div",{className:"text-lg font-mono text-orange-600",children:le(t.auto_approve_in)}),e.jsx(Se,{value:(300-t.auto_approve_in)/300*100,className:"w-20 mt-2"})]})]})}),e.jsxs(h,{children:[e.jsxs("div",{className:"grid grid-cols-1 lg:grid-cols-3 gap-6",children:[e.jsxs("div",{children:[e.jsx("h4",{className:"font-medium mb-2",children:"觸發條件"}),e.jsxs("div",{className:"text-sm space-y-1",children:[e.jsxs("p",{children:[e.jsx("span",{className:"text-gray-600",children:"類型:"})," ",t.trigger.type]}),e.jsxs("p",{children:[e.jsx("span",{className:"text-gray-600",children:"當前值:"})," ",t.trigger.value]}),e.jsxs("p",{children:[e.jsx("span",{className:"text-gray-600",children:"閾值:"})," ",t.trigger.threshold]}),e.jsxs("p",{children:[e.jsx("span",{className:"text-gray-600",children:"持續時間:"})," ",t.trigger.duration]})]})]}),e.jsxs("div",{children:[e.jsx("h4",{className:"font-medium mb-2",children:"預期影響"}),e.jsx("div",{className:"text-sm space-y-1",children:Object.entries(t.predicted_impact).map(([s,a])=>e.jsxs("p",{children:[e.jsxs("span",{className:"text-gray-600",children:[s==="confidence"?"信心度":s==="cost_increase"?"成本增加":s==="cpu_reduction"?"CPU降低":s==="response_time_improvement"?"響應時間改善":s,":"]})," ",s==="cost_increase"?`$${a}`:s==="confidence"?`${Math.round(a*100)}%`:typeof a=="number"?`${a}%`:a]},s))})]}),e.jsxs("div",{children:[e.jsx("h4",{className:"font-medium mb-2",children:"風險評估"}),e.jsxs("div",{className:"text-sm",children:[e.jsxs("p",{className:"mb-2",children:[e.jsx("span",{className:"text-gray-600",children:"風險等級:"})," ",e.jsx("span",{className:oe(t.risk_assessment.level),children:t.risk_assessment.level==="very_low"?"極低":t.risk_assessment.level==="low"?"低":t.risk_assessment.level==="medium"?"中":t.risk_assessment.level==="high"?"高":"極高"})]}),e.jsx("div",{className:"space-y-1",children:t.risk_assessment.factors.map((s,a)=>e.jsxs("p",{className:"text-gray-600",children:["• ",s]},a))})]})]})]}),e.jsxs("div",{className:"mt-4",children:[e.jsx("h4",{className:"font-medium mb-2",children:"執行步驟"}),e.jsx("div",{className:"space-y-2",children:t.strategy.actions.map((s,a)=>e.jsxs("div",{className:"flex items-center space-x-3 p-2 bg-gray-50 rounded",children:[e.jsx("div",{className:"w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium",children:a+1}),e.jsxs("div",{className:"flex-1",children:[e.jsx("p",{className:"text-sm font-medium",children:s.description}),e.jsxs("p",{className:"text-xs text-gray-500",children:["預計耗時: ",s.estimated_time]})]})]},a))})]}),e.jsxs("div",{className:"flex items-center justify-end space-x-3 mt-6",children:[e.jsxs(fe,{children:[e.jsx(we,{asChild:!0,children:e.jsxs(j,{variant:"outline",onClick:()=>y(t),children:[e.jsx(Be,{className:"w-4 h-4 mr-2"}),"詳細信息"]})}),e.jsxs(be,{className:"max-w-2xl",children:[e.jsxs(_e,{children:[e.jsx(Ne,{children:t.strategy.name}),e.jsx(De,{children:"決策詳細信息和審批操作"})]}),e.jsxs("div",{className:"space-y-4",children:[e.jsxs("div",{children:[e.jsx(ve,{htmlFor:"comment",children:"審批意見 (可選)"}),e.jsx(re,{id:"comment",placeholder:"請輸入審批意見或備註...",value:d,onChange:s=>p(s.target.value),className:"mt-2"})]}),e.jsxs("div",{className:"flex items-center justify-end space-x-3",children:[e.jsxs(j,{variant:"outline",onClick:()=>B(t.id,d),children:[e.jsx(I,{className:"w-4 h-4 mr-2"}),"拒絕"]}),e.jsxs(j,{onClick:()=>E(t.id,d),children:[e.jsx(k,{className:"w-4 h-4 mr-2"}),"批准執行"]})]})]})]})]}),e.jsxs(j,{variant:"outline",onClick:()=>B(t.id,"手動拒絕"),children:[e.jsx(I,{className:"w-4 h-4 mr-2"}),"拒絕"]}),e.jsxs(j,{onClick:()=>E(t.id),children:[e.jsx(k,{className:"w-4 h-4 mr-2"}),"批准"]})]})]})]},t.id))})]})};ie.__docgenInfo={description:"",methods:[],displayName:"DecisionApproval"};const Ze={title:"Components/DecisionApproval",component:ie,parameters:{layout:"fullscreen",docs:{description:{component:"Decision approval interface with Path Tracking for approve/reject actions. Monitors decision workflows and tracks success rates."}}},decorators:[r=>e.jsx(ue,{children:e.jsx(r,{})})],tags:["autodocs"]},f={name:"Default State",parameters:{docs:{description:{story:"Decision approval interface showing pending decisions awaiting review."}}}},w={name:"With Pending Decisions",parameters:{docs:{description:{story:"Interface displaying multiple pending decisions with details and action buttons."}}}},b={name:"Approve Action",parameters:{docs:{description:{story:"Demonstrates the approve action workflow. Verifies component structure and interactive elements."}}},play:async({canvasElement:r})=>{const n=A(r),l=n.queryAllByRole("button");g(l.length).toBeGreaterThanOrEqual(0);const i=n.container;g(i).toBeInTheDocument()}},_={name:"Reject Action",parameters:{docs:{description:{story:"Demonstrates the reject action workflow. Verifies component structure and interactive elements."}}},play:async({canvasElement:r})=>{const n=A(r),l=n.queryAllByRole("button");g(l.length).toBeGreaterThanOrEqual(0);const i=n.container;g(i).toBeInTheDocument()}},N={name:"With Comments",parameters:{docs:{description:{story:"Decision approval with comment field. Verifies component structure and form elements."}}},play:async({canvasElement:r})=>{const n=A(r),l=n.queryAllByRole("textbox");g(l.length).toBeGreaterThanOrEqual(0);const i=n.container;g(i).toBeInTheDocument()}},D={name:"Empty State",parameters:{docs:{description:{story:"Interface showing empty state when no decisions are pending."}}}},C={name:"Loading State",parameters:{docs:{description:{story:"Interface showing loading indicators while fetching decisions."}}}},T={name:"Mobile View",parameters:{viewport:{defaultViewport:"mobile1"},docs:{description:{story:"Decision approval interface optimized for mobile devices."}}}};var P,R,M;f.parameters={...f.parameters,docs:{...(P=f.parameters)==null?void 0:P.docs,source:{originalSource:`{
  name: 'Default State',
  parameters: {
    docs: {
      description: {
        story: 'Decision approval interface showing pending decisions awaiting review.'
      }
    }
  }
}`,...(M=(R=f.parameters)==null?void 0:R.docs)==null?void 0:M.source}}};var q,V,L;w.parameters={...w.parameters,docs:{...(q=w.parameters)==null?void 0:q.docs,source:{originalSource:`{
  name: 'With Pending Decisions',
  parameters: {
    docs: {
      description: {
        story: 'Interface displaying multiple pending decisions with details and action buttons.'
      }
    }
  }
}`,...(L=(V=w.parameters)==null?void 0:V.docs)==null?void 0:L.source}}};var O,W,$;b.parameters={...b.parameters,docs:{...(O=b.parameters)==null?void 0:O.docs,source:{originalSource:`{
  name: 'Approve Action',
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates the approve action workflow. Verifies component structure and interactive elements.'
      }
    }
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(0);
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  }
}`,...($=(W=b.parameters)==null?void 0:W.docs)==null?void 0:$.source}}};var z,G,U;_.parameters={..._.parameters,docs:{...(z=_.parameters)==null?void 0:z.docs,source:{originalSource:`{
  name: 'Reject Action',
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates the reject action workflow. Verifies component structure and interactive elements.'
      }
    }
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(0);
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  }
}`,...(U=(G=_.parameters)==null?void 0:G.docs)==null?void 0:U.source}}};var F,Z,H;N.parameters={...N.parameters,docs:{...(F=N.parameters)==null?void 0:F.docs,source:{originalSource:`{
  name: 'With Comments',
  parameters: {
    docs: {
      description: {
        story: 'Decision approval with comment field. Verifies component structure and form elements.'
      }
    }
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const textboxes = canvas.queryAllByRole('textbox');
    expect(textboxes.length).toBeGreaterThanOrEqual(0);
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  }
}`,...(H=(Z=N.parameters)==null?void 0:Z.docs)==null?void 0:H.source}}};var X,J,K;D.parameters={...D.parameters,docs:{...(X=D.parameters)==null?void 0:X.docs,source:{originalSource:`{
  name: 'Empty State',
  parameters: {
    docs: {
      description: {
        story: 'Interface showing empty state when no decisions are pending.'
      }
    }
  }
}`,...(K=(J=D.parameters)==null?void 0:J.docs)==null?void 0:K.source}}};var Q,Y,ee;C.parameters={...C.parameters,docs:{...(Q=C.parameters)==null?void 0:Q.docs,source:{originalSource:`{
  name: 'Loading State',
  parameters: {
    docs: {
      description: {
        story: 'Interface showing loading indicators while fetching decisions.'
      }
    }
  }
}`,...(ee=(Y=C.parameters)==null?void 0:Y.docs)==null?void 0:ee.source}}};var te,se,ae;T.parameters={...T.parameters,docs:{...(te=T.parameters)==null?void 0:te.docs,source:{originalSource:`{
  name: 'Mobile View',
  parameters: {
    viewport: {
      defaultViewport: 'mobile1'
    },
    docs: {
      description: {
        story: 'Decision approval interface optimized for mobile devices.'
      }
    }
  }
}`,...(ae=(se=T.parameters)==null?void 0:se.docs)==null?void 0:ae.source}}};const He=["Default","WithPendingDecisions","ApproveAction","RejectAction","WithComments","EmptyState","LoadingState","MobileView"];export{b as ApproveAction,f as Default,D as EmptyState,C as LoadingState,T as MobileView,_ as RejectAction,N as WithComments,w as WithPendingDecisions,He as __namedExportsOrder,Ze as default};
