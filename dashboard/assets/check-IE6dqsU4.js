import{r as c}from"./index-Dz3UJJSw.js";import{u as d,d as h}from"./createLucideIcon-CPl_Fi5k.js";function S(r){const e=c.useRef({value:r,previous:r});return c.useMemo(()=>(e.current.value!==r&&(e.current.previous=e.current.value,e.current.value=r),e.current.previous),[r])}function p(r){const[e,o]=c.useState(void 0);return d(()=>{if(r){o({width:r.offsetWidth,height:r.offsetHeight});const n=new ResizeObserver(t=>{if(!Array.isArray(t)||!t.length)return;const f=t[0];let i,s;if("borderBoxSize"in f){const u=f.borderBoxSize,a=Array.isArray(u)?u[0]:u;i=a.inlineSize,s=a.blockSize}else i=r.offsetWidth,s=r.offsetHeight;o({width:i,height:s})});return n.observe(r,{box:"border-box"}),()=>n.unobserve(r)}else o(void 0)},[r]),e}/**
 * @license lucide-react v0.510.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const b=[["path",{d:"M20 6 9 17l-5-5",key:"1gmf2c"}]],y=h("check",b);export{y as C,p as a,S as u};
