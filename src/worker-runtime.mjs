const security={'X-Content-Type-Options':'nosniff','Referrer-Policy':'strict-origin-when-cross-origin','X-Frame-Options':'SAMEORIGIN','Permissions-Policy':'camera=(), microphone=(), geolocation=()','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; form-action 'self'; base-uri 'self'; frame-ancestors 'self'"};
export default {async fetch(request,env={}){const url=new URL(request.url);let pathname;try{pathname=decodeURIComponent(url.pathname)}catch{return new Response('Bad request',{status:400})}
 if(['/api/orders','/api/orders.php'].includes(pathname))return handleOrder(request,env,PRODUCTS);
 if(['/api/config','/api/config.php'].includes(pathname))return Response.json({submissionEnabled:false,consentVersion:'2026-10-04'},{headers:{'Cache-Control':'no-store',...security}});
 if(!['GET','HEAD'].includes(request.method))return new Response('Method not allowed',{status:405,headers:{Allow:'GET, HEAD'}});
 let normalized=pathname.replace(/\/{2,}/g,'/').replace(/index\.html$/i,'');const lower=normalized.toLowerCase();if(ASSETS[lower]||ASSETS[lower+'index.html']||ASSETS[lower+'/index.html'])normalized=lower;if(!normalized.endsWith('/')&&ASSETS[normalized+'/index.html'])normalized+='/';if(normalized!==pathname)return Response.redirect(url.origin+normalized+url.search,301);
 let key=pathname.endsWith('/')?pathname+'index.html':pathname;
 if(!ASSETS[key]&&ASSETS[pathname+'/index.html'])return Response.redirect(url.origin+pathname+'/'+url.search,301);
 const found=ASSETS[key];const asset=found||ASSETS['/404/index.html'];let body=asset.body;
 if(asset.binary)body=Uint8Array.from(atob(body),c=>c.charCodeAt(0));
 return new Response(request.method==='HEAD'?null:body,{status:found&&pathname!=='/404/'?200:404,headers:{...security,'Content-Type':asset.type+(asset.binary?'':'; charset=utf-8'),'Cache-Control':pathname.startsWith('/assets/')?'public, max-age=86400':'public, max-age=0, must-revalidate',...(!INDEXABLE?{'X-Robots-Tag':'noindex, nofollow'}:(!found||['/404/','/privacy/','/consent/'].includes(pathname)||['q','sort','brand','filter','page','category'].some(k=>url.searchParams.has(k))?{'X-Robots-Tag':'noindex, follow'}:{}))}});
}};
