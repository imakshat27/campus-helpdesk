"""Build extractive, source-linked Q&A records without synthesizing campus facts."""
import json,re
from .seed import ROOT,official_documents,sections

def run():
 records=[]
 for doc in official_documents():
  for i,(heading,text) in enumerate(sections(doc)):
   if len(text)<100:continue
   # These are discovery prompts and verbatim extracts, not invented FAQs.
   question=f'What does {doc["title"]} say about {heading}?' if not heading.lower().startswith('page ') else f'What information is on {heading.lower()} of {doc["title"]}?'
   records.append({'id':f'{doc["id"]}:{i}','question':question,'answer_extract':text,'title':doc['title'],'heading':heading,'source_url':doc['source_url'],'campus':doc['campus'],'retrieved_at':doc['retrieved_at'],'method':'extractive; no generated facts'})
 (ROOT/'official/qna.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 print(f'Built {len(records)} extractive Q&A records from {len(official_documents())} sources.')
if __name__=='__main__':run()
