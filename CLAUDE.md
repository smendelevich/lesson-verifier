# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is
Lesson verifier: a Python CLI (verify.py). The spec is in SPEC.md. Read it before any task.

## Rules
- Follow SPEC.md. If the spec seems wrong or unclear, ask me; don't guess.
- Work on one rule or one small task at a time.
- Tests are written from SPEC.md, not from the implementation.
- Never change or delete a test just to make it pass. If a test fails, explain why and ask me whether the code or the test is wrong.
- Run `python -m pytest` before saying a task is done, and show the result.
- No new libraries without asking me.
- Don't touch files outside this project folder.
- Don't run git commit or git push. I do that.
- - Change files only with your file-editing tool, never with shell commands or scripts (sed, Python one-liners, redirects), so I can review every change as a diff. Running tests and read-only commands in the shell is fine.

