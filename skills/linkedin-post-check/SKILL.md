---
name: linkedin-post-check
description: Check and fix a LinkedIn post before it goes out - length, opening line, AI tells, engagement bait, hashtags, links, emoji, formatting and leftover placeholders - using the li-lint command plus a human-sounding rewrite. Use for "review my LinkedIn post", "does this sound like AI", "fix my hook", "proofread before posting", or before any publish.
---

# LinkedIn post check

## Run the checker
```bash
li-lint --file post.txt          # or: li-lint "text"   or: cat post.txt | li-lint -
li-lint --file post.txt --json   # machine-readable
li-lint --file post.txt --banned my-phrases.txt   # your own extra phrases to flag, one per line
```
Exit code 1 means a hard error (empty, over 3,000 characters, a leaked token or password, an unfilled placeholder such as `[Name]`). Warnings are questions, not orders.

## What it flags and what to do
| Flag | Meaning | Fix |
|---|---|---|
| Opening line long | the fold ("see more") comes after roughly 140-210 characters | one clear promise in the first line |
| AI or template phrases | "game-changer", "unlock the power", "I'm thrilled to announce", "delve"... | say it the way you would say it to a colleague |
| Engagement bait | "comment YES", "tag someone", "agree?" | end on the point, or a question you truly want answered |
| Em dashes (more than 2), "not just X but Y" | common AI rhythm | full stops and commas; state the claim directly |
| More than 5 hashtags | looks spammy | 3-5 specific tags on the last line |
| Link in the body | habit: put links in the first comment | move it; `li-post ... --first-comment` |
| More than 3 emoji, ALL CAPS | reads as shouting | trim |
| Very long paragraph | hard on a phone | 1-3 line paragraphs |

## Your job after the report
1. Fix every error.
2. For each warning decide: change it, or keep it on purpose (say why).
3. Do not "clean" the author's voice into corporate beige. Remove template phrases, keep personality.
4. Re-run until there are no errors. A score of 85+ with the warnings you consciously kept is fine.
5. Show the final text and the remaining warnings to the author. Do not publish: hand over to `linkedin-publisher` for approval.

The checker never edits text and never calls LinkedIn.
