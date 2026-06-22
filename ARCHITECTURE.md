# Architecture — Plain English Guide (AWS Bedrock Edition)

This document explains how the system works, piece by piece, using simple diagrams.
No technical background needed.

---

## The Big Picture

Think of this system like a **smart helpdesk with specialists**, running on Amazon Web Services.
You ask a question or make a request. A manager (the Supervisor) reads it, figures out
who is best placed to handle it, and routes it to the right expert.
The expert does the work and the answer comes back to you.

The AI brains come from **Amazon Bedrock** — AWS's managed AI service that runs
Anthropic's Claude models without you needing to manage any servers.

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                        YOUR APPLICATION                             │
 │                  (web app, chatbot, internal tool)                  │
 └───────────────────────────────┬─────────────────────────────────────┘
                                 │
                        You type a request
                    e.g. "What is the VPN policy?"
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │                     main.py  —  Entry Point                         │
 │                                                                     │
 │  • Checks you are authenticated to AWS (IAM credentials)            │
 │  • Starts up logging and tracing so nothing is invisible            │
 │  • Passes your request into the agent system                        │
 └───────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
```

---

## Layer 1 — The Supervisor (The Manager)

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                      SUPERVISOR AGENT                               │
 │                    agents/supervisor.py                             │
 │                                                                     │
 │  Powered by: Claude on Amazon Bedrock (via LiteLLM)                 │
 │  "I read every request and decide who should handle it."            │
 │                                                                     │
 │  ┌─────────────────────────────────────────────────────────────┐    │
 │  │  Routing Rules (plain English)                              │    │
 │  │                                                             │    │
 │  │  Is the user asking a QUESTION?                             │    │
 │  │    -> Send to RAG Agent  (the librarian)                    │    │
 │  │                                                             │    │
 │  │  Does the user want to DO something (create a ticket)?      │    │
 │  │    -> First check with Policy Agent  (the safety officer)   │    │
 │  │    -> If approved, send to Action Agent  (the executor)     │    │
 │  │                                                             │    │
 │  │  Is the user asking "am I allowed to do X?"                 │    │
 │  │    -> Send to Policy Agent  (the safety officer)            │    │
 │  └─────────────────────────────────────────────────────────────┘    │
 └──────┬───────────────────┬───────────────────┬───────────────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
   RAG Agent          Policy Agent         Action Agent
  (Librarian)        (Safety Officer)       (Executor)
```

---

## What is LiteLLM?

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                          LiteLLM                                    │
 │                                                                     │
 │  A translation layer that lets Google ADK (the agent framework)     │
 │  talk to Amazon Bedrock models.                                     │
 │                                                                     │
 │  Google ADK speaks its own language.                                │
 │  Amazon Bedrock speaks a different language.                        │
 │  LiteLLM translates between them so they work together.             │
 │                                                                     │
 │  You configure it with a simple prefix in your model name:          │
 │    "bedrock/anthropic.claude-sonnet-4-5"                            │
 │           ^                                                         │
 │           LiteLLM sees this prefix and routes to Bedrock            │
 └─────────────────────────────────────────────────────────────────────┘
