# Project Rules

## Git
- La seule branche est `main`. Il n'y a pas d'autre branche (feature/multi-agents n'existe plus).
- Ne jamais ajouter `Co-Authored-By` dans les commits.

## Architecture
- Les données (PDFs, documents) ne doivent JAMAIS etre incluses dans une image Docker. Separation logique : les donnees restent dans une source de donnees (GitHub archive, S3, etc.), pas dans une image.
- Le job `data-init` telecharge les donnees via curl depuis une archive GitHub, puis les insere via LlamaStack Files API.
