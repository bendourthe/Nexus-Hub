# Code Cleanup Review

## 📋 Overview

This review targets dead code, duplication, and drift so the codebase stays lean, current, and maintainable.

## 🎯 Objectives

- Identify and remove unused modules, functions, and feature flags
- Consolidate duplicated logic and near-duplicate implementations
- Modernize legacy patterns that conflict with current architecture
- Document refactoring opportunities with risk and effort estimates
- Verify that cleanup preserves behaviour through focused regression checks

## 📂 Available Templates

### Python
- **[Python Code Cleanup](python_cleanup.md)** – Comprehensive prompt covering dead code detection and removal, duplication analysis, refactoring prioritization, and validation steps

## ⏱️ Time Investment

**1-2 hours** for a focused cleanup sweep of a medium-sized service

## ✅ Success Criteria

- [ ] Dead code candidates identified and prioritized
- [ ] Duplicate logic catalogued with consolidation plan
- [ ] Legacy patterns flagged with modernization strategy
- [ ] Refactor tasks sized with risk/impact notes
- [ ] Regression safeguards defined (tests, toggles, rollout plan)

---

[← Back to Code Review](../README.md)
