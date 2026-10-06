import test from 'node:test';import assert from 'node:assert/strict';import {handleOrder} from '../src/orders.mjs';
test('overseas demo rejects collection without reading personal data',async()=>{const request={method:'POST',text(){throw new Error('Must not read PII')},json(){throw new Error('Must not read PII')}};const r=await handleOrder(request,{MAIL_API_KEY:'configured'});assert.equal(r.status,503);assert.equal((await r.json()).ok,false)});
test('order endpoint allows POST only',async()=>assert.equal((await handleOrder({method:'GET'})).status,405));
