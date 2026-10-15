# Internal FAQ - Selected Entries (placeholder organization: Apex Logistics)

### Who do I talk to on day one?

**Short answer**: Your hiring manager runs your day-one schedule; if you don't have one yet, message #people-ops.

**Details**:

Day one starts at 09:30 local time with a 30-minute orientation from People Ops, then a 1:1 with your hiring manager who will introduce your team channel and your starter project. Laptop and credentials should be ready at your desk; if anything is missing, ping #it-help. Your first-week schedule is pre-filled in your calendar by 17:00 the day before; review it, push back on conflicts.

**Related**:
- Onboarding handbook (canonical doc).
- New-hire checklist (sortable list).

**Last reviewed**: 2026-04-12 by People Ops Lead

---

### How do I request access to a production system?

**Short answer**: File a ticket in the access-request tracker; production access requires manager approval and a 24-hour audit window.

**Details**:

Production access is gated behind a four-step process: (1) you file the ticket with the system name and your business need, (2) your manager approves in the tracker, (3) the system owner reviews the request, (4) access is granted with a 24-hour audit window during which all your actions are logged for review. Read-only access usually completes in under 4 hours; write access takes 1-2 business days. Emergency access (active incident) bypasses the approval queue and goes through the on-call SRE; the audit happens after the fact.

**Related**:
- Access-request tracker (link).
- Production access policy (canonical doc).

**Last reviewed**: 2026-03-18 by Security Lead

---

### What do I do if I think I clicked a phishing link?

**Short answer**: Disconnect from the network, then immediately page #security-incident.

**Details**:

If you have just clicked a suspicious link or entered credentials into a page you now think was fake: disconnect from VPN and Wi-Fi (this stops further data exfiltration). Then page #security-incident or call the security on-call number on the back of your badge. Do not delete the email - the security team needs the headers. Do not panic; clicking a phishing link is not a fireable mistake; not reporting one is.

**Related**:
- Security incident playbook (canonical doc).
- Recent phishing campaign examples (gallery).

**Last reviewed**: 2026-04-02 by Security Lead
