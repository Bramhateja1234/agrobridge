# AgroBridge 🌾
**Smart Platform Between Farmers and Consumers**

A production-ready full-stack Django application connecting farmers directly with consumers, featuring Stripe payments, AI crop price prediction, geolocation-based filtering, and JWT authentication.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+ installed.
- (Optional) Stripe account for payments.

### 1. Setup Environment
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Settings
```bash
cp .env.example .env
# Open .env and add your Stripe keys if you have them.
```

### 3. Initialize Database & Translations
```bash
# Run migrations
python manage.py migrate --settings=agro_platform.settings.dev

# Compile language files (En, Hi, Te)
python manage.py compilemessages --settings=agro_platform.settings.dev

# Create admin account
python manage.py createsuperuser --settings=agro_platform.settings.dev
```

### 4. Start Server
```bash
python manage.py runserver --settings=agro_platform.settings.dev
```
👉 **Open http://127.0.0.1:8000 in your browser.**

---

## 💳 Stripe Integration
1. Get test keys from [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys).
2. Add to `.env`:
   ```
   STRIPE_SECRET_KEY=sk_test_xxxxx
   STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
   STRIPE_WEBHOOK_SECRET=whsec_xxxxx
   ```

---

## 🤖 AI Module
Endpoints available at: 
- `POST /api/predict-price/`
- `POST /api/predict-demand/`

---

## 🌍 Multi-language Support
AgroBridge supports:
- **English** (Default)
- **Hindi** (हिन्दी)
- **Telugu** (తెలుగు)

Switch languages using the dropdown in the navigation bar.

## 🌍 Deployment on Render (Free)

AgroBridge is ready to be hosted for free on [Render.com](https://render.com).

1.  **Push to GitHub**: Create a repository and push your code.
2.  **Connect to Render**:
    -   Click **"New"** → **"Blueprint"**.
    -   Connect your GitHub repository.
    -   Render will automatically read `render.yaml` and set up your **Web Service** and **MySQL Database**.
3.  **Set Environment Variables**: In the Render Dashboard, add these:
    -   `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `FRONTEND_URL`.
4.  **SEO Ready**: We've included a `robots.txt` and optimized meta tags so your site can be found on **Google**!

---

## 🏗️ Project Structure
```
agro_platform/
├── agro_platform/         # Django settings & routing
├── users/                 # Auth & Roles
├── crops/                 # Crop CRUD & Geo-filtering
├── orders/                # Order processing
├── payments/              # Stripe logic
├── reviews/               # Ratings & Moderation
├── ai_module/             # ML Price & Demand models
├── templates/             # HTML files (Bootstrap 5)
├── static/                # CSS/JS assets
├── locale/                # Translation files
├── README.md
├── READ_ME_FIRST.txt      # Simple guide for friends
└── requirements.txt
```

---

## 🔐 Security
- ✅ JWT Authentication
- ✅ Role-based access (Farmer vs Consumer)
- ✅ SQL Injection protection
- ✅ Environment variables for secrets

---

## 📄 License
MIT License
