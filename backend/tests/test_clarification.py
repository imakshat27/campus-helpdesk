from app.clarification import clarification_for
from app.schemas import Source

def event_source():
    return Source(id='event:0',document_id='event',title='Campus Hackathon registration',heading='Registration',content='How do I register for the Campus Hackathon?\nUse the portal.')

def test_named_event_and_context_resolve_generic_reference():
    source=event_source()
    assert clarification_for('How do I register for the Campus Hackathon?',[source],[]) is None
    assert clarification_for('How do I register for the event?',[source],[{'role':'user','content':'Tell me about the Campus Hackathon'}]) is None

def test_general_event_procedures_do_not_need_specific_subject():
    assert clarification_for('Where can I find the event registration confirmation?',[event_source()],[]) is None

def test_lab_booking_is_a_general_procedure():
    assert clarification_for('How do I book a lab workstation?',[],[]) is None
