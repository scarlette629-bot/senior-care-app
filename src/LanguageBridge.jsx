import React,{useEffect} from "react";
import {getLanguage,tr} from "./i18n";

const originals=new WeakMap();
const attributes=new WeakMap();
const TARGET_ATTRIBUTES=["placeholder","title","aria-label","alt"];
const excluded=new Set(["SCRIPT","STYLE","NOSCRIPT","TEXTAREA","OPTION","CODE","PRE","INPUT","SELECT"]);
function translateElement(root){
 const english=getLanguage()==="en-US";
 const visit=node=>{
   if(node.nodeType===3){
     const parent=node.parentElement;
     if(!parent||excluded.has(parent.tagName)||parent.closest("[contenteditable=true],[data-no-translate],.streamingCard,.streamingNews .streamingDescription,.contactItem .contactActions"))return;
     let source=originals.get(node);
     if(source===undefined){source=node.nodeValue;originals.set(node,source);}
     const desired=english?tr(source):source;
     if(node.nodeValue!==desired){
       // React may have changed this text since the last pass. Capture the
       // new source rather than restoring stale text on language changes.
       const prior=english?tr(source):source;
       if(node.nodeValue!==source && node.nodeValue!==prior){
         source=node.nodeValue;originals.set(node,source);
       }
       const finalText=english?tr(source):source;
       if(node.nodeValue!==finalText)node.nodeValue=finalText;
     }
     return;
   }
   if(node.nodeType!==1)return;
   const el=node;
   if(excluded.has(el.tagName)||el.hasAttribute("data-no-translate"))return;
   for(const attr of TARGET_ATTRIBUTES){
     if(!el.hasAttribute(attr))continue;
     let saved=attributes.get(el);
     if(!saved){saved={};attributes.set(el,saved);}
     const current=el.getAttribute(attr);
     const previous=saved[attr];
     if(!previous||(![previous.source,previous.output].includes(current)))saved[attr]={source:current,output:current};
     const src=saved[attr].source;
     const target=english?tr(src):src;
     saved[attr].output=target;
     if(current!==target)el.setAttribute(attr,target);
   }
   for(const child of [...el.childNodes])visit(child);
 };
 visit(root);
}
export default function LanguageBridge(){
 useEffect(()=>{
   const sync=()=>{const lang=getLanguage();document.documentElement.lang=lang==="en-US"?"en":"zh-Hant";document.title=lang==="en-US"?"WECARE Warm Care | Senior Daily Care":"WECARE 暖心守護｜長者生活照護";translateElement(document.getElementById("root"));};
   const root=document.getElementById("root");
   if(!root)return;
   const observer=new MutationObserver(records=>{
     // The localization pass is idempotent; translation writes are ignored on
     // subsequent passes when they already match the target language.
     if(records.some(record=>record.type!=="attributes"||TARGET_ATTRIBUTES.includes(record.attributeName)))translateElement(root);
   });
   observer.observe(root,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:TARGET_ATTRIBUTES});
   window.addEventListener("wecare-language-change",sync);
   sync();
   return()=>{observer.disconnect();window.removeEventListener("wecare-language-change",sync);};
 },[]);
 return null;
}
