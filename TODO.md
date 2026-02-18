# TODO - Multi-Agents Platform

## PRIORITE 1 : Suggested Actions dynamiques (LLM, pas hardcode)

**Probleme** : _fallback_classification() renvoie toujours suggested_actions: [] en dur.
Le prompt systeme demande au LLM de generer des actions contextuelles, mais elles ne sont jamais parsees/utilisees.
Sans ca, l'orchestrateur n'est pas vraiment "agentic".

### A FAIRE
- [x] orchestrator_service.py: dans process_message(), quand le LLM repond en JSON, parser le champ `suggested_actions` de la reponse
- [x] orchestrator_service.py: _fallback_classification() devrait aussi generer des actions basiques selon l'intent detecte (ex: intent=claims -> "Voir les sinistres", "Traiter un sinistre")
- [x] orchestrator_prompts.py: s'assurer que le prompt systeme decrit bien les actions possibles avec les bons formats (navigate, chat, process)
- [ ] Tester que les boutons d'actions apparaissent dans le chat apres chaque reponse du LLM
- [x] Actions de chainage inter-agents : apres un Go sur un AO, proposer "Deposer un claim assurance"

### Fichiers concernes
- `backend/app/services/agents/orchestrator_service.py` (lignes 123-128 : extraction, lignes 311-361 : fallback)
- `backend/app/llamastack/orchestrator_prompts.py` (prompt systeme avec format JSON)
- Frontend deja pret (ChatMessage.tsx affiche les suggested_actions, ChatPage.tsx gere onActionClick)

---

## PRIORITE 2 : i18n - Internationalisation FR/EN

### FAIT
- [x] Systeme i18n (LanguageContext + translations.ts)
- [x] Toggle FR/EN dans la navbar (Layout.tsx)
- [x] App.tsx wrape avec LanguageProvider
- [x] Layout.tsx - nav + footer traduits
- [x] HomePage.tsx - tous les strings traduits
- [x] ChatPage.tsx - sessions, orchestrateur, labels traduits
- [x] ChatWindow.tsx - placeholder, "agent reflechit", "demarrez une conversation"
- [x] ChatMessage.tsx - noms d'agents dynamiques via t()
- [x] AgentGraph.tsx - "Architecture Agents", "Orchestrateur"
- [x] AgentCard.tsx - "En attente", "En cours", "Termines", "Voir", "Chat"
- [x] SuggestedActions.tsx - "Actions suggerees"

### A FAIRE - Frontend i18n (composants restants)
- [ ] ClaimsListPage.tsx - ~30 strings (titres, filtres, tableau, pagination)
- [ ] ClaimDetailPage.tsx - "Back to Claims", "Claim not found"
- [ ] ClaimHeader.tsx - "Claim ID", "User ID", "Claim Type", "Submitted At", etc.
- [ ] ClaimActions.tsx - "Process Claim", "Processing...", "Failed to process"
- [ ] ClaimDecision.tsx - "Claim Decision", "System Decision", "Confidence", etc.
- [ ] ProcessingSteps.tsx - "Processing Steps", "Overall Progress", "Agent", etc.
- [ ] StepOutputDisplay.tsx - "Extracted Information", "User Information", etc.
- [ ] GuardrailsAlert.tsx - "PII Detected", "Severity", "Action", etc.
- [ ] TendersListPage.tsx - ~25 strings (deja partiellement en FR)
- [ ] TenderDetailPage.tsx - "Retour aux AOs"
- [ ] TenderHeader.tsx - ~20 strings (deja en FR mais hardcode)
- [ ] TenderActions.tsx - "Analyser l'AO", "Analyse en cours..."
- [ ] TenderDecision.tsx - "Decision Go/No-Go", "Analyse des Risques", etc.
- [ ] TenderProcessingSteps.tsx - "Etapes de Traitement", labels des steps, etc.
- [ ] ReviewChatPanel.tsx - "Manual Review Required", "Approve", "Reject", etc.
- [ ] AdminPage.tsx - ~40 strings (stats, reset, next steps)

### A FAIRE - Backend langue dynamique
- [ ] Ajouter detect_language() dans orchestrator_service.py (heuristique FR mots-cles + accents)
- [ ] Injecter directive de langue dans les instructions agent avant appel LLM
- [ ] Ajouter champ `language` optionnel dans ChatMessageRequest/Response schemas
- [ ] Passer locale du frontend au backend dans orchestratorService.ts sendMessage()

---

## PRIORITE 3 : Suppression de sessions

### FAIT
- [x] Backend: endpoint DELETE /orchestrator/sessions/{session_id}
- [x] Frontend: orchestratorService.deleteSession()
- [x] Frontend: bouton X au hover sur chaque session dans ChatPage sidebar
- [x] Frontend: confirmation avant suppression + navigation si session active

### A VERIFIER
- [ ] Verifier que delete_session() dans orchestrator_service.py supprime aussi les messages associes (CASCADE dans le schema SQL)

---

## PRIORITE 4 : Authentification OpenShift (differe)
- [ ] Ajouter systeme d'auth en haut a droite de la navbar
- [ ] Se relier a OpenShift OAuth / SSO
- [ ] Proteger les routes frontend
- [ ] Proteger les endpoints backend

---

## Ameliorations UX (nice-to-have)
- [ ] Mobile responsive pour la page Chat (sidebar cachee par defaut)
- [ ] Toast notifications au lieu de alert() pour les erreurs