```

---

## Layer 2 — The Specialist Agents

### RAG Agent — "The Librarian"

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                        RAG AGENT                                    │
 │                     agents/rag_agent.py                             │
 │                                                                     │
 │  Powered by: Claude on Amazon Bedrock (via LiteLLM)                 │
 │  "I look things up in your company's knowledge base and give        │
 │   answers backed by real documents — I never make things up."       │
 │                                                                     │
 │  Example requests it handles:                                       │
 │    • "What is the remote access policy?"                            │
 │    • "Show me the incident response runbook."                       │
 │    • "What does our SLA say about P1 incidents?"                    │
 │                                                                     │
 │  How it works:                                                      │
 │    1. Receives the question                                         │
 │    2. Runs it through Bedrock Guardrails first (safety check)       │
 │    3. Calls search_enterprise_knowledge tool  ────────────────┐     │
 │    4. Gets back matching documents from Bedrock Knowledge Base │     │
 │    5. Builds an answer using only those documents              │     │
 │    6. Cites the source so you know where it came from          │     │
 └────────────────────────────────────────────────────────────┬──┘     │
                                                              │        │
                    ┌─────────────────────────────────────────┘        │
                    ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │              BEDROCK KNOWLEDGE BASES  —  retrieval/retrieval.py     │
 │                                                                     │
 │  "I am the AWS-managed document library. Your company's knowledge   │
 │   is stored here. I handle all the hard work of search."            │
 │                                                                     │
 │  What it does automatically:                                        │
 │    • Ingests your documents (PDFs, Word, HTML, CSV)                 │
 │    • Splits them into chunks                                        │
 │    • Converts chunks to vector embeddings (numbers AI understands)  │
 │    • Indexes them for fast search                                   │
 │    • Returns the most relevant chunks for any query                 │
 │                                                                     │
 │  Supported data sources (where your documents live):                │
 │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
 │  │ Amazon S3 │  │SharePoint │  │Confluence │  │ OneDrive  │       │
 │  │ (files,   │  │(intranet) │  │  (wiki)   │  │(Microsoft)│       │
 │  │  PDFs)    │  │           │  │           │  │           │       │
 │  └───────────┘  └───────────┘  └───────────┘  └───────────┘       │
 └─────────────────────────────────────────────────────────────────────┘
```

---

### Policy Agent — "The Safety Officer"

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                       POLICY AGENT                                  │
 │                    agents/policy_agent.py                           │
 │                                                                     │
 │  Powered by: Claude Opus on Amazon Bedrock (stronger model)         │
 │  "Before anything is done, I check whether it is allowed.           │
 │   I also apply AWS Bedrock Guardrails to block harmful requests."   │
 │                                                                     │
 │  Two layers of protection:                                          │
 │                                                                     │
 │  Layer 1 — Bedrock Guardrails (automated, real-time):               │
 │    • Blocks requests about denied topics                            │
 │    • Detects and masks PII (names, emails, credit cards)            │
 │    • Filters harmful or toxic content                               │
 │    • Prevents prompt injection attacks                              │
 │                                                                     │
 │  Layer 2 — IAM / Policy engine check (your business rules):         │
 │    • "Can a developer delete production data?"   -> DENIED          │
 │    • "Can support create a ticket?"              -> PERMITTED        │
 │    • "Can a manager approve a large refund?"     -> NEEDS REVIEW    │
 │                                                                     │
 │  Always gives one of three verdicts:                                │
 │   [OK]    PERMITTED         -- safe to proceed                      │
 │   [NO]    DENIED            -- not allowed, stops here              │
 │   [WAIT]  REQUIRES_APPROVAL -- a human must sign off first          │
 └─────────────────────────────────────────────────────────────────────┘
```

---

### Action Agent — "The Executor"

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                       ACTION AGENT                                  │
 │                    agents/action_agent.py                           │
 │                                                                     │
 │  Powered by: Claude on Amazon Bedrock (via LiteLLM)                 │
 │  "Once the Policy Agent says it's OK, I do the actual work —        │
 │   talking to real enterprise systems on your behalf."               │
 │                                                                     │
 │  Example requests it handles:                                       │
 │    • "Create a P2 ticket: VPN is broken for payments team."         │
 │    • "What is the status of ticket INC0012345?"                     │
 │                                                                     │
 │  How it works:                                                      │
 │    1. Receives the pre-approved action                              │
 │    2. Calls the right tool:                                         │
 │         create_ticket     -> creates a ticket in ServiceNow/Jira    │
 │         get_ticket_status -> looks up a ticket by ID                │
 │    3. Reports back: ticket ID, current state, next steps            │
 │    4. If something goes wrong, returns a structured error           │
 └─────────────────────────────────────────────────────────────────────┘
```

