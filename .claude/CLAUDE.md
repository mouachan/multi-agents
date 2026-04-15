# Project Rules

## Git
- La seule branche est `main`. Il n'y a pas d'autre branche (feature/multi-agents n'existe plus).
- Ne jamais ajouter `Co-Authored-By` dans les commits.
- Ne JAMAIS committer de secrets, clés API, tokens ou mots de passe en clair dans un fichier versionné. Utiliser des placeholders (`REPLACE_WITH_KEY`, `change-me-*`, etc.) dans les fichiers YAML/JSON committés. Les vraies valeurs doivent être passées via `--set` au moment du `helm install/upgrade` ou via des secrets OpenShift/Kubernetes créés manuellement.

## Containers
- Utiliser **Podman** exclusivement (pas Docker). Remplacer `docker` par `podman` et `docker compose` par `podman compose` dans toutes les commandes.

## Architecture
- Les données (PDFs, documents) ne doivent JAMAIS etre incluses dans une image Docker. Separation logique : les donnees restent dans une source de donnees (GitHub archive, S3, etc.), pas dans une image.
- Le job `data-init` telecharge les donnees via curl depuis une archive GitHub, puis les insere via LlamaStack Files API.
