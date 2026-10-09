const BASE="/senior-care-app/";
const CACHE="wecare-v1.0.5-shell";
const SHELL=[BASE,BASE+"manifest.webmanifest",BASE+"icon.svg",BASE+"wecare-logo.svg"];
self.addEventListener("install",event=>{
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).catch(()=>{}));
});
self.addEventListener("activate",event=>{
  event.waitUntil(Promise.all([
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith("wecare-")&&k!==CACHE).map(k=>caches.delete(k)))),
    self.clients.claim()
  ]));
});
self.addEventListener("fetch",event=>{
  if(event.request.method!=="GET")return;
  const url=new URL(event.request.url);
  if(url.origin!==self.location.origin||!url.pathname.startsWith(BASE))return;
  // Version checks must use the network; cached version.json causes fake
  // "already latest" messages in installed iOS and Android PWAs.
  if(url.pathname===BASE+"version.json") {
    event.respondWith(fetch(event.request,{cache:"no-store"}));
    return;
  }
  if(event.request.mode==="navigate"){
    event.respondWith(fetch(event.request,{cache:"no-store"}).then(response=>{
      if(response.ok){const clone=response.clone();caches.open(CACHE).then(c=>c.put(BASE,clone)).catch(()=>{});}
      return response;
    }).catch(()=>caches.match(BASE)));
    return;
  }
  // Vite assets are content-hashed. Network-first and offline fallback for
  // static assets, but never cache server errors or cross-origin requests.
  event.respondWith(fetch(event.request).then(response=>{
    if(response.ok){const clone=response.clone();caches.open(CACHE).then(c=>c.put(event.request,clone)).catch(()=>{});}
    return response;
  }).catch(()=>caches.match(event.request)));
});
self.addEventListener("message",event=>{if(event.data==="SKIP_WAITING")self.skipWaiting()});