---

## Layer 3 — Tools (The Actual Connectors to Real Systems)

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                  TOOLS  --  tools/enterprise_tools.py               │
 │                                                                     │
 │  Tools are the hands of the agents. An agent thinks and decides;   │
 │  a tool reaches out and touches a real system.                      │
 │                                                                     │
 │  Every tool runs a Guardrail check on user input before acting.     │
 │                                                                     │
 │  ┌───────────────────────────┐   ┌───────────────────────────────┐  │
 │  │ search_enterprise_        │   │ get_ticket_status             │  │
 │  │ knowledge                 │   │                               │  │
 │  │                           │   │ Input:  ticket ID             │  │
 │  │ 1. Guardrail check        │   │ Output: ticket state,         │  │
 │  │ 2. Query Bedrock KB       │   │         priority, assignee    │  │
 │  │ 3. Return documents       │   │                               │  │
 │  └───────────────────────────┘   └───────────────────────────────┘  │
 │                                                                     │
 │  ┌───────────────────────────┐   ┌───────────────────────────────┐  │
 │  │ create_ticket             │   │ check_policy                  │  │
 │  │                           │   │                               │  │
 │  │ 1. Guardrail check        │   │ Input:  action, user role,    │  │
 │  │ 2. Create in ticketing    │   │         resource              │  │
 │  │    system                 │   │ Output: allowed? + reason     │  │
 │  │ 3. Return new ticket ID   │   │                               │  │
 │  └───────────────────────────┘   └───────────────────────────────┘  │
 │                                                                     │
 │  All tools follow the same return convention:                       │
 │    • Works     -> { "status": "success", ... }                     │
 │    • Fails     -> { "status": "error", "message": "..." }          │
 │    • Blocked   -> { "status": "blocked", "reason": "..." }         │
 └─────────────────────────────────────────────────────────────────────┘
```

---

## Layer 4 — Supporting Infrastructure

### Configuration — "The Settings File"

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                     CONFIG  --  config.py                           │
 │                                                                     │
 │  Reads all settings from your .env file at startup.                 │
 │  If a setting is wrong or missing, it stops with a clear message.   │
 │                                                                     │
 │  Key settings:                                                      │
 │    AWS_REGION          <- which AWS region to use (must have Bedrock)│
 │    KNOWLEDGE_BASE_ID   <- ID of your Bedrock Knowledge Base          │
 │    GUARDRAIL_ID        <- ID of your Bedrock Guardrail (optional)    │
 │    SUPERVISOR_MODEL    <- which Claude model the manager uses        │
 │    POLICY_MODEL        <- which Claude model the safety officer uses │
 │    LOG_LEVEL           <- how much logging output you want           │
 │                                                                     │
 │  Validates AWS_REGION against known Bedrock-supported regions.      │
 │  Bad region? Fails immediately with a helpful error message.        │
 └─────────────────────────────────────────────────────────────────────┘
```

### Security — "The ID Badge + Guardrails"

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                SECURITY  --  security/aws_security.py               │
 │                                                                     │
 │  Three functions that keep the system safe:                         │
 │                                                                     │
 │  get_identity()                                                     │
 │    Checks AWS credentials at startup via AWS STS.                   │
 │    "Who are you? Prove it." — if no credentials, fails immediately. │
 │    On a laptop: uses your 'aws configure' profile.                  │
 │    In production: uses the IAM role attached to ECS/EKS.            │
 │                                                                     │
 │  get_secret(name)                                                   │
 │    Retrieves sensitive values (passwords, API keys) from            │
 │    AWS Secrets Manager. Never stored in code or .env files.         │
 │    e.g. get_secret("db-password") fetches                           │
 │         "enterprise-agent/db-password" from Secrets Manager.       │
 │                                                                     │
 │  apply_guardrail(text)                                              │
 │    Sends text to Amazon Bedrock Guardrails before processing.       │
 │    Guardrails automatically:                                        │
 │      - Block questions about denied topics                          │
 │      - Detect and redact PII (names, emails, SSNs)                  │
 │      - Filter toxic or harmful content                              │
 │      - Detect prompt injection attempts                             │
 │    If no GUARDRAIL_ID is set, this is a no-op (safe to skip).       │
 └─────────────────────────────────────────────────────────────────────┘
