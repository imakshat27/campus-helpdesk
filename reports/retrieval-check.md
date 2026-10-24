# Neural retrieval check

Real all-MiniLM-L6-v2 embeddings and production ranking logic, using an isolated SQLite database with cosine similarity computed in Python. This checks retrieval recall and abstention only; it does not exercise the Neon pgvector SQL operator or OpenRouter generation.

| Query | Expected source / behaviour | Retrieved sources | Result |
|---|---|---|---|
| Where is SJT 301? | faq-01 | Finding room SJT 301; Campus building directory; Laboratory access guide | PASS |
| How can I find TT 204? | faq-02 | Finding room TT 204; Campus building directory | PASS |
| When does the robotics lab close on weekdays? | faq-05 | Robotics lab hours; Laboratory access guide; Computer lab hours; Library opening hours; Chemistry lab hours | PASS |
| Is the computer lab open on Sunday? | faq-06 | Computer lab hours; Laboratory access guide; Robotics lab hours; Laboratory access guide; Chemistry lab hours | PASS |
| How do I register for the Campus Hackathon? | faq-10 | Campus Hackathon registration; October 2026 event guide; Connecting to campus Wi-Fi; Resetting a portal password; Campus building directory | PASS |
| I lost my student ID. How do I get a replacement? | faq-14 | Replacing a lost student ID; Student services handbook; Resetting a portal password; Event registration confirmation; Reporting a maintenance issue | PASS |
| How do I request a bonafide certificate? | faq-15 | Requesting a bonafide certificate; Student services handbook | PASS |
| How late is the library open on Saturday? | faq-20 | Library opening hours; Computer lab hours; Laboratory access guide; Laboratory access guide; Robotics lab hours | PASS |
| What time does the lab open? | clarification | Computer lab hours; Chemistry lab hours; Robotics lab hours; Laboratory access guide; Laboratory access guide | PASS |
| How do I register for the event? | clarification | October 2026 event guide; October 2026 event guide; Event registration confirmation; Research Expo registration; Editing an event registration | PASS |
| What will the weather be in Chennai tomorrow? | escalated | None | PASS |
| What is my personal bank account balance? | escalated | None | PASS |
