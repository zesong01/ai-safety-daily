import fs from 'node:fs';
import {issueSchema} from '../src/brief-schema.ts';
const data=JSON.parse(fs.readFileSync('public/data/briefs.json','utf8').replace(/^\uFEFF/,''));
for(const issue of data.issues){const {updatedAt,automatic,...content}=issue;issueSchema.parse(content);}
if(new Set(data.issues.map(i=>i.date)).size!==data.issues.length)throw new Error('Duplicate issue dates');
console.log(`Validated ${data.issues.length} issues`);
