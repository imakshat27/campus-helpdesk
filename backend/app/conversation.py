"""Conversation-level actions do not depend on a vector match or LLM permission."""
import re

YES={'yes','yes please','please do','go ahead','sure','raise a ticket','raise ticket','yes raise a ticket','yes raise the ticket','please raise a ticket','create a ticket','yes create a ticket','yes please raise a ticket','please raise ticket','raise one','yes do that','yes go ahead','send it to staff','please send it to staff','yes send it to staff','raise a support ticket'}
NO={'no','no thanks','no thank you','not now','nope','dont','do not','dont raise a ticket','do not raise a ticket','cancel','skip'}

def normalized(text):
    return re.sub(r'[^\w\s]','',text.casefold()).strip()

def ticket_decision(query):
    value=normalized(query)
    if value in YES:return True
    if value in NO:return False
    return None

def conversational_reply(query):
    value=normalized(query)
    if value in {'hi','hello','hey','good morning','good afternoon','good evening'}:
        return 'Hi. What can I help you find on campus?'
    if value in {'thanks','thank you','thank you so much','thanks a lot','great thanks','got it thanks'}:
        return 'You’re welcome. Ask if you need anything else.'
    if value in {'ok','okay','got it','understood','cool'}:
        return 'Got it. Is there anything else you’d like to know?'
    return None
