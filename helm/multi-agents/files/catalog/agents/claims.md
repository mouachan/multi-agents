# Claims Processing Agent

## What this agent does
Processes insurance claims end to end and answers questions about them in the chat.

For a claim, the agent:
1. reads the claim and its document (OCR by the vision model);
2. retrieves the claimant's **active contracts** and the decisions of **similar past claims**;
3. computes the **payout** with `compute_payout`: coverage check and amount (claimed amount minus the
   franchise, capped by the coverage) computed by Python code run in the **OpenShell sandbox**;
4. decides **approve**, **deny** (no active contract covering the claim type) or **manual_review**,
   with its confidence and reasoning.

Its decision is saved by the platform, not by the agent. When it hands the case over to a person, it
writes a brief for the reviewer (why it did not decide, what to check, what it leans to); the reviewer
can question the agent before deciding (human in the loop). Personal data is masked before the model
sees it.

## Example requests
- *Process claim CLM-2024-0011*
- *What is the status of claim CLM-2024-0020?*
- *How many claims are waiting for a manual review?*
