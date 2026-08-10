---
name: linkedin-post-copywriter
description: Writes humanized, emotionally resonant LinkedIn post copy that sounds like a real person talking — not AI. Uses psychology, storytelling, and anti-AI-detection techniques to maximize engagement, saves, and reach. Self-improving — updated after every post.
---

# LinkedIn Post Copywriter Skill

This skill governs HOW to write LinkedIn post copy that feels human, relatable,
and emotionally connecting. The `viral-architecture-visualizer` skill handles
the VISUALS. This skill handles the WORDS.

---

## ⚠️ The One Rule: Sound Like a Person, Not a Press Release

Before publishing ANY post, read it aloud. If you stumble, if it sounds like a
corporate announcement, if a friend would say "that doesn't sound like you" —
rewrite it until it does.

---

## Part 1: Human Psychology (Why People Engage)

### 1.1 Empathy Triggers
People engage when they feel **seen**. When you describe a struggle they've lived
through, their brain mirrors the emotion. They don't just read — they FEEL.

**The mechanism**: Describe a specific, sensory moment. Not "it was frustrating"
but "I remember staring at the terminal at 2 AM, the cursor blinking, and
realizing the whole environment was corrupted because someone installed the wrong
version of CUDA three days ago."

### 1.2 The Curiosity Gap
The hook must raise a question in the reader's mind that can ONLY be answered by
reading the rest. The reader should think "wait, what happened next?" or "oh no,
I've been there."

### 1.3 Vulnerability = Authority
Admitting the struggle makes the solution credible. If you only show the polished
result, people don't believe it. If you show the mess that came before it, they trust
that you actually solved the problem.

### 1.4 Saves > Likes
In 2026, **saves** are the strongest algorithm signal. Content people bookmark for
later (frameworks, checklists, architecture breakdowns) gets amplified more than
content people merely "like." Design every post to be WORTH saving.

### 1.5 Dwell Time
Each second a reader spends on your post tells the algorithm "this is valuable."
Carousels drive dwell time through swiping. Long-form storytelling drives it
through emotional investment. Both work.

---

## Part 2: The Anti-AI Checklist (Remove Before Publishing)

### Words to NEVER use:
- "In today's fast-paced world"
- "In the ever-evolving landscape"
- "Game-changer", "paradigm shift", "leverage", "synergy"
- "Delve", "tapestry", "transformative"
- "To sum up", "In conclusion"
- "I'm excited to share", "I'm thrilled to announce"
- "Here's what I learned" (as a standalone line)

### Structural tells to avoid:
- Perfect bullet-point symmetry (all bullets same length, same rhythm)
- "Rule of three" lists that feel manufactured
- Every paragraph starting with the same structure
- Emotionless, balanced hedging ("on one hand... on the other hand")
- Generic "motivational" closing lines

### What to do instead:
- Use contractions: "I'm", "don't", "it's", "wasn't", "couldn't"
- Vary sentence length wildly: "The server crashed." followed by a long one
- Include imperfect details: "I think it was a Tuesday" or "I might be wrong about this"
- Use colloquial language: "broke everything", "nobody had any idea", "the whole thing was a mess"
- Address the reader directly: "you know that feeling when..."
- Use first person throughout: "I", "we", "our"

---

## Part 3: The Post Structure (Problem → Story → Solution → Features → CTA)

### 3.1 The Hook (first 2 lines — before "see more")

The hook is NOT about your project. The hook is about a PROBLEM the reader has
lived through. It must be:

- **Specific** — not "universities have shared servers" but "every CS department
  in Kashmir has that one Proxmox server that 30 students SSH into"
- **Sensory** — paint a picture: what did it look like, sound like, feel like?
- **Universal** — the reader must nod and think "yes, that's exactly what happens"

**Templates that work:**
```
"Every [group] has that one [thing]."
"You know [specific frustrating scenario]? Yeah, that was us."
"[Specific painful detail]. That's what [time period] looked like."
"Nobody tells you about [hidden problem] until it breaks at [worst time]."
```

### 3.2 The Story (1-2 paragraphs — the human context)

Write this as a PARAGRAPH, not bullets. This is where you humanize.

Tell the reader:
- What was the real situation? (be specific: university name, city, course)
- What was the daily pain? (specific moment, not abstract)
- Who suffered? (students, teachers, you personally)
- What was the emotional weight? (frustration, wasted time, embarrassment)

**Example (PrivateCloud)**:
"In our university in Kashmir, we had one Proxmox server for the entire CS
department. Thirty students, one machine, everyone SSHing into the same
environment. No isolation. Someone would install PyTorch with the wrong CUDA
version and suddenly nobody's models would run. If you needed the GPU at 2 AM to
train something for a deadline, good luck — someone else's process had been
hanging since Tuesday. The teachers had it worse. Lab starts in ten minutes, half
the laptops have different Python versions, pip is broken on three machines, and
the first twenty minutes of every lab session is just getting everyone's
environment working."

