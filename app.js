const media=window.WEDDING_MEDIA||[];let filter='all',shown=18,current=0;
const featuredGrid=document.querySelector('#featured-gallery'),featuredSection=document.querySelector('#featured-section');
const grid=document.querySelector('#gallery'),modal=document.querySelector('#lightbox');
const filtered=()=>media.filter(m=>filter==='all'||m.type===filter);
function render(){const list=filtered();grid.replaceChildren();featuredGrid.replaceChildren();featuredSection.hidden=!list.some(m=>m.featured);list.slice(0,shown).forEach((m,i)=>{const b=document.createElement('button');b.className='media-card';b.setAttribute('aria-label',`${m.type==='video'?'Ver vídeo':'Ampliar foto'} ${i+1}`);const img=document.createElement('img');img.src=m.thumb;img.alt=m.alt||`Un momento de la fiesta de Clara y Guillermo`;img.loading='lazy';img.width=m.width||500;img.height=m.height||650;b.append(img);if(m.type==='video'){const tag=document.createElement('span');tag.className='video-label';tag.textContent='▶ Vídeo';b.append(tag)}const n=document.createElement('span');n.className='media-index';n.textContent=String(i+1).padStart(2,'0');b.append(n);b.onclick=()=>openMedia(i);(m.featured?featuredGrid:grid).append(b)});document.querySelector('#load-more').hidden=list.length<=shown;document.querySelector('#all-count').textContent=media.length}
function display(){const list=filtered(),m=list[current];if(!m)return;const holder=modal.querySelector('.viewer');holder.replaceChildren();const el=document.createElement(m.type==='video'?'video':'img');el.src=m.src;if(m.type==='video'){el.controls=true;el.playsInline=true;el.poster=m.thumb;el.preload='metadata'}else el.alt=m.alt||'La fiesta de Clara y Guillermo';holder.append(el);document.querySelector('#position').textContent=`${current+1} / ${list.length}`;document.querySelector('#download').href=m.original||m.src;document.querySelector('#prev').disabled=list.length<2;document.querySelector('#next').disabled=list.length<2}
function openMedia(i){current=i;display();modal.showModal();document.body.classList.add('modal-open')}
function step(delta){current=(current+delta+filtered().length)%filtered().length;display()}
modal.querySelector('.close').onclick=()=>modal.close();modal.addEventListener('close',()=>{modal.querySelector('video')?.pause();modal.querySelector('.viewer').replaceChildren();document.body.classList.remove('modal-open')});document.querySelector('#prev').onclick=()=>step(-1);document.querySelector('#next').onclick=()=>step(1);document.addEventListener('keydown',e=>{if(!modal.open)return;if(e.key==='ArrowRight')step(1);if(e.key==='ArrowLeft')step(-1)});
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;shown=18;document.querySelectorAll('[data-filter]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b))});render()});document.querySelector('#load-more').onclick=()=>{shown+=18;render()};
document.querySelector('#share').onclick=async()=>{const data={title:'Clara y Guillermo · Menuda fiesta',text:'Las pruebas de la fiesta. Sube las tuyas también.',url:location.href.split('#')[0]};try{if(navigator.share)await navigator.share(data);else{await navigator.clipboard.writeText(data.url);document.querySelector('#share-status').textContent='Enlace copiado. ¡Al grupo!'}}catch(e){if(e.name!=='AbortError')document.querySelector('#share-status').textContent='Copia el enlace de la barra del navegador para compartirlo.'}};render();

// Refresh the public gallery feed without waiting for another OVH deployment.
const liveBase='https://raw.githubusercontent.com/eltermi/clarayguillermo/main/';
let pendingMedia=null,lastFeed='',refreshing=false;
function applyLiveMedia(items){media.splice(0,media.length,...items);render()}
function safeMediaPath(path){return typeof path==='string'&&/^assets\/[a-zA-Z0-9_./-]+$/.test(path)&&!path.split('/').includes('..')?new URL(path,liveBase).href:null}
async function refreshGallery(){
 if(refreshing||document.visibilityState==='hidden')return;
 refreshing=true;
 try{
  const response=await fetch(liveBase+'live-media.json?v='+Math.floor(Date.now()/60000),{credentials:'omit',cache:'no-store'});
  if(!response.ok)return;
  const feed=await response.json();if(!Array.isArray(feed.media)||!feed.media.length)return;
  const version=JSON.stringify(feed);if(version===lastFeed)return;
  const items=feed.media.map(m=>{const src=safeMediaPath(m.src),thumb=safeMediaPath(m.thumb);return src&&thumb&&['photo','video'].includes(m.type)?{...m,src,thumb,original:src}:null}).filter(Boolean);
  if(items.length!==feed.media.length)return;
  lastFeed=version;
  if(modal.open)pendingMedia=items;else applyLiveMedia(items);
 }catch(error){console.info('Se mantiene el álbum disponible; se volverá a comprobar la galería.')}finally{refreshing=false}
}
modal.addEventListener('close',()=>{if(pendingMedia){applyLiveMedia(pendingMedia);pendingMedia=null}});
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')refreshGallery()});
refreshGallery();setInterval(refreshGallery,60000);
