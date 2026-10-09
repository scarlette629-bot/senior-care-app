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
  const[revision,setRevision]=useState(0);
  const exportBox=useRef(null);
  const mode=(window.navigator.standalone===true||window.matchMedia&&window.matchMedia("(display-mode: standalone)").matches)?"主畫面 APP":"Safari 瀏覽器";
  const storedKeys=listCurrent();
  const counts={meds:summaryCount("wecare-meds"),events:summaryCount("wecare-events"),meals:summaryCount("wecare-meals"),contacts:summaryCount("wecare-contacts")};
  const other=storedKeys.length;
  const exportBackup=()=>{
    const backup=backupCurrent();
    setCopyText(JSON.stringify(backup));
    setStatus("備份文字已產生。請長按下方文字 → 全選 → 複製，再貼到自己的備忘錄中保管。");
  };
  const selectBackup=()=>{
    if(!copyText){setStatus("請先按「產生備份文字」。");return;}
    const box=exportBox.current;
    if(box){box.focus();box.select();box.setSelectionRange(0,box.value.length);}
    setStatus("已選取備份文字。若沒有出現複製選項，請長按文字並選擇「全選、複製」。");
  };
  const importBackup=()=>{
    const raw=pasteText.trim();
    if(!raw){setStatus("請貼上你之前保存的 WECARE 備份文字。");return;}
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
    {copyText&&<><p>下方文字包含你的健康與聯絡資訊，請只保存在自己的裝置，不要張貼到公開網站。</p>
      <textarea ref={exportBox} readOnly rows={5} value={copyText} aria-label="WECARE 本機備份文字" onClick={()=>{}}/>
      <button className="secondary" type="button" onClick={selectBackup}>選取全部備份文字</button>
    </>}
    <h3>從備份文字還原</h3>
    <p>先確認原本 APP 或 Safari 裡仍有舊資料，將備份文字複製過來，再貼到此欄位。</p>
    <textarea rows={4} value={pasteText} onChange={e=>setPasteText(e.target.value)} placeholder="在此貼上之前複製的 WECARE_LOCAL_BACKUP_V1 備份文字" aria-label="貼上 WECARE 備份文字"/>
    <button className="secondary" type="button" onClick={importBackup}>確認並匯入備份</button>
    {status&&<p role="status">{status}</p>}
  </section>;
}
export default DataBackup;
