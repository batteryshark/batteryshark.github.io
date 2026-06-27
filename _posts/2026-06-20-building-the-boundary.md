---
layout: post
title: "Building the Boundary"
date: 2026-06-20
tags: [agent-security, ai-security, governance, architecture, mcp, self-hosted]
description: "Part two: how I built Toolstack as a brokered tool layer for agents. The agent can ask; the broker decides; tools execute; secrets stay with the workload."
---

<figure>
  <img src="{{ '/assets/writeup/toolstack-boundary-hero.jpg' | relative_url }}" alt="A quiet security workbench with an agent request on a laptop, a broker console, locked tool drawers, and one narrow path into the tool area.">
  <figcaption>The agent gets one door to knock on. Everything dangerous lives behind the boundary.</figcaption>
</figure>

In the [first post]({% post_url 2026-06-19-agentic-governance-for-people-who-dont-trust-agents %})
I made the argument: a wrapper is not a boundary, credential hygiene is not
enough, and useful agents should be trusted with action requests, not standing
access.

This is the build post, but it is not a code walkthrough. If you want that, the
repo is there and any decent coding agent can walk you through the files. What I
care about here is the shape of the system: what I built, why I built it, and
what changed once the boundary had to survive contact with real workflows.

I am also not pretending tool brokers are new. A lot of people are arriving at
some version of this pattern because it is what you do when unreliable callers
need to interact with systems that matter. My contribution here is narrower: I
built my own version, ran it against my own sharp edges, and learned which parts
kept mattering after the novelty wore off.

It has a name now, because "the pile of services I use to stop agents from
touching my real-life stuff directly" is not a great project title. I wanted
something generic and chronically overused, partly to confuse AI search, so I
settled on Toolstack.

