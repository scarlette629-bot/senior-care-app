import React,{useRef,useState} from "react";

// Everything stays on the user's device. No backup content is uploaded,
// emailed, logged, or inserted into the address bar.
const PREFIX="wecare-";
const FORMAT="WECARE_LOCAL_BACKUP_V1";
const MAX_IMPORT_LENGTH=1500000;
const summaryCount=(key)=>{
  try {
    const item=JSON.parse(localStorage.getItem(key)||"null");
    return Array.isArray(item)?item.length:item?1:0;
  }catch{return 0;}
};
const listCurrent=()=>{
  const keys=[];
  try{
    for(let n=0;n<localStorage.length;n++){
      const k=localStorage.key(n);
      if(k&&k.indexOf(PREFIX)===0&&k.indexOf("wecare-recovery-before-import-")!==0)keys.push(k);
    }
  }catch{}
  return keys;
};
const backupCurrent=()=>{
  const data={};
  listCurrent().forEach(k=>{const val=localStorage.getItem(k);if(val!==null)data[k]=val;});
  return {format:FORMAT,exportedAt:new Date().toISOString(),data};
};
function DataBackup(){
  const[copyText,setCopyText]=useState("");
  const[pasteText,setPasteText]=useState("");
  const[status,setStatus]=useState("");
  const[verifyText,setVerifyText]=useState("");
  const exportBox=useRef(null);
  const mode=(window.navigator.standalone===true||window.matchMedia&&window.matchMedia("(display-mode: standalone)").matches)?"主畫面 APP":"Safari 瀏覽器";
  const storedKeys=listCurrent();
  const counts={meds:summaryCount("wecare-meds"),events:summaryCount("wecare-events"),meals:summaryCount("wecare-meals"),contacts:summaryCount("wecare-contacts")};
  const other=storedKeys.length;
  const exportBackup=()=>{
    const backup=backupCurrent();
    setCopyText(JSON.stringify(backup));
    setVerifyText("");
    setStatus("備份文字已產生。請按下方「一鍵複製備份」，然後貼到自己的備忘錄。");
  };
  const selectBackup=()=>{
    if(!copyText){setStatus("請先按「產生本機備份文字」。");return;}
    const box=exportBox.current;
    if(box){
      try{
        // Older iPhone Safari sometimes refuses to select read-only text.
        const readonly=box.readOnly;
        box.readOnly=false;
        box.focus();
        box.select();
        box.setSelectionRange(0,box.value.length);
        box.readOnly=readonly;
      }catch(e){
        console.warn("Manual backup selection unavailable",e);
      }
    }
    setStatus("已嘗試選取備份文字。請點畫面上的「複製」，或長按備份文字選擇「全選」再「複製」。只選取不代表已複製。");
  };
  const copyBackup=()=>{
    if(!copyText){setStatus("請先產生本機備份文字。");return;}
    // execCommand must execute directly in the button click for iOS 12.
    const box=exportBox.current;
    let copied=false;
    if(box){
      try{
        const readonly=box.readOnly;
        box.readOnly=false;
        box.focus();
        box.select();
        box.setSelectionRange(0,box.value.length);
        copied=typeof document.execCommand==="function"&&document.execCommand("copy")===true;
        box.readOnly=readonly;
      }catch(e){console.warn("Legacy iPhone copy failed",e);box.readOnly=true;}
    }
    if(copied){
      setStatus("✅ 已複製備份文字！請貼到自己的備忘錄，確認開頭是 WECARE_LOCAL_BACKUP_V1 而不是 APP 網址。");
      return;
    }
    if(navigator.clipboard&&typeof navigator.clipboard.writeText==="function"){
      navigator.clipboard.writeText(copyText).then(()=>{
        setStatus("✅ 已複製備份文字！請貼到自己的備忘錄，確認不是 APP 網址。");
      }).catch(()=>{
        setStatus("⚠️ 這台 iPhone 無法自動複製。請按「選取備份文字」，長按文字，選「全選」再按「複製」。");
      });
      return;
    }
    setStatus("⚠️ 這台 iPhone 無法自動複製。請按「選取備份文字」，長按文字，選「全選」再按「複製」。");
  };
  const testPaste=()=>{
    if(!copyText){setStatus("請先產生備份文字。");return;}
    const sample=verifyText.trim();
    if(sample===copyText){
      setStatus("✅ 測試通過：剪貼簿裡是完整的 WECARE 備份文字！請再貼到自己的備忘錄保存。");
    }else if(/^https?:\\/\\//i.test(sample)){
      setStatus("❌ 貼上的是網站網址，不是 WECARE 備份！請回到上方按「一鍵複製備份」，不要按匯入。");
    }else if(!sample){
      setStatus("請先長按下方測試框並點「貼上」，再按「檢查貼上內容」。");
    }else{
      setStatus("⚠️ 目前貼上的內容不等於完整備份，請重新按「一鍵複製備份」再測試。");
    }
  };
  const importBackup=()=>{
    const raw=pasteText.trim();
    if(!raw){setStatus("請貼上你之前保存的 WECARE 備份文字。");return;}
    if(/^https?:\\/\\//i.test(raw)){setStatus("這是 APP 網址，不是備份資料！沒有匯入也沒有改動原資料。");return;}
    if(raw.length>MAX_IMPORT_LENGTH){setStatus("備份內容過大，已取消匯入，以免手機儲存空間不足。");return;}
    let backup;
    try{backup=JSON.parse(raw);}catch{setStatus("這不是有效的 JSON 備份文字，沒有更動資料。");return;}
    if(!backup||backup.format!==FORMAT||!backup.data||typeof backup.data!=="object"||Array.isArray(backup.data)){
      setStatus("備份格式不正確，沒有更動資料。");return;
    }
    const entries=Object.entries(backup.data);
    if(!entries.length||entries.length>150||entries.some(([key,val])=>typeof key!=="string"||key.indexOf(PREFIX)!==0||key.length>128||key.indexOf("wecare-recovery-before-import-")===0||typeof val!=="string"||val.length>500000)){
      setStatus("備份內容驗證失敗，沒有更動資料。");return;
    }
    if(!window.confirm("將這份備份匯入目前的「"+mode+"」資料空間。同名紀錄會被備份內容覆蓋。程式會先保存目前資料的安全快照。確定繼續？"))return;
    const before=backupCurrent();
    const snapshotKey="wecare-recovery-before-import-"+Date.now();
    try{localStorage.setItem(snapshotKey,JSON.stringify(before));}
    catch(e){setStatus("手機無法保存匯入前的安全快照，因此已取消匯入，原資料未變動。");return;}
    try {
      entries.forEach(([key,val])=>localStorage.setItem(key,val));
    }catch(e){
      // Best-effort rollback if the older iPhone has run out of storage.
      const existing=before.data;
      entries.forEach(([key])=>{
        try{if(Object.prototype.hasOwnProperty.call(existing,key))localStorage.setItem(key,existing[key]);else localStorage.removeItem(key);}catch{}
      });
      setStatus("手機儲存空間不足，匯入未完成；已嘗試恢復原資料。請保留你貼上的備份文字。");
      return;
    }
    setStatus("匯入完成，現在重新讀取 WECARE。匯入前的資料快照仍留在此裝置。");
    window.location.reload();
  };
  return <section className="dataBackupPanel" aria-label="本機資料檢查與備份">
    <h2>🛡️ 本機資料檢查與備份</h2>
    <p>目前開啟方式：<strong>{mode}</strong>。iPhone 的主畫面 APP 和 Safari 可能有不同的本機資料，兩邊請分別檢查。</p>
    <p>此處目前找到：<strong>用藥設定 {counts.meds} 筆、行程 {counts.events} 筆、飲食 {counts.meals} 筆、聯絡人 {counts.contacts} 筆</strong>，另有 {Math.max(0,other)} 個 WECARE 資料項目。</p>
    <p>如果這裡找不到舊資料，請先回到原本使用的主畫面 APP 或 Safari 檢查；匯入功能不能從已被清除的儲存空間憑空找回紀錄。</p>
    <button className="secondary" type="button" onClick={exportBackup}>產生本機備份文字</button>
    {copyText&&<><p>下方是備份文字，不是網址。它可能含有健康資料及電話，請只保存到自己的備忘錄，不要傳給其他人。</p>
      <button className="primary" type="button" onClick={copyBackup}>📋 一鍵複製備份文字</button>
      <textarea ref={exportBox} readOnly spellCheck={false} rows={5} value={copyText} aria-label="WECARE 本機備份文字"/>
      <button className="secondary" type="button" onClick={selectBackup}>如果無法複製：選取備份文字</button>
      <h3>檢查是不是成功複製</h3>
      <p>可以先在下方框內長按「貼上」，再按「檢查貼上內容」。這個測試不會清除或匯入任何資料。</p>
      <textarea rows={3} spellCheck={false} value={verifyText} onChange={e=>setVerifyText(e.target.value)} placeholder="測試貼上區：請貼入剛才複製的備份文字" aria-label="測試剪貼簿的備份內容"/>
      <button className="secondary" type="button" onClick={testPaste}>檢查貼上內容</button>
    </>}
    <h3>從備份文字還原</h3>
    <p>先確認原本 APP 或 Safari 裡仍有舊資料，將備份文字複製過來，再貼到此欄位。</p>
    <textarea rows={4} value={pasteText} onChange={e=>setPasteText(e.target.value)} placeholder="在此貼上之前複製的 WECARE_LOCAL_BACKUP_V1 備份文字" aria-label="貼上 WECARE 備份文字"/>
    <button className="secondary" type="button" onClick={importBackup}>確認並匯入備份</button>
    {status&&<p role="status">{status}</p>}
  </section>;
}
export default DataBackup;
