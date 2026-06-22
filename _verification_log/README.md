# Verification Log

This directory records source checks for load-bearing methodological claims used
by Paper-WorkFlow references and templates.

## Files

- `methods-claims.md`: methods-claim evidence ledger.

## Validation

Run from the skill root:

```bash
python3 scripts/check_verification_log.py
```

The checker enforces stable claim IDs, kebab-case claim tags, required fields,
allowed status values, and valid `used-in` paths.