```

### Observability — "The Flight Recorder"

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │              OBSERVABILITY  --  observability/telemetry.py          │
 │                                                                     │
 │  Every request leaves a trail so you can see exactly what happened. │
 │                                                                     │
 │  CloudWatch Logs                                                    │
 │    Like a detailed diary. Every agent action, tool call, and        │
 │    error is logged. Searchable in the AWS Console.                  │
 │                                                                     │
 │  CloudWatch / X-Ray (via ADOT)                                      │
 │    Like a stopwatch for every step. Shows a visual timeline of      │
 │    the entire request: Supervisor -> Policy Agent -> Action Agent.  │
 │    You can see exactly how long each step took and where errors are. │
 │                                                                     │
 │  How traces get to CloudWatch:                                      │
 │    App -> OpenTelemetry -> ADOT Collector -> CloudWatch / X-Ray     │
 │                                                                     │
 │  ADOT = AWS Distro for OpenTelemetry. It runs as a small sidecar   │
 │  container next to your app on ECS/EKS.                             │
 │                                                                     │
 │  Set up once at startup — never duplicated across requests.         │
 └─────────────────────────────────────────────────────────────────────┘
```

---

## Full End-to-End Flow

Here is what happens from the moment you type a request to the moment you get an answer.

```
  YOU
   │
   │  "Create a P2 ticket: VPN is broken for payments team."
   │
   ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  main.py                                                             │
 │  • IAM credentials checked (get_identity)                            │
 │  • Trace span started (flight recorder on)                           │
 │  • Request passed to Supervisor Agent                                │
 └─────────────────────────────────┬────────────────────────────────────┘
                                   │
                                   ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  SUPERVISOR AGENT  (Claude on Bedrock)                               │
 │  "This is an action request — Policy check first."                   │
 └──────────────┬───────────────────────────────────────────────────────┘
                │
                │  "Is creating a ticket allowed for this user?"
                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  POLICY AGENT  (Claude Opus on Bedrock)                              │
 │  1. apply_guardrail("create_ticket...") -> NONE (safe)               │
 │  2. check_policy("create_ticket", "support-agent", "ticketing")      │
 │  Result: PERMITTED                                                   │
 └──────────────┬───────────────────────────────────────────────────────┘
                │
                │  "Approved — go ahead"
                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  ACTION AGENT  (Claude on Bedrock)                                   │
 │  1. apply_guardrail("VPN broken...") -> NONE (safe)                  │
 │  2. create_ticket(summary="VPN broken...", priority="P2")            │
 │  Result: { "status": "success", "ticket_id": "INC0099999" }         │
 └──────────────┬───────────────────────────────────────────────────────┘
                │
                │  "Ticket INC0099999 created."
                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  SUPERVISOR AGENT                                                    │
 │  Synthesizes into a clear, friendly reply                            │
 └──────────────┬───────────────────────────────────────────────────────┘
                │
                ▼
  YOU  <--  "Ticket INC0099999 has been created at P2 priority.
             The payments team VPN issue is now tracked."

  (CloudWatch logs every step. X-Ray shows the full timeline.)
```

---

## GCP vs AWS — What's Different, What's the Same

