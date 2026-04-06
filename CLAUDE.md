# Mission Control V2 — Project Memory

## What This Is
Central command dashboard for Apex Integrations, a dental-focused web and SEO agency. Built for two users: Owen (main) and Sam (business partner). Must always be accessible from both machines via Railway deployment.

## Business Context
- Company: Apex Integrations
- Niche: Dental practices
- Services: Website builds (one-time fee) + SEO (monthly recurring)
- Goal: $50K MRR by September 1 2026
- Agent system: IronSpider (Peter, Scout, Edith, Harry, Web Verification Agent)

## Tech Stack
- Frontend: Vanilla JS, HTML, CSS, Chart.js, D3.js
- Backend: Flask, SQLAlchemy
- Database: Postgres ONLY (Railway) — no SQLite, never
- Hosting: Railway (auto-deploys from GitHub)
- Repo: https://github.com/apexintegrations2006/mission-control-v2

## Rules You Must Always Follow
- After every change, run ./deploy.sh automatically — never make Owen push manually
- Always fetch data from the backend API, never localStorage
- Build one section at a time, only show that section in the sidebar until approved
- Keep the IronSpider branding in the sidebar
- Dark navy theme, clean card-based layout
- NEVER use SQLite — DATABASE_URL must always point to Postgres
- NEVER drop tables or delete data during deploys

## Data Safety — CRITICAL
- **Database**: Postgres only. app.py will crash on startup if DATABASE_URL is not set. No SQLite fallback exists.
- **Local .env**: Contains DATABASE_URL pointing to Railway Postgres public endpoint (junction.proxy.rlwy.net:57759)
- **Railway env**: DATABASE_URL set on web service pointing to internal Postgres (postgres.railway.internal:5432)
- **Automatic backups**: APScheduler runs daily at 00:00 UTC, saves to /backups/backup_YYYY-MM-DD.json, keeps last 30 days
- **Manual backup**: POST /api/backup triggers an immediate backup
- **Restore**: Run `python3 restore.py backups/<filename>.json` to restore any backup into Postgres
- **Health check**: GET /api/health returns database status, client count, template count, contract count, last backup time. If client count is 0, status returns WARNING.
- **Startup protection**: On every boot, db.create_all() ensures tables exist, seed_data() logs warnings if tables are empty
- **Backup files**: Stored locally in /backups/, excluded from git via .gitignore

## Sections Build Order
1. Clients ✅ DONE
2. Contracts ✅ DONE
3. Financials
4. War Room
5. CRM
6. Agents
7. Outreach
8. Geography

## Current State
- Clients section: full CRUD, detail view with inline editing, deployment/assets/SEO/billing sections
- Contracts section: 3 editable templates, send contracts from client detail, public signing page, sent contracts table
- 3 seed dental practice clients
- 3 contract templates (Website Only, SEO Only, Website + SEO)
- deploy.sh auto-pushes to GitHub on every change

## Data Models
- Client: business_name, owner_name, phone, email, website_url, plan, mrr, initial_payment, stripe_status, notes, created_at, github_repo, cloudflare_url, live_url, google_business, google_search_console, google_analytics, login_credentials, start_date, contract_length, contract_status, contract_doc_url, total_paid, payment_history
- ContractTemplate: plan_type, content, updated_at
- SentContract: client_id, template_id, filled_content, status, sent_at, signed_at, signer_name, signer_ip, client_meta
