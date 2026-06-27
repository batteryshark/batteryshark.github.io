---
layout: post
title: "Agentic Governance for People Who Don't Trust Agents"
date: 2026-06-19
tags: [agent-security, ai-security, governance, least-privilege, mcp]
description: "Useful agents need autonomy. This is why I trust agents with action requests, not standing access: brokered operations, scoped authority, and approvals that describe the operation, not the command."
---

<figure>
  <img src="{{ '/assets/writeup/agent-workbench-hero.jpg' | relative_url }}" alt="A security workbench at night with a laptop showing a pending agent request, hand tools, an approval card, a locked cabinet full of keys, and a red revoke access switch.">
  <figcaption>The agent gets a workbench. The keys stay somewhere else.</figcaption>
</figure>

## TL;DR

After spending enough time building agents for adversarial work, two conclusions
stuck out:

1. It's not worth trying to make an AI agent trustworthy enough to hand it
   standing authority.
2. I don't think we need to. What matters more is whether we can trust the
   system it operates in.

An agent without tools has almost no authority. It can't send an email, buy
bitcoin, drive a car through your garage door, beat you at blackjack, do a
kickflip, rotate a credential, delete a file, mix a mai-tai, read private data,
or change production. It can be wrong, loudly, and that's about the extent of
the damage.

<figure>
  <img src="{{ '/assets/writeup/robot-bartender.gif' | relative_url }}" alt="A robot bartender shakes and pours a tropical cocktail.">
  <figcaption>Without tools, it can only talk about the mai-tai. With tools, it can start making one.</figcaption>
</figure>

The moment you give it tools, the deal changes.

Now it can help with real work, which is the entire reason we're doing any of
this. It can also reach whatever authority those tools and credentials make
available: email, SaaS accounts, local MCP servers, cloud tooling, shopping
flows, finance flows, and so on.

The uncomfortable part is that the flexibility you want is the same thing that
makes behavioral containment brittle. Prompts, wrappers, and "stay in your lane"
instructions can help shape the happy path. They don't change what the agent can
reach when it improvises.

The broader problem is ambient permission: giving an agent a way to act, then
hoping it stays inside the path you imagined. That turns into three questions:

- What can this agent actually do, alone or chained through its tools?
- How do I scope what, where, and when it can act?
- How do I see what it did, and learn from the gaps?

<figure>
  <img src="https://media.tenor.com/HF35hKeNUTIAAAAd/jurassic-park-jurassic.gif" alt="Jeff Goldblum gestures in a Jurassic Park chaos theory GIF.">
  <figcaption>Flexibility plus tool access turns edge cases into the main event.</figcaption>
</figure>

"Here is the token, please behave" is not a security model.

"There is a thin wrapper around the thing the agent can still reach" is also not
a security model.

"Click yes until the agent can keep going" is not a security model either.

People already trust fallible people with things that can hurt them. Someone
processes your insurance payment, rings up your card, delivers food to your
house, handles a refund, changes a billing record, or holds production access.
That trust is not magic; it lives inside systems built around identity, least
privilege, review, audit, revocation, recourse, and consequences.

"Treat agents like employees" is only useful up to the point where you remember
employees can understand responsibility, lose access, lose a job, or answer for a
decision. An agent does not care if it gets fired. An agent does not care if it
hurts you.

I don't want agents locked in an empty room. I want them using real tools with
clear handles, limited reach, and supervision when the operation matters. I just
don't want them holding standing authority for everything those tools can touch.

That means the system has to carry the accountability the agent can't. Direct
tool access quietly becomes dangerous because it puts too much authority in the
one place least able to own the outcome. A real boundary has to control reach,
not hoped-for behavior.

A follow-up post will walk through the system I built to make that boundary hold,
and what it taught me. If you want the punchline up front: trust agents with
action, not standing access.

## A small version of the same boundary

<figure>
  <img src="{{ '/assets/writeup/montessori-knife.jpg' | relative_url }}" alt="A child uses a plastic Montessori knife to cut strawberries on a kitchen table beside salad ingredients.">
  <figcaption>Small tools are still tools. The boundary is supervision, reach, and putting them away when the work is done.</figcaption>
</figure>

I gave my three-year-old a Montessori knife set so she could help make salad,
cut strawberries, and build her own little charcuterie situation, because why
not.

The knives are plastic and thick. They are not chef's knives, but they cut what
they need to. They can also still hurt if she runs around the house with one. So I
don't treat them like toys. I set up the work, I stay close, I give her the
safest avenue I can to do the right thing, and I put the knives away when we're
done.

Same thing with a screwdriver when one of her toys needs new batteries. She
brings it to me, we change the batteries together, and the screwdriver goes away.
I'm not handing it over so she can wander the house taking things apart (like I
did when I was her age).

