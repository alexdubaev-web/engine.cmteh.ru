// This public demo never processes customer data. Production forms use the
// separately packaged PHP backend on the owner's Russian hosting.
export async function handleOrder(request){
 if(request.method!=='POST')return Response.json({ok:false,message:'Method not allowed'},{status:405,headers:{Allow:'POST','Cache-Control':'no-store'}});
 return Response.json({ok:false,message:'Приём заявок включается после подключения российского обработчика.'},{status:503,headers:{'Cache-Control':'no-store'}});
}
