"""Reproducible public VIT Vellore import. No portals or unrestricted crawling."""
import argparse,hashlib,io,json,re,time,subprocess,tempfile,shutil
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse,urldefrag
from urllib.robotparser import RobotFileParser
import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader
from markdownify import markdownify
ROOT=Path(__file__).resolve().parents[2]/'knowledge/official'
SEEDS={
'library':['/academics/library'],
'academics':['/academics/ffcs','/academics/academic-regulations','/academics/academic-calendar','/sites/default/files/academic/Academic-Regulations.pdf'],
'hostels':['/campuslife/hostels','/wp-content/uploads/2026/05/First-year-2026-27.pdf','/wp-content/uploads/2026/05/LH-NRI-fees-2026-27.pdf','/wp-content/uploads/2026/06/MH-First-Year-FEE-structure-Indian-NRI-FOREIGN-Category-2026-27.pdf'],
'welfare':['/campuslife/studentswelfare','/student-grievance-redressal-committee','/centre-for-vit-happiness-and-well-being','/counselling-division'],
'facilities':['/about/infrastructure','/campuslife/sports','/campuslife/healthservices','/campuslife/transport','/campuslife/otheramenities'],
'procedures':['/about/administrative-offices','/contactus','/ug-downloads','/scholarship','/internationalrelations'],
'events':['/campuslife/clubs','/campuslife/chapters','/campuslife/campus-events'],
'admissions':['/admissions/ug','/admissions/pg','/admissions/faq'],
'careers':['/cdc-overview','/placement-process','/cdc-office','/cdc-contact-us'],
'accessibility':['/service-and-support-differently-abled-learners-sasdal'],
'safety':['/anti-ragging-committee','/sites/default/files/Student-Code-of-Conduct.pdf'],
'research':['/research/academic','/research/centers-list','/admissions/research'],
'alumni':['/academics/transcripts','/transcripts-for-alumni','/alumni-office-contact'],
'admissions_more':['/admissions/overview','/admissions/international/overview','/admissions/international/research'],
'global':['/internationalrelations/itp','/international-projects-sap']}
PDF_TERMS=('academic-regulation','library-policy','code-of-conduct','codeofconduct','hostel','disabil','anti-ragging','student-handbook','student-guideline')
LINK_TERMS=('disability','grievance','counselling','healthservices','sports','clubs','chapters','ffcs','scholarship','hostels')
def clean(text):return '\n'.join(re.sub(r'[ \t]+',' ',line).rstrip() for line in text.replace('\xa0',' ').splitlines()).strip()
def extract_html(data):
 soup=BeautifulSoup(data,'html.parser');title=clean(soup.title.get_text(' ',strip=True) if soup.title else 'VIT document')[:190]
 main=soup.find('main') or soup.find('article')
 if main is None:raise ValueError('No main content')
 for tag in main.select('script,style,nav,header,footer,form,noscript,.breadcrumb,.breadcrumbs'):tag.decompose()
 # Preserve direct text in divs and table cell relationships as well as paragraphs.
 content=markdownify(str(main),heading_style='ATX',strip=['img','svg','a'])
 blocks=[clean(b) for b in re.split(r'\n\s*\n',content) if clean(b)]
 return title,blocks

