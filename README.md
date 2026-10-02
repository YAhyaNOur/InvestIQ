# SmartStart — Intelligent Investment & Startup Analysis Platform

> **BI & AI academic project** developed as a team project during the second semester of the fourth year of the **Data Science & Artificial Intelligence Engineering Program** at Tek-up university


**Academic Year:** 2025–2026

---

## Overview

**SmartStart** is an intelligent decision-support platform designed to connect **startup founders** with **investors**.

The platform combines **machine learning, natural language processing, time-series forecasting, hybrid recommendation systems, generative AI, and workflow automation** to support investment-related decision-making.

SmartStart helps investors identify potentially relevant companies, assess business and financial risks, analyze financial and cryptocurrency trends, and receive personalized recommendations. For founders, the platform provides project analysis and an AI-powered assistant.

This repository contains the **Angular frontend** of the SmartStart platform. It communicates with a **FastAPI backend** and dedicated **machine learning services** through the `Service_ml` module.

---

## Key Features

### Authentication & User Management

* User registration and authentication
* Role-based access for **Founders** and **Investors**
* Support for multiple roles associated with the same email address

### Founder Features

* Startup onboarding
* AI-powered project analysis
* Overall project scoring and sector classification
* Project strengths, risks, and recommendations
* AI assistant powered by an n8n workflow

### Investor Features

* Personalized investor onboarding
* AI-driven company recommendations
* Company growth probability and financial risk analysis
* Hybrid investment scoring
* Cryptocurrency market analysis
* Price forecasting for **7, 14, and 30-day horizons**
* Buy/sell market signals
* Recommended investment budget
* Anomaly detection
* Analysis history
* **Like / Interest** functionality triggering an automated report to the startup founder

---

# AI & Machine Learning Architecture

## Growth & Financial Risk Prediction

SmartStart uses two **CatBoost classification models**:

* A growth model estimating the probability that a company will experience positive growth
* A financial risk model estimating the probability of high financial risk

These predictions contribute to the company's overall investment assessment.





https://github.com/user-attachments/assets/208c7c9f-505b-42c1-bb48-10931c9df697






## Hybrid Recommendation System

The investor recommendation engine combines multiple signals to generate personalized company recommendations.

The final score is computed using four weighted components:

**Final Score = 0.45 × S<sub>ML</sub> + 0.25 × S<sub>Business</sub> + 0.20 × S<sub>User-Item</sub> + 0.10 × S<sub>User-User</sub>**

Where:

* **S<sub>ML</sub>** — machine-learning-based company assessment
* **S<sub>Business</sub>** — business and financial compatibility
* **S<sub>User-Item</sub>** — investor-to-company preference matching
* **S<sub>User-User</sub>** — similarity with other investors

The resulting score is used to generate investment recommendations and decision categories.

<img width="1885" height="917" alt="image" src="https://github.com/user-attachments/assets/26f8eea1-2a78-4dad-85f7-f756133683e5" />


---

## Time-Series Forecasting — Crypto & Financial Analysis

SmartStart combines several forecasting approaches to analyze financial and cryptocurrency time series:

* **ARIMA** for trend and autoregressive patterns
* **ETS / Holt-Winters** for trend and seasonality
* **Prophet** for forecasting with confidence intervals

The models are combined through a voting mechanism to produce:

* Market direction signals
* Price forecasts
* 7-, 14-, and 30-day predictions
* Recommended investment budget
* Forecast intervals, including 80% and 95% confidence levels



https://github.com/user-attachments/assets/74102e9b-f678-4f15-8e24-6f3fc1d9153e




---

## AI Project Analyzer

The `InternalProjectModelAnalyzer` provides an automated assessment of startup projects through a three-stage pipeline:

### 1. Sector Classification

The `nlp_service` identifies and classifies the project's business sector.

### 2. Weighted Scoring

The `scoring_service` computes an overall project score using weighted criteria:

**40% + 35% + 25%**

### 3. Generative AI Analysis

The `llm_service` uses **LLaMA 3 through Ollama** to generate a qualitative assessment, with an automatic fallback mechanism when the primary model is unavailable.

The analyzer addresses three main questions:

* Is the project potentially profitable?
* Is the project technically and commercially feasible?
* What are the main risks or potential failure factors?

<img width="800" height="730" alt="Invest" src="https://github.com/user-attachments/assets/e91d3e65-1b68-4379-8920-1f67b98c65cc" />


---

## Workflow Automation with n8n

SmartStart integrates **n8n** to automate communication and analysis workflows.

When an investor expresses interest in a company, a webhook can trigger an automated workflow that:

1. Launches growth and financial-risk analysis
2. Sends the report to the startup founder by email
3. Creates a notification within the platform

<img width="1241" height="414" alt="Invest (2)" src="https://github.com/user-attachments/assets/686e4c95-8aca-4f25-a70c-4bb534156601" />


---


# Technology Stack

### Frontend

* **Angular 21**
* Standalone Components
* **TypeScript**
* **Chart.js**

### Backend

* **FastAPI**
* **PostgreSQL**
* **SQLAlchemy**

### AI & Machine Learning

* **CatBoost**
* **scikit-learn**
* **ARIMA**
* **Prophet**
* **ETS / Holt-Winters**
* **LLaMA 3**
* **Ollama**
* Natural Language Processing

### Automation

* **n8n**
* Webhooks
* Automated email notifications

---

# Getting Started

## Prerequisites

Make sure the following are installed:

* **Node.js**
* npm
* A running SmartStart backend

The backend should be available at:

```text
http://localhost:8000
```

## Installation

Clone the repository and install the frontend dependencies:

```bash
npm install
```

## Run the Application

Start the Angular development server:

```bash
npm start
```

The application will be available at:

```text
http://localhost:4200
```

The backend API URL can be configured in:

```text
src/environments/environment.ts
```

---

# Project Structure

```text
src/
└── app/
    ├── core/
    │   ├── services/
    │   ├── models/
    │   ├── guards/
    │   └── interceptors/
    │
    ├── pages/
    │   ├── auth/
    │   ├── startuper/
    │   ├── investor/
    │   ├── risk/
    │   ├── growth/
    │   └── detection/
    │
    └── schemas/
        └── API response types
```

---

# Architecture

At a high level, SmartStart follows a modular architecture:

```text
                    ┌─────────────────────┐
                    │   Angular Frontend  │
                    │     SmartStart      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    FastAPI Backend  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌────────────┐   ┌─────────────┐   ┌────────────┐
       │ PostgreSQL │   │  ML Service  │   │    n8n     │
       └────────────┘   └─────────────┘   └────────────┘
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
             CatBoost     Forecasting     LLaMA 3
```

---

# Authors

**Nour Yahya** & **Eya Othmani**

Data Science & Artificial Intelligence Engineering Students
Tek-up University

**Academic Year:** 2025–2026
