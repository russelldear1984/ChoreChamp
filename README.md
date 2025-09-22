# Chore Champions 🏆

A playful, gamified task management web application designed for families with children. Help kids complete daily chores and behaviors by rewarding them with XP points, levels, streaks, and weekly pocket money payouts!

## Features

### For Kids (Martha & Betsy)
- 🎮 **Gamified Experience**: Complete tasks to earn XP and level up
- 🔥 **Streak System**: Build consecutive day streaks for bonus motivation  
- 🏆 **Badge Collection**: Earn special badges for achievements
- 🎉 **Celebrations**: Confetti animations and praise messages for completions
- 👥 **Sibling Competition**: See your sibling's progress and compete friendly
- 💰 **Pocket Money**: Earn weekly payouts based on task completion

### For Parents
- 📋 **Task Management**: Create and manage the family task catalog
- 📊 **Progress Tracking**: Monitor children's weekly progress and completion rates
- 💷 **Payout Configuration**: Set reward amounts and completion thresholds
- 🔒 **Simple Authentication**: PIN-based access to admin features
- 📈 **Weekly Summaries**: Review past performance and payouts

## Quick Start on Replit

1. **Fork this Repl** or import the code into a new Python Repl

2. **Install Dependencies** (should happen automatically):
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   Click the "Run" button or execute:
   ```bash
   python main.py
   ```

4. **Access the App**:
   - The app will be available at the Replit-provided URL
   - Default parent PIN: `1234`

## Project Structure

```
chore-champions/
├── main.py              # Flask application and routes
├── models.py            # SQLAlchemy database models
├── services.py          # Business logic (scoring, badges, etc.)
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── templates/          # Jinja2 HTML templates
│   ├── base.html       # Base template with common styling
│   ├── index.html      # Login/selection page
│   ├── kid_dashboard.html    # Child dashboard
│   ├── parent_dashboard.html # Parent admin interface
│   └── parent_login.html     # Parent PIN entry
└── chore_champions.db  # SQLite database (created automatically)
```

## Game Mechanics

### XP & Levels
- Earn XP points by completing tasks
- Level up every 50 XP
- Each task has configurable XP value

### Streaks 🔥
- Complete at least one required daily task to maintain streak
- Streaks reset if a day is missed
- Special "Streak Star" badge at 5 days

### Badges 🏆
- **Morning Hero** 🥇: Complete 3 tasks before 9 AM
- **All-Green Day** 💯: Complete all required tasks for the day
- **Streak Star** 🌟: Maintain a 5-day streak
- **Tidy Master** 🧹: Complete "Tidy Room" 10 times

### Weekly Payouts 💰
- **Full Payout**: £3.00 if all required tasks completed
- **Tiered Rewards**: Partial payouts based on point thresholds
  - 40+ points: £2.00
  - 25+ points: £1.00

## Default Tasks

The app comes with sample tasks for both children:

### Daily Tasks
- Make Bed (5 XP, required, streakable)
- Brush Teeth AM (3 XP, required, streakable)  
- Brush Teeth PM (3 XP, required, streakable)
- Homework (8 XP, required, weekdays only)

### Behavior Tasks
- Be Kind to Sibling (5 XP, streakable)

### Weekly Tasks
- Tidy Room (15 XP, required, Sundays)

## Configuration

### Parent Settings
- Access admin dashboard with PIN (default: 1234)
- Modify payout amounts and thresholds
- Add, edit, or remove tasks
- Close weeks manually and view summaries

### Environment Variables
- `SESSION_SECRET`: Flask session secret key (optional, has default)

## Database

Uses SQLite for simplicity and portability. The database includes:
- **Children**: Martha (🦊) and Betsy (🐣) with XP, levels, streaks
- **Tasks**: Configurable chores with categories, XP values, and schedules
- **Completions**: Track when tasks are completed with timestamps
- **Badges**: Achievement system with earned dates
- **Week Summaries**: Historical payout and performance data
- **Settings**: App configuration including payout rules

## Important Notes for Replit

⚠️ **Free Tier Sleep Mode**: Replit free tier apps go to sleep when idle. The app automatically initializes data on startup, but any active sessions will be lost.

🔄 **Manual Week Closure**: While the app could auto-close weeks, manual closure via the parent dashboard ensures reliable operation on Replit's platform.

## Technology Stack

- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: SQLite (file-based, no external dependencies)
- **Frontend**: HTML5, Vanilla JavaScript, TailwindCSS
- **Animations**: Canvas Confetti library for celebrations
- **Mobile**: Responsive design, mobile-first approach

## Security Notes

⚠️ This is designed for family use with simple PIN authentication. For production deployment beyond Replit, consider:
- Configurable session secrets
- HTTPS enforcement  
- CSRF protection
- Input validation hardening

## License

This project is for educational and family use. Feel free to modify and adapt for your family's needs!

---

Built with ❤️ for families who want to make chores fun! 🎮✨