```
 ┌─────────────────────────────┬──────────────────────┬──────────────────────┐
 │ Component                   │ GCP version          │ AWS version          │
 ├─────────────────────────────┼──────────────────────┼──────────────────────┤
 │ Agent framework             │ Google ADK           │ Google ADK           │
 │ (how agents are built)      │ (same)               │ (same)               │
 ├─────────────────────────────┼──────────────────────┼──────────────────────┤
 │ AI model                    │ Gemini               │ Claude               │
 │                             │ (Google-native)      │ (via LiteLLM)        │
 ├─────────────────────────────┼──────────────────────┼──────────────────────┤
 │ Document search / RAG       │ Agent Search         │ Bedrock              │
 │                             │ RAG Engine           │ Knowledge Bases      │
 │                             │ Vector Search        │                      │
 ├─────────────────────────────┼──────────────────────┼──────────────────────┤
 │ Content safety              │ Policy Agent         │ Bedrock Guardrails   │
 │                             │ + GCP IAM            │ + AWS IAM            │
 ├─────────────────────────────┼──────────────────────┼──────────────────────┤
 │ Secrets                     │ Secret Manager       │ Secrets Manager      │
 ├─────────────────────────────┼──────────────────────┼──────────────────────┤
 │ Traces                      │ Cloud Trace          │ ADOT -> X-Ray        │
 ├─────────────────────────────┼──────────────────────┼──────────────────────┤
 │ Logs                        │ Cloud Logging        │ CloudWatch Logs      │
 ├─────────────────────────────┼──────────────────────┼──────────────────────┤
 │ Production runtime          │ Agent Engine         │ ECS Fargate / EKS    │
 │                             │ Cloud Run            │                      │
 └─────────────────────────────┴──────────────────────┴──────────────────────┘
```

---

## What Lives Where — File Map

```
  multi_agent_aws_sol1/
  │
  ├── main.py              <- START HERE. Validates AWS auth, runs the system.
  ├── agent.py             <- Used by the ADK web/CLI tool for interactive testing.
  ├── config.py            <- All settings. Validates region and fails fast if wrong.
  ├── .env                 <- Your private settings (never committed to git).
  ├── .env.example         <- Template showing every setting you can configure.
  ├── pyproject.toml       <- Declares Python 3.11+ requirement and dependencies.
  │
  ├── agents/
  │   ├── supervisor.py    <- The manager. Routes requests to specialists.
  │   ├── rag_agent.py     <- The librarian. Queries Bedrock Knowledge Bases.
  │   ├── action_agent.py  <- The executor. Creates and looks up tickets.
  │   └── policy_agent.py  <- The safety officer. Runs Guardrails + IAM checks.
  │
  ├── tools/
  │   └── enterprise_tools.py  <- The connectors. Each function calls a real API.
  │                               All inputs checked via Guardrails before use.
  │
  ├── retrieval/
  │   └── retrieval.py     <- boto3 client for Bedrock Knowledge Bases.
  │
  ├── observability/
  │   └── telemetry.py     <- Idempotent OTEL -> ADOT -> CloudWatch / X-Ray setup.
  │
  └── security/
      └── aws_security.py  <- get_identity (startup check), get_secret, apply_guardrail.
```

---

## Glossary — Plain English Definitions

| Term | What it actually means |
|---|---|
| **Amazon Bedrock** | AWS's managed AI service — run powerful AI models without managing servers |
| **Claude** | Anthropic's AI model, available on Amazon Bedrock |
| **LiteLLM** | A translation library that lets Google ADK talk to Bedrock models |
| **Google ADK** | Google Agent Development Kit — the framework that orchestrates the agents |
| **Agent** | A piece of AI that can think, make decisions, and call tools |
| **Bedrock Knowledge Bases** | AWS-managed document search — ingest, index, and retrieve your company's documents |
| **Bedrock Guardrails** | AWS-managed safety filters — blocks harmful content, PII, and denied topics automatically |
| **RAG** | "Retrieval-Augmented Generation" — look it up first, then answer |
| **Tool** | A Python function the agent can call to interact with a real system |
| **IAM Role** | An identity with specific AWS permissions, attached to a service (no passwords needed) |
| **AWS STS** | AWS Security Token Service — the system that verifies your AWS identity |
| **Secrets Manager** | AWS service for storing API keys and passwords securely |
| **ADOT** | AWS Distro for OpenTelemetry — the AWS-optimized tracing collector |
| **X-Ray** | AWS service showing a visual timeline of requests across your system |
| **CloudWatch** | AWS's logging and monitoring service |
| **ECS Fargate** | AWS's serverless container runner — no EC2 instances to manage |
| **EKS** | AWS's managed Kubernetes service |
| **PrivateLink** | AWS network feature that keeps traffic to Bedrock inside the AWS network |

