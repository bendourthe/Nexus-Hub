# Framework Standards Reference

Worked mapping for the example used in this skill's body (`analyzing-network-traffic-of-malware`). Each row gives the framework identifier, the framework's own short title for it (cited, not paraphrased), the rationale that ties the artifact to the ID, and a deep link to the public source.

## ATT&CK T1071 -- Application Layer Protocol

- Framework: MITRE ATT&CK (Enterprise matrix), techniques sub-catalog.
- Short title: "Application Layer Protocol".
- Rationale: malware that hides command-and-control inside HTTP/HTTPS/DNS is performing T1071 from the network's perspective; analyzing that traffic is the detection lens.
- Source: https://attack.mitre.org/techniques/T1071/

## ATT&CK T1003.001 -- OS Credential Dumping: LSASS Memory

- Framework: MITRE ATT&CK, sub-technique of T1003.
- Short title: "LSASS Memory".
- Rationale: cited here as the canonical example used elsewhere in the skill body for "use the most specific sub-technique" guidance.
- Source: https://attack.mitre.org/techniques/T1003/001/

## ATLAS AML.T0047 -- ML-Enabled Product or Service

- Framework: MITRE ATLAS.
- Short title: "ML-Enabled Product or Service".
- Rationale: when the network-traffic analysis is being performed by or against an ML-enabled detection product, ATLAS frames the same observation in adversarial-ML terms.
- Source: https://atlas.mitre.org/techniques/AML.T0047

## D3FEND D3-NTA -- Network Traffic Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Network Traffic Analysis".
- Rationale: the defender action the skill teaches -- inspecting flow records and packet metadata for malicious patterns -- is exactly what D3FEND defines under D3-NTA.
- Source: https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/

## NIST CSF DE.CM -- Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: the skill is a continuous-monitoring practice; CSF's Detect / Continuous Monitoring category is its governance-level home.
- Source: https://www.nist.gov/cyberframework

## NIST CSF ID.RA -- Risk Assessment

- Framework: NIST Cybersecurity Framework, Identify function.
- Short title: "Risk Assessment".
- Rationale: cited as the secondary CSF category for any analysis skill whose findings feed an enterprise risk picture.
- Source: https://www.nist.gov/cyberframework

## NIST AI RMF MEASURE-2.6 -- AI System Safety Evaluation

- Framework: NIST AI Risk Management Framework, Measure function.
- Short title: "AI system is evaluated regularly for safety risks".
- Rationale: when the detection product being analyzed is itself an AI system, AI RMF MEASURE-2.6 governs the recurring safety evaluation the skill's output feeds.
- Source: https://www.nist.gov/itl/ai-risk-management-framework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, ATLAS, D3FEND) and the National Institute of Standards and Technology (NIST CSF, AI RMF).
