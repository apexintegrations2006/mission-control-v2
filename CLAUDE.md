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
- Database: SQLite locally, Postgres on Railway via DATABASE_URL
- Hosting: Railway (auto-deploys from GitHub)
- Repo: https://github.com/apexintegrations2006/mission-control-v2

## Rules You Must Always Follow
- After every change, run ./deploy.sh automatically — never make Owen push manually
- Always fetch data from the backend API, never localStorage
- Build one section at a time, only show that section in the sidebar until approved
- Keep the IronSpider branding in the sidebar
- Dark navy theme, clean card-based layout

## Sections Build Order
1. Clients ✅ DONE
2. Financials
3. War Room
4. CRM
5. Agents
6. Outreach
7. Geography

## Current State
- Clients section is fully built and live
- Full CRUD, Postgres-ready, 3 seed dental clients added
- deploy.sh is set up for auto git push

## Data Models
- Client: business_name, owner_name, phone, email, website_url, plan, mrr, initial_payment, stripe_status, notes, created_at
