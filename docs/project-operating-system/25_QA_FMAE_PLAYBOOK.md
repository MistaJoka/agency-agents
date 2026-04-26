# QA FMAE Playbook

## Purpose

Prevent shallow edits, broken working code, and untested assumptions.

FMAE means Failure Mode Analysis + Effects review.

## When to Use FMAE

Use FMAE for:

- New features
- Bug fixes
- Refactors
- Registry/data changes
- Source import/export changes
- Local API changes
- Security/privacy changes
- Deployment changes
- `supabase-web` runtime changes

Skip formal FMAE only for trivial copy edits or harmless documentation cleanup.

## FMAE Template

```md
## FMAE Review: <feature/change>

| Failure mode | Cause | Effect | Severity 1-5 | Likelihood 1-5 | Detection | Prevention | Test |
|---|---|---:|---:|---:|---|---|---|
|  |  |  |  |  |  |  |  |
```

## Severity Guide

- 1: cosmetic or minor inconvenience
- 2: small workflow issue with workaround
- 3: important feature partially broken
- 4: core flow broken or data reliability risk
- 5: data loss, privacy/security issue, or complete core failure

## Forward Review

Trace:

```text
User action -> UI/input -> validation -> processing -> storage/API -> output/result
```

## Backward Review

Trace:

```text
Expected result -> required output -> required data -> required logic -> required input -> required user action
```

## Working Code Protection Checklist

Before editing:

- [ ] What already works?
- [ ] How do we know it works?
- [ ] Which files should not be touched?
- [ ] What is the smallest safe change?
- [ ] What test/check proves old behavior still works?

After editing:

- [ ] Did we avoid unrelated changes?
- [ ] Did old behavior still pass?
- [ ] Did the new behavior pass?
- [ ] Did we update the changelog?
- [ ] Did we document remaining risks?

