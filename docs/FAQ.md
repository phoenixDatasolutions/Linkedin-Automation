# FAQ

**What is the difference between this and other LinkedIn skills for Claude?**
Other open-source collections focus on writing and engagement. This one adds the *API layer*: a setup wizard, OAuth sign-in, safe publishing and scheduling with approval, analytics within LinkedIn's limits, and a complete LinkedIn API knowledge base. You can use it alone or together with them.

**Is there really no LinkedIn API key?**
Correct. You create a developer *app* (client ID and client secret). Each person signs in with OAuth and the app receives an access token (60 days). "Getting an API key" means creating the app and adding products.

**Why can't it read other people's posts?**
LinkedIn does not allow it: `r_member_social` is closed to every developer. The comment helper works on text you paste in yourself.

**Why do I need a Company Page just to post as myself?**
LinkedIn requires every developer app to be associated with a Page. It does not have to be a big company.

**Can I post to a Company Page?**
Yes, with the Community Management API on your app and the Page administrator role (`--org <id>`). That product is reviewed by LinkedIn.

**Can it schedule posts?**
Yes, through `li-schedule` (LinkedIn's API cannot schedule). Items must be approved by a person; a cron job publishes approved items that are due.

**Will LinkedIn restrict my account?**
The toolkit uses only the official API and a documented sign-in. Account risk comes from behaviour: spam, engagement pods, mass or duplicate posting, scraping, fake accounts. Don't. The daily cap, approval gate and writing check are there to keep you on the right side. No tool can guarantee how LinkedIn will treat an account.

**Does LinkedIn allow AI-written posts?**
LinkedIn's Developer AI Policy asks developers to keep the user involved and give them tools to edit AI-generated content before it is posted. Everything here is built around that. You decide what goes out under your name.

**What does it store, and where?**
Your client ID/secret and token (owner-only files in `~/.config/linkedin-automation/`), a call counter, a 6-hour stats cache and your schedule queue. Nothing is sent anywhere except to LinkedIn. LinkedIn also limits how long certain data may be stored; see the rules guide.

**Which Claude plans work?**
Claude Code (recommended: it can run the commands). Claude Desktop and claude.ai with Skills can use the knowledge, writing and checking skills; running the `li-*` commands needs a terminal.

**How do I update?**
`pipx upgrade linkedin-automation`, then `/plugin` update in Claude Code. The knowledge base carries a snapshot date; re-check the linked LinkedIn page for anything critical.

**Can I use it for several people or clients?**
Each person must sign in themselves, and LinkedIn's terms restrict managing other people's profiles. For a team, use Company Page posting via the Community Management API and follow LinkedIn's review requirements.

**Something is broken. Where do I look?**
`li-auth check`, `li-auth status`, then the troubleshooting table in the knowledge skill.