---

## Key Design Decisions — Interview Guide

This section explains the important architectural choices made in this system and the reasoning
behind each one. These are the questions you are most likely to face in a technical interview.

---

### 1. Why use Google ADK on AWS instead of a native AWS agent framework?

**Decision:** Google ADK orchestrates all agents, even though the AI backend is AWS Bedrock.

**Why:**
ADK provides a production-grade agent loop out of the box — session management, tool
calling, streaming responses, sub-agent delegation, and a built-in web UI for testing.
AWS's native agent framework (Bedrock Agents) is tightly coupled to AWS infrastructure
and harder to test locally. ADK is cloud-agnostic at the orchestration level — it talks
to any model via LiteLLM. This means the agent logic is portable: the same code can run
against GCP Gemini or AWS Claude by changing one environment variable.

**Interview angle:** "We separated orchestration (ADK) from inference (Bedrock). This
gives us cloud portability at the agent layer while still using the best managed AI
services on each cloud. It is the same principle as using Kubernetes instead of ECS
for portability."

---

### 2. Why LiteLLM to connect ADK to Bedrock?

**Decision:** LiteLLM translates between ADK's model interface and Bedrock's API.

**Why:**
ADK natively speaks the Google Gemini API. Bedrock speaks the Anthropic/Amazon API.
LiteLLM acts as a universal adapter — it exposes a single interface and routes to
any supported model backend. This means the agent code never changes when switching
models. A developer can test locally against a cheaper model and deploy against Claude
Opus in production by changing one string in .env.

**Interview angle:** "LiteLLM is the adapter pattern applied to AI model APIs. It
decouples the agent logic from the model vendor, which is critical for cost management,
model upgrades, and avoiding vendor lock-in."

---

### 3. Why a Supervisor + specialist agent pattern instead of one big agent?

**Decision:** One SupervisorAgent routes to three specialist agents (RAG, Action, Policy).

**Why:**
A single agent given all responsibilities becomes unreliable — the model tries to do
everything and does nothing well. Separating concerns means:
- Each agent has a narrow, well-defined prompt — easier to test and tune
- Each agent can use a different Claude model (e.g. Claude Opus for Policy, Sonnet for RAG)
- Failures are isolated — a broken Action agent does not affect knowledge retrieval
- New specialists can be added without touching existing agents

**Interview angle:** "This is the same principle as microservices applied to AI agents —
separation of concerns, independent deployability, and fault isolation."

---

### 4. Why is PolicyAgent always checked before ActionAgent?

**Decision:** Every write action must pass through PolicyAgent before ActionAgent executes.

**Why:**
Without a policy gate, the Action agent could create tickets, modify records, or trigger
workflows for any user regardless of their role. The Policy agent acts as an explicit
authorisation layer, mirroring how real enterprise systems work (IAM, RBAC). Bedrock
Guardrails add an automated layer on top — blocking dangerous requests before the model
even reasons about them.

**Interview angle:** "We applied defence in depth at the agent level. Layer 1 is Bedrock
Guardrails (automated, real-time content filtering). Layer 2 is the Policy agent (business
rule enforcement). No action executes without passing both gates."

---

### 5. Why Bedrock Knowledge Bases instead of building a custom RAG pipeline?

**Decision:** Bedrock Knowledge Bases handles ingestion, chunking, embedding, and retrieval.

