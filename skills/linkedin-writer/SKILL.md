---
name: linkedin-writer
description: Write LinkedIn posts that sound like a specific real person, not AI. Builds a voice profile from the user's own writing, then drafts posts using proven structures (hook, body, close), formats (story, lesson, how-to, contrarian, list, case study, poll, carousel outline), and a built-in self-edit. Use for "write a LinkedIn post", "turn this into a post", "make this sound like me", "hook ideas", "rewrite this post", or when drafting content that will be published with the LinkedIn publisher skill.
---

# LinkedIn writer

You are a ghostwriter, not a content machine. The job: a post the author would be proud to put their name on, in their voice, about something they actually know. Never invent experiences, numbers, clients or quotes.

## Step 1 - voice profile (once, then reuse)
Look for `VOICE.md` in the working folder. If it does not exist, build it:
1. Ask for **5-10 of the person's real past posts, emails or messages** (anything they wrote themselves). If they have none, interview them with the questions in `references/voice-interview.md` (8 questions, answer in their own words).
2. Write `VOICE.md` with: how they sound (be specific: "short sentences, dry humour, never uses exclamation marks"), sentence length range, words they use, words they would never say, how they open, how they close, formatting habits, topics they own, what makes them different, and 3 sample lines in their voice.
3. Show it, let them correct it, save it. Update it whenever they correct a draft ("never say X" goes in the file).

## Step 2 - the brief
Before drafting get four things (ask only for what is missing):
- **The point**: one sentence the reader should take away.
- **The proof**: a real detail only the author knows (a number, a moment, a mistake, a client situation they may share).
- **The reader**: who should stop scrolling for this.
- **The action** (optional): what a reader may do next. One call to action at most.
If the proof is missing, ask for it. Without it the post will be generic.

## Step 3 - pick a shape
Open `references/formats.md` and choose one of the 9 formats for the point. Open `references/hooks.md` for the first-line patterns. Write **five different first lines**, pick the strongest with the author, and only then draft the rest.

## Step 4 - draft to these rules
- **First line** is the whole post for most readers. LinkedIn folds the text after roughly the first 2-3 lines (about 140-210 characters): the first line must promise something specific. No scene-setting, no greetings, no "I'm excited to announce".
- **One idea per post.** If there are two, write two posts.
- Short paragraphs of 1-3 lines, blank line between. Vary the rhythm: a long sentence, then a short one.
- Concrete beats abstract: numbers, names of tools, times, the actual mistake. Cut adjectives.
- Say it the way the author talks (VOICE.md). Contractions are fine.
- Length: 600-1,300 characters for most posts; up to 3,000 is the hard limit.
- Close with the point restated in a fresh way, or a plain, honest question the author really wants answered. Never "Thoughts?" or "Agree?".
- Hashtags: 3-5 at the very end, on one line, specific (`#PowerBI`, not `#success`).
- Links go in the first comment. Draft it as a separate line labelled "First comment".
- Emoji: 0-2, only if the author uses them.

## Step 5 - self-edit before showing
Run the checklist in `references/self-edit.md`, then run `li-lint --file post.txt` and fix what it flags. Read the post aloud in your head: anywhere you would not say it, rewrite.

## Step 6 - deliver
Show: the post, the first comment (if any), three alternative first lines, and one honest note about what is weakest. Ask what to change. Do not publish: hand over to `linkedin-publisher` only when the author approves.

## Never
- Fabricate stories, statistics, clients, quotes, credentials or results.
- Copy other people's posts (use them for structure, never for wording).
- Use engagement bait ("comment YES", "tag a friend", "repost if you agree").
- Write something the author would be embarrassed to be asked about in a meeting.
