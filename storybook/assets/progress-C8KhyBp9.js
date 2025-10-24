import{b as m,c as _}from"./chunk-NISHYRIK-CfUWBg2t.js";import{j as i}from"./jsx-runtime-D_zvdyIk.js";import{r as v}from"./index-DbOFzPHX.js";import{c as $,P as f}from"./Combination-CEeXFs5e.js";/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I=[["line",{x1:"12",x2:"12",y1:"2",y2:"22",key:"7eqyqh"}],["path",{d:"M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6",key:"1b0p4s"}]],q=m("dollar-sign",I);/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w=[["polyline",{points:"22 7 13.5 15.5 8.5 10.5 2 17",key:"126l90"}],["polyline",{points:"16 7 22 7 22 13",key:"kwv8wd"}]],G=m("trending-up",w);var u="Progress",d=100,[E]=$(u),[j,M]=E(u),g=v.forwardRef((r,e)=>{const{__scopeProgress:n,value:o=null,max:a,getValueLabel:N=R,...b}=r;(a||a===0)&&!p(a)&&console.error(D(`${a}`,"Progress"));const t=p(a)?a:d;o!==null&&!c(o,t)&&console.error(V(`${o}`,"Progress"));const s=c(o,t)?o:null,h=l(s)?N(s,t):void 0;return i.jsx(j,{scope:n,value:s,max:t,children:i.jsx(f.div,{"aria-valuemax":t,"aria-valuemin":0,"aria-valuenow":l(s)?s:void 0,"aria-valuetext":h,role:"progressbar","data-state":y(s,t),"data-value":s??void 0,"data-max":t,...b,ref:e})})});g.displayName=u;var x="ProgressIndicator",P=v.forwardRef((r,e)=>{const{__scopeProgress:n,...o}=r,a=M(x,n);return i.jsx(f.div,{"data-state":y(a.value,a.max),"data-value":a.value??void 0,"data-max":a.max,...o,ref:e})});P.displayName=x;function R(r,e){return`${Math.round(r/e*100)}%`}function y(r,e){return r==null?"indeterminate":r===e?"complete":"loading"}function l(r){return typeof r=="number"}function p(r){return l(r)&&!isNaN(r)&&r>0}function c(r,e){return l(r)&&!isNaN(r)&&r<=e&&r>=0}function D(r,e){return`Invalid prop \`max\` of value \`${r}\` supplied to \`${e}\`. Only numbers greater than 0 are valid max values. Defaulting to \`${d}\`.`}function V(r,e){return`Invalid prop \`value\` of value \`${r}\` supplied to \`${e}\`. The \`value\` prop must be:
  - a positive number
  - less than the value passed to \`max\` (or ${d} if no \`max\` prop is set)
  - \`null\` or \`undefined\` if the progress is indeterminate.

Defaulting to \`null\`.`}var k=g,A=P;function L({className:r,value:e,...n}){return i.jsx(k,{"data-slot":"progress",className:_("bg-primary/20 relative h-2 w-full overflow-hidden rounded-full",r),...n,children:i.jsx(A,{"data-slot":"progress-indicator",className:"bg-primary h-full w-full flex-1 transition-all",style:{transform:`translateX(-${100-(e||0)}%)`}})})}L.__docgenInfo={description:"",methods:[],displayName:"Progress"};export{q as D,L as P,G as T};
