# AZAM RIZWAN SHAH

> **CV engine note (2026-07-24):** A deeper, fully-researched profile now lives in the project's
> `profile/` folder — **`profile/master-profile.md`** (identity, four signature differentiators, full
> skills, metrics bank) and **`profile/projects-catalog.md`** (all 20 projects, sourced). Pull from there
> first for richer CVs; this file remains a valid condensed summary.

**DevOps Engineer · Full-Stack Developer · AI Systems Builder**

Portfolio: [azamshah.me](https://azamshah.me) · GitHub: [github.com/AzamShah668](https://github.com/AzamShah668) · GitHub Org: [github.com/verventech](https://github.com/verventech)

---

## About Me

I build things end-to-end. My work sits at the intersection of infrastructure, backend engineering, and applied AI — I have designed CI/CD pipelines that deploy to bare-metal Kubernetes clusters, written production FastAPI services that manage virtual machines through a hypervisor's REST API, and built content-generation systems that create and upload videos on a daily cron with zero manual intervention.

I am finishing my B.Tech in Computer Science and have spent the past two years doing exactly the kind of work I want to do professionally: setting up Jenkins pipelines, writing Ansible playbooks that provision entire server stacks from a single command, containerising multi-service applications with Docker Compose, and deploying ML workloads on GPU-equipped Kubernetes nodes.

I learn by building. Every project listed below is something I have written, deployed, and maintained.

---

## Technical Skills

**Languages & Scripting:** Python · JavaScript / TypeScript · Bash · PowerShell

**Backend Development:** FastAPI · Pydantic · JWT auth (bcrypt, passlib) · Celery + Redis (async task queues) · psycopg2 (raw SQL, connection pooling) · SQLAlchemy · SQLite / PostgreSQL 16 · REST API design

**Frontend Development:** React 19 · TypeScript · Vite · Tailwind CSS · HTML5/CSS3

**DevOps & Infrastructure:**
- **Containers:** Docker, Docker Compose (multi-service stacks with health checks, named volumes, internal networks)
- **CI/CD:** Jenkins (declarative pipelines, Docker builds, SSH deploy), GitHub Actions
- **Configuration Management:** Ansible (playbooks, roles, Jinja2 templates, group vars, inventory management)
- **Orchestration:** Kubernetes (K3s clusters, GPU scheduling, PVCs, ConfigMaps, Ingress, NVIDIA device plugin)
- **Virtualisation:** Proxmox VE (VM lifecycle, golden image templates, QEMU guest agent, cloud-init)
- **Web Servers & Proxies:** Nginx (reverse proxy, static file serving), Apache Guacamole (HTML5 RDP gateway)
- **Security & Hardening:** Rate limiting (slowapi), CORS policy, Fernet encryption for secrets at rest, Redis auth, production/dev config separation

**AI / ML Engineering:**
- RAG Systems: ChromaDB, LangChain text splitting, ONNX embeddings (all-MiniLM-L6-v2), agentic retrieval
- MLOps: DVC (data versioning), MLflow (experiment tracking), LLM-as-a-Judge evaluation, quality gates in CI
- LLM Integration: OpenRouter, Ollama (local inference on GPU), OpenAI function-calling agents, Claude API
- Voice & Video AI: GPT-SoVITS (voice cloning), LivePortrait / MuseTalk (face animation + lip sync), edge-tts, FFmpeg (video compilation, subtitle burning, audio processing)

**Other:** Git (branching strategies, rebasing, conflict resolution) · Linux server administration · Proxmox networking (bridges, port proxying) · Windows Server / Hyper-V · MCP protocol

---

## Education

**B.Tech in Computer Science & Engineering**
Central University of Kashmir · 2022 – 2026

Capstone Project: *PrivateCloud — A Self-Hosted VM Management Platform on Proxmox VE*
(6-sprint agile project; full-stack + infrastructure + CI/CD + AI features)

---

## Projects

### PrivateCloud — Self-Hosted VM Management Platform
**Stack:** FastAPI · PostgreSQL 16 · React + TypeScript · Celery + Redis · Docker Compose · Proxmox VE · Apache Guacamole · Ansible · Jenkins

A production-grade web platform that lets users provision, manage, and access virtual machines through a browser. Built as my university capstone across 6 development sprints.

What I built:
- A multi-container application (7 services in Docker Compose: PostgreSQL, Redis, FastAPI backend, Celery worker, Guacamole stack, React frontend) orchestrated behind a single `docker compose up` command
- Asynchronous VM provisioning using Celery — the API accepts creation requests immediately and provisions VMs in background workers, preventing server lockup on long-running operations
- A Proxmox API client that handles token authentication, VM cloning from golden image templates, start/stop/resize operations, and QEMU guest agent IP polling with retry logic
- Cross-device browser access to VM consoles — Linux terminals via ttyd and Windows desktops via Apache Guacamole RDP, with URL rewriting so it works from phones on different subnets
- An admin dashboard with user management, audit logging, system settings, daily quota enforcement, and role-based access control
- A clone-from-template system where teachers publish preconfigured VMs as templates and bulk-distribute them to a whole class in one action, with race-free VMID allocation using Redis distributed locks
- An agentic RAG system embedded in the platform's ChatOps interface — admins upload PDF documentation, the system indexes it into ChromaDB with ONNX embeddings, and the LLM agent retrieves and synthesises answers alongside VM management commands
- Self-healing data recovery: if VM provisioning fails partway through, the GET endpoint automatically detects missing IP/credentials on page load and backfills them from the hypervisor — no manual intervention required
- Production hardening: pinned dependencies, Fernet-encrypted secrets in DB, Redis authentication, rate limiting on auth endpoints, request-ID middleware, separated dev/prod Docker Compose configurations
- 98 passing tests covering auth, crypto, reconciliation, and API routes

Infrastructure automation:
- Wrote 5 Ansible roles (proxmox-host setup, Linux template creation, Windows template creation, admin VM deployment, Jenkins VM deployment) that take a bare Proxmox server to a fully running platform with one command: `ansible-playbook playbooks/site.yml`
- Built a Jenkins CI/CD pipeline that builds Docker images on push, tags and pushes to Docker Hub, then SSH-deploys to the admin VM with a health check

---

### RAG PDF MLOps — Production RAG on Kubernetes with GPU Orchestration
**Stack:** FastAPI · ChromaDB · DVC · MLflow · Ollama (Llama-3) · K3s · Jenkins · NVIDIA GPU Plugin · SentenceTransformers

Evolved a basic "upload PDF → ask questions" application into a fully governed ML pipeline. This project is the reason I understand MLOps, not just DevOps.

What I built:
- A 2-node K3s cluster: Intel NUC as control plane + Ubuntu machine with an RTX 3090 as GPU worker node, with NVIDIA device plugin for GPU scheduling
- Data versioning with DVC — PDFs and the ChromaDB vector store are version-controlled alongside the code, so any ingestion change can be rolled back to a known-good state
- Experiment tracking with MLflow — every ingestion run logs chunk_size, overlap, embedding model, and total chunks; every evaluation run logs per-question judge scores
- LLM-as-a-Judge automated evaluation: a separate Llama-3 instance scores the RAG system's answers against a gold-set of Q&A pairs, producing a quantitative quality metric
- A CI/CD quality gate in Jenkins: if the average judge score falls below the threshold, the build fails and deployment is blocked — bad models cannot reach production
- Kubernetes manifests with GPU resource limits, PVC-backed ChromaDB persistence, Traefik ingress routing, and health probes

---

### YouTube Content Automation Pipeline
**Stack:** Python · FFmpeg · YouTube Data API · Claude API · Notion · Remotion (React + TypeScript video rendering) · edge-tts · Playwright · yt-dlp

A fully automated system that scrapes, compiles, and publishes genre-specific compilation videos to YouTube Shorts with zero manual intervention. Supports 7 genre categories (fails, satisfying moments, rankings, transformations, mind-blowing facts, life-threatening moments, insane skill moments) with content sourced from YouTube, Reddit, TikTok, Instagram, and Facebook.

What I built:
- A 690-line pipeline orchestrator (`run_pipeline.py`) with three operating modes: YouTube scrape mode, manual segment mode (precise timestamp extraction), and Notion-input mode (database-driven content queue)
- **44 purpose-built Python tools** covering the full production chain: multi-platform scraping (YouTube, Reddit, TikTok, Instagram, Facebook via Playwright), Notion database management (6 different Notion tools for genre DBs, input clips, reference videos), LLM-powered treatment decisions, emotion sequencing, and YouTube Analytics integration
- **13 specialised agents** (each as its own module with dedicated orchestration): scraper, analyzer, downloader, segment extractor, sequencer, treatment planner, compiler, Remotion renderer, SEO metadata generator, title narrator, uploader, and orchestrator
- A **Remotion (React + TypeScript) video rendering engine** with 9 custom components: BassBoostVisual, EditingMovesLayer, FrameTemplate, FreezeFrame, InstantReplay, ScreenShake, SpeedRamp, WordCaptions, and ZoomPunchIn — programmatic video effects rendered at the frame level
- **State checkpoint system**: every pipeline phase saves progress to JSON so a crash at minute 29 of a 30-minute run doesn't lose all prior work — safe to re-run, fully idempotent
- Word-by-word ASS caption generation (CapCut-style animated subtitles), audio impact moment detection using librosa, SFX injection at detected impact timestamps, and ranking transition card animations
- Notion as a content database: one table per genre, with clips classified and tracked through the production pipeline with status updates at each stage
- YouTube OAuth upload with automated title/description/tag generation, plus YouTube Analytics API integration for tracking channel performance
- A voiceover system with graceful fallback: tries Qwen TTS server first, falls back to captions if the server is unavailable

---

### Football YouTube Shorts Automation ("The Footy Verdict")
**Stack:** Python · Flask · Remotion (React + TypeScript) · OpenRouter · Gemini Flash · edge-tts · Chatterbox TTS (voice cloning) · FFmpeg · PIL · YouTube Data API · YouTube Analytics OAuth · Football-Data API · SQLite · Playwright

The largest project in my portfolio by code volume — a fully automated, faceless football YouTube Shorts channel built to ride the YouTube × FIFA World Cup 2026 wave. **1,103 code nodes** in the knowledge graph, **64 purpose-built tools**, **14 video format generators**, and **5 Remotion (React) video compositions**. Goal: 1+ Short/day, zero manual intervention, monetizable via YouTube Partner Programme.

What I built:
- **64 Python tools** covering every aspect of content production: LLM scriptwriting, deep competitor research, match data fetching (Football-Data API), player photo management (rembg cutouts, alpha matting, country→ISO mapping), stat verification, TTS voice generation (edge-tts + Chatterbox voice cloning with audition system), music generation and download, video compilation, SEO metadata, YouTube upload, YouTube Analytics tracking, community post generation, poll engine, Excel export, and performance tracking
- **14 video format generators** (`formats/`): stat_bomb, comparison_pro (head-to-head debates), debate_fire, news_pro, on_this_day, player_spotlight, prediction_pro, quiz_challenge, recap_pro (match recaps), script_pro, skill_reel, story_pro (inspirational player stories), rotation engine, and a format evolution system
- **5 Remotion (React + TypeScript) video compositions** — programmatic video rendering at the frame level: ComparisonShort (head-to-head debates with verified stats), NewsShort (breaking football news), RecapShort (71KB component — full match recaps with scoreboard punching per goal, rembg player stickers, minute timer, closing stats board), StoryShort (cinematic rise-from-adversity arcs), and ScriptShort (paste-any-script-to-video). Plus 14 shared scene components for hooks, stats panels, transitions, and closing credits
- **A Flask web control panel** (`app.py`, 722 lines + full web UI) — a local dashboard with Dashboard/Story/Versus/News/Library views that drives every pipeline from a browser. Long-running jobs (rendering, research) execute in background threads with streaming log output and status polling
- **A self-improving growth loop** with 5 organs: Deep Research (competitor analysis), Playbook (strategy-as-data with per-format duration targets), Performance (YouTube Analytics OAuth — connected and verified), Evolve (proposes strategy upgrades behind a never-degrade gate with code-computed evidence), and Transparency (archive/auto-rollback)
- **Verified stat database** (`data/players/*.json`, `data/stories/*.json`, `data/matches/*.json`): every number a video states is real, dated, and sourced. The scriptwriter builds debates from verified data and never invents statistics
- **Match recap engine**: copyright-clean ~60s World Cup recaps using country flags, animated scoreboards, rembg-cutout player stickers with count-up minute timers, and closing full-match stats boards — no match footage
- **Research layer** (`tools/researcher.py`): a cheap free-LLM strategist grounded in real YouTube view-velocity data that outputs schema-validated `data/next_videos.json` briefs. Free-model fallback chain (Qwen → gpt-oss → Gemma) survives 429 rate limits
- **21 knowledge base files** (Brain 2) documenting every decision: World Cup opportunity analysis, content strategy, architecture, deployment plan, debugging journal, reference video analysis, clip engine evolution, and growth strategy iterations
- Studied 13 reference viral Shorts and extracted a common DNA: hook techniques, emoji-loaded titles, speed ramps, zoom effects, slowed+reverb music patterns — then built systems to replicate each pattern programmatically
- **Content compliance by design**: the channel is 100% footage-free (flags, photos, stats, AI voice — no match clips). Documented analysis of why Content ID makes lifted footage non-monetizable, even with heavy editing

---

### Avatar Reels Studio — Local AI Video Generation
**Stack:** FastAPI · GPT-SoVITS (voice cloning) · LivePortrait · MuseTalk (lip sync) · Ollama (Llama-3) · FFmpeg · PyTorch + CUDA 12.1

A locally-hosted pipeline that generates realistic video reels using voice cloning and face animation — runs entirely on a consumer GPU, no cloud APIs needed.

What I built:
- A 4-stage pipeline: Ollama Llama-3 script generation → GPT-SoVITS voice cloning (fine-tuned on 10-30 minutes of personal recordings) → face animation with lip sync (LivePortrait/MuseTalk drives a template video with cloned audio) → post-production with ffmpeg (auto-captions, transitions, background music)
- A **GPU memory manager** (`gpu_manager.py`) that loads/unloads models sequentially to fit within a single RTX 3090's 24GB VRAM — SoVITS ~4GB, MuseTalk/LivePortrait ~3-6GB, Ollama ~6GB (separate process)
- A complete training pipeline: audio slicing, voice model fine-tuning (1-3 hours on RTX 3090), face detection and template processing
- A web UI (FastAPI backend + static HTML frontend) for the full studio workflow: upload voice recordings, upload template videos, start voice training, generate reels, preview and download
- 12 REST API endpoints covering system status, script generation, voice training, template management, and full pipeline execution

---

### HeroVault — Full-Stack Hero Management App
**Stack:** FastAPI · SQLModel · PostgreSQL 15 · React · Framer Motion · Nginx · Docker Compose · JWT Auth

A full-stack web application for managing heroes and users, deployed as a 3-container Docker Compose stack.

What I built:
- FastAPI backend with SQLModel ORM, JWT authentication (bcrypt password hashing, 30-minute token expiry), user CRUD, and hero CRUD with protected routes
- React frontend with React Router, Axios HTTP client, Framer Motion animations, and Lucide React icons, served via Nginx in production
- Docker Compose with 3 services: PostgreSQL 15 database, FastAPI backend (depends on db), React frontend served by Nginx (depends on backend)
- Automatic database table creation on startup via SQLModel

---

### 3-Tier Voter Application
**Stack:** Docker · Docker Compose · Ansible · Kubernetes

A full-stack voting application deployed across three tiers (frontend, backend, database), used for DevOps training exercises.

What I built:
- Complete containerisation with Docker and orchestration with Docker Compose
- Ansible playbooks for automated deployment including setup, teardown, and GitHub deploy key management
- Kubernetes manifests (namespace, storage, database, backend, frontend) for cluster deployment

---

### Personal AI Assistant — Multi-Agent WhatsApp Bot
**Stack:** FastAPI · OpenRouter (Llama 3.3 70B) · NVIDIA free API · Twilio · Gmail/Calendar/Sheets/Drive APIs · GitHub API · Obsidian integration

A zero-cost AI assistant that acts as a DevOps mentor, delivered via WhatsApp.

What I built:
- Multi-agent orchestration: intent classifier routes messages to specialised agents (main mentor, researcher, planner, email specialist, assessor)
- Self-updating knowledge base: after every 5+ messages, an assessor agent extracts insights and updates user profile, skill assessment, and learning gaps
- DevOps skill tracking with a 16-topic roadmap, dependency graph, and progress visualisation
- Accountability system with GitHub commit monitoring and streak tracking
- Full Google Workspace integration (Gmail, Calendar, Sheets, Drive) at zero cost

---

### Products Management System
**Stack:** FastAPI · React + TypeScript · Vite · Tailwind CSS · SQLModel · SQLite · Docker Compose · JWT Auth · Nginx

A full-stack CRUD application with user authentication, deployed via Docker Compose with a production deployment guide covering Railway, Render, Vercel, and Heroku.

What I built:
- FastAPI backend with JWT authentication (bcrypt, configurable token expiry), product CRUD, Pydantic schemas, and auto-generated API documentation
- React + TypeScript frontend with Vite build system, Tailwind CSS styling, protected routes, authentication state management, ESLint + Prettier configuration
- Docker Compose with separate backend (Dockerfile) and frontend (Dockerfile + Nginx) containers, Vercel deployment config
- Comprehensive production deployment guide with security checklist, monitoring recommendations, and troubleshooting

---

### QwenTTS Voice Automation
**Stack:** Python · PyTorch + CUDA · Qwen3-TTS-12Hz-1.7B · HuggingFace · SoundFile · PowerShell

A GPU-accelerated text-to-speech system with voice cloning capabilities, wrapped in a complete service lifecycle (start/stop/status/open) for Windows.

What I built:
- A Python TTS engine (`qwen_tts_engine.py`) with two modes: **clone** (voice cloning from a reference audio using the Base model + x-vector embeddings) and **ai** (preset speaker generation using the CustomVoice model). Supports speaker selection, style instructions, and language detection
- Intelligent **HuggingFace checkpoint management**: auto-discovers local model snapshots (CustomVoice → Base → remote fallback), verifies `model.safetensors` presence before loading, supports explicit checkpoint overrides
- PowerShell service lifecycle scripts: `Start-QwenTTS-GPU.ps1` (kills conflicting port listeners, sets CUDA env vars, configures SoX path, starts server with readiness polling for up to 60 seconds), `Stop-QwenTTS.ps1`, `QwenTTS-Status.ps1` (checks port/process/GPU memory), and `.cmd` wrappers for double-click launch
- GPU configuration: `float16` precision on `cuda:0`, 8-thread concurrency, no flash attention (compatibility), SoX audio processing integration

---

### PDF Compressor
**Stack:** Flask · PyMuPDF · Docker

A web tool for compressing PDF documents, containerised with Docker and also deployed to Kubernetes as a hands-on DevOps exercise.

---

### Image Upscaler (VervenAI Upscale Factory)
**Stack:** Python · Real-ESRGAN · NVIDIA RTX 3090 · CUDA

A GPU-accelerated image enhancement tool using Real-ESRGAN for high-resolution upscaling on consumer hardware.

---

### Verventech Website
**Stack:** Web technologies

Company website designed and deployed for the Verventech organisation.

---

## DevOps & Infrastructure Competencies

This is not a list of tools I have read about — these are things I have configured, debugged, and shipped:

- **Jenkins Pipelines:** Wrote multiple declarative Jenkinsfiles: PrivateCloud (parallel backend/frontend Docker builds, Docker Hub push, SSH deploy with health checks) and MY_Own_RAG_Model (6-stage pipeline: checkout → build & push → staging deploy → automated smoke tests → manual approval gate → production deploy to separate VMs). Debugged credential binding, workspace isolation, and agent configuration.
- **Ansible Automation:** Built 5 production Ansible roles for PrivateCloud (proxmox-host, linux-template, windows-template, admin-vm, jenkins-vm). Also wrote K8s cluster provisioning playbooks (kubeadm reset, kernel module loading, containerd setup, CNI installation, master init, worker join), 3-tier voter deployment playbooks (setup + teardown), and monitoring playbooks (Prometheus, Blackbox exporter, app agents). Total: 15+ playbooks across multiple projects.
- **Docker & Compose:** Regularly work with multi-service Compose files (7+ services in PrivateCloud; 2-3 in RAG, Products, HeroVault). Understand multi-stage builds, health checks, named volumes, bridge networks, build contexts, and dev/prod configuration separation. Built Dockerfiles for FastAPI, Next.js, and React+Nginx frontends.
- **Kubernetes:** Deployed workloads on K3s with GPU scheduling (NVIDIA device plugin), PersistentVolumeClaims, ConfigMaps, Secrets, Services (ClusterIP, NodePort), and Traefik Ingress. Wrote 15 K8s manifest files for the RAG project alone (namespace, PVs, PVCs, ConfigMap, Secret, Redis, Celery, backend deployment with resource limits, frontend deployment, services). Also completed hands-on labs: hello world pods, namespaces, storage demos, resource quotas, and full application deployments.
- **CI/CD Design:** Built pipelines with quality gates (LLM-as-a-Judge evaluation that blocks deployment if answer quality drops), automated smoke testing in Docker containers, staging→production promotion with manual approval gates, and environment variable templating across environments.
- **Monitoring:** Wrote Ansible playbooks for Prometheus + Blackbox exporter setup, including application agent monitoring configuration.

---

## AI & Automation Competencies

- Built and maintained a three-brain knowledge management system (Obsidian global vault + per-project knowledge base + auto-generated code graphs) for managing context across multiple AI coding assistants. Projects with Brain 2: PrivateCloud (15 knowledge files), football automation (21 knowledge files), YouTube automation
- Designed resilient automation pipelines with state-machine checkpoint systems, multi-account resource pooling, and structured JSON-L observability dashboards
- Created production RAG systems with ChromaDB, local embeddings (ONNX), and agentic retrieval patterns. Built 6 RAG sub-labs in the DevOps curriculum (chunking, embedding, parent-child retrieval, vector DB, PDF RAG, PDF RAG with Groq)
- Operated local LLM inference on GPU hardware (Ollama, GPT-SoVITS, MuseTalk, Qwen3-TTS, Real-ESRGAN) with VRAM management and service lifecycle automation
- Built multi-agent orchestration systems with intent classification, skill-based routing, and self-updating knowledge stores
- **Open-source contribution**: Active contributor to [Everything Claude Code](https://github.com/affaan-m/everything-claude-code) (140K+ stars, 170+ contributors, Anthropic Hackathon winner) — the performance optimisation system for AI agent harnesses, shipping 47 agents, 181 skills, and 79 commands across 12 language ecosystems. Works across Claude Code, Codex, Cursor, OpenCode, and Gemini

---

## DevOps Curriculum & Continuous Learning

- **Structured DevOps Training (Devops-batch1)**: Completed a comprehensive hands-on curriculum covering Docker (9 containerised projects including AI apps, weather apps, PDF compressor, student enrollment, voter app), Docker Compose (multi-service orchestration), Ansible (Apache setup, website deployment, 3-tier voter app, Prometheus monitoring), Kubernetes (pods, namespaces, services, storage, deployments, ConfigMaps, Secrets), and FastAPI backend development
- **MLOps & ML Engineering**: DVC data versioning, MLflow experiment tracking, LLM-as-a-Judge automated evaluation, RAG pipeline engineering (6 lab modules: chunking, embeddings, parent-child retrieval, vector DB, PDF RAG, Groq-accelerated RAG), KS-test embedding drift detection
- **Self-directed specialisation**: Infrastructure-as-Code with Terraform (in progress), GPU-accelerated inference, voice cloning, video generation pipelines

---

## What I Am Looking For

Roles in DevOps Engineering, Platform Engineering, Backend Development, or MLOps where I can apply my hands-on experience with CI/CD, containerisation, infrastructure automation, and AI systems. Open to remote, hybrid, or on-site work.

---

*References available on request.*