Notice: NO bullets. NO arrows. Just a person telling you what their life was like.

### 3.3 The Pivot (1 line)

One short sentence that transitions from problem to solution:
- "So we built something."
- "That's what made us build this."
- "We decided to fix it."

NOT: "Here is what I built:" (too corporate)

### 3.4 The Features (structured, but still human)

NOW you can use bullets/arrows. But frame them as **what the USER gets**,
not what the SYSTEM does.

- ✅ "Students get their own isolated VM in seconds"
- ❌ "Celery workers provision VMs from a Redis queue"

The technical details (Celery, Redis, Ansible) come AFTER the human benefits,
at the bottom, for the technical audience who kept reading.

Two audience blocks work well:
1. **"For students:"** — what students get
2. **"For teachers:"** — what teachers get

### 3.5 The Stack (brief, at the bottom)

One line. Comma-separated. This is for the technical credibility audience.

### 3.6 The Closing (Ending cleanly without AI tells)

- ❌ NEVER use generic engagement bait: "What do you think? Let me know in the comments!"
- ❌ NEVER use "I'd genuinely love to hear your stories" or "Comment below if you agree" (classic AI tells that readers spot immediately)
- ❌ NEVER use "Agree? ♻️ Repost if this resonated."

**What to do instead**:
- End on a strong, definitive final sentence that leaves an impression.
- Or drop a sharp, opinionated takeaway that naturally makes people want to respond.

---

### 3.7 Hashtags

Use **3–5 targeted hashtags** in **PascalCase** at the very end. Combine 1–2 broad tags with 2–3 niche tags relevant to the post topic.

Examples for Cloud/DevOps:
`#DevOps #CloudComputing #PlatformEngineering #SoftwareEngineering #SelfHosted`


---

## Part 4: LinkedIn Algorithm Rules (2026)

| Factor | Rule |
|--------|------|
| **Format** | Carousel/PDF = 3.7x more engagement |
| **Dimensions** | 1080 x 1350 px (portrait) for maximum mobile real estate |
| **Slide count** | 6-10 sweet spot |
| **Saves** | #1 algorithm signal — make content worth bookmarking |
| **Dwell time** | Each second = quality signal. Carousels + long stories maximize this |
| **Comments** | Meaningful comments > likes. Reply to EVERY comment in the first hour |
| **Hashtags** | Max 2. More reduces reach |
| **Links** | NEVER put external links in the post. Kills reach. |
| **Posting time** | Tue-Thu, 8:00-10:00 AM IST |
| **Frequency** | 2-5 posts/week |

---

## Part 5: The Process (Every Post)

1. **Research the project** — read the actual code, docs, screenshots. Know it deeply.
2. **Find the universal problem** — what pain point does this project solve that
   EVERYONE has experienced? This is the hook.
3. **Write the story paragraph** — specific place, specific people, specific moment.
   Use the "I remember" technique. Make the reader nod.
4. **List the features as user benefits** — what does the student/teacher/user GET?
5. **Add the tech stack** — brief, at the bottom, for credibility.
6. **Write the CTA** — ask for stories, not opinions.
7. **Run the anti-AI checklist** — remove every corporate phrase, jargon, and AI tell.
8. **Read it aloud** — if it doesn't sound like you talking to a friend, rewrite.

---

## Part 6: Self-Improvement Protocol

After EVERY post is published:

1. Note what worked (engagement, saves, comments) and what didn't
2. Update this skill with new patterns discovered
3. Add any new anti-AI phrases found
4. Record successful hooks and CTAs in the "Proven Hooks" section below

### Proven Hooks (updated after each post)
- "I automated my entire LinkedIn" → Post 1 (full platform) — APPROVED
- "Every university has that one shared server" → Post 2 (PrivateCloud) — DRAFT

### Proven CTAs (updated after each post)
- "What repetitive workflow are you still doing manually?" → Post 1
- "What does your lab infrastructure look like?" → Post 2 (draft)

---

## Part 7: The Read-Aloud Test (Final Gate)

Before EVERY post is approved, mentally read it as if you're telling a friend
about your project over chai. If any sentence makes you cringe or sounds like a
LinkedIn influencer, delete it.

Questions to ask:
- Would I say this to a friend? If no → rewrite
- Does this sound like ChatGPT wrote it? If yes → rewrite
- Is there a specific, real detail in the first 3 lines? If no → add one
- Can the reader picture the scene? If no → add sensory details
- Does the CTA invite a STORY? If no → rephrase
