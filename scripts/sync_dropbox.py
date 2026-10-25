#!/usr/bin/env python3
"""Import the public Dropbox folder ZIP into the wedding gallery incrementally."""
import argparse,hashlib,json,os,subprocess,tempfile,time,urllib.request,zipfile
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'.dropbox-sync/state.json'
FEED=ROOT/'live-media.json'
IMAGE_EXT={'.jpg','.jpeg','.png','.webp','.heic','.heif','.avif'}
VIDEO_EXT={'.mov','.mp4','.m4v','.webm','.avi','.mkv','.3gp'}
def initial_media():
 return json.loads((ROOT/'media.js').read_text().split('=',1)[1].rstrip(';\n'))
def zip_url(url):
 p=urlsplit(url)
 if p.scheme!='https' or p.hostname not in {'www.dropbox.com','dropbox.com'}:raise ValueError('Expected a Dropbox HTTPS shared folder link')
 query=dict(parse_qsl(p.query));query['dl']='1'
 return urlunsplit((p.scheme,p.netloc,p.path,urlencode(query),''))
def head_size(url):
 req=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'ClaraGuillermoGallery/1.0'})
 with urllib.request.urlopen(req,timeout=60) as r:
  return int(r.headers.get('original-content-length') or r.headers.get('Content-Length') or 0)
def file_key(info):return hashlib.sha256((info.filename+'\0'+str(info.CRC)+'\0'+str(info.file_size)).encode()).hexdigest()
def photo(src,dest,thumb):
 try:
  import pillow_heif
  pillow_heif.register_heif_opener()
 except ImportError:pass
 with Image.open(src) as original:
  im=ImageOps.exif_transpose(original).convert('RGB');im.thumbnail((1800,1800));im.save(dest,'JPEG',quality=86,optimize=True)
  im.thumbnail((600,800));im.save(thumb,'WEBP',quality=80)
  return im.size
def video(src,dest,thumb):
 p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(src)]))
 audio=next((s['index'] for s in p['streams'] if s.get('codec_type')=='audio' and s.get('codec_name') not in (None,'none','unknown')),None)
 cmd=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-i',str(src),'-map','0:v:0']
 cmd+=['-map',f'0:{audio}'] if audio is not None else ['-an']
 cmd+=['-vf',"scale='min(960,iw)':'min(960,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1,fps=30",'-c:v','libx264','-preset','veryfast','-crf','28','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-movflags','+faststart','-threads','2',str(dest)]
 subprocess.run(cmd,check=True,timeout=2400)
 if dest.stat().st_size>95*1024*1024:raise ValueError('Optimized video exceeds GitHub individual file limit')
 subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-i',str(dest),'-frames:v','1','-vf','scale=500:-1',str(thumb)],check=True,timeout=120)
 with Image.open(thumb) as im:return im.size
def atomic_json(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
def sync(url,force=False,archive=None):
 state=json.loads(STATE.read_text()) if STATE.exists() else {'files':{},'last_full_scan':0,'zip_size':0}
 media=json.loads(FEED.read_text())['media'] if FEED.exists() else initial_media()
 url=zip_url(url);size=0 if archive else head_size(url)
 # Folder ZIPs expose length but no ETag. A daily full scan also detects equal-size replacements.
 if not archive and not force and size>0 and size==state.get('zip_size') and time.time()-state.get('last_full_scan',0)<86400:
  print('Dropbox size unchanged; daily integrity scan not due.');return 0
 with tempfile.TemporaryDirectory(prefix='wedding-sync-') as work:
  work=Path(work);zpath=Path(archive) if archive else work/'dropbox.zip'
  if not archive:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ClaraGuillermoGallery/1.0'}),timeout=180) as response,zpath.open('wb') as out:
    import shutil
    shutil.copyfileobj(response,out)
  assets=ROOT/'assets/live';assets.mkdir(parents=True,exist_ok=True);added=[];errors=[]
  with zipfile.ZipFile(zpath) as z:
   for info in z.infolist():
    suffix=Path(info.filename).suffix.lower()
    if info.is_dir() or suffix not in IMAGE_EXT|VIDEO_EXT:continue
    key=file_key(info)
    if key in state['files']:continue
    src=work/(key+suffix)
    with z.open(info) as inp,src.open('wb') as out:
     import shutil
     shutil.copyfileobj(inp,out)
    typ='photo' if suffix in IMAGE_EXT else 'video';dest=assets/(key[:24]+('.jpg' if typ=='photo' else '.mp4'));thumb=assets/(key[:24]+('-thumb.webp' if typ=='photo' else '-thumb.jpg'))
    try:
     width,height=photo(src,dest,thumb) if typ=='photo' else video(src,dest,thumb)
     m={'id':key,'type':typ,'src':str(dest.relative_to(ROOT)),'thumb':str(thumb.relative_to(ROOT)),'width':width,'height':height,'alt':'Un momento de la fiesta de Clara y Guillermo','time':Path(info.filename).name}
     state['files'][key]={'name':info.filename,'src':m['src']};added.append(m);print('Imported',typ,Path(info.filename).name,flush=True)
    except Exception as e:
     dest.unlink(missing_ok=True);thumb.unlink(missing_ok=True);errors.append(info.filename);print('Unable to import',Path(info.filename).name,type(e).__name__,str(e),flush=True)
    finally:src.unlink(missing_ok=True)
  media=added+media
  if added:
   atomic_json(FEED,{'updated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'media':media})
   (ROOT/'media.js').write_text('window.WEDDING_MEDIA='+json.dumps(media,ensure_ascii=False)+';\n')
  if added:
   download_paths=[ROOT/n for n in ['index.html','app.js','style.css','media.js','live-media.json']]
   download_paths += [p for p in (ROOT/'assets').rglob('*') if p.is_file() and not p.name.startswith('.')]
   atomic_json(ROOT/'download-files.json',[{'path':str(p.relative_to(ROOT)),'size':p.stat().st_size} for p in sorted(download_paths)])
  state.update(zip_size=size or zpath.stat().st_size,last_full_scan=0 if errors else int(time.time()))
  atomic_json(STATE,state)
  print('Imported',len(added),'new files;',len(errors),'failed.',flush=True)
  if errors:raise RuntimeError('Some media failed; successful imports are retained and failed files will be retried.')
 return len(added)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--force',action='store_true');p.add_argument('--archive');args=p.parse_args()
 url=os.environ.get('DROPBOX_SHARED_LINK')
 if not url:raise SystemExit('Set the DROPBOX_SHARED_LINK repository secret to the shared folder URL.')
 sync(url,args.force,args.archive)