def run(refresh=False):
 for folder in ['raw','processed']:(ROOT/folder).mkdir(exist_ok=True,parents=True)
 previous={d['id']:d for d in json.loads((ROOT/'manifest.json').read_text()).get('documents',[])} if (ROOT/'manifest.json').exists() else {}
 pending=[('https://vit.ac.in'+path,cat) for cat,paths in SEEDS.items() for path in paths];docs=[];failures=[];seen=set();robots=RobotFileParser()
 with httpx.Client(timeout=35,follow_redirects=True,headers={'User-Agent':'CampusHelpdeskResearch/1.0 (student project; public sources)'}) as client:
  robots.parse(client.get('https://vit.ac.in/robots.txt').text.splitlines())
  while pending and len(seen)<85:
   url,category=pending.pop(0);url=urldefrag(url)[0]
   category={'admissions_more':'admissions','global':'international'}.get(category,category)
   if url in seen:continue
   seen.add(url)
   if urlparse(url).hostname not in ('vit.ac.in','www.vit.ac.in') or not robots.can_fetch('*',url):
    failures.append({'url':url,'reason':'Outside allowed public scope'});continue
   ident='vit-'+hashlib.sha256(url.encode()).hexdigest()[:14];cache=ROOT/'raw'/ident
   try:
    if cache.exists() and not refresh:data=cache.read_bytes()
    else:
     time.sleep(.35);response=client.get(url);response.raise_for_status()
     if urlparse(str(response.url)).hostname not in ('vit.ac.in','www.vit.ac.in'):raise ValueError('External redirect')
     data=response.content
     if len(data)>18_000_000:raise ValueError('Source exceeds 18 MB')
     cache.write_bytes(data)
    if data.startswith(b'%PDF') and (ROOT/'processed'/f'{ident}.md').exists() and not refresh and previous.get(ident,{}).get('sha256')==hashlib.sha256(data).hexdigest():
     blocks=(ROOT/'processed'/f'{ident}.md').read_text().split('\n\n')
     title=urlparse(url).path.split('/')[-1].replace('.pdf','').replace('-',' ')
    elif data.startswith(b'%PDF'):
     reader=PdfReader(io.BytesIO(data));blocks=[]
     for i,page in enumerate(reader.pages[:150]):
      text=page.extract_text() or ''
      if len(text.strip())<50 and shutil.which('pdftoppm') and shutil.which('tesseract'):
       with tempfile.TemporaryDirectory() as tmp:
        pdf=Path(tmp)/'source.pdf';pdf.write_bytes(data)
        subprocess.run(['pdftoppm','-f',str(i+1),'-l',str(i+1),'-scale-to','1800','-png','-singlefile',str(pdf),str(Path(tmp)/'page')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=40)
        text=subprocess.run(['tesseract',str(Path(tmp)/'page.png'),'stdout'],capture_output=True,text=True,check=True,timeout=45).stdout
      if text.strip():blocks.extend(['## Page '+str(i+1),clean(text)])
     title=urlparse(url).path.split('/')[-1].replace('.pdf','').replace('-',' ')
    else:
     title,blocks=extract_html(data);main=BeautifulSoup(data,'html.parser').find('main')
     if main:
      for a in main.find_all('a',href=True):
       link=urljoin(url,a['href']);path=urlparse(link).path.lower()
       if urlparse(link).hostname not in ('vit.ac.in','www.vit.ac.in') or '?' in link:continue
       if path.endswith('.pdf') and any(t in path for t in PDF_TERMS):
        if 'hostel' in path and re.search(r'202[0-5]|2[0-5]-2[1-6]',path):continue
        pending.append((link,category))
       elif any(t in path for t in LINK_TERMS) and not path.endswith(('.pdf','.jpg','.png','.docx','.zip')):pending.append((link,category))
    if sum(map(len,blocks))<200:raise ValueError('Too little extractable content')
    content='\n\n'.join(blocks);(ROOT/'processed'/f'{ident}.md').write_text(content)
    docs.append({'id':ident,'title':clean(title)[:190],'category':category,'kind':'official','file':f'processed/{ident}.md','source_url':url,'campus':'Vellore','retrieved_at':datetime.fromtimestamp(cache.stat().st_mtime,timezone.utc).isoformat(),'format':'PDF (text extraction or OCR)' if data.startswith(b'%PDF') else 'HTML','sha256':hashlib.sha256(data).hexdigest(),'content_characters':len(content),'approved':True})
    print('Downloaded',category,title[:75],len(content),flush=True)
   except Exception as exc:failures.append({'url':url,'reason':str(exc)[:160]});print('Excluded',url,type(exc).__name__,flush=True)
 unique={}
 for d in docs:
  digest=hashlib.sha256((ROOT/d['file']).read_bytes()).hexdigest()
  if digest not in unique:unique[digest]=d
 docs=list(unique.values())
 counts={}
 for d in docs:
  for block in set((ROOT/d['file']).read_text().split('\n\n')):counts[block]=counts.get(block,0)+1
 for d in docs:
  path=ROOT/d['file'];blocks=[b for b in path.read_text().split('\n\n') if counts[b]<3 or len(b)>400 or b.startswith('## Page')]
  path.write_text('\n\n'.join(blocks));d['content_characters']=sum(map(len,blocks))
 for d in docs:
  if d['content_characters']<200:failures.append({'url':d['source_url'],'reason':'Too little content after boilerplate removal'})
 docs=[d for d in docs if d['content_characters']>=200]
 (ROOT/'manifest.json').write_text(json.dumps({'scope':'VIT Vellore public website; current pages and dated documents','documents':docs,'excluded':failures},indent=2)+'\n')
 print('Imported',len(docs),'sources;',len(failures),'excluded',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');run(p.parse_args().refresh)
