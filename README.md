# 🚇 CityPulseTransit

![Live Dashboard Demonstration](assets/dashboard_preview.gif)

## Overview
CityPulseTransit is an end-to-end, event-driven data engineering pipeline and public transit simulation. It models a live transit network, streaming real-time passenger and fleet telemetry through a distributed architecture to power a live analytical dashboard.

This project was built to demonstrate enterprise-grade engineering patterns, specifically: **streaming data capture, idempotent state recovery, dimensional modeling, and decoupled presentation layers.**

## 🏗️ Architecture & Tech Stack

* **Producer / Simulator:** Python (Custom Object-Oriented Simulation)
* **Message Broker:** Apache Kafka & Zookeeper (Dockerized)
* **Data Warehouse:** PostgreSQL (Dockerized)
* **Transformation:** dbt (Data Build Tool)
* **Presentation:** Streamlit & Altair

## 🧠 Key Engineering Decisions

Reviewers evaluating this repository should note the following architectural patterns:

### 1. Single-Command CI/CD Emulator (`build.py`)
To ensure total reproducibility, the entire infrastructure is orchestrated via a custom Python build script. Running `python build.py` automatically isolates the environment, installs dependencies, executes `pytest` suites, provisions Docker containers, and runs the `dbt build` DAG. It mimics a clean CI/CD deployment pipeline.

### 2. Idempotent Disaster Recovery
Kafka consumers utilize SQLAlchemy's `ON CONFLICT DO UPDATE` constraints mapped to composite primary keys. If the analytical layer crashes, the consumer can safely replay the entire Kafka retention window. The database will idempotently heal its state without duplicating historical records.

### 3. Decoupled "Clean Slate" UI Architecture
The presentation layer (Streamlit) is completely decoupled from the simulation and the message broker. Rather than relying on fragile `while True` websocket loops, the UI uses a "Clean Slate" architecture via `st.rerun()`, polling exclusively from dbt's materialized dimensional marts.

### 4. Dynamic Metric Aggregation via dbt
Complex metrics, such as Average Wait Times and live Train Headways, are not approximated in Python memory. Raw arrival logs are streamed to Postgres, and dbt window functions dynamically calculate the exact physical gaps and wait times.

### 5. Finite State Machine Routing
The transit logic relies on a routing table structure (`route_id`, `stop_number`, `station_id`) to form a directed graph, drawing heavy algorithmic inspiration from GTFS (General Transit Feed Specification) data structures.

---

## 📂 Repository Structure

```text
CityPulseTransit/
├── assets/                 # Architecture diagrams and UI demonstrations
├── dbt/                    # dbt project: staging, intermediate, and mart models
├── src/                    
│   ├── simulation/         # Core simulation engine and data generators
│   ├── streaming/          # Kafka consumer and Postgres ingestion logic
│   └── dashboard/          # Streamlit UI and DataService layer
├── tests/                  # Pytest suite verifying complex state rehydration
├── build.py                # System orchestrator & dependency manager
├── run.py                  # Entry point to execute the simulation and UI
└── docker-compose.yml      # Containerized Kafka, Zookeeper, and Postgres


🚀 Local Quickstart
This project is designed to run seamlessly on any local machine with Docker and Python 3.10+ installed.

1. Clone the repository

git clone [https://github.com/YourUsername/CityPulseTransit.git](https://github.com/YourUsername/CityPulseTransit.git)
cd CityPulseTransit

2. Run the Build Script
This will handle the virtual environment, dependencies, Docker containers, and dbt initialization
python build.py

# On Mac/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

python run.py

