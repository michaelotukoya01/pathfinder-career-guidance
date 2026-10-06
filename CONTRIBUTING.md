# Contributing

Use Python 3.13 and Node 24. Follow the README setup, create a branch, and keep each change focused.

Before opening a pull request:

```bash
python -m unittest discover -s tests -v
python scripts/check_repository.py
cd frontend
npm ci
npm run lint
npm test
npm run build
```

Add English and Spanish text for user-facing changes. Preserve keyboard navigation, reduced-motion behavior, retry states, and access protection. Add regression coverage for meaningful behavior changes, especially profile privacy and persistence.

Model changes must include training provenance, excluded features, a reproducible evaluation, and updated hashes. Do not tune against the test set, claim real-world accuracy from synthetic data, or commit private datasets or user profiles.

Do not commit `.env` files, device access backups, dependency directories, runtime model versions, databases, or logs. Avoid mass dependency upgrades that have not passed the build, tests, and audits.
