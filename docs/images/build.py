"""Builds the README infographics (HTML -> PNG). Optional: only needed if you want to change the pictures.
    pip install playwright && playwright install chromium && python docs/images/build.py
"""
import pathlib, sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "src"
SRC.mkdir(exist_ok=True)

ICONS = {
    "pen": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/>',
    "check": '<path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/>',
    "user": '<path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M16 11l2 2 4-4"/>',
    "send": '<path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4z"/>',
    "chart": '<path d="M18 20V10M12 20V4M6 20v-6"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>',
    "key": '<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.78 7.78 5.5 5.5 0 017.78-7.78zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/>',
    "cal": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "msg": '<path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>',
    "term": '<path d="M4 17l6-6-6-6M12 19h8"/>',
    "cog": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 01-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 010-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 014 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 010 4h-.1a1.7 1.7 0 00-1.5 1z"/>',
    "x": '<path d="M18 6L6 18M6 6l12 12"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 010 20M12 2a15 15 0 000 20"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "stop": '<circle cx="12" cy="12" r="10"/><path d="M8 12h8"/>',
}
def ico(n, cls="ico", color=None):
    st = f' style="background:{color}"' if color else ""
    return f'<div class="{cls}"{st}><svg viewBox="0 0 24 24">{ICONS[n]}</svg></div>'

def page(w, h, body, extra_css=""):
    return f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="style.css"><style>{extra_css}</style></head>
<body><div id="canvas" style="width:{w}px;height:{h}px">{body}</div></body></html>'''

IMAGES = {}

# ---------------------------------------------------------------- hero
steps = [("pen", "Write", "in your voice"), ("check", "Check", "no AI tells"), ("user", "You approve", "every post"), ("send", "Publish", "official API"), ("chart", "Measure", "within limits")]
rows = "".join(f'<div class="hstep">{ico(i)}<div><b>{t}</b><span>{s}</span></div></div>' + ('<div class="harrow"></div>' if k < 4 else "") for k, (i, t, s) in enumerate(steps))
IMAGES["hero"] = (1600, 820, page(1600, 820, f'''
<div class="bg"></div>
<div class="left">
  <div class="kicker">OPEN SOURCE  ·  MIT  ·  OFFICIAL LINKEDIN API</div>
  <div class="h1 title">LinkedIn<br>Automation<br><span>for Claude</span></div>
  <p class="sub">Connect Claude to LinkedIn in 15 minutes. Write posts that sound like you, check them, approve them, publish and measure. No scraping. No stored passwords. Nothing posts without your yes.</p>
  <div class="chips"><span class="chip c1">8 Claude skills</span><span class="chip c2">5 commands</span><span class="chip c3">0 dependencies</span><span class="chip c4">44 tests</span></div>
</div>
<div class="right card">
  <div class="rt">The loop</div>
  {rows}
