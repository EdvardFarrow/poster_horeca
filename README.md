[![Django CI](https://github.com/EdvardFarrow/poster_horeca/actions/workflows/main.yml/badge.svg)](https://github.com/EdvardFarrow/poster_horeca/actions/workflows/main.yml)
# 📊 Poster Horeca Payroll Engine

An automated ETL and Payroll Calculation system designed for the restaurant industry. This solution integrates with the **Poster POS API** to fetch sales data, processes complex commission logic, and generates salary reports in real-time.

## 🚀 Key Features

* **Async Data Ingestion:** Implemented a robust ETL pipeline using `asyncio` and `aiohttp/requests` to fetch transaction history. Includes **Semaphore-based Rate Limiting** to respect API quotas.
* **Complex Event Processing:** Custom algorithm to attribute sales to shifts, handling edge cases (e.g., pre-opening sales) and dynamic splitting of tips/bonuses among staff groups.
* **Data Integrity:** Implemented manual Bulk Upsert operations to optimize database performance and ensure data consistency using atomic transactions.
* **Infrastructure:** Fully dockerized application (Django + Postgres + Redis) ready for AWS deployment.

## 🛠 Tech Stack

* **Backend:** Python 3.11, Django 5, DRF
* **Data Processing:** Asyncio, Pandas-like manual aggregation
* **Database:** PostgreSQL, Redis (Caching)
* **Infrastructure:** Docker, Docker Compose, AWS EC2, Gunicorn, Nginx
* **Frontend:** React (Vite)

## ⚙️ Architecture Highlights

The system follows a modular monolith architecture with strict separation of concerns:
* `client.py`: Async wrapper for external API communication.
* `aggreg.py`: Core business logic for financial calculations.
* `saving.py`: Optimized bulk-write operations to minimize DB hits.

## 📦 Installation & Setup

To run the project locally, you need Docker and Docker Compose installed.

```bash
# 1. Clone the repository
git clone [https://github.com/EdvardFarrow/poster_horeca.git](https://github.com/EdvardFarrow/poster_horeca.git)
cd poster_horeca

# 2. Setup environment variables
# Copy the example config to the backend folder where Docker expects it
cp .env.example backend/.env

# 3. Build and run containers
docker-compose up --build -d

# 4. Run migrations
docker-compose exec backend python manage.py migrate

# 5. Create superuser (to access Admin panel)
# Follow the prompts to create your admin account
docker-compose exec backend python manage.py createsuperuser
