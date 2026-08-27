---
name: specialization-workflow
description: Plan and implement a scoped software epic through isolated user stories, actionable tickets, TDD, and per-ticket commits. Use when a user asks to follow this specialization workflow or when organizing substantial feature work into an epic before coding.
---

# Specialization Workflow

Do not generate code ad hoc unless the user specifically requests it. Treat a
direct request as a scoped bypass for debugging, an ad-hoc fix, or an
experiment; Git provides the recovery path for that work.

Otherwise, follow this directory-based workflow for the epic currently being
worked on. Do not modify artifacts belonging to another independent epic or
user story.

1. **User-story step.** Create `developer/<YYYY-MM-DD>-<epic-slug>/`. Put the
   epic's structured user stories in `user-stories.md` and relevant reviews in
   that directory, for example `security-review.md` or `refactoring-review.md`.
2. **Ticket step.** Commit the current epic's relevant user-story or review
   file before this step. Develop it into actionable implementation-ordered
   tickets in `tickets.md` in the same directory. Use the TDD skill while
   developing tickets.
3. **Code-generation step.** Commit the epic's `tickets.md` before beginning
   this step. Generate code from tickets using the TDD skill. When a ticket is
   complete, commit it using the git-commit skill; only then proceed to the
   next ticket.
