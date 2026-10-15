# Claims Processing Agent

## What this agent does
Processes insurance claims end to end and answers questions about them in the chat.

For a claim, the agent:
1. reads the claim and its document (OCR by the vision model);
2. retrieves the claimant's **active contracts** and the decisions of **similar past claims**;
3. computes the **payout** with `compute_payout`: coverage check and amount (claimed amount minus the
   franchise, capped by the coverage) computed by Python code run in the **OpenShell sandbox**;
4. decides **approve**, **deny** (no active contract covering the claim type) or **manual_review**,
   with its confidence and reasoning, and saves the decision (indexed for future similarity searches).

Decisions in manual review go to a human reviewer, who can question the agent before deciding
(human in the loop).

## Example requests
- *Process claim CLM-2024-0011*
- *What is the status of claim CLM-2024-0020?*
- *How many claims are waiting for a manual review?*
