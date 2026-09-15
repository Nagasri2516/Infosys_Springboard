# Agentic AI for Smart Event Management Operations

EventCore is a modern, AI-powered Event Management and Telemetry Platform designed for enterprise-grade event operational intelligence. It provides real-time registration tracking, QR-code check-ins, automated venue optimization, sponsorship tracking, incident management, and executive analytics dashboards.

---

## 🌟 Key Features

### 1. Executive Intelligence & Analytics Dashboard
- Real-time KPIs: Attendance Velocity, Revenue Telemetry, Venue Utilization, Speaker Confirmation Rate, Incident Resolution SLA.
- Dynamic Health Score Engine: Computes real-time event health status based on live database metrics.
- Scenario Simulator: Allows executives to project attendance targets, revenue models, and operational targets.

### 2. Event Intelligence Engine
- Duplicate Detection: Automatically scans email and phone numbers in SQLite records to detect duplicates.
- Predictive Risk Scanning: Identifies potential venue over-capacity, check-in queue delays, and speaker schedule conflicts.
- AI Recommendations: Provides actionable, rule-based recommendations for event coordinators.

### 3. Agentic Workflow Orchestration
- **Venue Agent**: Automated room allocation matching expected attendees, budget, and required facilities.
- **Speaker Agent**: Speaker recommendation and automated session scheduling.
- **Sponsorship Agent**: Deliverable tracking, contract status, engagement metrics, and automated prospect proposal generation.
- **Incident Agent**: Operational alert monitoring, urgency-based ticket routing, and automated resolution workflows.

### 4. Participant & Organizer Portals
- **Organizer Portal**: Full operational control panel for managing registrations, sessions, venues, sponsors, and incidents.
- **Participant Portal**: Mobile-responsive portal allowing attendees to view event schedules, access personalized QR codes, submit live feedback, and report incidents.

---

## 📁 Repository Architecture

```
infosys/
├── run.py                 # Application Entrypoint
├── requirements.txt       # Project Dependencies
├── .env                   # Environment Variables
├── .env.example           # Example Environment Configuration
├── backend/               # Flask Application & Services
│   ├── app.py             # Main REST API Router & Controllers
│   ├── config.py          # Centralized Application Configuration
│   ├── models.py          # SQLite Data Models & Helper Queries
│   ├── db_setup.py        # Database Initializer & Seed Script
│   ├── database.db        # SQLite Database File
│   ├── requirements.txt   # Backend Dependencies
│   ├── services/          # Core Business & Agent Intelligence Services
│   │   ├── ai_agent_service.py
│   │   ├── ai_insights_service.py
│   │   ├── event_intelligence_service.py
│   │   ├── incident_service.py
│   │   ├── optimization_service.py
│   │   ├── scheduling_service.py
│   │   ├── sponsorship_service.py
│   │   └── venue_service.py
│   └── utils/             # Utility Functions (Email dispatch, QR generator)
└── frontend/              # Web Application Interface
    ├── index.html         # Single Page Interface Structure
    ├── app.js             # Dynamic Dashboard & API Connector Logic
    └── style.css          # Glassmorphic Design System & Responsive Styles
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9+ installed on your system.

### 1. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/your-username/event-core.git
cd event-core
pip install -r requirements.txt
```

### 2. Running the Platform
Launch the application server:
```bash
python run.py
```

The application will start automatically at:
- **Web Interface**: `http://localhost:5000`
- **REST API Base**: `http://localhost:5000/api/`

---

## 🔌 API Endpoints Summary

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/executive-dashboard` | `GET` | Fetches real-time executive metrics, health score, and scenario projections. |
| `/api/insights` | `GET` | AI Insights, attendance forecasts, and duplicate detection records. |
| `/api/registrations` | `GET / POST` | Fetch or submit new event registrations. |
| `/api/checkins` | `POST` | Process QR code or manual participant check-ins. |
| `/api/venues/recommend` | `POST` | Query Venue AI Agent for venue recommendations. |
| `/api/sponsors` | `GET` | Retrieve sponsorship tiers, contracts, and deliverable metrics. |
| `/api/incidents` | `GET / POST` | Retrieve or log operational incidents. |
| `/api/analytics/sessions` | `GET` | Session popularity, speaker feedback, and venue occupancy telemetry. |

---

## 💻 Technical Stack
- **Backend Framework**: Python / Flask
- **Database**: SQLite3
- **Frontend Architecture**: Vanilla JavaScript (ES6+), HTML5, Custom Glassmorphic CSS3
- **Visualization**: Chart.js
- **Icons & Typography**: FontAwesome 6, Google Fonts (Outfit / Inter)

---

## 📄 License
This project is licensed under the MIT License.
