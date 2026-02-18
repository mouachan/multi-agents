# ⚠️  DO NOT EDIT FILES IN THIS DIRECTORY

This directory contains **symlinks** to the source SQL files:

- `init.sql` → `../../../../database/init.sql`
- `seed.sql` → `../../../../database/seed_data/001_sample_data.sql`

## To modify database initialization:

1. **Edit the source files** in `/database/`:
   - `/database/init.sql` for schema
   - `/database/seed_data/001_sample_data.sql` for seed data

2. Changes will **automatically be reflected** here via symlinks

3. Test with: `helm template test agentic-claims-demo`

## Why symlinks?

- ✅ **Single source of truth** in `/database/`
- ✅ **No duplication** = no sync errors
- ✅ Helm can still read files via `.Files.Glob`
- ✅ Respects separation: code in `/database/`, deployment in `/helm/`
