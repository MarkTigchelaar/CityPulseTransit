# CityPulseTransit

## Overview
CityPulseTransit is an end-to-end, event-driven data engineering pipeline and public transit simulation.

It models a live transit network, streaming real-time passenger and fleet telemetry through a distributed architecture to power a live analytical dashboard.

This project was built to demonstrate data engineering design patterns, specifically: 
**streaming data capture, idempotent state recovery, dimensional modeling, and decoupled presentation layers.**

## Architecture & Tech

* **Producer / Simulator:** Python (Custom Object-Oriented Simulation)
* **Message Broker:** Apache Kafka & Zookeeper (Dockerized)
* **Data Warehouse:** PostgreSQL (Dockerized)
* **Transformation:** dbt (Data Build Tool)
* **Presentation:** Streamlit & Altair

## Key Engineering Goals Achived

Reviewers evaluating this repository should note the following architectural patterns:

### 1. Single-Command CI/CD Emulator (`build.py`)
To ensure ease of use, this project is build by running a single build script, with one command.
Running `python build.py` automatically isolates the environment, installs dependencies, executes `pytest` suites, provisions Docker containers, and runs the `dbt build` DAG. It mimics a clean CI/CD deployment pipeline.

### 2. Idempotent Disaster Recovery
Kafka consumers utilize SQLAlchemy's `ON CONFLICT DO UPDATE` constraints mapped to composite primary keys. If the analytical layer crashes, the data consumer can safely replay the entire Kafka retention window. The database will heal its state without duplicating historical records.

### 3. Decoupled "Clean Slate" UI Architecture
The presentation layer (Streamlit) is decoupled from the simulation and the message broker. By polling exclusively from dbt's materialized dimensional marts, it cleanly shows the live state
of the simulation.

### 4. Metric Aggregation via dbt
Average Wait Times, live Train Headways, passenger and train movement are streamed to Postgres, and processed to mart grade data view views defined using dbt.

### 5. Finite State Machine Routing
The transit logic relies on static routing rules that each entity (Train and passenger) uses correctly to follow their routes, including passengers moving across multiple train routes.

### 6. Small Amounts Of Non Determinism
Passengers get deplayed at stations due to traffic, trains maintain ordering as part of routing groups, but can be interleaved with trains from other routes, creating more realistic data.

---



## Quickstart Guide
This project is designed to run seamlessly on any local machine with Docker and Python 3.10+ installed.

### 1. Clone the repository
```
git clone (https://github.com/MarkTigchelaar/CityPulseTransit.git)
cd CityPulseTransit
```
### 2. Run build script
```
python build.py
```

### 3. Activate python venv

```
On Mac/Linux:
source .venv/bin/activate
```

```
On Windows:
.venv\Scripts\activate
```
### 4. Run the system
```
python run.py
```

### 5. Open dahsboards, and data dictionary
in your browser, open any of the following to observe the architecture, or the dashboard of the system:

```
Live Dashboard: http://localhost:8501

dbt Data Dictionary: http://localhost:8081

Kafka Dashboard:   http://localhost:8080
```