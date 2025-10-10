const http=require('http');const port=process.env.PORT||3000;
http.createServer((_,res)=>{res.writeHead(200,{'Content-Type':'text/plain'});res.end('MorningAI Fly Web OK\n');}).listen(port,'0.0.0.0');
console.log('listening on',port);
