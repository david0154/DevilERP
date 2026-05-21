# 🐉 Devil ERP

<p align="center">
  <img src="assets/logo.png" alt="Devil ERP Logo" width="180"/>
</p>

<p align="center">
  <b>AI-Powered · Offline-First · Indian Business ERP</b><br/>
  Built on <a href="https://github.com/tryton/tryton">Tryton ERP Engine</a> · Developed by Devil One Pvt Ltd & Nexuzy Lab
</p>

---

## 📌 About

**Devil ERP** is a modern, offline-first, AI-powered Enterprise Resource Planning system designed for Indian SMEs — retail stores, wholesalers, manufacturers, warehouses, distributors, and multi-branch offices.

It combines the rock-solid Tryton ERP engine with a modern PySide6 desktop UI, an offline AI layer (Gemma/Phi-3), OCR bill scanning, Google Drive backup, and Firebase authentication — all without requiring a dedicated server.

---

## 👨‍💻 Developers

| Role | Name | Contact |
|------|------|--------|
| Lead Developer | David K. Angel | devilonepvtltd@gmail.com |
| Organization | Devil One Pvt Ltd | devilonepvtltd@gmail.com |
| Lab | Nexuzy Lab | nexuzylab@gmail.com |

---

## 🏗️ Architecture

```
Tryton ERP Engine
    +
Custom PySide6 Desktop UI
    +
Offline AI Layer (Gemma GGUF / Phi-3 Mini)
    +
OCR Bill Scanner Engine
    +
Google Drive Backup
    +
Firebase Authentication
    +
SQLite (Small Business) / PostgreSQL (Large Business)
    =
🐉 Devil ERP
```

---

## 📁 Project Structure

```
DevilERP/
│
├── core/              # Tryton core engine integration
├── accounting/        # Accounting, GST, tax modules
├── inventory/         # Stock, warehouse, batch tracking
├── billing/           # POS, billing, barcode, thermal print
├── ai/                # Offline AI engine (Gemma/Phi-3)
├── ocr/               # AI bill scanner, OCR pipeline
├── backup/            # Google Drive sync & restore
├── auth/              # Firebase login, roles, device verify
├── reports/           # PDF/Excel reports, GST reports
├── ui/                # PySide6 UI screens, themes, widgets
├── assets/            # logo.png, icon.ico, fonts, styles
├── models/            # AI model storage (GGUF files)
├── database/          # SQLite/PostgreSQL schema & migrations
└── installer/         # PyInstaller build scripts
```

---

## 🌟 Key Features

### ✅ Complete ERP Modules (via Tryton)
- 📊 Accounting — GL, Chart of Accounts, Balance Sheet, P&L
- 📦 Inventory — Multi-warehouse, batch/serial, stock valuation
- 🛒 Sales — Quotations, orders, invoicing, price lists
- 🏭 Manufacturing — BOM, production orders, work centers
- 👥 HR — Employees, attendance, payroll, departments
- 🤝 CRM — Leads, opportunities, follow-ups
- 📋 Projects — Tasks, teams, time tracking
- 🏢 Multi-Company & Multi-User with role-based access

### 🆕 New Features
- 🤖 **AI Bill Scanner** — Upload JPG/PNG/PDF, auto-extract vendor/invoice/product data via OCR + Gemma AI → creates ERP entries automatically
- 🧠 **Offline AI Assistant** — CPU-friendly Gemma/Phi-3 GGUF model, answers business queries, predicts sales, detects dead stock
- 📈 **Smart Inventory AI** — Reorder prediction, fast-selling detection, demand forecasting
- ☁️ **Google Drive Backup** — Serverless backup/restore, no dedicated server needed
- 🔐 **Firebase Auth** — Login, device verification, password recovery
- 🧾 **Indian GST System** — CGST, SGST, IGST, GST invoices, GST reports
- 💰 **Billing & POS** — Barcode, thermal printer, UPI/Cash/Card, credit sales
- 🌍 **Multi-language** — English, Hindi, Bengali

---

## 🗺️ Development Roadmap

| Phase | Work |
|-------|------|
| Phase 1 | Tryton integration + project structure |
| Phase 2 | Custom PySide6 UI (Tally-style dark mode) |
| Phase 3 | Billing / POS system |
| Phase 4 | AI OCR bill scanner |
| Phase 5 | Offline AI analytics |
| Phase 6 | Google Drive sync |
| Phase 7 | Installer packaging (PyInstaller → .exe) |
| Phase 8 *(Future)* | Android sync app, WhatsApp invoice, voice billing |
| Phase 9 *(Future)* | Multi-branch live sync, AI fraud detection |

---

## 🚀 Quick Start

```bash
git clone https://github.com/david0154/DevilERP.git
cd DevilERP
pip install -r requirements.txt
python main.py
```

---

## 📜 License

This project is based on [Tryton](https://github.com/tryton/tryton) (GPL-3.0). Devil ERP custom code is © Devil One Pvt Ltd & Nexuzy Lab.

---

<p align="center">
  Made with ❤️ in India 🇮🇳 by <b>David K. Angel</b> | Devil One Pvt Ltd · Nexuzy Lab
</p>
