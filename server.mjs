import http from 'node:http';
import worker from './dist/server/index.js';
const port=Number(process.env.PORT||3000);
http.createServer(async(req,res)=>{try{const url=`http://${req.headers.host}${req.url}`;const request=new Request(url,{method:req.method,headers:req.headers,...(!['GET','HEAD'].includes(req.method)?{body:req,duplex:'half'}:{})});const result=await worker.fetch(request,process.env);res.writeHead(result.status,Object.fromEntries(result.headers));res.end(Buffer.from(await result.arrayBuffer()))}catch{res.writeHead(500);res.end('Server error')}}).listen(port,'0.0.0.0',()=>console.log(`СМ ТЕХНО: http://localhost:${port}`));
