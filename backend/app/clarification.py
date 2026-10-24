"""Prevent guesses when an operational question leaves its subject unnamed."""
import re
from .schemas import Source

IGNORED_NAME_WORDS={'the','campus','event','lab','laboratory','2026'}

def clarification_for(query: str, sources: list[Source], history: list[dict]) -> str | None:
    lower=query.casefold()
    official=any(s.source_url for s in sources)
    hostel_fee=re.search(r'\bhostel\b',lower) and re.search(r'\b(fees?|cost|price)\b',lower)
    fee_procedure=re.search(r'\b(refund|pay|payment|withdraw|book|booking)\b',lower)
    if official and hostel_fee and not fee_procedure:
        # A fee cannot be selected from a multi-category fee sheet without scope.
        details=[(r'\b(men|mens|ladies|women|boys|girls)\b',"men’s or ladies’ hostel"),
                 (r'\b(?:[1-8]|one|two|three|four|six|eight)[ -]?(?:bed|sharing|person)|single|double',"room type and AC/non-AC preference"),
                 (r'\b(indian|nri|foreign|international)\b',"Indian, NRI or foreign student category"),
                 (r'20\d{2}',"academic year")]
        missing=[label for pattern,label in details if not re.search(pattern,lower)]
        if missing:
            return 'To find the applicable hostel fee, please specify: '+ '; '.join(missing)+'.'

    match=re.search(r'\b(?:the|an?|my)\s+(event|lab|laboratory)\b',lower)
    if not match:
        return None
    topic='event' if match.group(1)=='event' else 'lab'
    if topic=='event' and (not re.search(r'\b(register|sign up|deadline|when|where|time|start|held)\b',lower) or re.search(r'\b(confirmation|edit|change|cancel)\b',lower)):
        return None
    if topic=='lab' and not re.search(r'\b(open|close|hours|timings?|when|where|time)\b',lower):
        return None
    names=[]
    for source in sources:
        candidate=(re.search(r'^How do I register for (?:the )?(.+?)\?',source.content,re.I)
                   if topic=='event' else re.match(r'(.+?) lab hours$',source.title,re.I))
        if candidate:
            name=candidate.group(1).strip()
            if name not in names:
                names.append(name)
    # A named subject in the student's recent context can resolve "the event".
    context=' '.join([m['content'] for m in history[-4:] if m['role']=='user']+[query]).casefold()
    context_words=set(re.findall(r'\w+',context))
    if any((set(re.findall(r'\w+',name.casefold()))-IGNORED_NAME_WORDS) & context_words for name in names):
        return None
    if history and not names:
        return None
    choices=', '.join(names)
    if topic=='event':
        return 'Which event would you like to register for?' + (f' The available information covers {choices}.' if choices else '')
    return 'Which lab do you mean?' + (f' The available information covers {choices}.' if choices else '')


def asks_for_price(query: str) -> bool:
    """An exact price request cannot be satisfied by an office/contact answer."""
    q=query.casefold()
    return bool(re.search(r'\bhow much\b.*\b(for|pay|fee|cost|price|charge|fine)\b',q) or
                (re.search(r'\bhow much (?:is|are)\b',q) and not re.search(r'\b(time|duration|distance|days|hours|credits|attendance|percentage)\b',q)) or
                re.search(r'\b(?:what|tell|give)\b.*\b(?:fee|cost|price|charge|amount)\b',q)) and not bool(re.search(r'\b(refund policy|how to pay|payment process)\b',q))


def contains_price(answer: str) -> bool:
    return bool(re.search(r'(?:₹|\$|\bINR\b|\bRs\.?|\brupees?\b)\s*[\d,]+|[\d,]+\s*(?:rupees?|INR)|\b(?:fee|cost|price|charge|amount)\s+(?:is|of|:)\s*\d|\b(?:free of charge|no (?:fee|charge)|complimentary)\b|\b(?:is|are) free\b',answer,re.I))
