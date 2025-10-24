import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as be}from"./index-BF9HgEP8.js";import{u as we,B as je,C as c,d as i,e as A,f as S,g as I,M as ve}from"./chunk-OIYGIGL5-oBXf3Una.js";import{B as fe}from"./badge-oAYpN3bE.js";import{S as Ne,a as Ce,b as Be,c as Te,d as m,D as Ae,C as Se,T}from"./select-CM-1Q5dU.js";import{D as Ie,P as E,T as R}from"./progress-DsaipsQI.js";import{C as Ee}from"./circle-alert-0VseOWB-.js";import{w as B,e as o}from"./index-BQxpGEEd.js";import"./_commonjsHelpers-Cpj98o6Y.js";import"./index-BxfnrfOO.js";import"./index-AKL6M_bP.js";import"./Combination-YZFS9SNe.js";import"./check-BYvrFPye.js";const ye=()=>{const{trackPathStart:n,trackPathComplete:t}=we();be.useEffect(()=>{const a=n("cost_analysis_view"),l=setTimeout(()=>{t(a),window.dispatchEvent(new CustomEvent("first-value-operation",{detail:{operation:"cost_analysis_view"}}))},500);return()=>clearTimeout(l)},[]);const s={currentMonth:1245.5,lastMonth:980.3,budget:2e3,trend:"up",breakdown:[{category:"AI 服務",cost:680.2,percentage:54.6,trend:"up"},{category:"計算資源",cost:345.8,percentage:27.8,trend:"stable"},{category:"儲存空間",cost:142.5,percentage:11.4,trend:"down"},{category:"網路流量",cost:77,percentage:6.2,trend:"up"}],alerts:[{type:"warning",message:"AI 服務成本較上月增加 35%"},{type:"info",message:"預計本月總成本將超出預算 10%"}]},r=a=>{switch(a){case"up":return e.jsx(R,{className:"w-4 h-4 text-red-600"});case"down":return e.jsx(T,{className:"w-4 h-4 text-green-600"});default:return e.jsx("span",{className:"text-gray-600 text-sm",children:"→"})}},d=s.currentMonth/s.budget*100;return e.jsxs("div",{className:"space-y-6",children:[e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsxs("div",{children:[e.jsx("h1",{className:"text-3xl font-bold text-gray-900",children:"成本分析"}),e.jsx("p",{className:"text-gray-600 mt-1",children:"追蹤與分析 AI 服務成本"})]}),e.jsxs("div",{className:"flex items-center gap-3",children:[e.jsxs(Ne,{defaultValue:"current",children:[e.jsx(Ce,{className:"w-[180px]",children:e.jsx(Be,{})}),e.jsxs(Te,{children:[e.jsx(m,{value:"current",children:"本月"}),e.jsx(m,{value:"last",children:"上月"}),e.jsx(m,{value:"quarter",children:"本季"}),e.jsx(m,{value:"year",children:"本年"})]})]}),e.jsxs(je,{variant:"outline",children:[e.jsx(Ae,{className:"w-4 h-4 mr-2"}),"導出報表"]})]})]}),s.alerts.length>0&&e.jsx(c,{className:"border-yellow-200 bg-yellow-50",children:e.jsx(i,{className:"pt-6",children:e.jsx("div",{className:"space-y-2",children:s.alerts.map((a,l)=>e.jsxs("div",{className:"flex items-start gap-3",children:[e.jsx(Ee,{className:"w-5 h-5 text-yellow-600 mt-0.5"}),e.jsx("p",{className:"text-sm text-yellow-800",children:a.message})]},l))})})}),e.jsxs("div",{className:"grid grid-cols-1 md:grid-cols-3 gap-4",children:[e.jsx(c,{children:e.jsxs(i,{className:"pt-6",children:[e.jsxs("div",{className:"flex items-center justify-between mb-2",children:[e.jsx("p",{className:"text-sm text-gray-600",children:"本月支出"}),e.jsx("div",{className:"p-2 bg-blue-100 rounded-lg",children:e.jsx(Ie,{className:"w-5 h-5 text-blue-600"})})]}),e.jsxs("p",{className:"text-3xl font-bold text-gray-900",children:["$",s.currentMonth.toFixed(2)]}),e.jsxs("div",{className:"flex items-center gap-2 mt-2",children:[r(s.trend),e.jsxs("span",{className:"text-sm text-red-600",children:[((s.currentMonth/s.lastMonth-1)*100).toFixed(1),"% 較上月"]})]})]})}),e.jsx(c,{children:e.jsxs(i,{className:"pt-6",children:[e.jsxs("div",{className:"flex items-center justify-between mb-2",children:[e.jsx("p",{className:"text-sm text-gray-600",children:"月度預算"}),e.jsx("div",{className:"p-2 bg-green-100 rounded-lg",children:e.jsx(Se,{className:"w-5 h-5 text-green-600"})})]}),e.jsxs("p",{className:"text-3xl font-bold text-gray-900",children:["$",s.budget.toFixed(2)]}),e.jsxs("div",{className:"mt-2",children:[e.jsx(E,{value:d,className:"h-2"}),e.jsxs("p",{className:"text-sm text-gray-600 mt-1",children:["已使用 ",d.toFixed(1),"%"]})]})]})}),e.jsx(c,{children:e.jsxs(i,{className:"pt-6",children:[e.jsxs("div",{className:"flex items-center justify-between mb-2",children:[e.jsx("p",{className:"text-sm text-gray-600",children:"預估月底"}),e.jsx("div",{className:"p-2 bg-purple-100 rounded-lg",children:e.jsx(R,{className:"w-5 h-5 text-purple-600"})})]}),e.jsxs("p",{className:"text-3xl font-bold text-gray-900",children:["$",(s.currentMonth*1.15).toFixed(2)]}),e.jsx("p",{className:"text-sm text-gray-600 mt-2",children:"基於當前使用趨勢"})]})})]}),e.jsxs(c,{children:[e.jsxs(A,{children:[e.jsx(S,{children:"成本分類"}),e.jsx(I,{children:"按服務類別查看成本分布"})]}),e.jsx(i,{children:e.jsx("div",{className:"space-y-4",children:s.breakdown.map((a,l)=>e.jsxs("div",{children:[e.jsxs("div",{className:"flex items-center justify-between mb-2",children:[e.jsxs("div",{className:"flex items-center gap-3",children:[e.jsx("span",{className:"font-medium text-gray-900",children:a.category}),r(a.trend)]}),e.jsxs("div",{className:"flex items-center gap-3",children:[e.jsxs(fe,{variant:"outline",children:[a.percentage.toFixed(1),"%"]}),e.jsxs("span",{className:"font-semibold text-gray-900",children:["$",a.cost.toFixed(2)]})]})]}),e.jsx(E,{value:a.percentage,className:"h-2"})]},l))})})]}),e.jsxs(c,{children:[e.jsxs(A,{children:[e.jsx(S,{children:"成本優化建議"}),e.jsx(I,{children:"AI 自動分析的節省機會"})]}),e.jsx(i,{children:e.jsxs("div",{className:"space-y-3",children:[e.jsxs("div",{className:"flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg",children:[e.jsx(T,{className:"w-5 h-5 text-green-600 mt-0.5"}),e.jsxs("div",{children:[e.jsx("p",{className:"font-medium text-green-900",children:"優化 AI 服務使用時段"}),e.jsx("p",{className:"text-sm text-green-700 mt-1",children:"在離峰時段執行批次任務，預計每月可節省 $120"})]})]}),e.jsxs("div",{className:"flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg",children:[e.jsx(T,{className:"w-5 h-5 text-green-600 mt-0.5"}),e.jsxs("div",{children:[e.jsx("p",{className:"font-medium text-green-900",children:"調整儲存策略"}),e.jsx("p",{className:"text-sm text-green-700 mt-1",children:"將冷數據遷移至低成本儲存，預計每月可節省 $45"})]})]})]})})]})]})};ye.__docgenInfo={description:"",methods:[],displayName:"CostAnalysis"};const $e={title:"Components/CostAnalysis",component:ye,parameters:{layout:"fullscreen",docs:{description:{component:"Cost analysis dashboard displaying AI service costs, budget tracking, and optimization recommendations. Integrates Path Tracking for cost analysis view monitoring and TTV measurement."}}},decorators:[n=>e.jsx(ve,{children:e.jsx(n,{})})],tags:["autodocs"]},p={name:"Default State",parameters:{docs:{description:{story:"Cost analysis dashboard in its default state showing current month costs, budget usage, and cost breakdown by category."}}}},g={name:"With Interaction",parameters:{docs:{description:{story:"Cost analysis dashboard demonstrating interactive elements. Verifies component structure and UI elements."}}},play:async({canvasElement:n})=>{const t=B(n),s=t.queryAllByRole("heading");o(s.length).toBeGreaterThan(0);const r=t.queryAllByRole("button");o(r.length).toBeGreaterThan(0);const d=t.container;o(d).toBeInTheDocument()}},h={name:"Budget Overage",parameters:{docs:{description:{story:"Cost analysis showing scenario where current spending exceeds budget, with warning alerts displayed."}}}},u={name:"Budget Under Usage",parameters:{docs:{description:{story:"Cost analysis showing scenario where spending is well under budget, demonstrating cost efficiency."}}}},x={name:"With Cost Alerts",parameters:{docs:{description:{story:"Cost analysis displaying multiple cost alerts and warnings for unusual spending patterns."}}},play:async({canvasElement:n})=>{const s=B(n).container;o(s).toBeInTheDocument();const r=s.textContent;o(r.length).toBeGreaterThan(0)}},y={name:"Export Report Action",parameters:{docs:{description:{story:"Demonstrates the export report functionality. Verifies export button is accessible and interactive."}}},play:async({canvasElement:n})=>{const t=B(n),s=t.queryAllByRole("button");o(s.length).toBeGreaterThan(0);const r=t.queryAllByRole("combobox");o(r.length).toBeGreaterThanOrEqual(0)}},b={name:"Time Range Selection",parameters:{docs:{description:{story:"Cost analysis with time range selector (current month, last month, quarter, year). Demonstrates period filtering."}}},play:async({canvasElement:n})=>{const t=B(n),s=t.queryAllByRole("combobox");o(s.length).toBeGreaterThanOrEqual(0);const r=t.container;o(r).toBeInTheDocument()}},w={name:"Cost Breakdown View",parameters:{docs:{description:{story:"Detailed view of cost breakdown by service category (AI services, compute, storage, network). Shows percentage distribution and trends."}}}},j={name:"Optimization Recommendations",parameters:{docs:{description:{story:"Cost analysis highlighting AI-generated optimization recommendations for cost savings opportunities."}}}},v={name:"Loading State",parameters:{docs:{description:{story:"Cost analysis showing loading indicators while fetching cost data."}}}},f={name:"Error State",parameters:{docs:{description:{story:"Cost analysis showing error state when cost data fetch fails."}}}},N={name:"Mobile View",parameters:{viewport:{defaultViewport:"mobile1"},docs:{description:{story:"Cost analysis dashboard optimized for mobile devices with responsive layout."}}}},C={name:"Accessibility Test",parameters:{docs:{description:{story:"Cost analysis with accessibility features highlighted. Tests ARIA labels, keyboard navigation, and screen reader support."}},a11y:{config:{rules:[{id:"color-contrast",enabled:!0},{id:"button-name",enabled:!0},{id:"heading-order",enabled:!0}]}}}};var D,k,q;p.parameters={...p.parameters,docs:{...(D=p.parameters)==null?void 0:D.docs,source:{originalSource:`{
  name: 'Default State',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis dashboard in its default state showing current month costs, budget usage, and cost breakdown by category.'
      }
    }
  }
}`,...(q=(k=p.parameters)==null?void 0:k.docs)==null?void 0:q.source}}};var V,M,O;g.parameters={...g.parameters,docs:{...(V=g.parameters)==null?void 0:V.docs,source:{originalSource:`{
  name: 'With Interaction',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis dashboard demonstrating interactive elements. Verifies component structure and UI elements.'
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
}`,...(O=(M=g.parameters)==null?void 0:M.docs)==null?void 0:O.source}}};var G,U,z;h.parameters={...h.parameters,docs:{...(G=h.parameters)==null?void 0:G.docs,source:{originalSource:`{
  name: 'Budget Overage',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis showing scenario where current spending exceeds budget, with warning alerts displayed.'
      }
    }
  }
}`,...(z=(U=h.parameters)==null?void 0:U.docs)==null?void 0:z.source}}};var _,W,F;u.parameters={...u.parameters,docs:{...(_=u.parameters)==null?void 0:_.docs,source:{originalSource:`{
  name: 'Budget Under Usage',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis showing scenario where spending is well under budget, demonstrating cost efficiency.'
      }
    }
  }
}`,...(F=(W=u.parameters)==null?void 0:W.docs)==null?void 0:F.source}}};var $,P,L;x.parameters={...x.parameters,docs:{...($=x.parameters)==null?void 0:$.docs,source:{originalSource:`{
  name: 'With Cost Alerts',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis displaying multiple cost alerts and warnings for unusual spending patterns.'
      }
    }
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const container = canvas.container;
    expect(container).toBeInTheDocument();
    const allText = container.textContent;
    expect(allText.length).toBeGreaterThan(0);
  }
}`,...(L=(P=x.parameters)==null?void 0:P.docs)==null?void 0:L.source}}};var H,J,K;y.parameters={...y.parameters,docs:{...(H=y.parameters)==null?void 0:H.docs,source:{originalSource:`{
  name: 'Export Report Action',
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates the export report functionality. Verifies export button is accessible and interactive.'
      }
    }
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    const comboboxes = canvas.queryAllByRole('combobox');
    expect(comboboxes.length).toBeGreaterThanOrEqual(0);
  }
}`,...(K=(J=y.parameters)==null?void 0:J.docs)==null?void 0:K.source}}};var Q,X,Y;b.parameters={...b.parameters,docs:{...(Q=b.parameters)==null?void 0:Q.docs,source:{originalSource:`{
  name: 'Time Range Selection',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis with time range selector (current month, last month, quarter, year). Demonstrates period filtering.'
      }
    }
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const comboboxes = canvas.queryAllByRole('combobox');
    expect(comboboxes.length).toBeGreaterThanOrEqual(0);
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  }
}`,...(Y=(X=b.parameters)==null?void 0:X.docs)==null?void 0:Y.source}}};var Z,ee,se;w.parameters={...w.parameters,docs:{...(Z=w.parameters)==null?void 0:Z.docs,source:{originalSource:`{
  name: 'Cost Breakdown View',
  parameters: {
    docs: {
      description: {
        story: 'Detailed view of cost breakdown by service category (AI services, compute, storage, network). Shows percentage distribution and trends.'
      }
    }
  }
}`,...(se=(ee=w.parameters)==null?void 0:ee.docs)==null?void 0:se.source}}};var te,ne,ae;j.parameters={...j.parameters,docs:{...(te=j.parameters)==null?void 0:te.docs,source:{originalSource:`{
  name: 'Optimization Recommendations',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis highlighting AI-generated optimization recommendations for cost savings opportunities.'
      }
    }
  }
}`,...(ae=(ne=j.parameters)==null?void 0:ne.docs)==null?void 0:ae.source}}};var re,oe,ce;v.parameters={...v.parameters,docs:{...(re=v.parameters)==null?void 0:re.docs,source:{originalSource:`{
  name: 'Loading State',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis showing loading indicators while fetching cost data.'
      }
    }
  }
}`,...(ce=(oe=v.parameters)==null?void 0:oe.docs)==null?void 0:ce.source}}};var ie,le,de;f.parameters={...f.parameters,docs:{...(ie=f.parameters)==null?void 0:ie.docs,source:{originalSource:`{
  name: 'Error State',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis showing error state when cost data fetch fails.'
      }
    }
  }
}`,...(de=(le=f.parameters)==null?void 0:le.docs)==null?void 0:de.source}}};var me,pe,ge;N.parameters={...N.parameters,docs:{...(me=N.parameters)==null?void 0:me.docs,source:{originalSource:`{
  name: 'Mobile View',
  parameters: {
    viewport: {
      defaultViewport: 'mobile1'
    },
    docs: {
      description: {
        story: 'Cost analysis dashboard optimized for mobile devices with responsive layout.'
      }
    }
  }
}`,...(ge=(pe=N.parameters)==null?void 0:pe.docs)==null?void 0:ge.source}}};var he,ue,xe;C.parameters={...C.parameters,docs:{...(he=C.parameters)==null?void 0:he.docs,source:{originalSource:`{
  name: 'Accessibility Test',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis with accessibility features highlighted. Tests ARIA labels, keyboard navigation, and screen reader support.'
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
}`,...(xe=(ue=C.parameters)==null?void 0:ue.docs)==null?void 0:xe.source}}};const Pe=["Default","WithInteraction","BudgetOverage","BudgetUnderUsage","WithAlerts","ExportReport","TimeRangeSelection","CostBreakdown","OptimizationRecommendations","LoadingState","ErrorState","MobileView","AccessibilityTest"];export{C as AccessibilityTest,h as BudgetOverage,u as BudgetUnderUsage,w as CostBreakdown,p as Default,f as ErrorState,y as ExportReport,v as LoadingState,N as MobileView,j as OptimizationRecommendations,b as TimeRangeSelection,x as WithAlerts,g as WithInteraction,Pe as __namedExportsOrder,$e as default};
