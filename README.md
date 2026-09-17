# Amirreza Radjou

Backend and distributed-systems engineer, Toronto (ON).

Go, Rust, Java and Python; MSc Computer Science (York University, 2025). I build peer-to-peer databases, blockchain-consensus simulators and LLM-driven services.

[amirradjou.com](https://amirradjou.com) | [LinkedIn](https://www.linkedin.com/in/amirreza-radjou/) | [CV (PDF, June 2026)](https://amirradjou.com/CV.pdf) | amirreza.radjou@gmail.com

## Now (updated 2026-09-17)

- Senior Full Stack Developer at CIBC (Toronto) since March 2026: service mesh on OpenShift (mTLS, traffic policy, observability) and gRPC APIs between microservices.
- Learning focus: Kubernetes (CKAD track) and agentic-AI systems — public lab repos will appear here as they ship.

## Highlights

- **orbitdb/go-orbitdb**: authored 194 of 201 commits through 15 merged PRs (#2-#16, 6 Nov - 5 Dec 2024): identities and keystore, log/entry with CID generation, modular storage and IPFS block storage, core database with tests, orbit-sync, and the Go CI workflow.
- **CNSim (York University, cmg-york)**: extended the open-source Java consensus-network simulator with Bitcoin protocol behaviour (malicious-node attacks, hashpower changes) and a Transaction Finality metric; 33 commits across cnsim, cnsim-bitcoin and cnsim-engine (12 shared pre-split history, 21 new in Dec 2025 - Jan 2026, continued after graduation). MSc thesis: *Simulation-based Evaluation of Transaction Finality in Bitcoin using CNSim*.
- **dtg2sim / RLGen / mx2dtx (cmg-york)**: research tooling for goal-model-driven simulation and RL environment generation; 17 commits in dtg2sim (which absorbed the 4 RLGen commits) and 2 in mx2dtx, top contributor on dtg2sim and RLGen (May 2025).

## Experience

| When | Where | What |
|---|---|---|
| Mar 2026 - present | CIBC, Toronto | Senior Full Stack Developer: service mesh on OpenShift, gRPC inter-service APIs, Enterprise Product Catalog onboarding (incl. Simplii Financial). |
| May 2024 - Mar 2025 | Dandelion Network (remote) | Software Engineer: Go/Python wallet backend (REST, GraphQL, gRPC), led the network-simulator team, Substrate/Ink! (Rust) multisig and vault contracts on Polkadot. |
| Sep 2022 - May 2025 | York University | Research Assistant - Software Engineer: CNSim Bitcoin and Tangle protocols, finality metric, JUnit harnesses, Python post-processing and visualisation GUI. |

## Projects

| Project | What it is | Stack | Role / when |
|---|---|---|---|
| **Distributed systems** | | | |
| [go-orbitdb](https://github.com/orbitdb/go-orbitdb) | Go port of OrbitDB, the peer-to-peer database on IPFS: key-value, event-log and document stores, replication, cryptographic access control | Go, IPFS/libp2p | 194/201 commits, Nov-Dec 2024 |
| [cnsim (thesis fork)](https://github.com/amirradjou/cnsim) — tag `thesis-v1.0-artifact` | MSc thesis experiments on CNSim: thesis configs, finality-score calculator, belief-analysis scripts, processing-delay model | Java 21, Python (pandas, scipy), R | 15 commits, Feb-Jun 2025 |
| [cnsim-bitcoin](https://github.com/cmg-york/cnsim-bitcoin) / [cnsim-engine](https://github.com/cmg-york/cnsim-engine) | Bitcoin module and discrete-event engine of CNSim: malicious-node attack model, configurable hashpower and attack parameters, behaviour/hashpower-change events, tests | Java, JUnit | 16 + 5 new commits, Dec 2025 - Jan 2026 |
| **AI / agents** | | | |
| [dnd-game-master](https://github.com/amirradjou/dnd-game-master) | LLM game master for tabletop sessions over FastAPI WebSocket rooms | Python, FastAPI, LangChain | Author, Nov 2024 hobby build |
| [java-grading-assistant](https://github.com/amirradjou/java-grading-assistant) | Stdlib-only CLI that compiles each student's Java submission against a JUnit test file, runs every test with a timeout and writes CSV grades | Python | Author, Jan-Mar 2025 |
| [dtg2sim](https://github.com/cmg-york/dtg2sim) | Model-driven generation of RL training simulators from goal models (RLGen): unified CLI with config.json entry point, gymnasium terminated/truncated API, updated dependencies; also open as [cmg-york/RLGen PR #3](https://github.com/cmg-york/RLGen/pull/3) | Python, Prolog | Top contributor (17 of 19 commits), May 2025 |
| **Web and hobby** | | | |
| [amirradjou.com](https://amirradjou.com) | Professional site ([source](https://github.com/amirradjou/amirradjou-site)) — one page, generated from a single `profile.yaml` | Astro, TypeScript, Netlify | Author, Sep 2026 |
| [terminal.amirradjou.com](https://terminal.amirradjou.com) | Terminal-style portfolio PWA ([source](https://github.com/amirradjou/terminal-portfolio), built on satnaing/terminal-portfolio) | React, TypeScript, Vite, Netlify | 12 own commits, Mar 2024 - Sep 2026 |
| [task-manager](https://github.com/amirradjou/task-manager) | Task manager with token-auth REST API, filtering, Bootstrap UI and a 41-test suite | Django 5.2, DRF, SQLite | Author, Sep 2025 |
| CO2 emissions in Bitcoin mining | Interactive, time-ranged geospatial heatmap of mining CO2 with a daily multi-source ETL pipeline and REST API | React/TypeScript, Django/Flask, PostgreSQL | Full-stack developer (team project), Sep 2023 - Apr 2024 |
| [FoF](https://github.com/amirradjou/FoF) | "Friends of Friends" contacts app: sign-in/sign-up, contacts via REST API, per-contact weather | Dart, Flutter | Author, Dec 2020 - Jan 2021 |

## Skills

| Area | Tools |
|---|---|
| Languages | Go, Python, TypeScript, JavaScript, Java, Rust, SQL |
| Backend and APIs | gRPC, REST, GraphQL, Django, Flask |
| Distributed systems | Microservices, service mesh, peer-to-peer (IPFS/libp2p), consensus and blockchain protocols (Substrate/Polkadot), discrete-event simulation |
| DevOps and platforms | Docker, Docker Compose, Kubernetes, OpenShift, Jenkins, GitHub Actions, Netlify |
| Data | PostgreSQL, SQLite, ETL/ELT pipelines |
| Testing and security | JUnit, pytest, Cypress; API security and mTLS, threat modelling, cryptography |
| AI | LLM agent pipelines (Gemini, OpenAI/LangChain) |

## Education

- **MSc Computer Science**, York University, Toronto, Sep 2022 - Oct 2025. Thesis: *Simulation-based Evaluation of Transaction Finality in Bitcoin using CNSim*.
- **BSc Computer Science**, Amirkabir University of Technology, Tehran, Oct 2018 - Aug 2022.

---

Open source: [orbitdb/go-orbitdb](https://github.com/orbitdb/go-orbitdb) · [cmg-york/cnsim-bitcoin](https://github.com/cmg-york/cnsim-bitcoin) · [cmg-york/cnsim-engine](https://github.com/cmg-york/cnsim-engine) · [cmg-york/dtg2sim](https://github.com/cmg-york/dtg2sim) · [cmg-york/RLGen](https://github.com/cmg-york/RLGen) · [cmg-york/mx2dtx](https://github.com/cmg-york/mx2dtx). Last updated 2026-09-17.
