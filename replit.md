# Chore Champions

## Overview

Chore Champions is a gamified task management web application designed for families with children. The app helps kids complete daily chores and behaviors by rewarding them with XP points, levels, streaks, and weekly pocket money payouts. Built with a playful, kid-friendly interface featuring confetti animations, badges, and colorful avatars, it transforms mundane household tasks into engaging quests.

The application supports two primary user roles: children (Martha and Betsy) who complete tasks and earn rewards, and parents who manage the task catalog, configure payout rules, and monitor progress through an admin dashboard.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology Stack**: HTML templates with Vanilla JavaScript and TailwindCSS via CDN
- **Design Philosophy**: Mobile-first responsive design with bright, fun aesthetics
- **Interactive Elements**: Canvas-confetti library for celebration animations, custom CSS animations for streaks and level-ups
- **Template Engine**: Jinja2 templates extending a base layout for consistent UI structure

### Backend Architecture
- **Framework**: Python Flask with minimal complexity for rapid development
- **Session Management**: Flask sessions with configurable secret key for parent authentication
- **API Design**: RESTful endpoints serving both HTML pages and JSON responses
- **Business Logic**: Separated into service layer (`services.py`) handling XP calculations, streak tracking, badge awards, and weekly payouts

### Data Storage Architecture
- **Database**: SQLite with SQLAlchemy ORM for simplicity and portability
- **Schema Design**: 
  - Core entities: Child, Task, TaskCompletion, Badge, WeekSummary, Settings
  - Relationship modeling: One-to-many between Child and completions/badges
  - JSON columns for flexible data like active_days and threshold_rules
- **Indexing Strategy**: Optimized queries on TaskCompletion by child_id and date

### Authentication & Authorization
- **Parent Access**: PIN-based authentication (default: 1234) with session storage
- **Child Access**: Simple avatar/name selection without passwords for MVP simplicity
- **Security Model**: Minimal authentication suitable for family use, with approval system for task completions

### Game Mechanics Architecture
- **XP System**: Linear progression with 50 XP per level
- **Streak Tracking**: Consecutive day completion of required daily tasks
- **Badge System**: Event-driven awards triggered by completion actions
- **Payout Calculation**: Tiered reward system with full payout for 100% completion and threshold-based partial payouts

## External Dependencies

### Core Dependencies
- **Flask 2.3.3**: Web framework for routing and request handling
- **SQLAlchemy 2.0.23**: ORM for database operations and schema management
- **Flask-CORS 4.0.0**: Cross-origin request handling for API endpoints
- **pytz 2023.3**: Timezone handling for completion timestamps

### Frontend Libraries
- **TailwindCSS**: Utility-first CSS framework loaded via CDN for responsive design
- **Canvas-Confetti 1.6.0**: JavaScript library for celebration animations on task completion

### Infrastructure
- **SQLite**: File-based database for data persistence (no external database server required)
- **Replit Environment**: Designed for deployment on Replit's free tier with considerations for sleep mode

### Configuration
- **Environment Variables**: SESSION_SECRET for Flask session security
- **Default Settings**: Configurable parent PIN, payout amounts, and timezone settings stored in database