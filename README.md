# Morning AI

An enterprise-level intelligent decision-making system with autonomous SaaS capabilities.

## Project Structure

This repository contains a curated, optimized handoff bundle organized as follows:

- `handoff/20250928/` - Main project directory with dated structure
  - `10_Product/` - Product requirements, user stories, roadmap
  - `20_Architecture/` - System diagrams, ERD, blueprints  
  - `30_API/` - OpenAPI/Swagger specifications
  - `40_App/` - Application code and configuration
    - `morningai_enhanced/` - Core application
      - `frontend-dashboard/` - React frontend with Vite
      - `api-backend/` - Flask API backend
  - `50_Infra/` - Infrastructure as Code (Terraform/Helm/K8s/Docker)
  - `60_Design/` - Design tokens, brand assets, Figma notes
  - `80_Scripts/` - Automation scripts
  - `90_Compliance_Legal/` - Privacy, SLA, security, terms
  - `99_Original_Bundle/` - Core system documentation
    - `morningai_enhanced/` - Comprehensive system documentation

## Key Features

- **AI Agent Ecosystem**: 15 specialized AI agents for autonomous operations
- **Meta-Agent Decision Center**: Intelligent decision-making and coordination
- **Multi-tenant SaaS Architecture**: Enterprise-ready scalable platform
- **Modern Tech Stack**: Next.js 14, FastAPI, PostgreSQL, Redis
- **Comprehensive Documentation**: Complete handoff with architecture, deployment guides

## Quick Start

### Frontend Dashboard
```bash
cd handoff/20250928/40_App/morningai_enhanced/frontend-dashboard
pnpm install
pnpm dev
```

### API Backend
```bash
cd handoff/20250928/40_App/morningai_enhanced/api-backend
pip install -r requirements.txt
python app.py
```

## Documentation

The primary system documentation is located in:
- `handoff/20250928/99_Original_Bundle/morningai_enhanced/ULTIMATE_HANDOFF_SUMMARY.md` - Comprehensive system overview
- `handoff/20250928/99_Original_Bundle/morningai_enhanced/morning_ai_knowledge_base.md` - Complete knowledge base

## Optimization Notes

This repository has been optimized to remove redundant files and reduce size:
- Removed duplicate package documentation (was 1.4M)
- Consolidated multiple overlapping summary files into single authoritative version
- Excluded node_modules from git tracking (can be regenerated from package.json)
- Cleaned up redundant package copies and libraries

The working application structure and all essential configuration files have been preserved.