**Why:**
Building a custom RAG pipeline requires managing: an embedding model, a vector database,
a chunking strategy, an ingestion pipeline, and a retrieval API. Bedrock Knowledge Bases
handles all of this as a managed service. It also integrates natively with S3, SharePoint,
Confluence, and OneDrive — data sources that enterprises already use. Custom RAG should
only be chosen when you need non-standard chunking, custom ranking, or a vector DB that
Bedrock does not support.

**Interview angle:** "Managed RAG eliminates an entire class of operational problems —
embedding drift, index corruption, ingestion failures. We only build custom infrastructure
when a managed service genuinely cannot meet the requirement."

---

### 6. Why use Bedrock Guardrails instead of just relying on the Policy agent?

**Decision:** Guardrails run before the model — the Policy agent runs after.

**Why:**
Bedrock Guardrails operate at the API level, before any model inference happens. They
block harmful inputs before spending a single token on them. The Policy agent operates
at the reasoning level — it understands business context and user roles. Together they
form two independent safety layers. If the Policy agent made a mistake (which LLM-based
systems can), Guardrails still catch harmful content. This is defence in depth.

**Interview angle:** "Guardrails are the input validation layer. The Policy agent is the
business logic layer. You always validate at the boundary before applying business rules —
the same pattern used in web APIs (middleware vs. controller)."

---

### 7. Why is setup_telemetry() called once at module level, not inside run()?

**Decision:** Telemetry is initialised once at startup, not per request.

**Why:**
If called per request, every invocation of run() would register a new TracerProvider
and a new logging handler. After 100 requests, there are 100 handlers writing duplicate
log entries to CloudWatch. In a long-running ECS/EKS service this causes memory growth
and log flooding. Module-level initialisation is idiomatic for any shared resource.

**Interview angle:** "This is the singleton pattern applied to infrastructure setup.
The rule is: initialise once, use everywhere. The same principle applies to boto3 clients
and database connection pools."

---

### 8. Why does credential validation happen at startup, not on the first request?

**Decision:** get_identity() calls AWS STS at module load time before any request is served.

**Why:**
Failing at startup is far better than failing mid-request. If the IAM role is missing
or the credentials are wrong, the service should refuse to start and emit a clear error
rather than serving requests and crashing mid-flow. This pattern also surfaces
misconfigurations in staging before they reach production users.

**Interview angle:** "In production systems, you want the health check to fail at boot,
not at runtime. The STS call costs one API call at startup and saves every user from
hitting a mid-request auth failure."

---

### 9. Why does run() raise RuntimeError instead of returning "No response."?

**Decision:** If no final response event arrives, the function raises an exception.

**Why:**
Returning a silent fallback string like "No response." hides failures. The caller has
no way to distinguish between a real agent response and a failure. Raising an exception
forces the caller to handle it explicitly — log it, retry it, or surface it to the user
with a proper error message. Silent failures are the hardest bugs to diagnose in a
distributed system.

**Interview angle:** "This follows the principle of making errors visible. A string that
looks like a valid response but isn't is a silent failure — the worst kind in any system,
let alone an AI one where the user cannot see what went wrong."

---

### 10. Why are all tools wrapped in try/except with structured return values?

**Decision:** Every tool returns {"status": "success"|"error"|"blocked"} and never raises.

**Why:**
If a tool raises an uncaught exception, the ADK agent loop crashes and the user gets
nothing. By catching all exceptions and returning a structured dict, the agent can
decide what to do — retry, apologise, or escalate. The "blocked" status is unique to
the AWS version: it signals that Bedrock Guardrails intercepted the input, which is
different from an error. This three-state model gives the agent precise information
to reason about.

**Interview angle:** "Tools are the boundary between the AI layer and real AWS services.
Boundaries must be hardened. The agent should always receive a signal it can reason
about — never a raw exception. The three-state return (success/error/blocked) is
more expressive than a boolean and maps cleanly to HTTP 200/500/403."