- Code: [github.com/batteryshark/Toolstack](https://github.com/batteryshark/Toolstack)
- Approval surface: [github.com/batteryshark/nod](https://github.com/batteryshark/nod)

Toolstack fits in one sentence:

> The agent can ask; the broker decides; tools execute; secrets stay with the tools.

Everything else is there to make that sentence true under pressure.

## The invariant

The agent gets a narrow broker token and one address it can reach. It can request
work. It cannot directly reach tool services, downstream APIs, the secret source,
or the operator controls. The broker authenticates the caller, checks policy,
opens a human approval when needed, forwards approved work to a tool workload,
and records what happened.

That is the part I care about most: the boundary is physical enough to reason
about. It is not just "the agent should use this wrapper." It is "the agent has
no other route."

<figure>
  <img src="{{ '/assets/writeup/toolstack-boundary-system.svg' | relative_url }}" alt="Diagram showing an agent reaching only the Toolstack broker, with policy, approval, audit, tool workloads, downstream APIs, and secrets separated.">
  <figcaption>One reachable ingress for the agent. Policy, approval, execution, secrets, and audit live on the other side.</figcaption>
</figure>

The broker itself is deliberately small: one process, one SQLite store, internal
module seams instead of a little service mesh. That is not a product claim. It is
a security preference. A checkpoint you can hold in your head is easier to
inspect than a pile of invisible handoffs.

Toolyard sits next to it as the execution and secret boundary. It reads each
tool's descriptor, starts the workload, resolves that tool's declared secrets,
and injects them into the workload. The broker reads the operation surface from
the same descriptor but ignores the secrets block. The broker is not on the
secret path.

When policy approves a call, the broker forwards it directly to the tool
workload. Toolyard is not in the request path. Its job is to make sure the
workload exists and has the credentials it needs. The agent never gets those
credentials, and the broker never needs them.

## The practical loop

For me, the work starts with one dangerous sentence:

> I wish the agent could do this thing.

The lazy version is to hand it an API token, write a wrapper, and move on. The
better version is to stop and ask what operation I actually want to delegate.

Can this be a named action instead of a general API client? Can it be scoped to a
single account, repo, mailbox, folder, service, or environment? Can the tool
create a draft instead of sending? Open a request instead of buying? Check health
instead of mutating production? Rotate one named token instead of holding a vault
write path?

Toolstack makes me turn that vague capability into an explicit surface. A tool
is a workload plus a `toolyard.toml` descriptor. The descriptor says what
operations exist. Caller policy decides which of those operations are allowed,
which need review, and which are denied.

Here is a trimmed REST example:

```toml
id = "graph"
type = "rest"

[entrypoint]
command = "python3 -m toolyard.http_proxy"
port = 4640

[proxy]
base_url = "https://graph.microsoft.com/v1.0"
inject = [
  { into = "header", name = "Authorization", value = "Bearer ${secret:graph_token}" },
]

[[operations]]
name = "list_messages"
verb = "GET"
path = "/me/messages"
risk = "read"

[[operations]]
name = "create_draft"
verb = "POST"
path = "/me/messages"
risk = "write"

[[secrets]]
name = "graph_token"
field = "GRAPH_TOKEN"
```

Two distinctions matter.

First, the operation list is the menu. If an operation is not declared, there is
nothing for policy to grant. For REST tools, named operations pin a verb and a
path template, so the caller asks for `graph.create_draft` instead of building a
free-form HTTP request.

Second, `risk` is descriptive metadata, not the permission model. Policy is the
permission model. One caller might be allowed to list messages automatically,
another might need review for the same operation, and another might not see it at
all. The useful unit is not "the Graph API." It is "this caller may perform this
named operation under this policy."

<figure>
  <img src="{{ '/assets/writeup/toolstack-capability-menu.svg' | relative_url }}" alt="Diagram showing custom APIs, MCP servers, REST APIs, and OpenAPI specs becoming named Toolstack operations with allow, review, or deny policy decisions.">
  <figcaption>The protocol can vary. The policy surface should still be a finite menu of named operations.</figcaption>
</figure>

That is what makes the risk discussable. I can look across a caller's whole
capability set and ask normal security questions. What can this agent touch?
What can those tools touch? What happens when two boring capabilities compose
into something sharp? Where can data leave? Which actions should be fast, which
should be reviewed, and which should not be reachable at all?

You cannot threat-model "whatever the agent can reach." You can threat-model a
list of named operations.

## Capability onboarding without capability soup

This is where the project changed the most after the original draft.

I do not want a boundary that only works when every integration is hand-built in
one blessed style. That would make the secure path too slow, and slow secure
paths have a way of becoming bypassed secure paths.

Toolstack supports a few different ways to bring capability behind the broker:

- Custom API tools for workflows where the tool should be a small purpose-built
  service.
- Existing MCP servers, when there is already a useful server and I want the same
  broker policy, approval, and audit lifecycle around it.
- REST tools for HTTP APIs, including a generic proxy that injects credentials
  inside the workload and pins requests to the declared upstream.
- OpenAPI import for documented APIs, so a spec can become the first cut of a
  `toolyard.toml` full of named operations.
- The agent-side `toolstack` client, skill, and MCP adapter, so agents can
  discover and call only the operations their caller policy exposes.

The important part is not the wire format. It is that every path collapses into
the same request lifecycle: caller, tool, operation, arguments, policy decision,
approval if needed, execution, audit.

OpenAPI is a good example because it is tempting to hand the agent a general
client and call it done. The safer move is less glamorous: generate a first-cut
operation menu, delete what should not exist, route sharp actions through review,
and let the broker judge each request by name. The importer is not a substitute
for threat modeling. It is a way to make the thing you need to threat-model
visible.

That is the ergonomics lesson. If adding capability to the boundary is painful,
people will route around the boundary. If adding capability is cheap and still
lands in a finite policy surface, the secure path has a fighting chance of being
the normal path.

## The approval has to mean something

For a while my approval surface was a messaging app, because that is the fastest
thing to wire up. An agent wants to do something sharp, a bot posts a card, I tap
a button. It works for a demo.

I do not recommend it for anything you care about, especially on an account tied
to your workplace. Accounts get compromised. People drown in notifications and
start clearing prompts on reflex. A chat thread is a weak substitute for a
durable approval, policy, and audit surface.

So the approval surface in my setup is nod: a self-hosted approval layer for
personal agents, automations, and services. The human decision lives in one place
I control, on my phone, instead of being scattered across chat apps.

<figure>
  <img src="{{ '/assets/writeup/toolstack-approval-card.svg' | relative_url }}" alt="A mock approval card showing caller, tool, operation, risk, reason, and approve or reject options.">
  <figcaption>Approve the operation, not the process that happened to carry it.</figcaption>
</figure>

The surface is still not the authority. The broker owns approval truth. nod
collects a human answer and reports it back; the broker validates that answer
against its own request state and timeout.

That led to a few rules I now care about a lot:

- The card describes the operation, not the command.
- Raw arguments, secrets, and tokens are stripped before the approval leaves the
  broker.
- Resolution is poll-only. There is no inbound callback route into the broker.
- The broker's timer wins. Late approvals fail closed.
- Surface identity is audit metadata, not authority by itself.

The poll-only part sounds boring until you think about the alternative. A push
callback that says "approved" is convenient, but if the receiver can be reached
and the callback is not strongly authenticated, you built a forgery path into
your approval gate. I would rather poll a durable surface and let the broker make
the final call.

## Friction belongs where risk lives

The obvious objection is that this is slower.

Yes. It is. Sometimes.

That is the point. Most useful work is not equally risky. Reading one approved
thread is not exporting a mailbox. Creating a draft is not sending externally.
Checking deployment health is not mutating production. Opening a purchase
request is not checking out.

Low-risk reads, metadata lookups, draft creation, status checks, and safe
diagnostics can stay fast. The broker allows them by policy. The expensive gates
belong on external sends, purchases, deletes, credential changes, production
mutations, durable access creation, and anything else where I want a human to see
the target and reason first.

The point is not to make the agent ask permission for every breath. The point is
to move the permission decision to a place that can see the real operation.

## What building it changed

I thought I was building a broker. The broker turned out to be the least
interesting part.

The interesting part was everything that had to be true around it before I would
let agents near sharp tools:

- The agent could only reach one ingress.
- The operation surface had to be finite and discoverable.
- Caller policy had to be default-deny.
- Secrets had to live with the workload, not the broker or agent.
- Review had to describe the operation.
- Audit had to answer what was asked, what was decided, what ran, and who was
  involved.
- New capabilities had to be easy to onboard without becoming general access.

I spent a lot of time testing intentionally sharp combinations: local execution,
broad tool access, wrappers that hid too little, credentials that made the
wrapper more of a suggestion than a boundary. That testing kept pushing me toward
the same split. Move sensitive tools away from the agent. Give it a narrow
request path back to them. Put policy, approval, secrets, and audit somewhere the
agent cannot rewrite.

MCP helps standardize tool access, but it does not remove the need for an
authority boundary. Local wrappers are ergonomic, but they are not enough around
sensitive systems. Prompt instructions help shape behavior, but they are not
access control.

The useful abstraction turned out to be smaller than I expected: named
operations, caller policy, explicit review gates, workload-owned secrets, and an
audit trail. Nothing magical. Just a place where intent gets judged before real
authority is used.

## The code is personal

I want to be careful about the claim.

The implementation is personal. One operator, one host, a loopback admin panel,
my phone as the approval surface, a tailnet as ingress. That footprint will not
survive contact with a large organization, and I am not pretending it should.

The model is the part worth carrying forward. It is built from primitives
security teams already understand: least privilege, reference monitors, workload
identity, separation of duties, secrets management, audit, revocation, and
network segmentation.

That is why I like it. The interesting part is not that I invented a new control.
I did not. The interesting part is that agentic systems make the boring controls
matter in new places.

When someone asks whether this is ready for a larger environment, the honest
answer is: the stack is not, and the shape is. Swap my homelab pieces for
hardened equivalents and the boundary still has the same job. Agents are callers.
Callers get least privilege. Sharp actions are mediated. Secrets live with the
workload. Every meaningful action resolves to a policy or human decision that can
be audited later.

The capability is not the hard part anymore. The boundary is the work.

## Trust agents with action

Agents are useful because they can plan and act. Those same properties make
ambient authority dangerous.

The design goal should not be "how do I safely give this agent all my keys?" It
should be "how do I let this agent request useful work while keeping authority
somewhere else?"

I want capable agents. I want them using custom tools, MCP servers, external
APIs, local workflows, and whatever else turns out to be useful. I just want
those capabilities to arrive as named operations with policy, approval, secrets,
and audit wrapped around the actual authority.

Without that, you do not have a trustworthy agentic system. You have an agentic
system and a hope.

The implementation is personal. The boundary is the thing worth stealing.

Give agents a workbench, not a keyring.

Trust agents with action. Do not trust them with standing access.

---

*Code: [Toolstack](https://github.com/batteryshark/Toolstack). Approval surface:
[nod](https://github.com/batteryshark/nod). The argument behind all of this is in
[part one]({% post_url 2026-06-19-agentic-governance-for-people-who-dont-trust-agents %}).*
