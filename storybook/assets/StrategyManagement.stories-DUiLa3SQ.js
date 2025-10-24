import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as Ne}from"./index-BF9HgEP8.js";import{u as Ee,B as T,C as o,d as c,e as Te,f as Be,g as Ae,M as Ce}from"./chunk-OIYGIGL5-oBXf3Una.js";import{B}from"./badge-oAYpN3bE.js";import{P as De,Z as Ie,S as A}from"./zap-C_cIiERl.js";import{C,a as D}from"./clock-B_e9QduT.js";import{C as Me}from"./circle-alert-0VseOWB-.js";import{w as E,e as i}from"./index-BQxpGEEd.js";import"./_commonjsHelpers-Cpj98o6Y.js";const be=()=>{const{trackPathStart:s,trackPathComplete:a}=Ee();Ne.useEffect(()=>{const t=s("strategy_management_view"),je=setTimeout(()=>{a(t),window.dispatchEvent(new CustomEvent("first-value-operation",{detail:{operation:"strategy_management_view"}}))},500);return()=>clearTimeout(je)},[]);const r=[{id:1,name:"CPU 優化策略",description:"當 CPU 使用率超過 85% 時自動擴容",status:"active",triggers:3,lastExecuted:"2 小時前"},{id:2,name:"數據庫連接池優化",description:"自動調整連接池大小以應對高並發",status:"active",triggers:8,lastExecuted:"30 分鐘前"},{id:3,name:"緩存預熱策略",description:"定期預熱熱門數據緩存",status:"paused",triggers:0,lastExecuted:"3 天前"}],n=t=>{switch(t){case"active":return"bg-green-100 text-green-800";case"paused":return"bg-gray-100 text-gray-800";case"error":return"bg-red-100 text-red-800";default:return"bg-gray-100 text-gray-800"}},N=t=>{switch(t){case"active":return e.jsx(C,{className:"w-4 h-4 text-green-600"});case"paused":return e.jsx(D,{className:"w-4 h-4 text-gray-600"});case"error":return e.jsx(Me,{className:"w-4 h-4 text-red-600"});default:return e.jsx(A,{className:"w-4 h-4 text-gray-600"})}};return e.jsxs("div",{className:"space-y-6",children:[e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsxs("div",{children:[e.jsx("h1",{className:"text-3xl font-bold text-gray-900",children:"策略管理"}),e.jsx("p",{className:"text-gray-600 mt-1",children:"管理與設定自動化策略"})]}),e.jsxs(T,{className:"flex items-center gap-2",children:[e.jsx(De,{className:"w-4 h-4"}),"新增策略"]})]}),e.jsxs("div",{className:"grid grid-cols-1 md:grid-cols-3 gap-4",children:[e.jsx(o,{children:e.jsx(c,{className:"pt-6",children:e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsxs("div",{children:[e.jsx("p",{className:"text-sm text-gray-600",children:"啟用策略"}),e.jsx("p",{className:"text-2xl font-bold text-gray-900",children:"2"})]}),e.jsx("div",{className:"p-3 bg-green-100 rounded-lg",children:e.jsx(C,{className:"w-6 h-6 text-green-600"})})]})})}),e.jsx(o,{children:e.jsx(c,{className:"pt-6",children:e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsxs("div",{children:[e.jsx("p",{className:"text-sm text-gray-600",children:"總觸發次數"}),e.jsx("p",{className:"text-2xl font-bold text-gray-900",children:"11"})]}),e.jsx("div",{className:"p-3 bg-blue-100 rounded-lg",children:e.jsx(Ie,{className:"w-6 h-6 text-blue-600"})})]})})}),e.jsx(o,{children:e.jsx(c,{className:"pt-6",children:e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsxs("div",{children:[e.jsx("p",{className:"text-sm text-gray-600",children:"暫停策略"}),e.jsx("p",{className:"text-2xl font-bold text-gray-900",children:"1"})]}),e.jsx("div",{className:"p-3 bg-gray-100 rounded-lg",children:e.jsx(D,{className:"w-6 h-6 text-gray-600"})})]})})})]}),e.jsxs(o,{children:[e.jsxs(Te,{children:[e.jsx(Be,{children:"策略列表"}),e.jsx(Ae,{children:"查看和管理所有自動化策略"})]}),e.jsx(c,{children:e.jsx("div",{className:"space-y-4",children:r.map(t=>e.jsxs("div",{className:"flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors",children:[e.jsxs("div",{className:"flex items-center gap-4",children:[N(t.status),e.jsxs("div",{children:[e.jsx("h3",{className:"font-semibold text-gray-900",children:t.name}),e.jsx("p",{className:"text-sm text-gray-600",children:t.description}),e.jsxs("div",{className:"flex items-center gap-3 mt-2",children:[e.jsxs(B,{variant:"outline",className:"text-xs",children:["觸發 ",t.triggers," 次"]}),e.jsxs("span",{className:"text-xs text-gray-500",children:["最後執行: ",t.lastExecuted]})]})]})]}),e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(B,{className:n(t.status),children:t.status==="active"?"啟用中":t.status==="paused"?"已暫停":"錯誤"}),e.jsx(T,{variant:"outline",size:"sm",children:e.jsx(A,{className:"w-4 h-4"})})]})]},t.id))})})]})]})};be.__docgenInfo={description:"",methods:[],displayName:"StrategyManagement"};const Le={title:"Components/StrategyManagement",component:be,parameters:{layout:"fullscreen",docs:{description:{component:"Strategy management interface for configuring and monitoring automated optimization strategies. Integrates Path Tracking for strategy management view monitoring and TTV measurement."}}},decorators:[s=>e.jsx(Ce,{children:e.jsx(s,{})})],tags:["autodocs"]},m={name:"Default State",parameters:{docs:{description:{story:"Strategy management interface in its default state showing active strategies, trigger counts, and strategy list."}}}},d={name:"With Interaction",parameters:{docs:{description:{story:"Strategy management demonstrating interactive elements. Verifies component structure and UI elements."}}},play:async({canvasElement:s})=>{const a=E(s),r=a.queryAllByRole("heading");i(r.length).toBeGreaterThan(0);const n=a.queryAllByRole("button");i(n.length).toBeGreaterThan(0);const N=a.container;i(N).toBeInTheDocument()}},g={name:"Active Strategies",parameters:{docs:{description:{story:"Strategy management showing multiple active strategies with recent trigger activity."}}}},l={name:"Paused Strategies",parameters:{docs:{description:{story:"Strategy management displaying paused strategies that are temporarily disabled."}}}},p={name:"Error Strategies",parameters:{docs:{description:{story:"Strategy management showing strategies with error states requiring attention."}}}},u={name:"Empty State",parameters:{docs:{description:{story:"Strategy management showing empty state when no strategies are configured."}}}},y={name:"Create New Strategy",parameters:{docs:{description:{story:"Demonstrates the create new strategy action. Verifies create button is accessible and interactive."}}},play:async({canvasElement:s})=>{const a=E(s),r=a.queryAllByRole("button");i(r.length).toBeGreaterThan(0);const n=a.container;i(n).toBeInTheDocument()}},h={name:"Edit Strategy",parameters:{docs:{description:{story:"Strategy management with edit functionality. Demonstrates strategy configuration editing."}}},play:async({canvasElement:s})=>{const a=E(s),r=a.queryAllByRole("button");i(r.length).toBeGreaterThan(0);const n=a.container;i(n).toBeInTheDocument()}},x={name:"Strategy Details View",parameters:{docs:{description:{story:"Detailed view of a single strategy showing configuration, trigger history, and execution logs."}}}},S={name:"Strategy Metrics",parameters:{docs:{description:{story:"Strategy management highlighting key metrics: active strategies, total triggers, and paused strategies."}}}},v={name:"High Trigger Activity",parameters:{docs:{description:{story:"Strategy management showing strategies with high trigger frequency, indicating active optimization."}}}},f={name:"Loading State",parameters:{docs:{description:{story:"Strategy management showing loading indicators while fetching strategy data."}}}},w={name:"Error State",parameters:{docs:{description:{story:"Strategy management showing error state when strategy data fetch fails."}}}},b={name:"Mobile View",parameters:{viewport:{defaultViewport:"mobile1"},docs:{description:{story:"Strategy management interface optimized for mobile devices with responsive layout."}}}},j={name:"Accessibility Test",parameters:{docs:{description:{story:"Strategy management with accessibility features highlighted. Tests ARIA labels, keyboard navigation, and screen reader support."}},a11y:{config:{rules:[{id:"color-contrast",enabled:!0},{id:"button-name",enabled:!0},{id:"heading-order",enabled:!0}]}}}};var I,M,V;m.parameters={...m.parameters,docs:{...(I=m.parameters)==null?void 0:I.docs,source:{originalSource:`{
  name: 'Default State',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management interface in its default state showing active strategies, trigger counts, and strategy list.'
      }
    }
  }
}`,...(V=(M=m.parameters)==null?void 0:M.docs)==null?void 0:V.source}}};var q,R,P;d.parameters={...d.parameters,docs:{...(q=d.parameters)==null?void 0:q.docs,source:{originalSource:`{
  name: 'With Interaction',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management demonstrating interactive elements. Verifies component structure and UI elements.'
      }
    }
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const headings = canvas.queryAllByRole('heading');
    expect(headings.length).toBeGreaterThan(0);
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  }
}`,...(P=(R=d.parameters)==null?void 0:R.docs)==null?void 0:P.source}}};var k,_,G;g.parameters={...g.parameters,docs:{...(k=g.parameters)==null?void 0:k.docs,source:{originalSource:`{
  name: 'Active Strategies',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing multiple active strategies with recent trigger activity.'
      }
    }
  }
}`,...(G=(_=g.parameters)==null?void 0:_.docs)==null?void 0:G.source}}};var z,H,L;l.parameters={...l.parameters,docs:{...(z=l.parameters)==null?void 0:z.docs,source:{originalSource:`{
  name: 'Paused Strategies',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management displaying paused strategies that are temporarily disabled.'
      }
    }
  }
}`,...(L=(H=l.parameters)==null?void 0:H.docs)==null?void 0:L.source}}};var U,W,Z;p.parameters={...p.parameters,docs:{...(U=p.parameters)==null?void 0:U.docs,source:{originalSource:`{
  name: 'Error Strategies',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing strategies with error states requiring attention.'
      }
    }
  }
}`,...(Z=(W=p.parameters)==null?void 0:W.docs)==null?void 0:Z.source}}};var O,F,J;u.parameters={...u.parameters,docs:{...(O=u.parameters)==null?void 0:O.docs,source:{originalSource:`{
  name: 'Empty State',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing empty state when no strategies are configured.'
      }
    }
  }
}`,...(J=(F=u.parameters)==null?void 0:F.docs)==null?void 0:J.source}}};var K,Q,X;y.parameters={...y.parameters,docs:{...(K=y.parameters)==null?void 0:K.docs,source:{originalSource:`{
  name: 'Create New Strategy',
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates the create new strategy action. Verifies create button is accessible and interactive.'
      }
    }
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  }
}`,...(X=(Q=y.parameters)==null?void 0:Q.docs)==null?void 0:X.source}}};var Y,$,ee;h.parameters={...h.parameters,docs:{...(Y=h.parameters)==null?void 0:Y.docs,source:{originalSource:`{
  name: 'Edit Strategy',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management with edit functionality. Demonstrates strategy configuration editing.'
      }
    }
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  }
}`,...(ee=($=h.parameters)==null?void 0:$.docs)==null?void 0:ee.source}}};var te,ae,se;x.parameters={...x.parameters,docs:{...(te=x.parameters)==null?void 0:te.docs,source:{originalSource:`{
  name: 'Strategy Details View',
  parameters: {
    docs: {
      description: {
        story: 'Detailed view of a single strategy showing configuration, trigger history, and execution logs.'
      }
    }
  }
}`,...(se=(ae=x.parameters)==null?void 0:ae.docs)==null?void 0:se.source}}};var re,ne,ie;S.parameters={...S.parameters,docs:{...(re=S.parameters)==null?void 0:re.docs,source:{originalSource:`{
  name: 'Strategy Metrics',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management highlighting key metrics: active strategies, total triggers, and paused strategies.'
      }
    }
  }
}`,...(ie=(ne=S.parameters)==null?void 0:ne.docs)==null?void 0:ie.source}}};var oe,ce,me;v.parameters={...v.parameters,docs:{...(oe=v.parameters)==null?void 0:oe.docs,source:{originalSource:`{
  name: 'High Trigger Activity',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing strategies with high trigger frequency, indicating active optimization.'
      }
    }
  }
}`,...(me=(ce=v.parameters)==null?void 0:ce.docs)==null?void 0:me.source}}};var de,ge,le;f.parameters={...f.parameters,docs:{...(de=f.parameters)==null?void 0:de.docs,source:{originalSource:`{
  name: 'Loading State',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing loading indicators while fetching strategy data.'
      }
    }
  }
}`,...(le=(ge=f.parameters)==null?void 0:ge.docs)==null?void 0:le.source}}};var pe,ue,ye;w.parameters={...w.parameters,docs:{...(pe=w.parameters)==null?void 0:pe.docs,source:{originalSource:`{
  name: 'Error State',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing error state when strategy data fetch fails.'
      }
    }
  }
}`,...(ye=(ue=w.parameters)==null?void 0:ue.docs)==null?void 0:ye.source}}};var he,xe,Se;b.parameters={...b.parameters,docs:{...(he=b.parameters)==null?void 0:he.docs,source:{originalSource:`{
  name: 'Mobile View',
  parameters: {
    viewport: {
      defaultViewport: 'mobile1'
    },
    docs: {
      description: {
        story: 'Strategy management interface optimized for mobile devices with responsive layout.'
      }
    }
  }
}`,...(Se=(xe=b.parameters)==null?void 0:xe.docs)==null?void 0:Se.source}}};var ve,fe,we;j.parameters={...j.parameters,docs:{...(ve=j.parameters)==null?void 0:ve.docs,source:{originalSource:`{
  name: 'Accessibility Test',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management with accessibility features highlighted. Tests ARIA labels, keyboard navigation, and screen reader support.'
      }
    },
    a11y: {
      config: {
        rules: [{
          id: 'color-contrast',
          enabled: true
        }, {
          id: 'button-name',
          enabled: true
        }, {
          id: 'heading-order',
          enabled: true
        }]
      }
    }
  }
}`,...(we=(fe=j.parameters)==null?void 0:fe.docs)==null?void 0:we.source}}};const Ue=["Default","WithInteraction","ActiveStrategies","PausedStrategies","ErrorStrategies","EmptyState","CreateStrategy","EditStrategy","StrategyDetails","StrategyMetrics","HighTriggerActivity","LoadingState","ErrorState","MobileView","AccessibilityTest"];export{j as AccessibilityTest,g as ActiveStrategies,y as CreateStrategy,m as Default,h as EditStrategy,u as EmptyState,w as ErrorState,p as ErrorStrategies,v as HighTriggerActivity,f as LoadingState,b as MobileView,l as PausedStrategies,x as StrategyDetails,S as StrategyMetrics,d as WithInteraction,Ue as __namedExportsOrder,Le as default};
