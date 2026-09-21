# Commercialization Strategy: EviBite AI

**Supermarket Product Intelligence & Allergen Safety Platform**

---

## 1. Target Market & User Segments

EviBite AI targets three primary market segments in the retail food & health technology space:

1. **B2C Consumers (Health-Conscious & Allergic Shoppers)**:
   - Individuals with food allergies (peanuts, milk/lactose, gluten, soy, eggs).
   - Consumers following strict dietary regimes (vegan, vegetarian, low-sugar, keto).

2. **B2B Supermarket Retailers & E-Commerce Platforms**:
   - Supermarket chains (e.g. Tesco, Sainsbury's, Walmart, Woolworths) seeking to embed AI search into their online grocery storefronts.
   - Food delivery apps (Instacart, Deliveroo) needing instant allergen & ingredient verification.

3. **B2B Food Manufacturers & Regulatory Compliance Teams**:
   - Food brands auditing ingredient labels and ensuring compliance with allergen declaration laws (e.g. Natasha's Law in the UK, FDA Food Allergen Labeling in the US).

---

## 2. Commercialization & Pricing Model (SaaS)

EviBite AI adopts a **Hybrid B2C / B2B SaaS (Software-as-a-Service) Pricing Model**:

| Tier | Target Audience | Pricing | Key Features |
| :--- | :--- | :--- | :--- |
| **Free Tier** | B2C Shoppers | **$0 / month** | Up to 15 product searches/day, barcode scanner, basic allergen alerts. |
| **Pro Shopper** | Allergic & Special Diet Individuals | **$4.99 / month** | Unlimited searches, custom family allergen profiles, instant AI safety reasoning, offline database access. |
| **Supermarket API (Starter)** | Independent Grocers & Apps | **$299 / month** | 50,000 API calls/month, RESTful Chat/Triage endpoints, 99.9% uptime SLA. |
| **Enterprise Retail** | Large Supermarket Chains | **Custom / $2,500+ / mo** | Unlimited API volume, custom SKU database integration, dedicated LLM fine-tuning, priority support. |

---

## 3. Deployment & Cloud Architecture

```
[ B2C React Web / Mobile App ] <---> [ FastAPI REST API (Python) ]
                                            |
                         +------------------+------------------+
                         |                                     |
              [ Local SQLite/PG Database ]            [ Open Food Facts API ]
                         |                                     |
                         +------------------+------------------+
                                            |
                                  [ Gemini LLM Engine ]
```

- **Containerization**: Dockerized microservices (`FastAPI` backend + `Vite React` frontend).
- **Orchestration & Hosting**: AWS ECS / Kubernetes cluster with automated horizontal pod autoscaling.
- **Caching Layer**: Redis cache for high-frequency product queries and barcode lookups.
- **LLM Provider**: Multi-provider failover (Primary: Google Gemini 3.1 Flash-Lite; Fallback: OpenAI GPT-4o-mini).
