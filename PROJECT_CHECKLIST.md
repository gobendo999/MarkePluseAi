# 🚀 MarketPulse AI — Master Project Checklist & Roadmap
**Project Directory:** `E:\Price_tracking\Price_tracing`  
**Python Version:** `3.10.11`  
**Django Version:** `5.1.15`

---

## 📋 Course Topics to Checklist Mapping (100% Coverage)

### Phase 1: Foundation, Advanced Models & Authentication
- [x] **Topic 21: User Authentication**
  - [x] Custom User model (`apps.accounts.models.CustomUser`) using UUID & Email
  - [x] Role-Based Access Control (Admin, Enterprise, Pro, Free)
  - [x] Initial credit balance assignment (25 credits on signup)
- [x] **Topic 19: Admin Interface**
  - [x] Jazzmin modern SaaS admin dashboard setup
  - [x] Customized UserAdmin with search, filters, and credit management
  - [x] ProductAdmin with TabularInline PriceHistory
- [x] **Topic 37: Authentication in Django Rest Framework**
  - [x] SimpleJWT integration (`/api/auth/login/`, `/api/auth/refresh/`)
  - [x] Token blacklisting enabled
  - [x] User Registration endpoint (`/api/auth/register/`)
  - [x] Authenticated Profile endpoint (`/api/auth/me/`)
- [x] **Topic 41: Important Features of DRF**
  - [x] `drf-spectacular` OpenAPI 3.0 & Swagger UI documentation at `/api/docs/`
  - [x] Redoc interactive API documentation at `/api/redoc/`
- [x] **Topic 16: Django Models Level 2**
  - [x] Custom Model Managers & QuerySets (`Product.objects.all()`, SoftDeleteManager)
  - [x] Model Meta options, UniqueConstraints (`unique_active_product_per_user`), CheckConstraints (`product_current_price_non_negative`)
  - [x] Soft Delete model mixin (`is_deleted`)
  - [x] Native Multi-Currency tracking (`currency` field in Product & PriceHistory)
- [x] **Topic 22: Django Advance Stuff**
  - [x] Query optimization: removing N+1 problems using `select_related("user")` and `prefetch_related("price_history")`

---

### Phase 2: Core Domain APIs & DRF ViewSets
- [x] **Topic 35: Serializers in DRF**
  - [x] Nested Serializers (`ProductSerializer` containing nested `PriceHistorySerializer`)
  - [x] `SerializerMethodField` for dynamic price difference & percentage calculation
  - [x] Field-level validation (`validate_target_url`)
  - [x] Context-based user auto-assignment in `create()`
- [x] **Topic 36: Mixins in Django Rest Framework**
  - [x] ModelViewSet full mixin architecture (List, Create, Retrieve, Update, Destroy)
- [x] **Topic 38: Django ModelViewsets and Action Project**
  - [x] `ProductViewSet` with full REST CRUD
  - [x] Custom `@action` for price stats (`GET /api/products/{id}/price-stats/`)
  - [x] Custom `@action` for simulating price changes (`POST /api/products/{id}/simulate-price-drop/`)
  - [x] Custom `@action` for real-time scraping (`POST /api/products/{id}/scrape-now/`)
- [x] **Topic 39: Custom Permissions in DRF (Important)**
  - [x] `IsOwnerOnly` object-level permission (IDOR vulnerability prevention)
- [x] **Topic 40: Pagination in DRF With Custom Classes**
  - [x] Custom `StandardResultsSetPagination`
  - [x] Custom `CursorPagination` for real-time high-throughput price histories

---

### Phase 3: Security, Middleware & Throttling
- [x] **Topic 20: Django Middleware**
  - [x] Custom Execution Time Middleware (`X-Execution-Time` header calculation)
  - [x] Request Logging & Audit Middleware
- [x] **Topic 45: Creating a Rate Limiter in DRF (Important)**
  - [x] Custom Throttling classes based on user subscription tiers (`TierBasedUserRateThrottle`):
    - Free tier: 10 requests / minute
    - Pro tier: 60 requests / minute
    - Enterprise: 300 requests / minute
    - Admin / Staff: Unrestricted (None)

---

### Phase 4: Async Processing, Web Scraping & AI Engine
- [x] **Topic 23: Web-Scraper in Django**
  - [x] Hybrid Scraper Service (`ScraperService`) with custom browser headers
  - [x] Playwright Headless Chromium integration for dynamic JavaScript sites (Daraz, Amazon)
  - [x] Schema.org (JSON-LD) extraction
  - [x] OpenGraph meta tag fallback
  - [x] Automatic multi-currency detection (USD, BDT, EUR, GBP, INR)
  - [x] Direct live integration with `ProductViewSet` via `scrape-now` action
- [x] **Topic 25: Introduction to Celery**
  - [x] Celery setup (`celery.py`, task discovery, `__init__.py` integration)
  - [x] Background task execution for asynchronous scraping (`scrape_product_task.delay()`)
  - [x] Instant HTTP 202 Accepted response with task ID and status tracking
- [ ] **Topic 26: Django with RabbitMQ**
  - [ ] RabbitMQ as the message broker for Celery
- [x] **Topic 46: Integrating LLM Models**
  - [x] Google Gemini 3.8 Flash API integration via official `google-genai` SDK
  - [x] Automated product executive summary, pros/cons, and sentiment score (1-100)
  - [x] Dynamic AI Price Verdict engine ("STRONG_BUY", "WAIT_FOR_DROP", "FAIR_PRICE")
  - [x] AI Credit consumption engine integrated with User credit balance (1 credit / analysis)
- [ ] **Topic 48: Celery Project PDF Summarizer with LLM**
  - [ ] Celery Beat periodic scheduler (daily price check)
  - [ ] Automated executive PDF report generator

---

### Phase 5: High-Speed Search & Big-Data Event Streaming
- [ ] **Topic 18: Fulltext Search in Django**
- [ ] **Topic 24: Integrating Elasticsearch in Django**
- [ ] **Topic 27: Using Kafka in Django**

---

### Phase 6: Real-Time WebSockets (Django Channels)
- [ ] **Topic 30: Introduction to Django Channels**

---

### Phase 7: Monetization, Billing & E-Commerce Flow
- [ ] **Topic 17: Project - Expense Tracker**
- [ ] **Topic 33: Creating a Full-Fledged E-commerce Application**
- [ ] **Topic 44: Building Subscription Apps in Django Rest Framework**

---

### Phase 8: Testing, DevOps, Docker & Production Deployment
- [ ] **Topic 28: Dockerising Django Application**
- [ ] **Topic 31: Load Testing on Django Application (Locust)**
- [ ] **Topic 32: Django Project Deployment**
- [ ] **Topic 29 & 47: Interview Preparation & Doubt Clearings**
