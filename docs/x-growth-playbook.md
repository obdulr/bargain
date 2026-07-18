# X/Twitter Growth Playbook — BargainHuntrs

> **Account:** [@bargain4huntrs](https://x.com/bargain4huntrs)
> **Site:** [bargainhuntrs.com](https://bargainhuntrs.com)
> **Document type:** MANUAL growth strategy (separate from the automated engagement bot)
> **Last updated:** 2025-07-09

---

## Current State Analysis

| Metric | Value |
|---|---|
| Handle | @bargain4huntrs |
| Followers | 0 |
| Following | 5 |
| Posts | 17 |
| Post type | Deal alerts with affiliate links |
| Engagement | None |
| Content variety | None — single post format only |
| Community building | None |
| Localization issue | Product names appear in French/German, making posts look spammy/automated |

### Core Problems

1. **Zero engagement** — No replies, likes, or retweets from or to the account.
2. **No content variety** — Every post is a raw deal alert. No threads, polls, or conversation starters.
3. **Spammy appearance** — Localized (French/German) product names leak into English posts, making them look like bot spam rather than a curated deal account.
4. **No profile optimization** — Bio, header, and pinned tweet are not set up to convert visitors into followers.
5. **No community** — No hashtag, no UGC, no interaction with the broader deal-hunting community.
6. **No scheduling** — Posts are clustered rather than spread across peak engagement windows.

### Localization Fix (Immediate Priority)

- Ensure all deal posts pull **English** product titles from the Amazon Product Advertising API (use `Marketplace=ATVPDKIKX0DER` for US).
- Strip/replace any non-English characters before posting.
- Add a fallback: if the product title is not English, skip the post or rewrite it manually.
- This single fix will dramatically improve perceived legitimacy.

---

## 1. Profile Optimization

### Bio

```
Deal hunter 🔥 | Amazon, Walmart, eBay + more | Glitch deals & price errors | Turn on notifications 🔔
```

- Keep it under 160 characters (currently ~110 — room to spare).
- Add link line: `👇 Today's best deals: bargainhuntrs.com`

### Header Image

- **Dimensions:** 1500 x 500 px
- **Content:** Bold "BARGAINHUNTRS" wordmark on a dark background with a subtle deal/price-tag motif.
- **Include:** 3-4 retailer logos (Amazon, Walmart, eBay, Target) along the bottom edge.
- **Tagline overlay:** "Glitch deals. Price errors. Real savings."
- **Tool:** Canva template — use the "Twitter Header" preset.

### Profile Image

- 400 x 400 px logo on a solid color background (brand orange/red for urgency feel).
- Must be readable at 24x24 px (the size shown in timelines).

### Pinned Tweet Strategy

Pin a **"Best Deals This Week"** thread that is updated continuously:

- **Tweet 1 (pinned):** "🧵 Best Deals This Week — Updated Daily\n\nBookmark this thread. I update it every morning with the top 5 deals I've found.\n\nFollow @bargain4huntrs and turn on notifications so you never miss a glitch deal. 🔔\n\nbargainhuntrs.com"
- **Replies:** Each reply = one deal (image + price + link).
- **Cadence:** Add 3-5 new deal replies every morning; delete deals that expire.
- **Why:** A pinned thread is the first thing visitors see. It demonstrates value instantly and gives them a reason to follow.

### Link in Bio

- Set the profile website link to: `https://bargainhuntrs.com?utm_source=x&utm_medium=profile&utm_campaign=bio`
- Use a UTM tag so bio clicks are trackable in analytics.

---

## 2. Content Mix

Target ratios for daily output. With 8-12 posts/day, the breakdown looks like this:

| Content Type | Target % | Posts/Day (at 10 avg) | Purpose |
|---|---|---|---|
| Deal alerts (improved format) | 60% | 6 | Core value — the reason people follow |
| Deal threads | 15% | 1-2 | High-impression, save-worthy content |
| Engagement bait | 10% | 1 | Boosts reply rate and algorithmic reach |
| Retweets/quotes of other deal accounts | 10% | 1 | Builds relationships, fills gaps in schedule |
| Brand building | 5% | 0-1 (weekly) | Humanizes the account, builds trust |

### Deal Alert Format (Improved)

**Current (bad):**
```
[Localized product name] - $XX.XX
https://amzn.to/xxx
```

**Improved template:**
```
🔥 PRICE DROP: [English product name]
was $XX → now $XX (XX% off)

✅ Free shipping w/ Prime
⏰ Limited stock — deal won't last

#DealAlert #AmazonDeals

🔗 bargainhuntrs.com/deal/[slug]
```

Rules for every deal alert:
- Always show the **was → now** price drop.
- Always include the **discount %**.
- Always include a **scarcity/urgency cue** (limited stock, ends today, etc.).
- Always include an **image** (product photo or screenshot of the price).
- Rotate 2-3 hashtags — never reuse the exact same set back-to-back.
- Link to bargainhuntrs.com/deal/[slug] (with affiliate redirect) rather than raw amzn.to links — this drives site traffic and looks less spammy.

### Deal Thread Example

```
🧵 Top 5 Amazon Deals Under $50 This Week

1/6
```
(Each subsequent tweet = one deal with image, price drop, and link)

### Engagement Bait Examples

- "What's the best deal you've ever scored? 👇"
- "Would you buy this at this price? Yes or No 👇"
- "RT if you want more glitch deals like this one 🔥"
- "Tag someone who needs to see this deal 👀"

### Brand Building Examples

- "We just hit 100 followers! 🎉 Thank you for hunting with us. Here's what's coming next..."
- "Site update: You can now filter deals by discount % at bargainhuntrs.com 🔍"
- "Shoutout to @username for finding today's best glitch deal 👏"

---

## 3. Posting Schedule

### Best Times (US Eastern Time)

| Window | Why |
|---|---|
| 8:00 - 10:00 AM ET | Morning scroll / commute |
| 12:00 - 2:00 PM ET | Lunch break |
| 7:00 - 9:00 PM ET | Evening unwind — highest engagement |

### Daily Frequency

- **Target:** 8-12 posts/day
- **Distribution:** Spread evenly across the 3 windows above. **Never cluster** 5 posts in 10 minutes — it triggers spam signals and annoys followers.
- **Rough cadence:** 3-4 posts per window, spaced 30-60 minutes apart.

### Weekly Schedule

| Day | Focus | Notes |
|---|---|---|
| Monday | Deal alerts + 1 engagement bait | Standard cadence |
| Tuesday | Deal alerts + 1 quote-tweet | Standard cadence |
| Wednesday | Deal alerts + 1 deal thread | Mid-week thread performs well |
| Thursday | Deal alerts + 1 engagement bait | Standard cadence |
| Friday | Deal alerts + 1 quote-tweet | Slightly higher volume — people scrolling into weekend |
| Saturday | 6-8 posts, lighter cadence | More lifestyle/home deals; evening window strongest |
| Sunday | 6-8 posts + weekly "Top 10 Deals" thread (evening) | Thread goes live 7 PM ET |

### Weekend vs Weekday

- **Weekdays:** 8-12 posts, tech and office deals perform well, morning + lunch windows critical.
- **Weekends:** 6-8 posts, home/kitchen/fashion deals perform better, evening window is the peak. Post the weekly thread Sunday evening.

### Special Event Schedules

| Event | Schedule Adjustment |
|---|---|
| **Prime Day** (July, October) | 15-20 posts/day. Live-updating mega-thread. Post every 30-60 min during active hours. Pre-event teaser thread 3 days prior. |
| **Black Friday / Cyber Monday** | 15-20 posts/day starting Thanksgiving evening through Cyber Monday. Mega-thread updated hourly. |
| **Back to School** (late July - August) | +3 posts/day focused on school/tech deals. Dedicated thread each week. |
| **Holiday season** (December) | 12-15 posts/day. Gift-guide threads weekly. Last shipping cutoff reminder tweets. |
| **Major retailer sales** (Walmart+, Target Circle Week) | +5 posts/day during the event window. |

---

## 4. Engagement Strategy (Manual)

### Daily Tasks

| Task | Count | How |
|---|---|---|
| Reply to tweets from target deal accounts | 5 | Reply with genuine commentary or an added deal — never just "great post!" |
| Like deal-related tweets | 20 | Search hashtags (#DealAlert, #AmazonDeals) and like recent posts |
| Check notifications and reply to any mentions | All | Respond within 1 hour during active hours (8 AM - 10 PM ET) |

**Target accounts to engage with:**
- @DealsFinderIO
- @nextgendeals
- @Wario64
- @TheDealGuy
- @BradsDeals
- @DealsDaddyCom
- @Slickdeals
- @BensBargains

### Weekly Tasks

| Task | Count | When |
|---|---|---|
| Follow new accounts in deal/savings niche | 30 | Monday morning |
| Quote-tweet deals from other accounts with added commentary | 2-3 | Spread across the week |
| Post the weekly "Top 10 Deals This Week" thread | 1 | Sunday 7 PM ET |
| Review analytics and adjust strategy | 1 | Friday afternoon |

### Monthly Tasks

| Task | Count | When |
|---|---|---|
| DM micro-influencers for cross-promotion | 5-10 | First week of the month |
| Refresh pinned tweet thread | 1 | Ongoing — but fully refresh monthly |
| Audit follower list — unfollow inactive/spam accounts | As needed | End of month |
| Review and update this playbook | 1 | End of month |

### Engagement Rules

1. **Never** reply with generic comments ("Nice!", "Great deal"). Always add value.
2. **Never** self-promote in replies unless directly relevant.
3. **Do** ask questions in replies — they boost engagement on the original tweet and your reply.
4. **Do** quote-tweet with added context ("This is a great deal, but here's a similar one $10 cheaper 👇").
5. **Do** build genuine rapport — deal accounts talk to each other. Become part of the community.

---

## 5. Hashtag Strategy

### Primary (use 1-2 per post, rotate)

- `#DealAlert`
- `#AmazonDeals`
- `#BargainHunt`
- `#Clearance`
- `#PriceDrop`

### Secondary (use for specific contexts)

- `#SaveMoney`
- `#Frugal`
- `#DealOfTheDay`
- `#BlackFriday`
- `#PrimeDay`

### Niche (use when relevant)

- `#PriceError`
- `#GlitchDeal`
- `#TechDeals`
- `#HomeDeals`
- `#FashionDeals`

### Avoid

- `#deals` — too generic, gets buried in seconds.
- `#sale` — same problem.
- `#shopping` — too broad, attracts spam followers.
- More than 3 hashtags per post — looks spammy and X algorithm penalizes it.

### Rules

- **2-3 hashtags per post, maximum.**
- **Rotate them** — never use the same combination two posts in a row.
- **Match the tag to the deal** — don't tag a kitchen deal with `#TechDeals`.
- **Use `#BargainHuntrsFind`** for user-submitted deals (see Community Building).

---

## 6. Thread Strategy

### Weekly: "Top 10 Deals This Week"

- **When:** Sunday 7 PM ET
- **Format:**
  ```
  🧵 Top 10 Deals This Week — [Date Range]

  I scanned 1,000+ products this week. These are the 10 best.
  Bookmark this. Share with a friend who loves a bargain.

  1/11
  ```
- Each subsequent tweet: product image, was → now price, discount %, link, 1-2 hashtags.
- Final tweet: "That's the list! Follow @bargain4huntrs for daily deals. See you next Sunday 🔔"

### Bi-Weekly: "Best Amazon Finds Under $25"

- **When:** 1st and 3rd Wednesday of each month, 12 PM ET
- **Format:** Same as weekly thread but filtered to sub-$25 items.
- **Angle:** Budget-friendly, impulse-buy territory. High save/retweet rate.

### Monthly: "Deal Hunting Tips" (Educational)

- **When:** 2nd Tuesday of each month, 8 AM ET
- **Format:** 7-10 tweet thread teaching a skill:
  - "How to spot a fake Amazon discount"
  - "How to use camelcamelcamel to verify price history"
  - "How to stack Walmart clearance with coupons"
  - "How to find glitch deals before they're patched"
- **Purpose:** Establishes authority, high save rate, drives profile visits.

### Event Mega-Threads (Prime Day, Black Friday)

- **Format:** Single pinned thread, updated live throughout the event.
- **Tweet 1:** "🧵 PRIME DAY 2025 LIVE DEAL THREAD — Bookmark this. Updating every 30 min."
- **Cadence:** Add a new reply every 30-60 minutes with the best current deal.
- **Delete expired deals** to keep the thread clean.
- **Pre-event:** Post a teaser thread 3 days before ("Here's what to expect on Prime Day...").
- **Post-event:** Post a recap thread ("The 10 best Prime Day deals that sold out fastest").

---

## 7. Community Building

### User-Generated Deals

- Encourage followers to submit deals at `bargainhuntrs.com/community`.
- Feature the best submissions in daily deal alerts with credit: "Found by @username 🔍"
- Create the hashtag **`#BargainHuntrsFind`** for user-submitted deals on X.

### Hunter of the Week

- Every Friday, feature the community member who submitted the best deal that week.
- **Tweet format:**
  ```
  🏆 Hunter of the Week: @username

  They found this [product] glitch deal that dropped to $X (XX% off) — and shared it with the community first.

  Want to be next week's Hunter? Submit deals at bargainhuntrs.com/community

  #BargainHuntrsFind
  ```

### Weekly Polls

- Post 1 poll per week (Wednesday, 12 PM ET).
- **Examples:**
  - "Would you buy this at this price? 👇 Yes / No / Already bought it"
  - "Which deal category do you want more of? 👇 Tech / Home / Fashion / Grocery"
  - "Best deal you've ever scored? Reply with the price 👇"

### Response SLA

- **During active hours (8 AM - 10 PM ET):** Respond to every reply within **1 hour**.
- **Outside active hours:** Respond by 9 AM the next day.
- **Every reply gets a response** — even if it's just a like. Never leave a follower hanging.

### Community Rituals

- **"Deal of the Day"** — every morning, tweet the single best deal found that day with the hashtag `#DealOfTheDay`.
- **"Glitch Alert"** — when a price error is found, tweet immediately with `#GlitchDeal` and a warning that it may be cancelled.
- **"Restock Alert"** — when a previously-sold-out deal comes back, tweet it and tag the original thread.

---

## 8. Influencer Outreach

### Target Persona

| Attribute | Criteria |
|---|---|
| Niche | Personal finance, frugal living, mom blogs, couponing, side hustles |
| Follower count | 1,000 - 50,000 (micro-influencer) |
| Engagement rate | > 2% (check manually — likes/replies vs followers) |
| Audience overlap | US-based, deal-conscious, 25-54 age range |
| Account age | > 6 months (avoid brand-new accounts) |

### Offer

- **Free Hunter subscription** (or free premium features on bargainhuntrs.com).
- **Shoutout** from @bargain4huntrs in exchange for a mention/retweet.
- **Affiliate revenue share** if applicable (discuss case-by-case).

### Outreach DM Template

```
Hi [Name] — love your content on [specific topic they posted about].

I run BargainHuntrs (@bargain4huntrs) — we track glitch deals and price errors across Amazon, Walmart, and eBay.

I'd love to send you a free Hunter subscription in exchange for a mention or retweet. No pressure, but I think your audience would love our daily deal alerts.

Let me know if you're interested and I'll set you up. 🙌

— [Your name]
```

### Tracking

- Maintain a spreadsheet (Google Sheets) with columns:
  - Handle
  - Follower count
  - Niche
  - Date contacted
  - Status (No response / Responded / Declined / Accepted)
  - Follow-up date
  - Notes

### Cadence

- Contact 5-10 new micro-influencers per month.
- Follow up once after 7 days if no response. Do not follow up twice.
- Track conversion rate. Adjust target persona if response rate is below 20%.

---

## 9. Analytics & KPIs

### Weekly Tracking

| Metric | Source | Target (Month 1) |
|---|---|---|
| Follower growth | X Analytics | +25/week |
| Impressions | X Analytics | 10K/week |
| Engagement rate | X Analytics | > 3% |
| Link clicks | UTM tags in Google Analytics | 200/week |
| Profile visits | X Analytics | 500/week |
| Thread saves/retweets | Manual count | 10/week |

### Milestone Targets

| Milestone | Target Date | Followers |
|---|---|---|
| First 100 followers | End of Month 1 | 100 |
| 500 followers | End of Month 3 | 500 |
| 2,000 followers | End of Month 6 | 2,000 |
| 5,000 followers | End of Month 12 | 5,000 |

### Tools

| Tool | Purpose |
|---|---|
| **X Analytics** (analytics.x.com) | Native impressions, engagement, follower growth |
| **Buffer** (buffer.com) | Scheduling + post-level analytics |
| **Google Analytics** (with UTM tags) | Link click tracking from X to bargainhuntrs.com |
| **Spreadsheet** (Google Sheets) | Manual weekly KPI log + influencer outreach tracker |

### UTM Tag Convention

All links posted to X should use this format:

```
https://bargainhuntrs.com/deal/[slug]?utm_source=x&utm_medium=social&utm_campaign=[deal_type]&utm_content=[post_id]
```

- `utm_campaign`: `deal_alert`, `thread`, `pinned`, `bio`, `community`
- `utm_content`: the X post ID or a short slug (e.g., `top10_week28`)

### Weekly Review (Friday afternoon)

Every Friday, log the week's numbers and answer:

1. Which post got the most impressions? Why?
2. Which post got the most link clicks? Why?
3. Did any post lose followers? Why?
4. What content type overperformed vs underperformed its ratio?
5. What should we do more of next week?

---

## 10. Quick Wins (First 48 Hours)

### Hour 0-2: Profile Fix

- [ ] Update bio to: `Deal hunter 🔥 | Amazon, Walmart, eBay + more | Glitch deals & price errors | Turn on notifications 🔔`
- [ ] Set profile website link to `https://bargainhuntrs.com?utm_source=x&utm_medium=profile&utm_campaign=bio`
- [ ] Upload header image (1500 x 500 px)
- [ ] Upload profile image (400 x 400 px logo)
- [ ] Fix localization issue — ensure all future deal posts use English product titles

### Hour 2-6: Community Entry

- [ ] Follow 50 deal/savings accounts immediately (use the target list in Section 4 as a starting point)
- [ ] Like 50 deal-related tweets (search `#DealAlert`, `#AmazonDeals`)
- [ ] Reply to 20 trending deal tweets with genuine commentary

### Hour 6-12: First Content

- [ ] Post a "Hello X!" intro tweet:
  ```
  👋 Hello X!

  I'm BargainHuntrs — I hunt glitch deals, price errors, and hidden clearance across Amazon, Walmart, eBay + more.

  Turn on notifications 🔔 and I'll save you money every day.

  Today's best deals: bargainhuntrs.com
  ```
- [ ] Pin the intro tweet (until you have enough deals for a pinned thread — swap by end of week 1)
- [ ] Post 3-4 deal alerts using the improved format from Section 2

### Hour 12-24: Momentum

- [ ] Post 4-5 more deal alerts across the day, spread out
- [ ] Reply to 5 more deal tweets from target accounts
- [ ] Like 20 more deal tweets
- [ ] Post 1 engagement bait tweet ("What's the best deal you've ever scored? 👇")

### Hour 24-48: Consistency

- [ ] Post the first "Top 5 Deals Under $50" mini-thread
- [ ] Continue deal alerts at 8-12/day cadence
- [ ] Replace pinned intro tweet with a "Best Deals This Week" thread
- [ ] Log Day 1 and Day 2 metrics in the tracking spreadsheet
- [ ] Identify the 3 best-performing posts and note what worked

### 48-Hour Checklist Summary

| Action | Count | Done |
|---|---|---|
| Fix bio + header + profile image | 1 | ☐ |
| Fix localization issue | 1 | ☐ |
| Follow deal accounts | 50 | ☐ |
| Like deal tweets | 50 | ☐ |
| Reply to deal tweets | 20 | ☐ |
| Post intro tweet | 1 | ☐ |
| Pin welcome tweet | 1 | ☐ |
| Post deal alerts (improved format) | 8-10 | ☐ |
| Post engagement bait | 1 | ☐ |
| Post first mini-thread | 1 | ☐ |
| Swap pinned tweet to deals thread | 1 | ☐ |
| Log metrics | 2 days | ☐ |

---

## Appendix: Content Templates

### Deal Alert Template

```
🔥 PRICE DROP: [English product name]
was $XX → now $XX (XX% off)

✅ Free shipping w/ Prime
⏰ Limited stock — deal won't last

#[Hashtag1] #[Hashtag2]

🔗 bargainhuntrs.com/deal/[slug]
```

### Glitch Deal Template

```
⚠️ GLITCH DEAL: [English product name]
was $XX → now $XX (XX% off)

This looks like a price error — order fast before it's fixed.
⚠️ May be cancelled by the retailer.

#GlitchDeal #PriceError

🔗 bargainhuntrs.com/deal/[slug]
```

### Thread Opener Template

```
🧵 [Thread title]

[1-sentence hook]

Bookmark this. Share with a friend who loves a bargain.

1/[N+1]
```

### Thread Closer Template

```
That's the list! ✅

Follow @bargain4huntrs for daily deals.
Turn on notifications so you never miss a glitch deal. 🔔

See you next [day]. 👋

bargainhuntrs.com
```

### Engagement Bait Templates

```
What's the best deal you've ever scored? 👇 Reply with the price.
```

```
Would you buy this at this price? 👇
Yes / No / Already bought it
```

```
RT if you want more glitch deals like this one 🔥
```

```
Tag someone who needs to see this deal 👀
```

---

## Appendix: Target Accounts to Engage With

| Handle | Niche | Priority |
|---|---|---|
| @Wario64 | Gaming/tech deals | High |
| @DealsFinderIO | General deals | High |
| @nextgendeals | General deals | High |
| @TheDealGuy | Tech deals | High |
| @BradsDeals | General deals | Medium |
| @Slickdeals | Community deals | Medium |
| @BensBargains | General deals | Medium |
| @DealsDaddyCom | General deals | Medium |
| @MattSlickdeals | Slickdeals founder | Low |
| @FreeStuffFinder | Freebies/coupons | Medium |

---

*This playbook is a living document. Review and update it monthly based on what the analytics show is working.*
