'use strict';
const $ = id => document.getElementById(id);
let user = null, currentPoint = null, markers = [], selectedSearch = null;
let authMode = 'login';
let map, trailLayer, selectedMarker, highlightedOfficialSegment=null;
let drawMode=false, drawPoints=[], drawLine=null, routeLayers=[], routesCache=[];
const GEO_TILES = 'https://wmts.geo.admin.ch/1.0.0/';

function toast(message) { const e=$('toast'); e.textContent=message; e.classList.remove('hidden'); clearTimeout(toast.timer); toast.timer=setTimeout(()=>e.classList.add('hidden'),3500); }
async function callApi(url, options={}) {
  const res=await fetch(url,{credentials:'same-origin',...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});
  let data; try {data=await res.json();}catch {data={detail:'Unerwartete Serverantwort.'};}
  if(!res.ok) throw new Error(typeof data.detail==='string'?data.detail:'Anfrage fehlgeschlagen.');
  return data;
}
function modal(name, open){$(name+'Modal').classList.toggle('hidden',!open);}
function setUser(value) {
  user=value;
  $('loginButton').classList.toggle('hidden',!!user);
  $('userArea').classList.toggle('hidden',!user);
  $('userName').textContent=user?'@'+user.username:'';
  loadPlaces();
  loadRoutes();
}
function switchTab(tab) {
  document.querySelectorAll('.nav').forEach(e=>e.classList.toggle('active',e.dataset.tab===tab));
  $('exploreView').classList.toggle('hidden',tab!=='explore');
  $('savedView').classList.toggle('hidden',tab!=='saved');
  $('routesView').classList.toggle('hidden',tab!=='routes');
  $('pageCrumb').textContent=({explore:'KARTE',saved:'MERKLISTE',routes:'ROUTEN'})[tab];
  if(tab==='saved')loadPlaces();
  if(tab==='routes')loadRoutes();
  if(tab==='explore')setTimeout(()=>map&&map.invalidateSize(),70);
}
function openAuth(mode='login') {
  authMode=mode;
  $('authTitle').textContent=mode==='login'?'Willkommen zurück.':'Dein Abenteuer beginnt.';
  $('authSubtitle').textContent=mode==='login'?'Melde dich an, um deine Lieblingsorte zu speichern.':'Erstelle ein Konto und speichere Wanderziele.';
  $('authSubmit').textContent=mode==='login'?'Anmelden →':'Konto erstellen →';
  $('authSwitchHint').textContent=mode==='login'?'Noch kein Konto?':'Bereits ein Konto?';
  $('authSwitch').textContent=mode==='login'?'Registrieren':'Anmelden';
  $('authError').classList.add('hidden');modal('auth',true);
}
function escapeHtml(v){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function initMap(){
  if(typeof L==='undefined'){$('map').textContent='Kartenbibliothek konnte nicht geladen werden. Bitte Internetverbindung prüfen.';return;}
  map=L.map('map',{zoomControl:false}).setView([46.83,8.22],8);
  L.control.zoom({position:'bottomright'}).addTo(map);
  L.tileLayer(GEO_TILES+'ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg',{attribution:'© <a href="https://www.swisstopo.admin.ch/" target="_blank">swisstopo</a>',maxZoom:18,maxNativeZoom:18}).addTo(map);
  trailLayer=L.tileLayer(GEO_TILES+'ch.swisstopo.swisstlm3d-wanderwege/default/current/3857/{z}/{x}/{y}.png',{attribution:'Wanderwege: swisstopo / GeoAdmin',opacity:0.92,maxZoom:18,maxNativeZoom:18}).addTo(map);
  map.on('click',async e=>{ if(drawMode){addDrawPoint(e.latlng);return;} if($('officialTrailToggle').checked){await inspectOfficialTrail(e.latlng);return;} currentPoint={lat:e.latlng.lat,lon:e.latlng.lng,name:'Mein Wanderziel'}; if(user)openPlace(); else {toast('Melde dich an, um diesen Ort zu merken.');openAuth();} });
}

async function inspectOfficialTrail(latlng){
  toast('Suche offiziellen Wanderweg in der Nähe …');
  try {
    const result=await callApi(`/api/trails/nearby?lat=${encodeURIComponent(latlng.lat)}&lon=${encodeURIComponent(latlng.lng)}`);
    if(!result.found){toast('Hier liegt kein amtlicher Wanderwegabschnitt im Umkreis von 65 m. Zoome näher heran und klicke auf einen Wanderweg.');return;}
    const s=result.segment;
    if(highlightedOfficialSegment)map.removeLayer(highlightedOfficialSegment);
    highlightedOfficialSegment=L.polyline(s.coordinates.map(c=>[c[1],c[0]]),{color:'#e04e29',weight:7,opacity:.95}).addTo(map);
    const root=document.createElement('div');root.className='route-popup';
    const title=document.createElement('strong');title.textContent='Offizieller Wanderwegabschnitt';
    const details=document.createElement('div');details.className='route-stats';
    const len=document.createElement('span');len.className='route-stat';len.textContent=Number(s.length_km).toFixed(2)+' km';
    const category=document.createElement('span');category.className='route-stat';category.textContent=s.category;
    const caveat=document.createElement('small');caveat.textContent='Länge dieses Abschnitts, nicht die gesamte Wanderroute. Kategorie: swisstopo.';
    details.append(len,category);root.append(title,details,caveat);
    highlightedOfficialSegment.bindPopup(root).openPopup(latlng);
  } catch(e) {toast('Wanderweg-Abfrage fehlgeschlagen: '+e.message);}
}
function openPlace(){if(!currentPoint)return; $('placeName').value=currentPoint.name||'Mein Wanderziel';$('placeNotes').value='';$('coordinates').textContent=`Koordinaten: ${currentPoint.lat.toFixed(5)}, ${currentPoint.lon.toFixed(5)}`;$('placeError').classList.add('hidden');modal('place',true);}
function selectPlace(place){
  selectedSearch=place;
  $('searchInput').value=place.name;
  $('searchResults').classList.add('hidden');
  switchTab('explore');
  if(!map)return;
  map.setView([place.lat,place.lon],13);
  if(selectedMarker)map.removeLayer(selectedMarker);
  selectedMarker=L.marker([place.lat,place.lon]).addTo(map);
  const wrap=document.createElement('div');
  const title=document.createElement('strong');title.textContent=place.name;wrap.append(title);
  const br=document.createElement('br');wrap.append(br);
  const btn=document.createElement('button');btn.textContent='♡ Ort merken';btn.onclick=()=>{currentPoint={lat:place.lat,lon:place.lon,name:place.name};if(!user)openAuth();else openPlace();};wrap.append(btn);
  selectedMarker.bindPopup(wrap).openPopup();
}
async function search(){
  const q=$('searchInput').value.trim(); if(q.length<2){toast('Mindestens zwei Zeichen eingeben.');return;}
  const box=$('searchResults');box.classList.remove('hidden');box.replaceChildren();
  const loading=document.createElement('div');loading.className='result empty';loading.textContent='Orte werden gesucht …';box.append(loading);
  try{
    const {results}=await callApi('/api/geoadmin/search?q='+encodeURIComponent(q));
    box.replaceChildren();
    if(!results.length){const row=document.createElement('div');row.className='result empty';row.textContent='Keine Orte gefunden. Versuche einen anderen Ortsnamen.';box.append(row);return;}
    results.forEach(item=>{const row=document.createElement('button');row.className='result';row.textContent=item.name;const sub=document.createElement('small');sub.textContent='Schweiz · Ort anzeigen ↗';row.append(sub);row.onclick=()=>selectPlace(item);box.append(row);});
  }catch(err){box.replaceChildren();const div=document.createElement('div');div.className='result empty';div.textContent=err.message;box.append(div);}
}
async function loadPlaces(){
  const box=$('savedList'); if(!user){$('savedCount').textContent='0';box.innerHTML='<div class="empty-state"><div style="font-size:35px">♡</div><h2>Deine Merkliste wartet.</h2><p>Melde dich an, um Orte dauerhaft zu speichern.</p><button class="primary" id="loginFromSaved">Jetzt anmelden →</button></div>';$('loginFromSaved').onclick=()=>openAuth();return;}
  try{
    const places=await callApi('/api/places');$('savedCount').textContent=places.length;box.replaceChildren();
    markers.forEach(m=>map&&map.removeLayer(m));markers=[];
    if(!places.length){box.innerHTML='<div class="empty-state"><div style="font-size:35px">♡</div><h2>Noch keine Orte gespeichert.</h2><p>Suche auf der Karte nach einem Ort und merke ihn dir.</p><button class="primary" id="backExplore">Zur Karte →</button></div>';$('backExplore').onclick=()=>switchTab('explore');return;}
    places.forEach(place=>{
      if(map){const marker=L.circleMarker([place.lat,place.lon],{radius:7,color:'#216e4d',weight:2,fillColor:'#66b583',fillOpacity:.9}).addTo(map);marker.bindPopup(escapeHtml(place.name));markers.push(marker);}
      const card=document.createElement('article');card.className='saved-card';
      card.innerHTML=`<span style="font-size:25px;color:#398263">⌖</span><h3>${escapeHtml(place.name)}</h3><small>${place.lat.toFixed(4)}, ${place.lon.toFixed(4)}</small><p>${place.notes?escapeHtml(place.notes):'Noch keine Notizen hinzugefügt.'}</p><div class="saved-card-actions"><button class="goto">Auf Karte ↗</button><button class="edit">Notiz</button><button class="danger delete">Löschen</button></div>`;
      card.querySelector('.goto').onclick=()=>selectPlace(place);
      card.querySelector('.edit').onclick=async()=>{const notes=prompt('Persönliche Notiz (maximal 1000 Zeichen):',place.notes);if(notes===null)return;try{await callApi('/api/places/'+place.id,{method:'PATCH',body:JSON.stringify({notes})});await loadPlaces();toast('Notiz aktualisiert.');}catch(e){toast(e.message);}};
      card.querySelector('.delete').onclick=async()=>{if(!confirm('Diesen Ort wirklich löschen?'))return;try{await callApi('/api/places/'+place.id,{method:'DELETE'});await loadPlaces();toast('Ort entfernt.');}catch(e){toast(e.message);}};
      box.append(card);
    });
  }catch(err){toast(err.message);}
}
// Events
$('loginButton').onclick=()=>openAuth();
$('logoutButton').onclick=async()=>{try{await callApi('/api/logout',{method:'POST'});setUser(null);toast('Du bist abgemeldet.');}catch(e){toast(e.message);}};
$('authSwitch').onclick=()=>openAuth(authMode==='login'?'register':'login');
document.querySelectorAll('[data-close]').forEach(e=>e.onclick=()=>modal(e.dataset.close,false));
document.querySelectorAll('[data-tab]').forEach(e=>e.onclick=()=>switchTab(e.dataset.tab));
document.querySelectorAll('.quick').forEach(e=>e.onclick=()=>{switchTab('explore');if(map)map.setView([+e.dataset.lat,+e.dataset.lon],+e.dataset.z);});
$('searchButton').onclick=search;$('searchInput').addEventListener('keydown',e=>{if(e.key==='Enter')search();});
$('trailToggle').onclick=()=>{if(!map)return;const on=map.hasLayer(trailLayer);if(on)map.removeLayer(trailLayer);else map.addLayer(trailLayer);$('trailToggle').classList.toggle('on',!on);$('trailToggle').setAttribute('aria-pressed',String(!on));};
$('authForm').onsubmit=async e=>{e.preventDefault();const btn=$('authSubmit');btn.disabled=true;$('authError').classList.add('hidden');try{const data=await callApi('/api/'+(authMode==='login'?'login':'register'),{method:'POST',body:JSON.stringify({username:$('authUser').value,password:$('authPassword').value})});setUser(data);modal('auth',false);$('authPassword').value='';toast('Willkommen bei SwissTrail!');}catch(err){$('authError').textContent=err.message;$('authError').classList.remove('hidden');}finally{btn.disabled=false;}};
$('placeForm').onsubmit=async e=>{e.preventDefault();const btn=e.target.querySelector('[type=submit]');btn.disabled=true;try{await callApi('/api/places',{method:'POST',body:JSON.stringify({...currentPoint,name:$('placeName').value,notes:$('placeNotes').value})});modal('place',false);await loadPlaces();toast('Ort zur Merkliste hinzugefügt!');}catch(err){$('placeError').textContent=err.message;$('placeError').classList.remove('hidden');}finally{btn.disabled=false;}};
// Routing: manual polyline digitising on top of the official raster hiking layer.
function kmBetween(points){
  let sum=0;
  for(let i=1;i<points.length;i++){
    const a=points[i-1],b=points[i],r=Math.PI/180;
    const dLat=(b.lat-a.lat)*r,dLon=(b.lon-a.lon)*r;
    const x=Math.sin(dLat/2)**2+Math.cos(a.lat*r)*Math.cos(b.lat*r)*Math.sin(dLon/2)**2;
    sum+=6371.0088*2*Math.asin(Math.min(1,Math.sqrt(x)));
  }
  return sum;
}
function resetDraw(){
  if(drawLine&&map){map.removeLayer(drawLine);}drawLine=null;drawPoints=[];
}
function setDraw(active){
  drawMode=active;
  $('drawToggle').classList.toggle('active-drawing',active);
  $('drawToggle').textContent=active?'✕ Zeichnen beenden':'＋ Route zeichnen';
  $('drawToggle').setAttribute('aria-pressed',String(active));
  $('undoPoint').classList.toggle('hidden',!active);
  $('finishRoute').classList.toggle('hidden',!active);
  if(map)map.getContainer().style.cursor=active?'crosshair':'';
  if(!active)resetDraw();
  if(active)toast('Klicke nacheinander auf den Verlauf deiner Route. Mindestens zwei Punkte.');
}
function drawPreview(){
  if(drawLine)map.removeLayer(drawLine);
  if(drawPoints.length)drawLine=L.polyline(drawPoints,{color:'#d25b35',weight:5,opacity:.95,dashArray:'10 5'}).addTo(map);
  if(drawPoints.length>1)toast(`${drawPoints.length} Punkte · ${kmBetween(drawPoints).toFixed(2)} km (2D-Streckenlänge)`);
}
function addDrawPoint(point){
  if(drawPoints.length>=120){toast('Maximal 120 Punkte pro Route.');return;}
  drawPoints.push({lat:point.lat,lon:point.lng});drawPreview();
}
function showRoute(route){
  if(!map)return;
  setDraw(false);
  switchTab('explore');
  const poly=routeLayers.find(item=>item.routeId===route.id);
  if(!poly){toast('Route konnte nicht angezeigt werden.');return;}
  const bounds=poly.getBounds();if(bounds.isValid())map.fitBounds(bounds.pad(.22));
  poly.openPopup();
}
function routePopup(route){
  const root=document.createElement('div');root.className='route-popup';
  const title=document.createElement('strong');title.textContent=route.name;
  const distance=document.createElement('div');distance.className='route-stats';
  const length=document.createElement('span');length.className='route-stat';length.textContent=Number(route.length_km).toFixed(2)+' km';
  const difficulty=document.createElement('span');difficulty.className='route-stat';difficulty.textContent=route.difficulty;
  distance.append(length,difficulty);
  const info=document.createElement('small');info.textContent='Distanz aus eingezeichneten Punkten · Schwierigkeit selbst angegeben';
  root.append(title,distance,info);
  if(route.notes){const note=document.createElement('p');note.textContent=route.notes;root.append(note);}
  return root;
}
async function loadRoutes(){
  const box=$('routeList');
  routeLayers.forEach(layer=>map&&map.removeLayer(layer));routeLayers=[];
  if(!user){$('routeCount').textContent='0';box.innerHTML='<div class="empty-state"><h2>Deine Routen warten.</h2><p>Melde dich an und zeichne deine erste Wanderroute.</p></div>';return;}
  try{
    routesCache=await callApi('/api/routes');
    $('routeCount').textContent=routesCache.length;box.replaceChildren();
    if(!routesCache.length){box.innerHTML='<div class="empty-state"><h2>Noch keine Routen</h2><p>Öffne die Karte und klicke auf „Route zeichnen“.</p><button class="primary" id="goDraw">Route zeichnen →</button></div>';$('goDraw').onclick=()=>{switchTab('explore');setDraw(true);};return;}
    routesCache.forEach(route=>{
      if(map){const points=route.points.map(p=>[p.lat,p.lon]);const poly=L.polyline(points,{color:'#186f91',weight:6,opacity:.9}).addTo(map);poly.routeId=route.id;poly.bindPopup(routePopup(route));routeLayers.push(poly);}
      const card=document.createElement('article');card.className='saved-card';
      const heading=document.createElement('h3');heading.textContent=route.name;
      const stats=document.createElement('div');stats.className='route-stats';
      [Number(route.length_km).toFixed(2)+' km',route.difficulty].forEach(t=>{const chip=document.createElement('span');chip.className='route-stat';chip.textContent=t;stats.append(chip);});
      const desc=document.createElement('p');desc.textContent=route.notes||'Eigene, auf der Karte eingezeichnete Route.';
      const hint=document.createElement('small');hint.textContent='Distanz: Stützpunktmessung · Schwierigkeit: Selbsteinschätzung';
      const actions=document.createElement('div');actions.className='saved-card-actions';
      const show=document.createElement('button');show.textContent='Auf Karte ↗';show.onclick=()=>showRoute(route);
      const del=document.createElement('button');del.className='danger';del.textContent='Löschen';del.onclick=async()=>{if(!confirm('Route endgültig löschen?'))return;try{await callApi('/api/routes/'+route.id,{method:'DELETE'});await loadRoutes();toast('Route gelöscht.');}catch(e){toast(e.message);}};
      actions.append(show,del);card.append(heading,stats,desc,hint,actions);box.append(card);
    });
  }catch(e){toast(e.message);}
}
$('drawToggle').onclick=()=>{if(!user){openAuth();toast('Zum Speichern von Routen bitte anmelden.');return;}setDraw(!drawMode);};
$('undoPoint').onclick=()=>{drawPoints.pop();drawPreview();};
$('finishRoute').onclick=()=>{
  if(drawPoints.length<2){toast('Wähle mindestens zwei Punkte auf der Karte.');return;}
  const length=kmBetween(drawPoints);
  if(length<.01||length>250){toast('Streckenlänge muss 10 m bis 250 km betragen.');return;}
  $('routeName').value='Meine Wanderroute';$('routeNotes').value='';$('routeDifficulty').value='Nicht bewertet';
  $('routeDistance').textContent=`${length.toFixed(2)} km · ${drawPoints.length} Punkte (2D-Distanz, keine automatische Wegführung)`;
  $('routeError').classList.add('hidden');modal('route',true);
};
$('routeForm').onsubmit=async e=>{
  e.preventDefault();const btn=e.target.querySelector('[type=submit]');btn.disabled=true;
  try{
    const route=await callApi('/api/routes',{method:'POST',body:JSON.stringify({name:$('routeName').value,difficulty:$('routeDifficulty').value,notes:$('routeNotes').value,points:drawPoints})});
    modal('route',false);setDraw(false);await loadRoutes();toast(`Route gespeichert: ${Number(route.length_km).toFixed(2)} km`);showRoute(route);
  }catch(err){$('routeError').textContent=err.message;$('routeError').classList.remove('hidden');}finally{btn.disabled=false;}
};
// Interactive destination cards are keyboard-accessible native buttons.
document.querySelectorAll('[data-discover-lat]').forEach(button=>{
  button.addEventListener('click',()=>{
    switchTab('explore');
    if(map){map.flyTo([Number(button.dataset.discoverLat),Number(button.dataset.discoverLon)],Number(button.dataset.discoverZ),{duration:1.15});}
    const name=button.querySelector('.destination-bottom strong')?.textContent||'Region';
    toast(name+' entdecken: Klicke auf die Wanderwege für die Details.');
    document.querySelector('.mapcard')?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});
  });
});
$('helpClose')?.addEventListener('click',()=>$('mapHelp')?.classList.add('hidden'));
$('officialTrailToggle')?.addEventListener('change',()=>{
  const label=$('mapHelpText');
  if(label)label.textContent=$('officialTrailToggle').checked?'Klicke auf einen Wanderweg, um Länge und Kategorie zu entdecken.':'Weg-Analyse aus. Klicke in die Karte, um einen Ort zu speichern.';
  $('mapHelp')?.classList.remove('hidden');
});
initMap();callApi('/api/me').then(setUser).catch(()=>setUser(null));

$('officialTrailToggle').addEventListener('change',()=>toast($('officialTrailToggle').checked?'Klicke in die Karte nahe an einen Wanderweg (max. 65 m).':'Wegabfrage deaktiviert – Orte können wieder gemerkt werden.'));