</div>''', '''
#canvas{background:#0B1B3F}
.bg{position:absolute;inset:0;background:radial-gradient(900px 600px at 85% 15%,rgba(106,206,226,.35),transparent 60%),radial-gradient(800px 700px at 10% 100%,rgba(147,67,134,.55),transparent 60%),linear-gradient(135deg,#0B1B3F 0%,#1D50B3 100%)}
.left{position:absolute;left:90px;top:80px;width:820px;color:#fff}
.kicker{font-size:21px;font-weight:700;letter-spacing:.14em;color:#BFE9F3;margin-bottom:26px}
.h1{font-size:112px;line-height:1.0;font-weight:900;letter-spacing:-.035em}
.h1 span{background:linear-gradient(90deg,#6ACEE2,#E9A5DC);-webkit-background-clip:text;color:transparent}
.sub{margin-top:34px;font-size:27px;line-height:1.5;color:#DCE6FF;max-width:760px}
.chips{margin-top:34px;display:flex;gap:14px;flex-wrap:wrap}
.chip{background:rgba(255,255,255,.14);color:#fff;border:1.5px solid rgba(255,255,255,.35)}
.right{position:absolute;right:80px;top:120px;width:520px;padding:34px 36px}
.rt{font-weight:800;font-size:22px;letter-spacing:.12em;text-transform:uppercase;color:var(--plum);margin-bottom:18px}
.hstep{display:flex;align-items:center;gap:20px;padding:6px 0}
.hstep b{display:block;font-size:30px;font-weight:800}
.hstep span{color:var(--mut);font-size:20px}
.harrow{height:22px;margin-left:27px;border-left:3px dotted #B8C5E8}
''' ))

# ---------------------------------------------------------------- 6 steps
flow = [
    ("term", "Install", "pipx install git+https://github.com/ phoenixDatasolutions/ Linkedin-Automation", "1 command"),
    ("globe", "Create an app", "LinkedIn Developer Portal: new app, add the products Share on LinkedIn and Sign in (OpenID)", "5 min"),
    ("key", "Add your keys", "li-auth setup  (client ID + secret, typed hidden, saved privately)", "1 min"),
    ("lock", "Sign in", "li-auth login  (approve in the browser, token lasts 60 days)", "1 min"),
    ("pen", "Draft with Claude", "Claude writes in your voice, li-lint checks it", "any time"),
    ("send", "Approve and post", "li-post text \"...\" --publish  (you type: publish)", "10 sec"),
]
cards = "".join(f'<div class="step card"><div class="num">{k+1}</div>{ico(i)}<div class="st">{t}</div><div class="sd mono">{d}</div><div class="tm">{tm}</div></div>' for k, (i, t, d, tm) in enumerate(flow))
IMAGES["flow"] = (1600, 640, page(1600, 640, f'''
<div class="top"><div class="title tt">From zero to your first post in 6 steps</div><div class="ts">About 15 minutes. No code to write.</div></div>
<div class="grid">{cards}</div>''', '''
#canvas{background:linear-gradient(180deg,#F6F8FC,#EAF0FB)}
.top{padding:44px 60px 0}.tt{font-size:48px;color:var(--ink)}.ts{font-size:24px;color:var(--mut);margin-top:6px}
.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:18px;padding:34px 40px}
.step{padding:22px 18px;display:flex;flex-direction:column;gap:14px;position:relative;min-height:380px}
.step .num{position:absolute;top:-18px;left:18px;width:44px;height:44px;font-size:22px}
.step .ico{margin-top:14px}
.st{font-size:27px;font-weight:800}
.sd{font-size:14.5px;line-height:1.45;color:var(--mut);word-break:break-word}
.tm{margin-top:auto;font-weight:700;color:var(--blue);font-size:18px}
'''))

# ---------------------------------------------------------------- architecture
IMAGES["architecture"] = (1600, 900, page(1600, 900, f'''
<div class="tt title">How the pieces fit</div>
<div class="row">
  <div class="col card a">{ico("msg")}<h3>Claude</h3><p>Claude Code, Claude Desktop or claude.ai</p>
    <ul><li>linkedin-api-setup</li><li>linkedin-writer</li><li>linkedin-post-check</li><li>linkedin-publisher</li><li>linkedin-comments</li><li>linkedin-planner</li><li>linkedin-analytics</li><li>linkedin-api (knowledge)</li></ul></div>
  <div class="arr">{ico("arrow","ico2")}<span>runs</span></div>
  <div class="col card b">{ico("term")}<h3>5 small commands</h3><p>Python, no dependencies</p>
    <ul class="mono"><li>li-auth</li><li>li-post</li><li>li-lint</li><li>li-stats</li><li>li-schedule</li></ul>
    <div class="note">Dry run by default.<br>Counts every API call.</div></div>
  <div class="arr">{ico("arrow","ico2")}<span>HTTPS</span></div>
  <div class="col card c">{ico("globe")}<h3>LinkedIn official API</h3><p>api.linkedin.com / OAuth 2.0</p>
    <ul><li>Posts &amp; media</li><li>Comments &amp; reactions</li><li>Post analytics</li><li>Sign in (OpenID)</li></ul>
    <div class="note">No scraping. No browser automation.</div></div>
</div>
<div class="vault card">{ico("lock")}<div><b>Your computer only</b><span>~/.config/linkedin-automation/  ·  .env (client ID + secret) and token.json, both owner-only (0600). Never in the repository, never in chat, never printed.</span></div></div>''', '''
#canvas{background:linear-gradient(180deg,#fff,#F1F5FD)}
.tt{font-size:52px;padding:44px 60px 0}
.row{display:flex;align-items:stretch;gap:14px;padding:30px 60px 0}
.col{flex:1;padding:26px 26px 22px}
.col h3{font-size:30px;font-weight:800;margin:14px 0 4px}.col p{color:var(--mut);font-size:19px;margin-bottom:12px}
.col ul{list-style:none;display:flex;flex-direction:column;gap:7px}.col li{font-size:20px;font-weight:600;padding:7px 12px;border-radius:10px;background:#F1F5FD}
.b li{background:#EFE3EC}.c li{background:#E2F6FB}
.note{margin-top:14px;font-size:17px;color:var(--plum);font-weight:700}
.arr{display:flex;flex-direction:column;align-items:center;justify-content:center;width:90px;color:var(--mut);font-weight:700;font-size:18px}
.ico2{width:56px;height:56px}.ico2 svg{width:46px;height:46px;stroke:var(--blue);fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.vault{margin:26px 60px 0;padding:18px 26px;display:flex;align-items:center;gap:20px;background:linear-gradient(90deg,#EAF7EE,#F4FBF6);border-color:#BDE6C9}
.vault b{display:block;font-size:24px}.vault span{font-size:18px;color:var(--mut);line-height:1.4}
'''))

# ---------------------------------------------------------------- access paths
IMAGES["paths"] = (1600, 640, page(1600, 640, f'''
<div class="tt title">Which LinkedIn access do you need?</div>
<div class="ts">There is no single "API key". You create an app (client ID + secret) and sign in with OAuth. What you can do depends on the products you add.</div>
<div class="row">
 <div class="card p1"><div class="badge g">Instant · no review</div><h3>A. Post to your profile</h3>
   <ul><li>Share on LinkedIn  <i>w_member_social</i></li><li>Sign in with LinkedIn (OpenID)  <i>openid profile</i></li></ul>
   <div class="can"><b>You can</b> publish text, images, PDFs, polls, links · comment · react · delete your posts</div>
   <div class="cant"><b>You cannot</b> read your numbers or other people's posts</div></div>
 <div class="plus">+</div>
 <div class="card p2"><div class="badge o">Reviewed · days to weeks</div><h3>B. Add your numbers</h3>
   <ul><li>Community Management API  <i>r_member_postAnalytics</i></li><li>A <u>second app</u> (it must be the only product on its app)</li></ul>
   <div class="can"><b>You can</b> read views, reactions, comments, reposts, followers · post as a Company Page</div>
   <div class="cant"><b>Limits</b> 100 calls / day / member · Development tier lasts 12 months</div></div>
</div>''', '''
#canvas{background:linear-gradient(180deg,#F6F8FC,#EAF0FB)}
.tt{font-size:50px;padding:42px 60px 0}.ts{font-size:23px;color:var(--mut);padding:8px 60px 0;max-width:1400px;line-height:1.45}
.row{display:flex;align-items:center;gap:20px;padding:34px 60px}
.card{flex:1;padding:28px 30px;min-height:380px}
.card h3{font-size:34px;font-weight:800;margin:14px 0 14px}
.badge{display:inline-block;padding:7px 16px;border-radius:999px;font-weight:700;font-size:18px}.g{background:#DCF5E5;color:#15803D}.o{background:#FFF1D6;color:#B45309}
ul{list-style:none;display:flex;flex-direction:column;gap:10px;margin-bottom:18px}li{font-size:21px;font-weight:600;padding:12px 16px;border-radius:12px;background:#F1F5FD}li i{font-style:normal;font-family:ui-monospace,monospace;font-size:16px;color:var(--blue);margin-left:6px}
.p2 li{background:#F7ECF4}
.can,.cant{font-size:20px;line-height:1.45;margin-top:10px}.can b{color:#15803D}.cant b{color:#B45309}
.plus{font-size:64px;font-weight:800;color:var(--plum)}
'''))

# ---------------------------------------------------------------- safety
gates = [("pen", "Draft", "Claude writes in your voice. Nothing leaves your computer."), ("check", "Check", "li-lint: length, hook, AI tells, bait, leaked secrets."), ("user", "You approve", "Explicit yes on the exact text. Changed text = ask again."), ("send", "Publish", "Dry run is the default. You type the word publish."), ("stop", "Guard rails", "Daily cap · call counter · mark-before-send · no auto retry")]
gcards = "".join(f'<div class="g card">{ico(i)}<div class="gt">{t}</div><div class="gd">{d}</div></div>' for i, t, d in gates)
secrets = ["Secrets live outside the repo", "Token file is owner-only (0600)", "Secret scan blocks commits", "Output is redacted", "No passwords, no scraping"]
sl = "".join(f'<li>{s}</li>' for s in secrets)
IMAGES["safety"] = (1600, 640, page(1600, 640, f'''
<div class="tt title">Safe by default</div>
<div class="gs">{gcards}</div>
<div class="sec card">{ico("shield")}<div><b>Your secrets stay yours</b><ul>{sl}</ul></div></div>''', '''
#canvas{background:linear-gradient(180deg,#fff,#F3F6FC)}
.tt{font-size:52px;padding:42px 60px 0}
.gs{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;padding:30px 60px 0}
.g{padding:22px 18px;display:flex;flex-direction:column;gap:10px}.gt{font-size:27px;font-weight:800}.gd{font-size:18px;color:var(--mut);line-height:1.45}
.sec{margin:26px 60px 0;padding:22px 28px;display:flex;gap:22px;align-items:center;background:linear-gradient(90deg,#EAF7EE,#F5FBF7);border-color:#BDE6C9}
.sec b{font-size:27px;display:block;margin-bottom:8px}
.sec ul{display:flex;flex-wrap:wrap;gap:10px;list-style:none}.sec li{background:#fff;border:1.5px solid #BDE6C9;padding:8px 14px;border-radius:999px;font-size:18px;font-weight:600}
.sec .ico{background:#fff}.sec .ico svg{stroke:#15803D}
'''))

# ---------------------------------------------------------------- limits
bars = [("Naive refresh", "refresh every post, all metrics, several times a day", 100, "#DC2626"), ("This toolkit", "new posts often, old posts rarely, cached 6 h, capped at 90", 28, "#16A34A")]
bhtml = "".join(f'<div class="bar"><div class="bl"><b>{t}</b><span>{d}</span></div><div class="track"><div class="fill" style="width:{v}%;background:{c}"></div><em>{ "25 posts x 3 metrics = 75 calls per refresh: the day is gone after one" if v==100 else "about 28 calls: room to spare"}</em></div></div>' for t, d, v, c in bars)
IMAGES["limits"] = (1600, 600, page(1600, 600, f'''
<div class="tt title">LinkedIn gives you 100 calls a day. Spend them well.</div>
<div class="ts">The analytics API answers <b>one post and one metric per call</b> (no batching). Limits reset at midnight UTC.</div>
<div class="card box">{bhtml}
<div class="legend"><span><i style="background:#DC2626"></i>over the limit</span><span><i style="background:#16A34A"></i>within it</span><span class="mono">li-stats budget</span></div></div>
<div class="tips"><div class="card tip"><b>0-7 days old</b>refresh often</div><div class="card tip"><b>8-30 days old</b>once a day</div><div class="card tip"><b>older</b>weekly or never</div><div class="card tip"><b>Trends</b>one call for ALL posts: li-stats me</div></div>''', '''
#canvas{background:linear-gradient(180deg,#F6F8FC,#EAF0FB)}
.tt{font-size:46px;padding:40px 60px 0}.ts{font-size:23px;color:var(--mut);padding:8px 60px 0}
.box{margin:26px 60px 0;padding:24px 30px}
.bar{margin:14px 0}.bl b{font-size:25px;font-weight:800;margin-right:12px}.bl span{font-size:18px;color:var(--mut)}
.track{margin-top:10px;height:52px;border-radius:14px;background:#EEF2FA;position:relative;overflow:hidden}.fill{height:100%;border-radius:14px}
.track em{position:absolute;left:18px;top:0;line-height:52px;font-style:normal;font-weight:700;font-size:20px;color:#fff}
.legend{display:flex;gap:26px;margin-top:10px;font-size:17px;color:var(--mut)}.legend i{display:inline-block;width:14px;height:14px;border-radius:4px;margin-right:8px;vertical-align:-1px}.legend .mono{margin-left:auto;color:var(--blue);font-weight:700}
.tips{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:20px 60px}.tip{padding:16px 18px;font-size:19px;color:var(--mut)}.tip b{display:block;font-size:23px;color:var(--ink);margin-bottom:4px}
'''))

# ---------------------------------------------------------------- skills grid
sk = [("book", "linkedin-api", "The whole LinkedIn API in 10 guides: auth, posting, analytics, limits, rules"), ("key", "linkedin-api-setup", "Step-by-step wizard: app, keys, sign-in, first test post"), ("pen", "linkedin-writer", "Voice profile, 9 formats, hook patterns, self-edit"), ("check", "linkedin-post-check", "li-lint: AI tells, bait, length, leaked secrets"), ("send", "linkedin-publisher", "Approval-gated publish and schedule"), ("msg", "linkedin-comments", "Comments and replies that add something"), ("cal", "linkedin-planner", "Pillars, weekly rhythm, backlog, calendar"), ("chart", "linkedin-analytics", "Your numbers within the daily call limit")]
sh = "".join(f'<div class="sk card">{ico(i)}<div class="sn mono">{n}</div><div class="sdsc">{d}</div></div>' for i, n, d in sk)
IMAGES["skills"] = (1600, 700, page(1600, 700, f'''
<div class="tt title">Eight skills. One workflow.</div>
<div class="g">{sh}</div>''', '''
#canvas{background:linear-gradient(180deg,#fff,#F3F6FC)}
.tt{font-size:52px;padding:42px 60px 0}
.g{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;padding:30px 60px}
.sk{padding:22px 20px;display:flex;flex-direction:column;gap:12px;min-height:240px}.sn{font-size:20px;font-weight:700;color:var(--blue)}.sdsc{font-size:19px;line-height:1.45;color:var(--mut)}
'''))

# ---------------------------------------------------------------- icon
IMAGES["icon"] = (1024, 1024, page(1024, 1024, '''
<div class="ic"><svg viewBox="0 0 24 24" width="560" height="560" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4z"/></svg></div>''', '''
#canvas{background:linear-gradient(135deg,#1D50B3,#934386)}.ic{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}
'''))


def main():
    from playwright.sync_api import sync_playwright
    for name, (w, h, html) in IMAGES.items():
        (SRC / f"{name}.html").write_text(html)
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        for name, (w, h, html) in IMAGES.items():
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1.5 if name != "icon" else 1)
            pg.goto((SRC / f"{name}.html").resolve().as_uri())
            pg.wait_for_timeout(900)
            pg.locator("#canvas").screenshot(path=str(HERE / f"{name}.png"))
            pg.close()
            print("built", name)
        b.close()


if __name__ == "__main__":
    main()
