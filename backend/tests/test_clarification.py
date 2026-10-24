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


def test_official_hostel_fee_needs_student_and_room_scope():
    from app.schemas import Source
    from app.clarification import clarification_for
    source=Source(id='official:0',document_id='official',title='Hostel fee 2026-27',heading='Fees',content='Fees depend on student and room categories.',source_url='https://vit.ac.in/hostel-fees.pdf')
    answer=clarification_for('How much is the hostel fee?',[source],[])
    assert 'room type' in answer and 'student category' in answer and 'academic year' in answer
    assert clarification_for('What is the hostel fee for men 4 bed AC Indian students in 2026-27?',[source],[]) is None
    assert clarification_for('How do I pay the hostel fee?',[source],[]) is None
    assert clarification_for('What is the hostel fee refund policy?',[source],[]) is None


def test_price_guard_does_not_treat_phone_numbers_as_a_fee():
    from app.clarification import asks_for_price,contains_price
    assert asks_for_price('How much for a new ID card?')
    assert asks_for_price('How much is a replacement ID card?')
    assert asks_for_price('What is the duplicate ID replacement fee?')
    assert not asks_for_price('How much time does ID replacement take?')
    assert not asks_for_price('How do I pay hostel fees?')
    assert not contains_price('Contact Records Section at 0416 220 2174.')
    assert not contains_price('Feel free to contact the office for the fee: phone 0416.')
    assert contains_price('The published fee is ₹500.')
    assert contains_price('The service is free of charge.')
