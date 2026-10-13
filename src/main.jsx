import React from "react";
import {createRoot} from "react-dom/client";
import App from "./App";
import "./styles.css";

class AppErrorBoundary extends React.Component {
  constructor(props){super(props);this.state={error:null}}
  static getDerivedStateFromError(error){return {error}}
  componentDidCatch(error,info){console.error("WECARE v1.06 render error",error,info)}
  render(){
    if(this.state.error)return <main style={{padding:"24px",fontFamily:"sans-serif",lineHeight:1.8,color:"#473e3e"}}>
      <h1>WECARE v1.06 暫時無法顯示</h1>
      <p>新版載入時發生錯誤。請先保留手機原有資料，不要清除儲存空間。</p>
      <p style={{wordBreak:"break-word",fontSize:"13px"}}>錯誤：{String(this.state.error.message||this.state.error)}</p>
      <a href="/senior-care-app/">返回原版 WECARE</a>
    </main>;
    return this.props.children;
  }
}
const root=document.getElementById("root");
try {
  createRoot(root).render(<React.StrictMode><AppErrorBoundary><App/></AppErrorBoundary></React.StrictMode>);
}catch(error){
  console.error("WECARE startup error",error);
  root.textContent="WECARE v1.06 載入失敗："+String(error.message||error);
}
if("serviceWorker"in navigator){
  window.addEventListener("load",async()=>{
    try{
      const base=import.meta.env.BASE_URL;
      const reg=await navigator.serviceWorker.register(base+"sw.js",{scope:base});
      reg.update();
    }catch(e){console.warn("WECARE service worker registration failed",e)}
  });
}
