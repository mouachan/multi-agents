# Tenders Analysis Agent

## What this agent does
Analyses BTP tenders (appels d'offres) and recommends whether to bid.

For a tender, the agent:
1. reads the tender and its documents (OCR by the vision model);
2. finds the company's **similar project references**, the **history of similar tenders** (won and
   lost, with their technical and price scores) and the **internal capabilities** required
   (certifications, teams, equipment);
3. weighs the risks and the fit, and decides **go**, **no_go** or **a_approfondir** (needs a closer
   look), with its confidence and reasoning.

Its decision is saved by the platform, not by the agent. When it hands the case over to a person, it
writes a brief for the reviewer (why it did not decide, what to check, what it leans to); the reviewer
can question the agent before deciding (human in the loop). Personal data is masked before the model
sees it.

## Example requests
- *Analyse tender AO-2026-0042*
- *Which tenders are still pending?*
- *Do we have references for school renovations in Île-de-France?*
