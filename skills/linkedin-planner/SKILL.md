---
name: linkedin-planner
description: Plan a month of LinkedIn content - choose content pillars, build a weekly rhythm, generate a topic backlog from the user's real work, and produce a calendar with formats and hook ideas. Use for "plan my LinkedIn content", "content calendar", "what should I post this week", "topic ideas", "posting schedule".
---

# LinkedIn planner

## 1. Pillars (do once, revisit quarterly)
Ask: who is the one reader, and what three narrow topics does the user know better than most? Turn them into **three pillars** and one optional "personal" pillar (about 1 post in 5). Write them in `PLAN.md`:
```
Reader: <one person>
Pillars: 1) ... 2) ... 3) ...
Personal angle: <what they are comfortable sharing>
Off limits: <clients, numbers, etc.>
```

## 2. Weekly rhythm
Default: **3 posts a week** (Tue / Wed / Thu mornings in the reader's time zone), 2 if time is tight. Quality beats frequency; do not exceed 1 a day.
| Slot | Job | Formats (see `linkedin-writer/references/formats.md`) |
|---|---|---|
| Post 1 | Teach | how-to, checklist, carousel |
| Post 2 | Prove | case study, result, behind the scenes |
| Post 3 | Opinion or story | contrarian take, mistake lesson, story |
Rotate pillars so each appears once or twice a week.

## 3. Backlog from real work (the part most people skip)
Each Friday ask the user five questions and add the answers to `BACKLOG.md` as one-line ideas:
1. What did you fix this week that took longer than it should have?
2. What did a client or colleague ask that you had to look up?
3. What did you change your mind about?
4. What would you tell yourself a year ago?
5. What numbers moved (time saved, errors reduced, adoption)?
Ideas without a real detail get a "needs proof" tag and are not scheduled.

## 4. Monthly calendar
Build a table: date, weekday, pillar, format, one-line point, hook idea, proof needed, status (idea / drafted / approved / scheduled / posted). Mark two "flex" slots for timely posts. Put the table in `PLAN.md`. Draft posts with `linkedin-writer`, check with `linkedin-post-check`, schedule with `linkedin-publisher` (`li-schedule add ... --at ... --tz ...`, then the user approves each).

## 5. Review (monthly, 15 minutes)
With numbers from `linkedin-analytics`: which two posts did best and why (topic, format, first line, day)? Which flopped? Update the pillar mix and the "never" list. One change at a time so you can tell what worked.

## Rules
- Never schedule a post the user has not seen. Never fill the calendar with generic topics.
- Keep a "do not post" list: anything confidential, legally sensitive or hostile.
- Respect LinkedIn's rules: no automation of the website, no engagement pods, no duplicate posting.
