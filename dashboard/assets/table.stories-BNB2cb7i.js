import{j as e}from"./jsx-runtime-D_zvdyIk.js";import"./index-Dz3UJJSw.js";import{c as y}from"./utils-ClSdSIbF.js";import{B as Be}from"./badge-BJ9Hlb5y.js";import{C as g}from"./checkbox-CGiH6C86.js";import"./_commonjsHelpers-CqkleIqs.js";import"./index-CN2Y8dJ9.js";import"./createLucideIcon-CPl_Fi5k.js";import"./check-IE6dqsU4.js";import"./index-WZXaWNJA.js";import"./index-CWPL_hnH.js";import"./index-CYANIyVc.js";import"./index-fUCaa9pg.js";function n({className:l,...s}){return e.jsx("div",{"data-slot":"table-container",className:"relative w-full overflow-x-auto",children:e.jsx("table",{"data-slot":"table",className:y("w-full caption-bottom text-sm",l),...s})})}function i({className:l,...s}){return e.jsx("thead",{"data-slot":"table-header",className:y("[&_tr]:border-b",l),...s})}function r({className:l,...s}){return e.jsx("tbody",{"data-slot":"table-body",className:y("[&_tr:last-child]:border-0",l),...s})}function v({className:l,...s}){return e.jsx("tfoot",{"data-slot":"table-footer",className:y("bg-muted/50 border-t font-medium [&>tr]:last:border-b-0",l),...s})}function o({className:l,...s}){return e.jsx("tr",{"data-slot":"table-row",className:y("hover:bg-muted/50 data-[state=selected]:bg-muted border-b transition-colors",l),...s})}function t({className:l,...s}){return e.jsx("th",{"data-slot":"table-head",className:y("text-foreground h-10 px-2 text-left align-middle font-medium whitespace-nowrap [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",l),...s})}function a({className:l,...s}){return e.jsx("td",{"data-slot":"table-cell",className:y("p-2 align-middle whitespace-nowrap [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",l),...s})}function d({className:l,...s}){return e.jsx("caption",{"data-slot":"table-caption",className:y("text-muted-foreground mt-4 text-sm",l),...s})}n.__docgenInfo={description:"",methods:[],displayName:"Table"};i.__docgenInfo={description:"",methods:[],displayName:"TableHeader"};r.__docgenInfo={description:"",methods:[],displayName:"TableBody"};v.__docgenInfo={description:"",methods:[],displayName:"TableFooter"};t.__docgenInfo={description:"",methods:[],displayName:"TableHead"};o.__docgenInfo={description:"",methods:[],displayName:"TableRow"};a.__docgenInfo={description:"",methods:[],displayName:"TableCell"};d.__docgenInfo={description:"",methods:[],displayName:"TableCaption"};n.__docgenInfo={description:"",methods:[],displayName:"Table"};i.__docgenInfo={description:"",methods:[],displayName:"TableHeader"};r.__docgenInfo={description:"",methods:[],displayName:"TableBody"};v.__docgenInfo={description:"",methods:[],displayName:"TableFooter"};t.__docgenInfo={description:"",methods:[],displayName:"TableHead"};o.__docgenInfo={description:"",methods:[],displayName:"TableRow"};a.__docgenInfo={description:"",methods:[],displayName:"TableCell"};d.__docgenInfo={description:"",methods:[],displayName:"TableCaption"};const We={title:"UI/Table",component:n,parameters:{layout:"padded",docs:{description:{component:`
The Table component is a comprehensive solution for displaying tabular data. It consists of multiple sub-components that provide semantic HTML structure and consistent styling.

### Sub-components
- **Table**: Main container with horizontal scroll support
- **TableHeader**: Contains column headers
- **TableBody**: Contains data rows
- **TableFooter**: Optional footer for summaries
- **TableRow**: Individual row with hover effects
- **TableHead**: Column header cell
- **TableCell**: Data cell
- **TableCaption**: Accessible table description

### Usage Guidelines
- Use for displaying structured data with multiple columns
- Include TableCaption for accessibility
- Use TableHeader for column labels
- Use TableFooter for totals or summaries
- Keep column count reasonable for mobile devices
- Consider pagination for large datasets

### Accessibility
- Semantic HTML table elements
- Caption support for screen readers
- Proper header associations
- Keyboard navigation support
- High contrast hover states
        `}}},tags:["autodocs"]},j=[{invoice:"INV001",paymentStatus:"Paid",totalAmount:"$250.00",paymentMethod:"Credit Card"},{invoice:"INV002",paymentStatus:"Pending",totalAmount:"$150.00",paymentMethod:"PayPal"},{invoice:"INV003",paymentStatus:"Unpaid",totalAmount:"$350.00",paymentMethod:"Bank Transfer"},{invoice:"INV004",paymentStatus:"Paid",totalAmount:"$450.00",paymentMethod:"Credit Card"},{invoice:"INV005",paymentStatus:"Paid",totalAmount:"$550.00",paymentMethod:"PayPal"}],c={render:()=>e.jsxs(n,{children:[e.jsx(d,{children:"A list of your recent invoices."}),e.jsx(i,{children:e.jsxs(o,{children:[e.jsx(t,{className:"w-[100px]",children:"Invoice"}),e.jsx(t,{children:"Status"}),e.jsx(t,{children:"Method"}),e.jsx(t,{className:"text-right",children:"Amount"})]})}),e.jsx(r,{children:j.map(l=>e.jsxs(o,{children:[e.jsx(a,{className:"font-medium",children:l.invoice}),e.jsx(a,{children:l.paymentStatus}),e.jsx(a,{children:l.paymentMethod}),e.jsx(a,{className:"text-right",children:l.totalAmount})]},l.invoice))})]}),parameters:{docs:{description:{story:"Basic table with caption showing invoice data."}}}},b={render:()=>e.jsxs(n,{children:[e.jsx(d,{children:"A list of your recent invoices."}),e.jsx(i,{children:e.jsxs(o,{children:[e.jsx(t,{className:"w-[100px]",children:"Invoice"}),e.jsx(t,{children:"Status"}),e.jsx(t,{children:"Method"}),e.jsx(t,{className:"text-right",children:"Amount"})]})}),e.jsx(r,{children:j.map(l=>e.jsxs(o,{children:[e.jsx(a,{className:"font-medium",children:l.invoice}),e.jsx(a,{children:l.paymentStatus}),e.jsx(a,{children:l.paymentMethod}),e.jsx(a,{className:"text-right",children:l.totalAmount})]},l.invoice))}),e.jsx(v,{children:e.jsxs(o,{children:[e.jsx(a,{colSpan:3,children:"Total"}),e.jsx(a,{className:"text-right",children:"$1,750.00"})]})})]}),parameters:{docs:{description:{story:"Table with footer row showing totals."}}}},T={render:()=>e.jsxs(n,{children:[e.jsx(d,{children:"Invoice status with visual indicators."}),e.jsx(i,{children:e.jsxs(o,{children:[e.jsx(t,{className:"w-[100px]",children:"Invoice"}),e.jsx(t,{children:"Status"}),e.jsx(t,{children:"Method"}),e.jsx(t,{className:"text-right",children:"Amount"})]})}),e.jsx(r,{children:j.map(l=>e.jsxs(o,{children:[e.jsx(a,{className:"font-medium",children:l.invoice}),e.jsx(a,{children:e.jsx(Be,{variant:l.paymentStatus==="Paid"?"default":l.paymentStatus==="Pending"?"secondary":"destructive",children:l.paymentStatus})}),e.jsx(a,{children:l.paymentMethod}),e.jsx(a,{className:"text-right",children:l.totalAmount})]},l.invoice))})]}),parameters:{docs:{description:{story:"Table with Badge components for status visualization."}}}},m={render:()=>e.jsxs(n,{children:[e.jsx(d,{children:"Selectable invoice list."}),e.jsx(i,{children:e.jsxs(o,{children:[e.jsx(t,{className:"w-[50px]",children:e.jsx(g,{})}),e.jsx(t,{className:"w-[100px]",children:"Invoice"}),e.jsx(t,{children:"Status"}),e.jsx(t,{children:"Method"}),e.jsx(t,{className:"text-right",children:"Amount"})]})}),e.jsx(r,{children:j.map(l=>e.jsxs(o,{children:[e.jsx(a,{children:e.jsx(g,{})}),e.jsx(a,{className:"font-medium",children:l.invoice}),e.jsx(a,{children:l.paymentStatus}),e.jsx(a,{children:l.paymentMethod}),e.jsx(a,{className:"text-right",children:l.totalAmount})]},l.invoice))})]}),parameters:{docs:{description:{story:"Table with checkboxes for row selection."}}}},p={render:()=>e.jsxs(n,{children:[e.jsx(d,{children:"No invoices found."}),e.jsx(i,{children:e.jsxs(o,{children:[e.jsx(t,{className:"w-[100px]",children:"Invoice"}),e.jsx(t,{children:"Status"}),e.jsx(t,{children:"Method"}),e.jsx(t,{className:"text-right",children:"Amount"})]})}),e.jsx(r,{children:e.jsx(o,{children:e.jsx(a,{colSpan:4,className:"h-24 text-center",children:"No results."})})})]}),parameters:{docs:{description:{story:"Table showing empty state when no data is available."}}}},h={render:()=>e.jsxs(n,{children:[e.jsx(d,{children:"Single invoice entry."}),e.jsx(i,{children:e.jsxs(o,{children:[e.jsx(t,{className:"w-[100px]",children:"Invoice"}),e.jsx(t,{children:"Status"}),e.jsx(t,{children:"Method"}),e.jsx(t,{className:"text-right",children:"Amount"})]})}),e.jsx(r,{children:e.jsxs(o,{children:[e.jsx(a,{className:"font-medium",children:"INV001"}),e.jsx(a,{children:"Paid"}),e.jsx(a,{children:"Credit Card"}),e.jsx(a,{className:"text-right",children:"$250.00"})]})})]}),parameters:{docs:{description:{story:"Table with only one data row."}}}},C={render:()=>e.jsxs(n,{children:[e.jsx(d,{children:"Invoice details with many columns."}),e.jsx(i,{children:e.jsxs(o,{children:[e.jsx(t,{children:"Invoice"}),e.jsx(t,{children:"Customer"}),e.jsx(t,{children:"Email"}),e.jsx(t,{children:"Status"}),e.jsx(t,{children:"Method"}),e.jsx(t,{children:"Date"}),e.jsx(t,{children:"Due Date"}),e.jsx(t,{className:"text-right",children:"Amount"})]})}),e.jsxs(r,{children:[e.jsxs(o,{children:[e.jsx(a,{className:"font-medium",children:"INV001"}),e.jsx(a,{children:"John Doe"}),e.jsx(a,{children:"john@example.com"}),e.jsx(a,{children:"Paid"}),e.jsx(a,{children:"Credit Card"}),e.jsx(a,{children:"2024-01-15"}),e.jsx(a,{children:"2024-02-15"}),e.jsx(a,{className:"text-right",children:"$250.00"})]}),e.jsxs(o,{children:[e.jsx(a,{className:"font-medium",children:"INV002"}),e.jsx(a,{children:"Jane Smith"}),e.jsx(a,{children:"jane@example.com"}),e.jsx(a,{children:"Pending"}),e.jsx(a,{children:"PayPal"}),e.jsx(a,{children:"2024-01-16"}),e.jsx(a,{children:"2024-02-16"}),e.jsx(a,{className:"text-right",children:"$150.00"})]})]})]}),parameters:{docs:{description:{story:"Table with many columns to demonstrate horizontal scrolling on small screens."}}}},u={render:()=>e.jsxs(n,{children:[e.jsx(d,{children:"Invoices with long text content."}),e.jsx(i,{children:e.jsxs(o,{children:[e.jsx(t,{className:"w-[100px]",children:"Invoice"}),e.jsx(t,{children:"Description"}),e.jsx(t,{children:"Status"}),e.jsx(t,{className:"text-right",children:"Amount"})]})}),e.jsxs(r,{children:[e.jsxs(o,{children:[e.jsx(a,{className:"font-medium",children:"INV001"}),e.jsx(a,{children:"Professional services for website development including design, frontend implementation, backend API development, and deployment"}),e.jsx(a,{children:"Paid"}),e.jsx(a,{className:"text-right",children:"$2,500.00"})]}),e.jsxs(o,{children:[e.jsx(a,{className:"font-medium",children:"INV002"}),e.jsx(a,{children:"Monthly subscription for cloud hosting services with premium support and automatic backups"}),e.jsx(a,{children:"Pending"}),e.jsx(a,{className:"text-right",children:"$150.00"})]})]})]}),parameters:{docs:{description:{story:"Table with long text content to test text wrapping behavior."}}}},x={render:()=>e.jsxs(n,{children:[e.jsx(d,{children:"Compact table with minimal data."}),e.jsx(i,{children:e.jsxs(o,{children:[e.jsx(t,{children:"ID"}),e.jsx(t,{children:"Name"})]})}),e.jsxs(r,{children:[e.jsxs(o,{children:[e.jsx(a,{children:"1"}),e.jsx(a,{children:"A"})]}),e.jsxs(o,{children:[e.jsx(a,{children:"2"}),e.jsx(a,{children:"B"})]}),e.jsxs(o,{children:[e.jsx(a,{children:"3"}),e.jsx(a,{children:"C"})]})]})]}),parameters:{docs:{description:{story:"Minimal table with just two columns and short content."}}}},w={render:()=>{const l=Array.from({length:20},(s,H)=>({invoice:`INV${String(H+1).padStart(3,"0")}`,paymentStatus:["Paid","Pending","Unpaid"][H%3],totalAmount:`$${(Math.random()*1e3).toFixed(2)}`,paymentMethod:["Credit Card","PayPal","Bank Transfer"][H%3]}));return e.jsxs(n,{children:[e.jsx(d,{children:"Large dataset with many rows."}),e.jsx(i,{children:e.jsxs(o,{children:[e.jsx(t,{className:"w-[100px]",children:"Invoice"}),e.jsx(t,{children:"Status"}),e.jsx(t,{children:"Method"}),e.jsx(t,{className:"text-right",children:"Amount"})]})}),e.jsx(r,{children:l.map(s=>e.jsxs(o,{children:[e.jsx(a,{className:"font-medium",children:s.invoice}),e.jsx(a,{children:s.paymentStatus}),e.jsx(a,{children:s.paymentMethod}),e.jsx(a,{className:"text-right",children:s.totalAmount})]},s.invoice))}),e.jsx(v,{children:e.jsxs(o,{children:[e.jsxs(a,{colSpan:3,children:["Total (",l.length," items)"]}),e.jsxs(a,{className:"text-right",children:["$",l.reduce((s,H)=>s+parseFloat(H.totalAmount.slice(1)),0).toFixed(2)]})]})})]})},parameters:{docs:{description:{story:"Table with many rows to test scrolling and performance."}}}};var N,f,R;c.parameters={...c.parameters,docs:{...(N=c.parameters)==null?void 0:N.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>A list of your recent invoices.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map(invoice => <TableRow key={invoice.invoice}>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>{invoice.paymentStatus}</TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>)}
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Basic table with caption showing invoice data.'
      }
    }
  }
}`,...(R=(f=c.parameters)==null?void 0:f.docs)==null?void 0:R.source}}};var S,I,A;b.parameters={...b.parameters,docs:{...(S=b.parameters)==null?void 0:S.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>A list of your recent invoices.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map(invoice => <TableRow key={invoice.invoice}>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>{invoice.paymentStatus}</TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>)}
      </TableBody>
      <TableFooter>
        <TableRow>
          <TableCell colSpan={3}>Total</TableCell>
          <TableCell className="text-right">$1,750.00</TableCell>
        </TableRow>
      </TableFooter>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with footer row showing totals.'
      }
    }
  }
}`,...(A=(I=b.parameters)==null?void 0:I.docs)==null?void 0:A.source}}};var B,M,P;T.parameters={...T.parameters,docs:{...(B=T.parameters)==null?void 0:B.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Invoice status with visual indicators.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map(invoice => <TableRow key={invoice.invoice}>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>
              <Badge variant={invoice.paymentStatus === 'Paid' ? 'default' : invoice.paymentStatus === 'Pending' ? 'secondary' : 'destructive'}>
                {invoice.paymentStatus}
              </Badge>
            </TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>)}
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with Badge components for status visualization.'
      }
    }
  }
}`,...(P=(M=T.parameters)==null?void 0:M.docs)==null?void 0:P.source}}};var _,$,k;m.parameters={...m.parameters,docs:{...(_=m.parameters)==null?void 0:_.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Selectable invoice list.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[50px]">
            <Checkbox />
          </TableHead>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map(invoice => <TableRow key={invoice.invoice}>
            <TableCell>
              <Checkbox />
            </TableCell>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>{invoice.paymentStatus}</TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>)}
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with checkboxes for row selection.'
      }
    }
  }
}`,...(k=($=m.parameters)==null?void 0:$.docs)==null?void 0:k.source}}};var F,V,D;p.parameters={...p.parameters,docs:{...(F=p.parameters)==null?void 0:F.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>No invoices found.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell colSpan={4} className="h-24 text-center">
            No results.
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table showing empty state when no data is available.'
      }
    }
  }
}`,...(D=(V=p.parameters)==null?void 0:V.docs)==null?void 0:D.source}}};var U,z,E;h.parameters={...h.parameters,docs:{...(U=h.parameters)==null?void 0:U.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Single invoice entry.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className="font-medium">INV001</TableCell>
          <TableCell>Paid</TableCell>
          <TableCell>Credit Card</TableCell>
          <TableCell className="text-right">$250.00</TableCell>
        </TableRow>
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with only one data row.'
      }
    }
  }
}`,...(E=(z=h.parameters)==null?void 0:z.docs)==null?void 0:E.source}}};var L,J,W;C.parameters={...C.parameters,docs:{...(L=C.parameters)==null?void 0:L.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Invoice details with many columns.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Invoice</TableHead>
          <TableHead>Customer</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead>Date</TableHead>
          <TableHead>Due Date</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className="font-medium">INV001</TableCell>
          <TableCell>John Doe</TableCell>
          <TableCell>john@example.com</TableCell>
          <TableCell>Paid</TableCell>
          <TableCell>Credit Card</TableCell>
          <TableCell>2024-01-15</TableCell>
          <TableCell>2024-02-15</TableCell>
          <TableCell className="text-right">$250.00</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">INV002</TableCell>
          <TableCell>Jane Smith</TableCell>
          <TableCell>jane@example.com</TableCell>
          <TableCell>Pending</TableCell>
          <TableCell>PayPal</TableCell>
          <TableCell>2024-01-16</TableCell>
          <TableCell>2024-02-16</TableCell>
          <TableCell className="text-right">$150.00</TableCell>
        </TableRow>
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with many columns to demonstrate horizontal scrolling on small screens.'
      }
    }
  }
}`,...(W=(J=C.parameters)==null?void 0:J.docs)==null?void 0:W.source}}};var K,O,G;u.parameters={...u.parameters,docs:{...(K=u.parameters)==null?void 0:K.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Invoices with long text content.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Description</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className="font-medium">INV001</TableCell>
          <TableCell>
            Professional services for website development including design, frontend implementation, backend API development, and deployment
          </TableCell>
          <TableCell>Paid</TableCell>
          <TableCell className="text-right">$2,500.00</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">INV002</TableCell>
          <TableCell>
            Monthly subscription for cloud hosting services with premium support and automatic backups
          </TableCell>
          <TableCell>Pending</TableCell>
          <TableCell className="text-right">$150.00</TableCell>
        </TableRow>
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with long text content to test text wrapping behavior.'
      }
    }
  }
}`,...(G=(O=u.parameters)==null?void 0:O.docs)==null?void 0:G.source}}};var q,Q,X;x.parameters={...x.parameters,docs:{...(q=x.parameters)==null?void 0:q.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Compact table with minimal data.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>Name</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>1</TableCell>
          <TableCell>A</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>2</TableCell>
          <TableCell>B</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>3</TableCell>
          <TableCell>C</TableCell>
        </TableRow>
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Minimal table with just two columns and short content.'
      }
    }
  }
}`,...(X=(Q=x.parameters)==null?void 0:Q.docs)==null?void 0:X.source}}};var Y,Z,ee;w.parameters={...w.parameters,docs:{...(Y=w.parameters)==null?void 0:Y.docs,source:{originalSource:`{
  render: () => {
    const manyInvoices = Array.from({
      length: 20
    }, (_, i) => ({
      invoice: \`INV\${String(i + 1).padStart(3, '0')}\`,
      paymentStatus: ['Paid', 'Pending', 'Unpaid'][i % 3],
      totalAmount: \`$\${(Math.random() * 1000).toFixed(2)}\`,
      paymentMethod: ['Credit Card', 'PayPal', 'Bank Transfer'][i % 3]
    }));
    return <Table>
        <TableCaption>Large dataset with many rows.</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">Invoice</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Method</TableHead>
            <TableHead className="text-right">Amount</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {manyInvoices.map(invoice => <TableRow key={invoice.invoice}>
              <TableCell className="font-medium">{invoice.invoice}</TableCell>
              <TableCell>{invoice.paymentStatus}</TableCell>
              <TableCell>{invoice.paymentMethod}</TableCell>
              <TableCell className="text-right">{invoice.totalAmount}</TableCell>
            </TableRow>)}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell colSpan={3}>Total ({manyInvoices.length} items)</TableCell>
            <TableCell className="text-right">
              $
              {manyInvoices.reduce((sum, inv) => sum + parseFloat(inv.totalAmount.slice(1)), 0).toFixed(2)}
            </TableCell>
          </TableRow>
        </TableFooter>
      </Table>;
  },
  parameters: {
    docs: {
      description: {
        story: 'Table with many rows to test scrolling and performance.'
      }
    }
  }
}`,...(ee=(Z=w.parameters)==null?void 0:Z.docs)==null?void 0:ee.source}}};var ae,le,te;c.parameters={...c.parameters,docs:{...(ae=c.parameters)==null?void 0:ae.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>A list of your recent invoices.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map(invoice => <TableRow key={invoice.invoice}>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>{invoice.paymentStatus}</TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>)}
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Basic table with caption showing invoice data.'
      }
    }
  }
}`,...(te=(le=c.parameters)==null?void 0:le.docs)==null?void 0:te.source}}};var oe,se,ne;b.parameters={...b.parameters,docs:{...(oe=b.parameters)==null?void 0:oe.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>A list of your recent invoices.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map(invoice => <TableRow key={invoice.invoice}>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>{invoice.paymentStatus}</TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>)}
      </TableBody>
      <TableFooter>
        <TableRow>
          <TableCell colSpan={3}>Total</TableCell>
          <TableCell className="text-right">$1,750.00</TableCell>
        </TableRow>
      </TableFooter>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with footer row showing totals.'
      }
    }
  }
}`,...(ne=(se=b.parameters)==null?void 0:se.docs)==null?void 0:ne.source}}};var ie,re,de;T.parameters={...T.parameters,docs:{...(ie=T.parameters)==null?void 0:ie.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Invoice status with visual indicators.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map(invoice => <TableRow key={invoice.invoice}>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>
              <Badge variant={invoice.paymentStatus === 'Paid' ? 'default' : invoice.paymentStatus === 'Pending' ? 'secondary' : 'destructive'}>
                {invoice.paymentStatus}
              </Badge>
            </TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>)}
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with Badge components for status visualization.'
      }
    }
  }
}`,...(de=(re=T.parameters)==null?void 0:re.docs)==null?void 0:de.source}}};var ce,be,Te;m.parameters={...m.parameters,docs:{...(ce=m.parameters)==null?void 0:ce.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Selectable invoice list.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[50px]">
            <Checkbox />
          </TableHead>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map(invoice => <TableRow key={invoice.invoice}>
            <TableCell>
              <Checkbox />
            </TableCell>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>{invoice.paymentStatus}</TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>)}
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with checkboxes for row selection.'
      }
    }
  }
}`,...(Te=(be=m.parameters)==null?void 0:be.docs)==null?void 0:Te.source}}};var me,pe,he;p.parameters={...p.parameters,docs:{...(me=p.parameters)==null?void 0:me.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>No invoices found.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell colSpan={4} className="h-24 text-center">
            No results.
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table showing empty state when no data is available.'
      }
    }
  }
}`,...(he=(pe=p.parameters)==null?void 0:pe.docs)==null?void 0:he.source}}};var Ce,ue,xe;h.parameters={...h.parameters,docs:{...(Ce=h.parameters)==null?void 0:Ce.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Single invoice entry.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className="font-medium">INV001</TableCell>
          <TableCell>Paid</TableCell>
          <TableCell>Credit Card</TableCell>
          <TableCell className="text-right">$250.00</TableCell>
        </TableRow>
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with only one data row.'
      }
    }
  }
}`,...(xe=(ue=h.parameters)==null?void 0:ue.docs)==null?void 0:xe.source}}};var we,ye,He;C.parameters={...C.parameters,docs:{...(we=C.parameters)==null?void 0:we.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Invoice details with many columns.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Invoice</TableHead>
          <TableHead>Customer</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead>Date</TableHead>
          <TableHead>Due Date</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className="font-medium">INV001</TableCell>
          <TableCell>John Doe</TableCell>
          <TableCell>john@example.com</TableCell>
          <TableCell>Paid</TableCell>
          <TableCell>Credit Card</TableCell>
          <TableCell>2024-01-15</TableCell>
          <TableCell>2024-02-15</TableCell>
          <TableCell className="text-right">$250.00</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">INV002</TableCell>
          <TableCell>Jane Smith</TableCell>
          <TableCell>jane@example.com</TableCell>
          <TableCell>Pending</TableCell>
          <TableCell>PayPal</TableCell>
          <TableCell>2024-01-16</TableCell>
          <TableCell>2024-02-16</TableCell>
          <TableCell className="text-right">$150.00</TableCell>
        </TableRow>
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with many columns to demonstrate horizontal scrolling on small screens.'
      }
    }
  }
}`,...(He=(ye=C.parameters)==null?void 0:ye.docs)==null?void 0:He.source}}};var ve,je,ge;u.parameters={...u.parameters,docs:{...(ve=u.parameters)==null?void 0:ve.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Invoices with long text content.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Description</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className="font-medium">INV001</TableCell>
          <TableCell>
            Professional services for website development including design, frontend implementation, backend API development, and deployment
          </TableCell>
          <TableCell>Paid</TableCell>
          <TableCell className="text-right">$2,500.00</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">INV002</TableCell>
          <TableCell>
            Monthly subscription for cloud hosting services with premium support and automatic backups
          </TableCell>
          <TableCell>Pending</TableCell>
          <TableCell className="text-right">$150.00</TableCell>
        </TableRow>
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Table with long text content to test text wrapping behavior.'
      }
    }
  }
}`,...(ge=(je=u.parameters)==null?void 0:je.docs)==null?void 0:ge.source}}};var Ne,fe,Re;x.parameters={...x.parameters,docs:{...(Ne=x.parameters)==null?void 0:Ne.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Compact table with minimal data.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>Name</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>1</TableCell>
          <TableCell>A</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>2</TableCell>
          <TableCell>B</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>3</TableCell>
          <TableCell>C</TableCell>
        </TableRow>
      </TableBody>
    </Table>,
  parameters: {
    docs: {
      description: {
        story: 'Minimal table with just two columns and short content.'
      }
    }
  }
}`,...(Re=(fe=x.parameters)==null?void 0:fe.docs)==null?void 0:Re.source}}};var Se,Ie,Ae;w.parameters={...w.parameters,docs:{...(Se=w.parameters)==null?void 0:Se.docs,source:{originalSource:`{
  render: () => {
    const manyInvoices = Array.from({
      length: 20
    }, (_, i) => ({
      invoice: \`INV\${String(i + 1).padStart(3, '0')}\`,
      paymentStatus: ['Paid', 'Pending', 'Unpaid'][i % 3],
      totalAmount: \`$\${(Math.random() * 1000).toFixed(2)}\`,
      paymentMethod: ['Credit Card', 'PayPal', 'Bank Transfer'][i % 3]
    }));
    return <Table>
        <TableCaption>Large dataset with many rows.</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">Invoice</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Method</TableHead>
            <TableHead className="text-right">Amount</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {manyInvoices.map(invoice => <TableRow key={invoice.invoice}>
              <TableCell className="font-medium">{invoice.invoice}</TableCell>
              <TableCell>{invoice.paymentStatus}</TableCell>
              <TableCell>{invoice.paymentMethod}</TableCell>
              <TableCell className="text-right">{invoice.totalAmount}</TableCell>
            </TableRow>)}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell colSpan={3}>Total ({manyInvoices.length} items)</TableCell>
            <TableCell className="text-right">
              $
              {manyInvoices.reduce((sum, inv) => sum + parseFloat(inv.totalAmount.slice(1)), 0).toFixed(2)}
            </TableCell>
          </TableRow>
        </TableFooter>
      </Table>;
  },
  parameters: {
    docs: {
      description: {
        story: 'Table with many rows to test scrolling and performance.'
      }
    }
  }
}`,...(Ae=(Ie=w.parameters)==null?void 0:Ie.docs)==null?void 0:Ae.source}}};const Ke=["Default","WithFooter","WithBadges","WithCheckboxes","EmptyState","SingleRow","ManyColumns","LongContent","CompactTable","ManyRows"];export{x as CompactTable,c as Default,p as EmptyState,u as LongContent,C as ManyColumns,w as ManyRows,h as SingleRow,T as WithBadges,m as WithCheckboxes,b as WithFooter,Ke as __namedExportsOrder,We as default};
