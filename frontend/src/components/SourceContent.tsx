import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function SourceContent({content,title}:{content:string;title:string}) {
  const lines=content.split('\n');
  if(lines[0]?.replace(/^#+\s*/,'').trim()===title)lines.shift();
  return <div className="source-document"><ReactMarkdown remarkPlugins={[remarkGfm]} components={{h1:({children})=><h3>{children}</h3>,h2:({children})=><h3>{children}</h3>,h3:({children})=><h3>{children}</h3>,table:({children})=><div className="source-table"><table>{children}</table></div>,a:({href,children})=><a href={href} target="_blank" rel="noreferrer">{children}</a>}}>{lines.join('\n')}</ReactMarkdown></div>;
}

