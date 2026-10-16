import type {Article,Topic} from './brief-schema';

export const sections:{id:Topic|'all';label:string;description:string}[]=[
 {id:'all',label:'全部',description:'所有研究板块'},
 {id:'safety',label:'Safety',description:'安全、对齐、可控性与智能体风险'},
 {id:'deep-learning',label:'Deep Learning',description:'神经网络、模型架构、表征学习与扩散模型'},
 {id:'rl',label:'RL',description:'强化学习、策略优化、奖励模型与 RLHF'},
 {id:'foundation-models',label:'基座模型研究',description:'语言与多模态模型、预训练、后训练与规模规律'},
];
export type Section=typeof sections[number]['id'];
export function inSection(article:Article,section:Section){
 return section==='all'||(article.topics??['safety']).includes(section);
}
export function initialSection():Section{
 try{const stored=localStorage.getItem('signal-section');if(sections.some(s=>s.id===stored))return stored as Section;}catch{}
 return 'safety';
}
