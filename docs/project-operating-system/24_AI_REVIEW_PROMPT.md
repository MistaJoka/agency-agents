# AI Review Prompt

Use this prompt when asking an AI assistant to review a proposed change:

```text
Review this repo change using the project operating system in docs/project-operating-system.

Return:
1. Project area affected
2. Working behavior that must be protected
3. Forward review from user action to result
4. Backward review from expected result to dependencies
5. FMAE risks
6. Regression commands/checks
7. Changelog note needed
8. Build/no-build recommendation

Do not recommend broad restructuring unless it is directly required by the requested change.
```

