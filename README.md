# Susanoo — "The Ultimate Defense"
### AI-Powered Parametric Income Insurance for Gig Economy Delivery Workers

![Flutter](https://img.shields.io/badge/Flutter-3.19+-02569B?style=flat-square&logo=flutter&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Python_3.9-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-RDS-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis6-EC2-DC382D?style=flat-square&logo=redis&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-MAE_₹1.30-FF6600?style=flat-square)
![AWS](https://img.shields.io/badge/Deployed-AWS_EC2_ap--south--2-FF9900?style=flat-square&logo=amazonaws&logoColor=white)
![Razorpay](https://img.shields.io/badge/Razorpay-X_Payouts-02042B?style=flat-square&logo=razorpay&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-FCM_V1-FFCA28?style=flat-square&logo=firebase&logoColor=black)
![i18n](https://img.shields.io/badge/Languages-English%20%7C%20Tamil%20%7C%20Hindi-blueviolet?style=flat-square)

> **Guidewire DEVTrails 2026 Hackathon — Phase 2 Submission**
> *"The worker does nothing. Trigger fires → system pays → done in minutes."*

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [Persona — Meet Arun](#2-persona--meet-arun)
3. [Solution — Susanoo](#3-solution--susanoo)
4. [Live Demo](#4-live-demo)
5. [Mobile App Features](#5-mobile-app-features)
6. [Registration & Underwriting](#6-registration--underwriting)
7. [Insurance Policy Management](#7-insurance-policy-management)
8. [Dynamic Premium Calculation](#8-dynamic-premium-calculation)
9. [5 Automated Disruption Triggers](#9-5-automated-disruption-triggers)
10. [Zero-Touch Claims & Settlement](#10-zero-touch-claims--settlement)
11. [AI / ML Models](#11-ai--ml-models)
12. [Actuarial Engine](#12-actuarial-engine)
13. [Fraud Defense & GPS Anti-Spoofing](#13-fraud-defense--gps-anti-spoofing)
14. [Tech Stack](#14-tech-stack)
15. [System Architecture](#15-system-architecture)
16. [Repository Structure](#16-repository-structure)

---

## 1. The Problem

India's gig economy employs over **15 million delivery workers** across Zomato, Swiggy, Blinkit, Zepto, and Amazon. These workers earn purely per delivery — no delivery, no income.

When disruptions hit — heavy rain, extreme heat, AQI spikes, traffic blockages, civic emergencies — **orders drop sharply and roads become impassable**. A worker earning ₹900/day can see income fall to ₹150 on a disrupted day.

**No insurance product in India protects gig workers against income loss due to environmental or civic disruptions. Susanoo fills this gap.**

---

## 2. Persona — Meet Arun

```
┌─────────────────────────────────────────────────────────┐
│  Name        : Arun Kumar                               │
│  Age         : 24                                       │
│  Location    : Bangalore, Karnataka (Pincode: 560001)   │
│  Role        : Quick-Commerce Grocery Delivery Partner  │
│  Platform    : Blinkit / Zepto / Swiggy Instamart       │
│  Earnings    : ₹800–₹1,200/day  |  ₹5,600–₹8,400/week  │
│  Active Days : 22 days in last 30 (eligible for cover)  │
│  Dependents  : Wife + 1 child. Monthly rent: ₹6,500     │
│  Savings     : Less than ₹2,000 at any given time       │
│  Insurance   : None. Never had any.                     │
└─────────────────────────────────────────────────────────┘
```

### Arun's Day With Susanoo

- Arun pays ₹49/week for Smart Shield
- At 8:00 AM, Susanoo detects 80mm/hr rainfall in Bangalore (OpenWeather API)
- `HEAVY_RAIN / EXTREME` disruption event created automatically
- Arun's claim triggered — **he does nothing**
- Fraud engine: city match ✅, active policy ✅, no duplicate ✅, fraud score 0/100
- Payout = ₹925 × 0.58 (Bangalore infra-adjusted DSS) × 0.75 (active hours) = ₹403
- **₹403 credited to his UPI ID. Phone call confirmation sent. Done.**

---

## 3. Solution — Susanoo

Susanoo is an **AI-powered parametric income insurance platform** for gig delivery workers.

### Core Principles

- **Parametric** — Payouts triggered by objective, measurable conditions. No claim filing.
- **Hyper-local** — DSS adjusted by city infrastructure quality, not just city name.
- **Actuarially sound** — BCR target 0.55–0.70. Loss ratio >85% auto-suspends new enrolments.
- **Weekly** — Aligned with gig worker payment cycles. Never monthly.
- **Zero-touch** — Trigger fires → fraud check → payout → confirmation. Worker does nothing.
- **Multilingual** — Full support for English, Tamil, and Hindi across all screens.

---

## 4. Live Demo

| Component | URL |
|-----------|-----|
| Backend API | http://16.112.121.102:8000 |
| API Docs | http://16.112.121.102:8000/docs |
| Admin Dashboard | Deployed via Netlify (see `dashboard/netlify.toml`) |
| Android APK | Build from `mobile/` with `flutter build apk --release` |

**Infrastructure:**
- Backend: AWS EC2 `t3.small` — `ap-south-2` (Hyderabad) — `susanoo-backend`
- Database: AWS RDS PostgreSQL — `susanoo-db.cz0ucow0ih0s.ap-south-2.rds.amazonaws.com`
- Redis: Redis6 on EC2 (`redis6-server`, port 6379)
- Process manager: `systemctl` — `susanoo.service` (gunicorn + uvicorn workers)
- Firebase: Project `susanoo-d13b0` — FCM V1 API for push notifications

**Demo credentials:**
- Phone number: `9999999999` (or any 10-digit number)
- OTP: `123456` (dev mode — unlocks Simulate Event button)
- Real OTP via phone call for actual phone numbers

### Dev Mode vs Production Mode

| Feature | Dev Mode (OTP: 123456) | Production Mode (Real OTP) |
|---------|----------------------|---------------------------|
| Phone | Any number e.g. `9999999999` | Your real registered number |
| OTP | `123456` — bypass | Real OTP via phone call |
| Simulate Event button | Visible on home screen | Hidden |
| Disruption creation | Manual tap → instant event | Celery auto-poll every 15 min |
| Payout | Mock Razorpay sandbox | Real Razorpay X UPI/IMPS |

> Dev mode is automatically activated when OTP `123456` is entered. The `devModeProvider` flag in Flutter shows/hides the Simulate Event button.

---

## 5. Mobile App Features

### Onboarding & Auth
- **Terms & Conditions screen** — shown on first launch only (persisted via SharedPreferences). Includes 5 collapsible sections: Terms of Service, Insurance Policy Terms, Privacy Policy, Location & Data Consent, Financial Terms. All 3 checkboxes must be accepted before proceeding.
- **Language selection** — available from the very first screen (phone number entry) as pill buttons. Persists across sessions via SharedPreferences.
- **Location permission** — native Android OS dialog triggered immediately on first launch via `Geolocator.requestPermission()`. Custom rationale dialog shown on subsequent denials.

### Multilingual Support (i18n)
Full translation across all screens in 3 languages:

| Language | Code | Coverage |
|----------|------|----------|
| English | `en` | All screens |
| Tamil (தமிழ்) | `ta` | All screens |
| Hindi (हिंदी) | `hi` | All screens |

Translated screens: Phone, OTP, Register, Platform, Home, Policy, Claims, Live Risk, Profile, Shell nav bar, Terms & Conditions.

Language switcher available on:
- Phone number entry screen (pill buttons, top-right)
- Terms & Conditions screen (pill buttons, top-right)
- Profile screen (list selector with checkmark)

### Home Screen
- Greeting with worker's name and city/platform
- Active policy shield card with pulse animation
- Stats: protected amount + claims filed
- Active disruptions (deduplicated by type)
- Quick Actions: Buy/Renew Policy, Simulate Event (dev mode only)
- Recent claims with translated status labels

### Live Risk Screen
- **Live weather card** — fetches real weather + AQI from OpenWeatherMap using the worker's GPS coordinates (lat/lon from last location ping, falls back to `Geolocator.getCurrentPosition`)
  - Shows: temperature, feels like, description, humidity, wind speed, rainfall, visibility
  - AQI with color-coded label (Good/Moderate/Poor/Very Poor) + PM2.5
  - "LIVE" badge with detected city name
- **Risk probability gauge** — animated arc gauge showing composite risk %
- **Risk factor breakdown** — animated progress bars per factor using raw API values
- **Active risk factor tiles** — deduplicated by disruption type, shows DSS%, raw value, description
- **Risk advice card** — adapts message based on Low/Moderate/High risk level
- Pull-to-refresh + refresh button

### Policy Screen
- Active policy card with tier, premium, validity dates
- Coverage details: max daily/weekly payout, total claimed, claims count
- Triggers covered chips (plain text, no emojis)
- Renew / Change Plan button

### Claims Screen
- Full claims history with slide-in animation
- Per-claim: date, status badge, AI Auto tag, DSS%, fraud score, claimed amount
- Animated payout counter

### Profile Screen
- Worker details: name, platform, city, mobile, UPI ID
- Risk profile: avg daily earnings, risk score
- Language switcher
- Logout

### UI Consistency
- All emojis replaced with Material Icons throughout the app
- Disruption labels: plain text (Heavy Rain, Extreme Heat, AQI Spike, Traffic Disruption, Civic Emergency)
- Nav bar labels fully translated with `maxLines: 1` + `overflow: TextOverflow.ellipsis` to prevent truncation

---

## 6. Registration & Underwriting

### Onboarding Flow
1. Accept Terms & Conditions (first launch only)
2. Select language (English / Tamil / Hindi)
3. Phone number → Real OTP via phone call
4. Platform selection (Blinkit, Zepto, Swiggy Instamart, Zomato, Amazon, BigBasket)
5. Auto-fetch avg daily earnings from platform mock API
6. City + pincode + UPI ID

### Underwriting Rules (IRDAI-aligned)
- **Minimum 7 active delivery days** in last 30 days before cover eligibility
- Workers with <7 active days → `is_verified=False` → cannot purchase policy
- **City-based pools** — Delhi AQI pool ≠ Mumbai rain pool
- Workers with <5 active days in 30 → eligible for Basic tier only

---

## 7. Insurance Policy Management

### Tier Structure

| Plan | Weekly Premium | Max Daily Payout | Max Weekly Payout | Triggers Covered |
|------|---------------|-----------------|-------------------|-----------------| 
| Basic Shield | ₹29 | ₹300 | ₹600 | Heavy Rain only |
| Smart Shield | ₹49 | ₹550 | ₹1,100 | Rain + Heat + AQI |
| Pro Shield | ₹79 | ₹750 | ₹1,500 | All 5 triggers |

### Policy Features
- Razorpay payment integration (test mode sandbox)
- Weekly cycle — 7-day coverage from purchase date
- Auto-expiry with status tracking
- **Loss ratio gate** — if BCR >85% → new enrolments suspended automatically

---

## 8. Dynamic Premium Calculation

### Actuarial Base Formula
```
Premium = Σ [P(trigger) × avg_income_lost_per_day × days_exposed] × safety_loading

Where safety_loading = 1.35 (15% expenses + 10% profit + 10% reserve)
```

### AI Model (XGBoost) — Live in Production
- **MAE: ₹1.30** on test set
- 11 features: pincode prefix, month, tier, tenure weeks, activity score, zone risk, season factor, disruption type, severity, DSS multiplier, civic emergency flag
- Falls back to rule-based formula if model file not found

### Hyper-Local Infrastructure Scoring

| Location | Infra Score | 45mm/hr Rain DSS | Payout on ₹600/day |
|----------|------------|-----------------|-------------------|
| Delhi central (110xxx) | 0.30 | 0.18 | ₹108 |
| Hyderabad (500xxx) | 0.42 | 0.22 | ₹132 |
| Chennai (600xxx) | 0.48 | 0.24 | ₹144 |
| Mumbai (400xxx) | 0.50 | 0.25 | ₹150 |
| Bangalore (560xxx) | 0.58 | 0.27 | ₹162 |
| Patna (800xxx) | 0.82 | 0.37 | ₹222 |
| Rural | 0.90 | 0.41 | ₹246 |

---

## 9. Five Automated Disruption Triggers

### Trigger Table

| # | Trigger | Data Source | Threshold | DSS Range |
|---|---------|------------|-----------|-----------| 
| 1 | Heavy Rain | OpenWeather API (Real) | >35mm/hr Moderate, >64.5mm/hr Severe, >115mm/day Extreme | 0.18–1.0 |
| 2 | Extreme Heat | OpenWeather API (Real) | >42°C Moderate, >44°C Severe, >46°C Extreme | 0.24–1.0 |
| 3 | AQI Spike | OpenWeather Air Pollution API (Real) | >200 Poor, >300 Very Poor, >400 Hazardous | 0.20–1.0 |
| 4 | Traffic Disruption | Mock (realistic scenarios) | Congestion index >60 | 0.30–0.80 |
| 5 | Civic Emergency | NewsAPI (Real) | Scans for bandh/curfew/strike/Section 144 | 0.50–1.0 |

### Live Weather API (GPS-based)
The `/location/weather` endpoint accepts `lat` and `lon` and calls OpenWeatherMap directly with GPS coordinates — not city name. Returns weather + AQI in one response used by the Live Risk screen.

---

## 10. Zero-Touch Claims & Settlement

### Settlement Flow
```
1. Trigger confirmed (API threshold crossed)
        ↓
2. Worker eligibility check (active policy, correct city pool, active hours, no duplicate)
        ↓
3. Fraud verified BEFORE payment (score 0–100)
        ↓
4. Payout calculated (income shortfall × active hours ratio × ward proximity)
        ↓
5. UPI transfer via Razorpay X (primary)
        ↓ if UPI fails
   IMPS bank transfer (fallback)
        ↓ if both fail
   Rollback → claim stays APPROVED for retry
        ↓ on success
6. Phone call confirmation sent via 2Factor.in
        ↓
7. Record updated (settlement_seconds tracked, reconciled=true)
```

### Payout Formula
```
Income Shortfall = worker_daily_avg × DSS × active_hours_ratio × ward_factor

Capped at: tier daily cap and weekly cap
```

---

## 11. AI / ML Models

### XGBoost Premium Engine
- **Purpose**: Predict weekly premium based on 11 risk features
- **MAE**: ₹1.30
- **Fallback**: Rule-based formula if model file unavailable

### Isolation Forest Fraud Detection
- **Purpose**: Unsupervised anomaly detection on claim behaviour
- **Civic fraud catch rate**: 73.1%
- **Verdict**: Score <30 → auto-approve, 30–69 → hold for review, ≥70 → auto-reject

---

## 12. Actuarial Engine

### BCR (Burning Cost Rate)
```
BCR = total claims paid / total premium collected
Target: 0.55–0.70
```

| BCR | Status | Action |
|-----|--------|--------|
| <0.55 | Low | Consider premium reduction |
| 0.55–0.70 | Healthy | Maintain |
| 0.70–0.85 | Elevated | Increase premium next cycle |
| >0.85 | Critical | **Auto-suspend new enrolments** |

---

## 13. Fraud Defense & GPS Anti-Spoofing

### GPS Location Tracking
Susanoo tracks worker location every **10 minutes** during active delivery hours (6am–10pm IST):

```
Flutter app → GPS ping every 10 min → POST /api/v1/location/ping
        ↓
Backend calculates:
  distance_km = haversine(last_ping, current_ping)
  speed_kmh   = distance_km / time_elapsed_hours
  is_suspicious = speed_kmh > 200 km/h  ← physically impossible
```

### Rule-Based Fraud Scoring

| Rule | Score |
|------|-------|
| City mismatch | +40 |
| GPS location mismatch | +35 |
| GPS spoof detected (>200 km/h) | +30 |
| Platform inactive | +25 |
| High claim frequency ≥5/week | +20 |
| Duplicate claim | +50 |

### Worker Privacy
- Location only tracked during active hours (6am–10pm)
- Only city-level data used for fraud check
- Worker can deny permission — app still works, fraud score sensitivity increases
- Permission dialog shown on first launch via native OS dialog

---

## 14. Tech Stack

### Mobile
| Technology | Purpose |
|-----------|---------|
| Flutter 3.19+ | Cross-platform Android/iOS app |
| Riverpod 2.x | State management |
| GoRouter | Navigation |
| Dio | HTTP client with JWT interceptor + auto-refresh |
| flutter_secure_storage | Secure token storage |
| shared_preferences | Language preference + terms acceptance persistence |
| Razorpay Flutter SDK | In-app payment sheet |
| Pinput | OTP input UI |
| permission_handler | Location permission settings redirect |
| geolocator | GPS coordinates + native permission dialog |

### Backend
| Technology | Purpose |
|-----------|---------|
| FastAPI (Python 3.9) | REST API (gunicorn + uvicorn workers) |
| SQLAlchemy 2.0 async | ORM |
| asyncpg | Async PostgreSQL driver |
| Celery + Redis6 | Background polling every 15 min |
| httpx | Async HTTP for external APIs |
| Razorpay Python SDK | UPI + IMPS payouts |
| google-auth | FCM V1 Service Account OAuth2 |

### Infrastructure
| Component | Service | Region |
|-----------|---------|--------|
| API Server | AWS EC2 t3.small | ap-south-2 (Hyderabad) |
| Database | AWS RDS PostgreSQL | ap-south-2 |
| Cache / OTP Store | Redis6 on EC2 | ap-south-2 |
| Push Notifications | Firebase FCM V1 | susanoo-d13b0 |
| Process Manager | systemctl (susanoo.service) | EC2 |
| Admin Dashboard | Netlify | Oregon |

### External APIs
| API | Purpose | Mode |
|-----|---------|------|
| OpenWeather API | Rain + Heat triggers + GPS weather | Real |
| OpenWeather Air Pollution API | AQI trigger + GPS AQI | Real |
| NewsAPI | Civic emergency detection | Real |
| 2Factor.in | OTP via phone call + payout SMS | Real |
| Razorpay X | UPI + IMPS payouts | Sandbox |
| Firebase FCM V1 | Push notifications (claim lifecycle) | Real |

---

## 15. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flutter Mobile App                        │
│                                                                   │
│  Terms & Conditions (first launch) → Language Select             │
│  → Phone OTP (phone call) → Register → Dashboard                 │
│                                                                   │
│  Screens: Home | Policy | Claims | Live Risk | Profile           │
│  Languages: English | Tamil | Hindi (all screens)                │
│  Live Risk: GPS weather + AQI from OpenWeatherMap                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS / REST
┌──────────────────────────▼──────────────────────────────────────┐
│                  FastAPI Backend (AWS EC2 ap-south-2)             │
│                                                                   │
│  /auth    /workers    /policies    /claims    /disruptions        │
│  /payouts /actuarial  /location    /admin                         │
│                                                                   │
│  /location/weather  ← GPS lat/lon → OpenWeatherMap (real)        │
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Premium Engine  │  │  Fraud Engine    │  │ Actuarial      │  │
│  │ XGBoost ML      │  │  Isolation Forest│  │ BCR / Stress   │  │
│  │ MAE ₹1.30       │  │  73.1% catch     │  │ Test / Suspend │  │
│  └─────────────────┘  └──────────────────┘  └────────────────┘  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Celery Workers (every 15 min)                  │ │
│  │  poll_weather → DisruptionEvent → auto_claim → UPI payout  │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────┬──────────────┬──────────────┬──────────────┬─────────────┘
       │              │              │              │
  PostgreSQL      Redis6         OpenWeather    NewsAPI
  (RDS)           (EC2)          + AQI API      Civic alerts
                               (Real data)    (Real data)
                                    │
                              2Factor.in
                              OTP phone call + SMS
                                    │
                            Razorpay X
                            UPI + IMPS
```

---

## 16. Repository Structure

```
susanoo/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py               # OTP login, JWT tokens
│   │   │   ├── workers.py            # Registration, dashboard, earnings, FCM token
│   │   │   ├── policies.py           # Buy policy, Razorpay, quote
│   │   │   ├── claims.py             # Trigger claim, city pools, GPS fraud, zone stats
│   │   │   ├── disruptions.py        # Simulate, list active events
│   │   │   ├── notifications.py      # In-app notification feed + mark-read
│   │   │   ├── payouts.py            # Payout history
│   │   │   ├── actuarial.py          # BCR, stress test, premium formula
│   │   │   ├── location.py           # GPS ping + spoof detection + /weather endpoint
│   │   │   └── admin.py              # Clear test data
│   │   ├── models/models.py          # SQLAlchemy ORM
│   │   ├── schemas/schemas.py        # Pydantic schemas
│   │   └── services/
│   │       ├── premium_service.py    # XGBoost + rule-based premium
│   │       ├── disruption_service.py # 5 triggers + hyper-local DSS
│   │       ├── fraud_service.py      # Rule-based + individual baseline + zone-level fraud scoring
│   │       ├── payout_service.py     # UPI + IMPS + rollback + SMS
│   │       ├── notification_service.py # FCM push + DB-persisted in-app notifications
│   │       ├── actuarial_service.py  # BCR, stress test
│   │       ├── auth_service.py       # OTP, JWT, 2Factor.in
│   │       └── platform_service.py   # Mock platform earnings API
├── mobile/
│   └── lib/
│       ├── main.dart                 # App entry + location permission (native dialog)
│       ├── router/app_router.dart    # Routes incl. /auth/terms
│       ├── l10n/
│       │   └── app_strings.dart      # All UI strings: English, Tamil, Hindi
│       ├── providers/
│       │   ├── app_providers.dart    # All Riverpod providers incl. liveWeatherProvider
│       │   └── locale_provider.dart  # Language state + SharedPreferences persistence
│       ├── services/
│       │   ├── api_service.dart      # HTTP client + getWeatherByLocation
│       │   └── location_service.dart # GPS ping every 10min background service
│       ├── screens/
│       │   ├── onboarding/
│       │   │   ├── terms_screen.dart # T&C with 5 sections + 3 checkboxes (first launch)
│       │   │   ├── phone_screen.dart # Language pills + translated strings
│       │   │   ├── otp_screen.dart
│       │   │   ├── platform_screen.dart
│       │   │   └── register_screen.dart
│       │   ├── home/home_screen.dart         # Fully translated
│       │   ├── policy/policy_screen.dart     # Fully translated
│       │   ├── claims/claims_screen.dart     # Fully translated
│       │   ├── risk/live_risk_screen.dart    # GPS weather + AQI + risk gauge
│       │   ├── profile/profile_screen.dart   # Language switcher
│       │   ├── shell_screen.dart             # Translated nav bar
│       │   └── splash_screen.dart            # Routes to terms on first launch
│       ├── theme/app_theme.dart
│       └── utils/constants.dart              # Plain text disruption labels (no emojis)
├── dashboard/                                # React admin panel
├── .gitignore
└── README.md
```

---

## Changelog

### Phase 3 Post-Review Improvements

#### 1. Celery Deployment Robustness
- Fixed fragile `api → worker → beat` dependency chain in `docker-compose.yml` — `worker` and `beat` now depend directly on `db` and `redis` with health checks, starting independently of the API
- Added `--scheduler celery.beat:PersistentScheduler` so the beat schedule survives container restarts
- Fixed missing `from app.config import settings` import in `main.py` that caused the global 500 handler to crash with a `NameError`

#### 2. Notification System
- **`notification_service.py`** — dual-channel engine: FCM push (optional) + DB-persisted in-app feed. Covers `claim_approved`, `claim_rejected`, `claim_paid`, `disruption_detected`, `policy_expiring`
- **`WorkerNotification` model** — in-app notification feed table with `is_read` tracking
- **`Worker.fcm_token`** — stores Firebase push token per device, registered via `POST /api/v1/workers/fcm-token`
- **`GET /api/v1/notifications`** — mobile app polls its notification feed (last 50)
- **`POST /api/v1/notifications/{id}/read`** and **`/read-all`** — mark notifications read
- Notifications wired into `claims.py` at all three lifecycle transitions: approved → rejected → paid
- FCM key is optional — without it, notifications are DB-only (in-app feed still works, SMS on payout still fires)

#### 3. Enhanced Fraud Detection — Individual vs Zone-Level Behavioral Analysis
- **Individual behavioral baseline** — compares current week's claims to the worker's own 12-week historical average. A worker who normally claims 0.5×/week suddenly claiming 4× is flagged (`INDIVIDUAL_BASELINE_SPIKE: +20`), not just anyone with 3+ claims
- **Zone-level corroboration** — if <5% of workers in the same pincode zone claimed this event, the event isn't corroborated (`ZONE_LOW_CORROBORATION: +15`); if >90% claimed, it's flagged as a coordinated fraud ring (`ZONE_COORDINATED_FRAUD_RISK: +20`)
- Zone stats (claim count + total active workers per pincode prefix) queried in `claims.py` and passed into `calculate_fraud_score()`

#### 4. Granular Geographic Risk Assessment — Ward-Level Premiums
- Added `SUB_ZONE_RISK` dict in `premium_service.py` with full 6-digit pincode multipliers derived from claim density, NDMA flood zone maps, and IMD heat island data
- Examples: Mumbai Dharavi (`400017: 1.55`) vs Bandra (`400050: 1.25`); Bangalore Koramangala (`560034: 1.40`) vs Whitefield (`560066: 1.10`)
- `get_sub_zone_risk()` uses ward-level multiplier when available, falls back to 3-digit zone risk
- A worker in 560034 pays ~27% more than one in 560066 for the same tier — same city, fairer pricing

### Latest Updates (Previous)
- **Phase 3 Judge Feedback Upgrades** — Added a complete Predictive Analytics HQ to the Admin Dashboard including:
  - **BCR & Loss Ratio Monitoring**: Real-time actuarial health tracking per city.
  - **Predictive Forecasts**: Next-week claim volume prediction using XGBoost.
  - **Fraud Deep-Dive**: Isolation Forest anomaly visualization per claim.
  - **Actuarial Stress Testing**: Simulation mode for extreme climate events.
  - **Worker Status Indicator**: Live health monitoring of Celery background polling tasks.
- **Terms & Conditions** — Professional T&C screen shown on first launch with 5 collapsible sections, 3 consent checkboxes, language picker. Accepted state persisted via SharedPreferences.
- **Multilingual (i18n)** — Full English / Tamil / Hindi support across all screens. Language picker on phone screen and profile. Persisted across sessions.
- **Location Permission** — Fixed to trigger native Android OS dialog immediately on first install using `Geolocator.requestPermission()`.
- **Live Risk Screen** — New screen with GPS-based live weather card (temperature, humidity, wind, AQI, PM2.5) from OpenWeatherMap using exact lat/lon coordinates. Risk probability gauge, factor breakdown, advice card.
- **Backend `/location/weather`** — New endpoint accepting `lat`/`lon`, returns full weather + AQI from OpenWeatherMap in one call.
- **Emoji removal** — All emojis replaced with Material Icons throughout the app for consistency and rendering reliability.
- **Nav bar** — Fixed Tamil label truncation with `Expanded` + `maxLines: 1` + `overflow: TextOverflow.ellipsis`.
- **OTP delivery** — Updated to reflect OTP delivery via phone call (not SMS).

---

## Conclusion

Susanoo — "The Ultimate Defense" — addresses a real, unmet financial need for India's 15 million gig delivery workers.

By combining **parametric insurance mechanics**, **hyper-local infrastructure-aware DSS**, **AI-driven pricing**, **actuarially sound BCR monitoring**, **automated fraud detection**, **instant UPI payouts**, **GPS-based live weather**, and **full multilingual support (English/Tamil/Hindi)**, it delivers a product that is:

- **Affordable** — ₹29–₹79/week, aligned with weekly earnings cycles
- **Automatic** — Zero manual claim filing. Trigger fires → system pays → done in minutes
- **Hyper-local** — Same rainfall = different payout based on city drainage quality
- **Actuarially sound** — BCR target 0.55–0.70, stress-tested for 14-day monsoon
- **Fraud-resistant** — GPS anti-spoofing + network-level ring detection
- **Accessible** — Full English, Tamil, and Hindi support from first screen to last
- **Scalable** — Celery workers handle city-wide events for thousands of workers simultaneously

---

*Built for Guidewire DEVTrails 2026 | Team Susanoo*
*"The Ultimate Defense for India's Delivery Heroes"*
