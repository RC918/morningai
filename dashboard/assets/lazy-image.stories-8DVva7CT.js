import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r}from"./storybook-vendor-CPzy2iGn.js";import{c as u}from"./utils-D-KgF5mV.js";import"./react-vendor-Bzgz95E1.js";const a=r.forwardRef(({src:n,alt:s,className:w,placeholderClassName:b,onLoad:g,onError:f,...I},N)=>{const[h,j]=r.useState(!1),[fe,z]=r.useState(!1),[L,we]=r.useState(!1),y=r.useRef(null),v=r.useRef(null);r.useImperativeHandle(N,()=>y.current),r.useEffect(()=>{if(!("IntersectionObserver"in window)){z(!0);return}return v.current=new IntersectionObserver(([t])=>{var S;t.isIntersecting&&(z(!0),(S=v.current)==null||S.disconnect())},{rootMargin:"50px",threshold:.01}),y.current&&v.current.observe(y.current),()=>{var t;(t=v.current)==null||t.disconnect()}},[]);const be=t=>{j(!0),g==null||g(t)},ye=t=>{we(!0),f==null||f(t)};return e.jsxs("div",{ref:y,className:u("relative overflow-hidden",w),...I,children:[!h&&!L&&e.jsx("div",{className:u("absolute inset-0 bg-muted animate-pulse",b),"aria-hidden":"true"}),L&&e.jsx("div",{className:u("absolute inset-0 flex items-center justify-center bg-muted text-muted-foreground",b),role:"img","aria-label":s||"Image failed to load",children:e.jsx("svg",{className:"w-8 h-8",fill:"none",stroke:"currentColor",viewBox:"0 0 24 24",xmlns:"http://www.w3.org/2000/svg",children:e.jsx("path",{strokeLinecap:"round",strokeLinejoin:"round",strokeWidth:2,d:"M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"})})}),fe&&e.jsx("img",{src:n,alt:s,loading:"lazy",decoding:"async",onLoad:be,onError:ye,className:u("transition-opacity duration-300",h?"opacity-100":"opacity-0",w)})]})});a.displayName="LazyImage";const x=r.forwardRef(({src:n,alt:s,sources:w=[],className:b,...g},f)=>{const[I,N]=r.useState(!1);return e.jsxs("picture",{className:u("block",b),children:[w.map((h,j)=>e.jsx("source",{srcSet:h.srcSet,media:h.media,type:h.type},j)),e.jsx("img",{ref:f,src:n,alt:s,loading:"lazy",decoding:"async",onLoad:()=>N(!0),className:u("transition-opacity duration-300",I?"opacity-100":"opacity-0"),...g})]})});x.displayName="ResponsiveImage";a.__docgenInfo={description:`LazyImage component with Intersection Observer for lazy loading
Includes loading placeholder and WebP support with fallback`,methods:[],displayName:"LazyImage"};x.__docgenInfo={description:"Picture component with multiple sources for responsive images",methods:[],displayName:"ResponsiveImage",props:{sources:{defaultValue:{value:"[]",computed:!1},required:!1}}};a.__docgenInfo={description:`LazyImage component with Intersection Observer for lazy loading
Includes loading placeholder and WebP support with fallback`,methods:[],displayName:"LazyImage"};x.__docgenInfo={description:"Picture component with multiple sources for responsive images",methods:[],displayName:"ResponsiveImage",props:{sources:{defaultValue:{value:"[]",computed:!1},required:!1}}};const je={title:"UI/LazyImage",component:a,parameters:{layout:"padded"},tags:["autodocs"]},o={render:()=>e.jsx("div",{className:"w-full max-w-md",children:e.jsx(a,{src:"https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop",alt:"Abstract gradient background",className:"w-full h-64 object-cover rounded-lg"})})},c={render:()=>e.jsx("div",{className:"w-full max-w-md",children:e.jsx(a,{src:"https://images.unsplash.com/photo-1557683316-973673baf926?w=800&h=600&fit=crop",alt:"Gradient mesh background",className:"w-full h-64 object-cover rounded-lg",placeholderClassName:"bg-gradient-to-br from-blue-100 to-purple-100"})}),parameters:{docs:{description:{story:"LazyImage with custom placeholder gradient."}}}},i={render:()=>e.jsx("div",{className:"space-y-8",children:[{src:"https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=400&fit=crop",alt:"Image 1"},{src:"https://images.unsplash.com/photo-1557683316-973673baf926?w=800&h=400&fit=crop",alt:"Image 2"},{src:"https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=800&h=400&fit=crop",alt:"Image 3"},{src:"https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=800&h=400&fit=crop",alt:"Image 4"}].map((n,s)=>e.jsx(a,{src:n.src,alt:n.alt,className:"w-full h-48 object-cover rounded-lg"},s))}),parameters:{docs:{description:{story:"Multiple images with lazy loading. Scroll down to see images load as they enter the viewport."}}}},l={render:()=>e.jsx("div",{className:"w-full max-w-md",children:e.jsx(a,{src:"https://invalid-url-that-will-fail.com/image.jpg",alt:"This image will fail to load",className:"w-full h-64 rounded-lg"})}),parameters:{docs:{description:{story:"LazyImage with error state when image fails to load."}}}},m={render:()=>e.jsxs("div",{className:"grid grid-cols-2 gap-4 max-w-2xl",children:[e.jsx(a,{src:"https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=400&fit=crop",alt:"Square image",className:"w-full aspect-square object-cover rounded-lg"}),e.jsx(a,{src:"https://images.unsplash.com/photo-1557683316-973673baf926?w=400&h=600&fit=crop",alt:"Portrait image",className:"w-full aspect-[2/3] object-cover rounded-lg"}),e.jsx(a,{src:"https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=600&h=400&fit=crop",alt:"Landscape image",className:"w-full aspect-[3/2] object-cover rounded-lg col-span-2"})]}),parameters:{docs:{description:{story:"LazyImage with different aspect ratios."}}}},p={render:()=>e.jsx("div",{className:"w-full max-w-2xl",children:e.jsx(x,{src:"https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop",alt:"Responsive image with multiple sources",sources:[{srcSet:"https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=300&fit=crop",media:"(max-width: 640px)",type:"image/webp"},{srcSet:"https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop",media:"(max-width: 1024px)",type:"image/webp"},{srcSet:"https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&h=900&fit=crop",media:"(min-width: 1025px)",type:"image/webp"}],className:"w-full h-auto rounded-lg"})}),parameters:{docs:{description:{story:"ResponsiveImage component with multiple sources for different screen sizes."}}}},d={render:()=>e.jsx("div",{className:"grid grid-cols-3 gap-4 max-w-4xl",children:Array.from({length:9}).map((n,s)=>e.jsx(a,{src:`https://images.unsplash.com/photo-${1618005182384+s}?w=400&h=400&fit=crop`,alt:`Grid image ${s+1}`,className:"w-full aspect-square object-cover rounded-lg"},s))}),parameters:{docs:{description:{story:"Grid of lazy-loaded images."}}}};var R,k,_;o.parameters={...o.parameters,docs:{...(R=o.parameters)==null?void 0:R.docs,source:{originalSource:`{
  render: () => <div className="w-full max-w-md">
      <LazyImage src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop" alt="Abstract gradient background" className="w-full h-64 object-cover rounded-lg" />
    </div>
}`,...(_=(k=o.parameters)==null?void 0:k.docs)==null?void 0:_.source}}};var q,G,P;c.parameters={...c.parameters,docs:{...(q=c.parameters)==null?void 0:q.docs,source:{originalSource:`{
  render: () => <div className="w-full max-w-md">
      <LazyImage src="https://images.unsplash.com/photo-1557683316-973673baf926?w=800&h=600&fit=crop" alt="Gradient mesh background" className="w-full h-64 object-cover rounded-lg" placeholderClassName="bg-gradient-to-br from-blue-100 to-purple-100" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'LazyImage with custom placeholder gradient.'
      }
    }
  }
}`,...(P=(G=c.parameters)==null?void 0:G.docs)==null?void 0:P.source}}};var A,E,M;i.parameters={...i.parameters,docs:{...(A=i.parameters)==null?void 0:A.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      {[{
      src: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=400&fit=crop',
      alt: 'Image 1'
    }, {
      src: 'https://images.unsplash.com/photo-1557683316-973673baf926?w=800&h=400&fit=crop',
      alt: 'Image 2'
    }, {
      src: 'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=800&h=400&fit=crop',
      alt: 'Image 3'
    }, {
      src: 'https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=800&h=400&fit=crop',
      alt: 'Image 4'
    }].map((image, index) => <LazyImage key={index} src={image.src} alt={image.alt} className="w-full h-48 object-cover rounded-lg" />)}
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple images with lazy loading. Scroll down to see images load as they enter the viewport.'
      }
    }
  }
}`,...(M=(E=i.parameters)==null?void 0:E.docs)==null?void 0:M.source}}};var $,C,O;l.parameters={...l.parameters,docs:{...($=l.parameters)==null?void 0:$.docs,source:{originalSource:`{
  render: () => <div className="w-full max-w-md">
      <LazyImage src="https://invalid-url-that-will-fail.com/image.jpg" alt="This image will fail to load" className="w-full h-64 rounded-lg" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'LazyImage with error state when image fails to load.'
      }
    }
  }
}`,...(O=(C=l.parameters)==null?void 0:C.docs)==null?void 0:O.source}}};var V,W,H;m.parameters={...m.parameters,docs:{...(V=m.parameters)==null?void 0:V.docs,source:{originalSource:`{
  render: () => <div className="grid grid-cols-2 gap-4 max-w-2xl">
      <LazyImage src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=400&fit=crop" alt="Square image" className="w-full aspect-square object-cover rounded-lg" />
      <LazyImage src="https://images.unsplash.com/photo-1557683316-973673baf926?w=400&h=600&fit=crop" alt="Portrait image" className="w-full aspect-[2/3] object-cover rounded-lg" />
      <LazyImage src="https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=600&h=400&fit=crop" alt="Landscape image" className="w-full aspect-[3/2] object-cover rounded-lg col-span-2" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'LazyImage with different aspect ratios.'
      }
    }
  }
}`,...(H=(W=m.parameters)==null?void 0:W.docs)==null?void 0:H.source}}};var T,D,B;p.parameters={...p.parameters,docs:{...(T=p.parameters)==null?void 0:T.docs,source:{originalSource:`{
  render: () => <div className="w-full max-w-2xl">
      <ResponsiveImage src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop" alt="Responsive image with multiple sources" sources={[{
      srcSet: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=300&fit=crop',
      media: '(max-width: 640px)',
      type: 'image/webp'
    }, {
      srcSet: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop',
      media: '(max-width: 1024px)',
      type: 'image/webp'
    }, {
      srcSet: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&h=900&fit=crop',
      media: '(min-width: 1025px)',
      type: 'image/webp'
    }]} className="w-full h-auto rounded-lg" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'ResponsiveImage component with multiple sources for different screen sizes.'
      }
    }
  }
}`,...(B=(D=p.parameters)==null?void 0:D.docs)==null?void 0:B.source}}};var U,F,J;d.parameters={...d.parameters,docs:{...(U=d.parameters)==null?void 0:U.docs,source:{originalSource:`{
  render: () => <div className="grid grid-cols-3 gap-4 max-w-4xl">
      {Array.from({
      length: 9
    }).map((_, index) => <LazyImage key={index} src={\`https://images.unsplash.com/photo-\${1618005182384 + index}?w=400&h=400&fit=crop\`} alt={\`Grid image \${index + 1}\`} className="w-full aspect-square object-cover rounded-lg" />)}
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Grid of lazy-loaded images.'
      }
    }
  }
}`,...(J=(F=d.parameters)==null?void 0:F.docs)==null?void 0:J.source}}};var K,Q,X;o.parameters={...o.parameters,docs:{...(K=o.parameters)==null?void 0:K.docs,source:{originalSource:`{
  render: () => <div className="w-full max-w-md">
      <LazyImage src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop" alt="Abstract gradient background" className="w-full h-64 object-cover rounded-lg" />
    </div>
}`,...(X=(Q=o.parameters)==null?void 0:Q.docs)==null?void 0:X.source}}};var Y,Z,ee;c.parameters={...c.parameters,docs:{...(Y=c.parameters)==null?void 0:Y.docs,source:{originalSource:`{
  render: () => <div className="w-full max-w-md">
      <LazyImage src="https://images.unsplash.com/photo-1557683316-973673baf926?w=800&h=600&fit=crop" alt="Gradient mesh background" className="w-full h-64 object-cover rounded-lg" placeholderClassName="bg-gradient-to-br from-blue-100 to-purple-100" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'LazyImage with custom placeholder gradient.'
      }
    }
  }
}`,...(ee=(Z=c.parameters)==null?void 0:Z.docs)==null?void 0:ee.source}}};var ae,se,re;i.parameters={...i.parameters,docs:{...(ae=i.parameters)==null?void 0:ae.docs,source:{originalSource:`{
  render: () => <div className="space-y-8">
      {[{
      src: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=400&fit=crop',
      alt: 'Image 1'
    }, {
      src: 'https://images.unsplash.com/photo-1557683316-973673baf926?w=800&h=400&fit=crop',
      alt: 'Image 2'
    }, {
      src: 'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=800&h=400&fit=crop',
      alt: 'Image 3'
    }, {
      src: 'https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=800&h=400&fit=crop',
      alt: 'Image 4'
    }].map((image, index) => <LazyImage key={index} src={image.src} alt={image.alt} className="w-full h-48 object-cover rounded-lg" />)}
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Multiple images with lazy loading. Scroll down to see images load as they enter the viewport.'
      }
    }
  }
}`,...(re=(se=i.parameters)==null?void 0:se.docs)==null?void 0:re.source}}};var te,oe,ce;l.parameters={...l.parameters,docs:{...(te=l.parameters)==null?void 0:te.docs,source:{originalSource:`{
  render: () => <div className="w-full max-w-md">
      <LazyImage src="https://invalid-url-that-will-fail.com/image.jpg" alt="This image will fail to load" className="w-full h-64 rounded-lg" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'LazyImage with error state when image fails to load.'
      }
    }
  }
}`,...(ce=(oe=l.parameters)==null?void 0:oe.docs)==null?void 0:ce.source}}};var ie,le,me;m.parameters={...m.parameters,docs:{...(ie=m.parameters)==null?void 0:ie.docs,source:{originalSource:`{
  render: () => <div className="grid grid-cols-2 gap-4 max-w-2xl">
      <LazyImage src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=400&fit=crop" alt="Square image" className="w-full aspect-square object-cover rounded-lg" />
      <LazyImage src="https://images.unsplash.com/photo-1557683316-973673baf926?w=400&h=600&fit=crop" alt="Portrait image" className="w-full aspect-[2/3] object-cover rounded-lg" />
      <LazyImage src="https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=600&h=400&fit=crop" alt="Landscape image" className="w-full aspect-[3/2] object-cover rounded-lg col-span-2" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'LazyImage with different aspect ratios.'
      }
    }
  }
}`,...(me=(le=m.parameters)==null?void 0:le.docs)==null?void 0:me.source}}};var pe,de,ne;p.parameters={...p.parameters,docs:{...(pe=p.parameters)==null?void 0:pe.docs,source:{originalSource:`{
  render: () => <div className="w-full max-w-2xl">
      <ResponsiveImage src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop" alt="Responsive image with multiple sources" sources={[{
      srcSet: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=300&fit=crop',
      media: '(max-width: 640px)',
      type: 'image/webp'
    }, {
      srcSet: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop',
      media: '(max-width: 1024px)',
      type: 'image/webp'
    }, {
      srcSet: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&h=900&fit=crop',
      media: '(min-width: 1025px)',
      type: 'image/webp'
    }]} className="w-full h-auto rounded-lg" />
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'ResponsiveImage component with multiple sources for different screen sizes.'
      }
    }
  }
}`,...(ne=(de=p.parameters)==null?void 0:de.docs)==null?void 0:ne.source}}};var he,ue,ge;d.parameters={...d.parameters,docs:{...(he=d.parameters)==null?void 0:he.docs,source:{originalSource:`{
  render: () => <div className="grid grid-cols-3 gap-4 max-w-4xl">
      {Array.from({
      length: 9
    }).map((_, index) => <LazyImage key={index} src={\`https://images.unsplash.com/photo-\${1618005182384 + index}?w=400&h=400&fit=crop\`} alt={\`Grid image \${index + 1}\`} className="w-full aspect-square object-cover rounded-lg" />)}
    </div>,
  parameters: {
    docs: {
      description: {
        story: 'Grid of lazy-loaded images.'
      }
    }
  }
}`,...(ge=(ue=d.parameters)==null?void 0:ue.docs)==null?void 0:ge.source}}};const ze=["Default","WithPlaceholder","MultipleImages","ErrorState","CustomAspectRatio","ResponsiveImageExample","Grid"];export{m as CustomAspectRatio,o as Default,l as ErrorState,d as Grid,i as MultipleImages,p as ResponsiveImageExample,c as WithPlaceholder,ze as __namedExportsOrder,je as default};
