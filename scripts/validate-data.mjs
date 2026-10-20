import fs from 'node:fs';
import {issueSchema,articleSchema} from '../src/brief-schema.ts';
const data=JSON.parse(fs.readFileSync('public/data/briefs.json','utf8').replace(/^\uFEFF/,''));
for(const issue of data.issues){const {updatedAt,automatic,...content}=issue;issueSchema.parse(content);}
if(new Set(data.issues.map(i=>i.date)).size!==data.issues.length)throw new Error('Duplicate issue dates');
if(fs.existsSync('public/data/feed-cache.json')){
 const pending=JSON.parse(fs.readFileSync('public/data/feed-cache.json','utf8'));
 for(const item of pending){const {_published,...article}=item;articleSchema.parse(article);
  const stamp=Date.parse(_published);
  if(!Number.isFinite(stamp)||stamp<Date.parse(data.collection.windowEnd)||stamp>=Date.parse(data.collection.scanEnd))throw new Error('Invalid pending publication time');
 }
 if(new Set(pending.map(a=>a.id)).size!==pending.length)throw new Error('Duplicate pending articles');
 console.log(`Validated ${pending.length} pending articles`);
}
console.log(`Validated ${data.issues.length} issues`);
