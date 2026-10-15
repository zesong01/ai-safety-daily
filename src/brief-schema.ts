import { z } from 'zod';
const day=z.string().regex(/^\d{4}-\d{2}-\d{2}$/).refine(s=>!isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s);
export const articleSchema=z.object({
 automatic:z.boolean().optional(),id:z.string().regex(/^[a-z0-9-]{1,80}$/),title:z.string().min(5).max(200),category:z.enum(['研究','工程','政策']),source:z.string().min(1).max(100),publishedDate:day,importance:z.number().int().min(1).max(5),summary:z.string().min(10).max(1800),why:z.string().min(5).max(1500),limitations:z.string().min(5).max(1500),points:z.array(z.string().max(1000)).max(8),tags:z.array(z.string().max(50)).max(8),evidence:z.enum(['已核验一手来源','原简报归档','自动采集 · 未人工核验']),links:z.array(z.object({label:z.string().min(1).max(120),url:z.string().url().refine(s=>s.startsWith('https://'))})).min(1).max(8),
}).strict();
export const issueSchema=z.object({date:day,title:z.string().min(5).max(200),intro:z.string().max(1800),window:z.string().min(5).max(250),note:z.string().max(1500),articles:z.array(articleSchema).max(60)}).strict().superRefine((v,c)=>{if(new Set(v.articles.map(a=>a.id)).size!==v.articles.length)c.addIssue({code:'custom',message:'Duplicate article IDs'});});
export type Article=z.infer<typeof articleSchema>;
export type Issue=z.infer<typeof issueSchema>&{updatedAt?:string;automatic?:boolean};
