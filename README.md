# 🧠 MyMindSpace: AI-Powered Mental Wellness Support Platform

A clinical support tool designed to help therapists deliver more effective, data-informed, and personalized care to young adults in India.

## 📖 Table of Contents

- [🎯 Project Overview](#-project-overview)
- [✨ Core Features](#-core-features)
- [🏛️ Technical Architecture](#️-technical-architecture)
- [🗺️ Project Ecosystem](#️-project-ecosystem)
- [📊 Development Status](#-development-status)
- [🛠️ Technology Stack](#️-technology-stack)

## 🎯 Project Overview

### The Problem
Mental health professionals working with young adults in India face significant systemic challenges:
- High patient-to-therapist ratios limiting individual session time
- Limited visibility into patient well-being *between* sessions
- Difficulty tracking mood trends and behavioral patterns over time
- Patients who are hesitant to open up verbally, especially early in treatment
- Administrative burden reducing time available for direct care

### Our Solution
MyMindSpace is a **therapist-first** clinical support platform. It empowers mental health professionals with AI-assisted insights, structured patient data, and between-session engagement tools — all while keeping the therapist firmly at the center of care. The platform never replaces clinical judgment; it amplifies it.

Patients interact with the app between sessions through journaling, mood tracking, and guided wellness activities. Therapists receive organized, AI-summarized data and alerts so they can walk into every session better prepared, catch warning signs earlier, and tailor their approach to each individual's journey.

> **Important**: MyMindSpace is a clinical adjunct tool. It does not provide diagnoses, replace therapy, or act as an autonomous mental health service. All AI-generated insights are supplementary and subject to therapist review.

---

## ✨ Core Features

### 🖊️ 1. Between-Session Journaling Module
*"See what your patient can't always say out loud"*
- Structured journaling prompts designed around CBT and ACT frameworks
- AI-assisted Named Entity Recognition (NER) to surface recurring themes, persons, and stressors
- Automatic mood pattern identification presented as therapist-readable summaries
- Empathetic in-app reflections to keep patients engaged between sessions
- All raw entries and AI summaries delivered to the therapist dashboard

### 📊 2. Therapist Dashboard & Patient Digital Twin
*"Every session starts with full context"*
- Unified view of each patient's mood, activity, journal, and skill progress
- Longitudinal trend charts across weeks and months
- AI-powered trigger identification with confidence indicators
- Session-ready summaries: key themes, emotional fluctuations, and notable entries since the last appointment
- Curated action suggestions for therapists to review and adapt

### 🧘 3. Guided Wellness Activities (Patient-Side)
*"Homework patients actually complete"*
- Therapist-assignable meditation and breathing exercises
- Adaptive yoga and mindfulness routines based on therapist-set goals
- Camera-based pose feedback with explicit patient consent
- Completion tracking and engagement data visible to the assigned therapist

### 💪 4. Social & Communication Skills Practice
*"Practice the skills your therapist is building with you"*
- Gamified, AI role-playing scenarios aligned to therapist treatment goals
- Safe environment for patients to rehearse difficult conversations
- Reinforcement Learning adaptation to patient progress
- Session transcripts and performance data surfaced to therapists for review

### 🏥 5. Crisis Triage & Professional Handoff Support
*"Your safety net between sessions"*
- Passive and active risk indicators flagged for immediate therapist review
- Escalation pathways directly to professional helplines (iCall, Vandrevala Foundation, etc.)
- Crisis alerts routed to the patient's assigned therapist
- Structured session handoff notes: AI-generated summaries for smooth transitions between providers

---

## 🏛️ Technical Architecture

Our platform is built on a modern, scalable, and decoupled microservices architecture:

```
📱 Patient App (In Development)   🌐 Backend (Complete)      🗄️ Database (Complete)
┌──────────────────────┐          ┌─────────────────┐        ┌─────────────────┐
│ React Native         │ ←→ HTTP →│ Node.js/Express │ ←→SDK→ │ Firebase        │
│ Redux Toolkit        │          │ Google Cloud    │        │ Firestore       │
│ Data Viz             │          │ Docker/Run      │        │ Collections     │
└──────────────────────┘          └─────────────────┘        └─────────────────┘
                                          ↕ HTTP
                                  ┌─────────────────┐
🖥️ Therapist Dashboard            │ AI Services     │
┌──────────────────────┐          │ Google Vertex   │
│ React Native / Web   │ ←→ HTTP →│ Custom LLMs     │
│ Patient Overview     │          └─────────────────┘
│ Alerts & Summaries   │
└──────────────────────┘
```

---

## 🗺️ Project Ecosystem

Our architecture is composed of specialized microservices across multiple repositories.

### 🤖 AI & Machine Learning Services

#### Journaling Engine
- **Component Integration**: Handles NER, mood tagging, and theme extraction from patient journal entries to produce therapist-facing summaries.
- **Gemini Engine Integration**: Powers empathetic in-app patient reflections and prompt generation — outputs are surfaced alongside raw entries for therapist review.

#### Therapy Support Models
- **Core Support Model (Lightweight)**: Provides session-prep summaries and between-session risk flagging for standard patient loads.
- **Advanced Support Model (Comprehensive)**: Deep longitudinal analysis for complex cases; generates structured clinical context reports.

#### Meditation & Wellness Module
- **Guided Wellness AI**: Manages therapist-assignable activity libraries, adaptive recommendations, and patient engagement tracking.

#### Speech Services
- **Speech-to-Text (STT)**: Enables voice journaling for patients who prefer speaking over writing; transcripts are stored and surfaced to therapists.
- **Text-to-Speech (TTS)**: Delivers guided meditation and breathing exercise audio to patients.

### 🗄️ Data & Persistence Layer

#### Vector Databases
- **Memory Embedding DB**: Stores long-term patient context for longitudinal pattern analysis.
- **Semantic Search DB**: Powers therapist-facing search across patient history, entries, and session notes.
- **Chat Embedding DB**: Maintains conversational context for in-app patient interactions.

#### Feature Engineering
- **Event & Temporal Features (NoSQL)**: Captures time-series behavioral and mood data for trend analysis and trigger identification.

### 🌐 Backend Services
- **Email Notification Service**: Therapist alerts for flagged entries, crisis indicators, and session reminders.
- **Core Backend API**: REST API layer connecting patient app, therapist dashboard, and AI services.
- **Authentication Service**: Role-based access control separating patient and therapist data scopes.

### 📱 Frontend Applications
- **Digital Twin Dashboard**: Therapist-facing analytics and patient management interface.
- **Main Mobile Application**: Patient-facing app for journaling, wellness activities, and between-session engagement.

---

## 📊 Development Status

### ✅ **COMPLETED COMPONENTS**

#### Backend API (Node.js/Express)
- **Status**: ✅ Production-ready
- **Features**:
  - JWT authentication with Firebase (role-based: patient / therapist / admin)
  - 5 core dashboard API endpoints
  - Google Cloud Run containerization
  - AI service integration (Vertex AI)
  - Comprehensive security and error handling

#### CRUD Services Layer
- **Status**: ✅ Production-ready
- **Features**:
  - 4 comprehensive service modules (Journal, Mood, Activity, Skill)
  - Firebase Firestore integration
  - Robust validation and analytics
  - Gamification system (10 predefined skills assignable by therapists)
  - Complete test suite

#### Firebase Infrastructure
- **Status**: ✅ Fully configured
- **Components**:
  - Firestore database with security rules and patient-therapist data isolation
  - Service account authentication
  - Optimized indexes for all queries
  - Data seeding and deployment scripts

### 🚧 **IN DEVELOPMENT**

#### Therapist Dashboard — Digital Twin View (Current Priority)
- **API Endpoints**: All 5 endpoints complete and tested
- **Data Sources**: Integrated mood, journal, activity, and skill data
- **Frontend**: React Native implementation in progress

### 📋 **NEXT PRIORITIES**

1. **Therapist Dashboard UI** — Patient list, session-prep summaries, trend charts, crisis alerts
2. **React Native Patient App Setup** — Navigation, state management, authentication
3. **Journal Feature Frontend** — AI feedback interface, mood selection, therapist-visible submission
4. **Advanced AI Features** — Voice journaling transcription, real-time sentiment flagging for therapist review

---

## 🛠️ Technology Stack

| Area | Technology |
|------|------------|
| **Mobile Frontend** | React Native, Redux Toolkit |
| **Therapist Dashboard** | React Native / Web, Data Visualization |
| **Backend** | Node.js, Express.js, Microservices |
| **Database** | Firebase Firestore, Vector Databases |
| **AI / ML** | Google Vertex AI, Gemini, Custom LLMs |
| **Authentication** | Firebase Authentication (JWT, RBAC) |
| **Deployment** | Docker, Google Cloud Run (Serverless) |

---

## 🎨 Design Philosophy

### Clinical Priorities
- **Therapist Authority**: Every AI output is a suggestion, never a directive. Final interpretation always rests with the clinician.
- **Between-Session Continuity**: Designed to extend the therapeutic relationship, not substitute for it.
- **Crisis Safety**: Escalation paths always lead to human professionals, never to an AI endpoint.
- **Informed Consent**: Patients are clearly informed of what data is collected, how it is used, and who can see it.

### Technical Priorities
- **Data Isolation**: Strict patient-therapist access controls; no cross-patient data leakage.
- **Privacy First**: End-to-end encryption and local data processing where possible.
- **Cultural Sensitivity**: Designed for the Indian youth context — language, stigma awareness, and relevant stressor categories.
- **Scalability**: Cloud-native architecture to support growing clinic and NGO deployments.
- **Reliability**: Comprehensive error handling and graceful degradation, especially critical for crisis pathways.

---

*MyMindSpace is a clinical support tool. It is not a substitute for professional mental health care.*  
*If you or someone you know is in crisis, please contact iCall (+91-9152987821) or the Vandrevala Foundation Helpline (1860-2662-345).*