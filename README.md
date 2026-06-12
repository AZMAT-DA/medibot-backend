---
title: Medibot Backend
emoji: 🏥
colorFrom: teal
colorTo: blue
sdk: docker
pinned: false
---

# MediBot Backend API

FastAPI backend for the MediBot hospital assistant system.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/doctors` | All doctors |
| GET | `/doctors/available` | Available doctors only |
| PUT | `/doctors/{id}/availability` | Update doctor availability |
| GET | `/appointments` | All appointments |
| GET | `/appointments/stats` | Appointment statistics |
| POST | `/appointments/book` | Book a new appointment |
| DELETE | `/appointments/{id}` | Cancel appointment |
| GET | `/nurses` | All nurses |
| POST | `/chat` | Chatbot response |
| GET | `/admin/overview` | Admin dashboard data |

## Docs
Visit `/docs` for the full interactive Swagger UI.