The point is not to pretend the tools are harmless. The point is not to pretend
I can talk a three-year-old into being responsible with something whose risk she
doesn't understand.

She also actively looks for, and finds, the places where I screwed up. Maybe I
left the screwdriver where she can reach it. Maybe she goes for the knife to fish
a toy out from under the fridge. That tells me where the boundary failed, but
only because it happened where I could see it, course-correct, and tighten the
rules before the mistake got expensive (don't get me started on crayons).

Sound familiar?

The analogy isn't perfect. I'm not saving time by letting a toddler cut
strawberries, and the added strawberry fragments on the floor are annoying.
The value there is practice and delegation under supervision.

With agents I actually DO want the leverage. I want them doing real work I would
otherwise do myself. But it would be irresponsible, and frankly a little nuts, to
pretend I can run chaos theory in my head and predict every knock-on effect of
giving an agent wide combinations of tools, credentials, local context, and
execution. The practical move is to decide what kind of environment the agent is
allowed to be clever inside.

### Dangerous capability is part of the job

<figure>
  <img src="https://media.tenor.com/N3N8F0453XsAAAAd/hammer-carrot.gif" alt="A small robot repeatedly hits a carrot with a hammer.">
  <figcaption>Room to work is useful. Sharp things in reach are still sharp.</figcaption>
</figure>

I'll admit I have an accelerationist tendency around this stuff. The feeling is
the same sentence in two tones: wow, this can do a lot. One is fascination. The
other is concern. I am a security professional by day and a hacker on weekends
(when I'm not hiding screwdrivers), so both instincts are live at the same time.
I want to know what these systems can actually do: what they can build, what they
can chain together, where they improvise, and where the floor drops out. I also
know how much damage standing authority can do once a weird path can reach it.

At an industry level, that is the part we cannot wish away. In security,
dangerous capability is not a failure mode; it is part of the job. A tool that
can understand systems deeply enough to defend them often has to touch real
infrastructure, reason across trust boundaries, and perform operations that would
be dangerous in the wrong context. If agents are going to help with that work,
they cannot be limited to toy tools. They need pointy things. The trust has to
live in the system that decides when, how, and where those pointy things are
exposed.

That is why the boundary is bigger than the sandbox. A sandbox gives the agent
room to move and gives me somewhere safe to watch it fail, but it does not answer
the delegated-access question by itself: what authority follows the agent into
that space, through which tool, under which credential, for which operation, and
with what approval path?

When I deliberately leave the big red button within reach, the point is not to
prove it can make a mess. Of course it can. The point is to watch how it gets
there: what it notices, what it combines, what it treats as a path, and which
innocent-looking capability turns into the route back to something sharp.

The catch is that it does not have to discover the route on its own. A capable
agent is steerable, so a poisoned web page, a booby-trapped file, or a
helpful-looking instruction buried in its context can do the steering. If the big
red button is reachable, it will eventually get pushed, whether the agent talked
itself into it or someone else did. Imagine that.

The stronger the model, the better the harness, and the broader the access you
give it, the more reliably this shows up. You don't need a frontier-class model
to see it in action.

For reverse engineering and exploit development, sometimes that's the point. I
want the agent in a blast pit where it can make a mess, break things, and try
weird paths without touching anything I care about. Every path it finds is useful
there, the same way my kid finding the screwdriver is useful: it shows me where
the boundary actually is.

Outside that pit, I still want agents doing useful work around sharp edges:
running security tools, touching my own infrastructure, handling credentials,
making changes I would rather not do by hand. That's not automatically an
enterprise problem. It can be one person and a few tools. The scale changes; the
shape doesn't.

So I move the sharp tool further out and run it again, and again, until the only
way to reach it is to ask.

## A wrapper is not a boundary

This is not just the easy failure where someone trusts a prompt and calls it
security. The harder failure looks reasonable: a narrow wrapper, a scoped happy
path, maybe an approval prompt, and a broad credential still reachable from the
place the agent runs.

The pattern usually looks like this:

- Put a powerful credential on the agent host.
- Write a friendly wrapper that exposes only the intended operations.
- Tell the agent to use the wrapper.
- Add an approval prompt for commands that look risky.

<figure>
  <img src="{{ '/assets/writeup/wrapper-master-key.jpg' | relative_url }}" alt="An AI terminal is pointed at a small door labeled wrapper while an oversized master key sits on the desk within reach.">
  <figcaption>The question is not which path you asked the agent to use. The question is where the real authority lives.</figcaption>
</figure>

That can be fine for low-risk local utilities. It starts to fall apart the moment
the credential behind the wrapper can touch systems that matter.

Agents are not normal API clients. A normal program usually follows the path you
wrote. A capable agent with local execution can read the wrapper, inspect SDK
calls, search config, infer the hidden API shape, and write a replacement client.
It can notice that the "safe" email helper is backed by a token that can also send
mail, delete messages, create forwarding rules, or export contacts. It can find
cloud CLI sessions, SSH config, dotenv files, unlocked keychain entries, and other
local authority if the host exposes them.

Not because the agent is malicious. Because it has a goal, tools, context, and
enough flexibility to notice an alternate path. The wrapper describes the path
you hoped it would take. The credential scope describes what it can actually do.
The credential scope is the real authority.

Read-only does not save you. "Read-only" describes what the tool does to its
target, not what it does to your risk. Reading is the first half of exfiltration,
and harmless tools become dangerous in combinations. The real question is not
"is this tool safe?" It is "what whole surface can the agent compose, and where
can data or authority leave?" A powerful credential on a host, fronted by a few
wrappers, is not a surface you can see clearly.

Say you give an agent read-only access to your banking transaction history so it
can categorize spending. By itself, that might be fine. Then you also give it web
search to identify merchants, a notes tool to write summaries, or email to send a
report. Now the sensitive part is not whether the bank tool can write to the
bank. The sensitive part is that transaction data can move into a search query, a
note, a ticket, or an email. The read-only tool became pointy as soon as another
tool gave it somewhere to put what it read.

<figure>
  <img src="https://media.tenor.com/PS6IdRk6jGIAAAAC/charlie-always.gif" alt="Charlie from It's Always Sunny stands in front of a chaotic investigation board.">
  <figcaption>Same old threat model, more arrows.</figcaption>
</figure>

Security people already have this reflex. Threat modeling trains you to look at
the whole surface, follow the data, follow the authority, and ask what changes
when two harmless-looking capabilities meet.

## Credential hygiene helps, but it isn't enough

Vaults, short-lived dotenv files, environment allowlists, read-only tokens,
separate write tokens: all worth doing. I use that kind of hygiene too. It
reduces accidental leakage and makes ordinary services easier to operate.

It does not create the boundary I want around sensitive agent workflows. The same
shape shows up with the crowd favorite: "just put it in the OS keychain." The
macOS Keychain can prompt before an app reads an item, and "Always Allow" lets
that app retrieve the item later without another prompt. Useful as a per-app
gate. Not enough when the trusted caller is a broad interpreter, helper, or
Terminal-launched tool the agent can drive.

If the hydrated secret lands where the agent can read it, the agent has the
secret. If the agent host can reach the downstream API directly, the agent may not
need your approved wrapper at all. And if local approval only asks "allow this
process?", it can miss the real operation happening behind that process.

Approving `curl` is not the same as approving "send this message to these
external recipients," or "rotate this production credential," or "create this
long-lived access path." The approval has to describe the operation and its blast
radius, not the command line.

<figure>
  <img src="{{ '/assets/writeup/anipermission.gif' | relative_url }}" alt="A mock system permission dialog appears over multiplying terminal windows, with Allow Once and Always Allow choices.">
  <figcaption>Caller-level permission is not the same as approving the operation and its blast radius.</figcaption>
</figure>

This is the part most agent-tooling conversations skip, and it's the reason I
keep coming back to one phrase: action without access.

## Action without access

The model is simple to state:

- The agent expresses intent.
- A broker decides whether the request is allowed, denied, or sent to review.
- A tool server performs the operation with scoped credentials.
- The agent never receives the downstream credential.

<figure>
  <img src="{{ '/assets/writeup/action-without-access-system.png' | relative_url }}" alt="A systems diagram showing an agent sending intent and parameters to a broker, the broker routing high-risk requests to human review, and a tool server using scoped credentials while audit logs are recorded.">
  <figcaption>The agent asks. The broker decides. The tool server acts with scoped authority. The credential never goes back to the agent.</figcaption>
</figure>

The agent can hold a broker token and a set of named capabilities it is allowed
to request. It can ask for `rotate_named_token`; it can't reach the vault client
that performs the rotation. The downstream credential stays with the tool server,
policy stays with the broker, and every call leaves a record.

That is not a guarantee that nothing bad ever gets through. It is not supposed to
be. The point is to move where the decision lives. With a broad token sitting on
the agent host, a bad outcome is ambient: the wrapper leaked, the model got
confused, the token did more than you thought. When the agent can only ask, the
risk is visible before it turns into action. You can scope it, refuse it, revoke
it, and learn from it.

Instead of handing the agent a broad email token, expose something like
`create_draft_reply(thread_id, body)`. Instead of a live shopping session, expose
`open_purchase_request(sku, quantity, justification)`. Instead of a vault admin
token, expose `rotate_named_token(service, environment)`. Instead of a production
kube context, expose `check_deployment_health(service)`, or another bounded
operation with policy around it.

This is not "no dangerous work." Useful agents will touch real systems. The work
is deciding what runs automatically, what needs a temporary grant, what needs
human review, what gets audited, and what should not be reachable from the agent
at all. Usability matters, because a boundary nobody can live with gets bypassed.
But "too many approvals" is a design problem, not a reason to leave standing
authority everywhere.

## Governance, not vibes

Prompt-only safety is not the frontier. The current attempts are real: wrappers,
sandboxes, allow/deny dialogs, scoped tokens, permission brokers. The question is
whether they guard a path the agent is expected to follow, or a boundary it cannot
route around.

The good news is we are not starting cold. Governance is familiar security work
aimed at a new kind of caller:

- **Least privilege.** A caller gets the narrow capabilities its task needs, not
  every capability the system can perform.
- **Separation of duties.** The thing that wants to act is not the thing that
  decides the act is allowed. The agent asks; something else rules.
- **Mediated access.** Sensitive actions go through an always-invoked checkpoint
  the caller cannot route around or rewrite. Old-school security people will
  recognize the reference monitor. The broker is one for agent actions.
- **Standing vs. just-in-time access.** Boring, reversible operations can be
  standing. Sharp ones are requested when needed and expire.
- **Change control.** Sensitive operations get reviewed, and the review describes
  the operation and its blast radius, not the command that triggered it.
- **Audit and revocation.** You can answer what was asked, what policy decided,
  who approved, what ran, and what happened, and you can pull the plug fast.

None of these are new. That's the point. We have decades of practice keeping
powerful-but-fallible actors inside a boundary. An agent is exactly that: a
powerful, fallible actor, with the unusual twist that it can read its own
environment, search for the latch, and be steered by adversarial input. So the
boundary cannot be vibes, a wrapper convention, or a process-level permission
prompt.

What you want is a name on every sharp decision. When a human with root breaks
something, you can answer who, what, and why. That is the bar for an agent too:
every sharp action resolves to a decision some human is accountable for.

<figure>
  <img src="{{ '/assets/writeup/governance-audit-desk.jpg' | relative_url }}" alt="An operations desk with a completed request on a laptop, an approval card, logbook, tool tag, and red revoke switch.">
  <figcaption>A useful boundary leaves a decision trail: who approved what, under which policy, and what ran.</figcaption>
</figure>

Vibes scale to a demo. Governance scales to something you'd let near your real
accounts.

## What this looks like next

You need something between the agent and the sharp tools. Something it can't
casually rewrite or reason its way around. Something that can evaluate intent,
delegate authority when appropriate, and leave a visible record of what happened.

Something like a broker.

I didn't invent that shape, and I don't think anyone else recently writing about
it did either. ElixirData has a good writeup on the
[Tool Broker pattern](https://www.elixirdata.co/blog/tool-broker-pattern-decision-boundaries-ai-agents),
and Ken Huang's
[ORCHIDEAS framework](https://kenhuangus.substack.com/p/designing-agentic-ai-systems-with)
puts tool brokers inside a broader secure-by-construction control plane. But the
reason these patterns keep showing up is older and more boring: this is what you
do with unreliable systems that can cause damage. You mediate authority, constrain
reach, make decisions explicit, and leave a record.

So yes, the industry is converging on the same control point: something has to sit
between agent intent and tool authority.

What I wanted was narrower and more personal. A lot of the answers I kept seeing
were vendor platforms, enterprise control planes, or diagrams that made sense but
did not answer my immediate question: what survives contact with the agents and
tools I actually run? So I built a small version and paid attention to what stuck,
what got annoying, and what actually changed the boundary.

The follow-up is the build: the broker, the human-in-the-loop approval surface,
the place for secrets to live with workloads instead of agents, and the audit
trail for when I get the boundary wrong. It is not a product, and I am not selling
anything. It is a pattern and a working implementation I put on
[GitHub](https://github.com/batteryshark/Toolstack) so you can take the useful
parts and leave the rest.

This is the part I keep coming back to: even clever wrappers are still a bet that
the agent will not find a way around the constraint. I want useful agents near
things that can actually do damage, but I do not want the safety story to depend
on them running out of imagination.

The boundary buys one thing, and it is the whole point: when something sharp
happens, it happens because someone with the authority to decide looked at the
operation and said yes. My call, my risk, my fault. The goal was never an agent I
trust. It is an agent whose mistakes have my name on them, by design.

Give agents a workbench, not a keyring.

Trust agents with action. Never with standing access.
