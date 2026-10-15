# Postal Services Agent

## What this agent does
One agent, three profiles, chosen by the orchestrator from the request:

- **Complaints (réclamations):** reads the complaint and its document, the parcel's tracking timeline
  and similar past complaints, then decides **rembourser** (refund), **reexpedier** (re-ship),
  **rejeter** (reject) or **escalader** (escalate), with its confidence and reasoning.
- **Parcel tracking:** timeline of a parcel by tracking number, or the parcels of a customer by email
  (asks for the number when none is given).
- **Postal information:** rates, delivery times, packaging, customs and refund rules from the postal
  knowledge base.

## Example requests
- *Process complaint RECL-2025-0001*
- *Where is my parcel 6C111222333FR?*
- *How much does it cost to send a 2 kg parcel to Canada?*
