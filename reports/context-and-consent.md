# Live conversation and ticket-consent regression

All checks passed against the configured OpenRouter model and Neon database. Covers the reported six-word fee follow-up, two further contextual questions, a new topic, a missing answer, decline, and explicit ticket consent. Staff queue counts were checked before and after consent. One test ticket is created only after “yes please”.

| Query | Outcome | Answer | Sources |
|---|---|---|---|
| How do I replace a lost student ID? | answered | To replace a lost student ID, report it through the Student portal → Student services → ID replacement. You will need to upload a recent photograph and pay a replacement fee of ₹200. The replacement ID can be collected from the Student Support Office after three working days, along with your application receipt. | Replacing a lost student ID, Student services handbook |
| so how much do i pay? | answered | The replacement fee for a lost student ID is ₹200. | Replacing a lost student ID, Student services handbook |
| And where do I collect it once it is ready? | answered | You can collect your replacement ID from the Student Support Office after three working days, along with your application receipt. | Replacing a lost student ID, Student services handbook |
| How long do I have to wait before I can collect it? | answered | You can collect your replacement ID after three working days. | Replacing a lost student ID, Student services handbook |
| What time does the library close on Sunday? | answered | The library closes at 5:00 PM on Sunday. | Library opening hours |
| What is my personal bank account balance? | needs_staff_confirmation | I couldn’t find an answer in the approved campus information. Would you like me to raise a ticket for student support? | — |
| no thanks | conversation | Okay, I won’t raise a ticket. You can ask another question whenever you’re ready. | — |
| Can you tell me tomorrow’s weather in Chennai? | needs_staff_confirmation | I couldn’t find an answer in the approved campus information. Would you like me to raise a ticket for student support? | — |
| yes please | escalated | I’ve raised a ticket for your question. Student support can review it in the staff queue. | — |
