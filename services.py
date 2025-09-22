from datetime import datetime, date, timedelta
from decimal import Decimal
import random
from models import Task, TaskCompletion, Badge, WeekSummary, Settings, get_or_create_settings

# Praise messages for task completion
PRAISE_MESSAGES = [
    "Superstar! 🌟",
    "Level up! 🚀", 
    "Nice streak! 🔥",
    "Amazing work! ✨",
    "Champion! 🏆",
    "Fantastic! 🎉",
    "Well done! 👏",
    "Excellent! 💫",
    "Outstanding! 🌈",
    "Brilliant! 💎"
]

def get_random_praise():
    """Get a random praise message"""
    return random.choice(PRAISE_MESSAGES)

def calculate_level(xp):
    """Calculate level based on XP (50 XP per level)"""
    return (xp // 50) + 1

def update_child_level(child):
    """Update child's level based on current XP"""
    new_level = calculate_level(child.xp)
    child.level = new_level
    return new_level

def get_week_start_date(target_date=None):
    """Get the Monday of the current week"""
    if target_date is None:
        target_date = date.today()
    
    # Calculate days since Monday (0=Monday, 6=Sunday)
    days_since_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_since_monday)
    return week_start

def update_streak(session, child, completion_date):
    """Update child's streak based on task completion"""
    # Get required daily tasks
    weekday = completion_date.weekday()
    required_daily_tasks = session.query(Task).filter(
        Task.category == 'DAILY',
        Task.is_required == True
    ).all()
    
    # Filter tasks active today
    active_required_tasks = [t for t in required_daily_tasks if t.is_active_today(weekday)]
    
    if not active_required_tasks:
        # No required tasks today, don't update streak
        return
    
    # Check if child completed at least one required task today
    completed_today = session.query(TaskCompletion).filter(
        TaskCompletion.child_id == child.id,
        TaskCompletion.date == completion_date,
        TaskCompletion.approved == True
    ).join(Task).filter(
        Task.category == 'DAILY',
        Task.is_required == True
    ).count()
    
    if completed_today > 0:
        # Check streak continuation
        yesterday = completion_date - timedelta(days=1)
        
        # If this is the first completion or yesterday had completions, continue streak
        if child.last_completion_date is None:
            child.streak_count = 1
        elif child.last_completion_date == yesterday:
            child.streak_count += 1
        elif child.last_completion_date < yesterday:
            # Gap in streak, reset
            child.streak_count = 1
        # If last_completion_date is today, don't change streak (already counted)
        
        child.last_completion_date = completion_date

def check_and_award_badges(session, child, task, completion_date):
    """Check and award badges based on task completion"""
    badges_earned = []
    
    # Check Morning Hero badge (3 tasks before 9 AM)
    if completion_date == date.today():
        morning_cutoff = datetime.combine(completion_date, datetime.min.time().replace(hour=9))
        morning_completions = session.query(TaskCompletion).filter(
            TaskCompletion.child_id == child.id,
            TaskCompletion.date == completion_date,
            TaskCompletion.timestamp < morning_cutoff,
            TaskCompletion.approved == True
        ).count()
        
        if morning_completions >= 3:
            if not session.query(Badge).filter(
                Badge.child_id == child.id,
                Badge.name == "Morning Hero"
            ).first():
                badge = Badge(
                    child_id=child.id,
                    name="Morning Hero",
                    emoji="🥇",
                    description="Completed 3 tasks before 9 AM",
                    earned_date=completion_date
                )
                session.add(badge)
                badges_earned.append("Morning Hero 🥇")
    
    # Check All-Green Day badge (all required tasks for today)
    weekday = completion_date.weekday()
    required_tasks_today = session.query(Task).filter(
        Task.category.in_(['DAILY', 'WEEKLY']),
        Task.is_required == True
    ).all()
    
    active_required_today = [t for t in required_tasks_today if t.is_active_today(weekday)]
    
    if active_required_today:
        completed_required_today = session.query(TaskCompletion).filter(
            TaskCompletion.child_id == child.id,
            TaskCompletion.date == completion_date,
            TaskCompletion.approved == True
        ).join(Task).filter(
            Task.category.in_(['DAILY', 'WEEKLY']),
            Task.is_required == True
        ).count()
        
        if completed_required_today >= len(active_required_today):
            if not session.query(Badge).filter(
                Badge.child_id == child.id,
                Badge.name == "All-Green Day",
                Badge.earned_date == completion_date
            ).first():
                badge = Badge(
                    child_id=child.id,
                    name="All-Green Day",
                    emoji="💯",
                    description="Completed all required tasks for the day",
                    earned_date=completion_date
                )
                session.add(badge)
                badges_earned.append("All-Green Day 💯")
    
    # Check Streak Star badge (5 day streak)
    if child.streak_count >= 5:
        if not session.query(Badge).filter(
            Badge.child_id == child.id,
            Badge.name == "Streak Star"
        ).first():
            badge = Badge(
                child_id=child.id,
                name="Streak Star",
                emoji="🌟",
                description="Maintained a 5-day streak",
                earned_date=completion_date
            )
            session.add(badge)
            badges_earned.append("Streak Star 🌟")
    
    # Check Tidy Master badge (10 "Tidy Room" completions)
    if task.name == "Tidy Room":
        tidy_count = session.query(TaskCompletion).filter(
            TaskCompletion.child_id == child.id,
            TaskCompletion.approved == True
        ).join(Task).filter(
            Task.name == "Tidy Room"
        ).count()
        
        if tidy_count >= 10:
            if not session.query(Badge).filter(
                Badge.child_id == child.id,
                Badge.name == "Tidy Master"
            ).first():
                badge = Badge(
                    child_id=child.id,
                    name="Tidy Master",
                    emoji="🧹",
                    description="Completed 'Tidy Room' 10 times",
                    earned_date=completion_date
                )
                session.add(badge)
                badges_earned.append("Tidy Master 🧹")
    
    session.commit()
    return badges_earned

def calculate_weekly_payout(session, child_id, week_start):
    """Calculate payout for a child for a specific week"""
    settings = get_or_create_settings(session)
    
    # Get all completions for the week
    week_end = week_start + timedelta(days=6)
    completions = session.query(TaskCompletion).filter(
        TaskCompletion.child_id == child_id,
        TaskCompletion.date >= week_start,
        TaskCompletion.date <= week_end,
        TaskCompletion.approved == True
    ).all()
    
    # Calculate total points
    total_points = sum(c.task.points for c in completions)
    
    # Check if all required tasks for the week are completed
    required_tasks = session.query(Task).filter(
        Task.is_required == True
    ).all()
    
    all_required_completed = True
    for day_offset in range(7):
        check_date = week_start + timedelta(days=day_offset)
        weekday = check_date.weekday()
        
        # Get required tasks for this day
        required_for_day = [t for t in required_tasks if t.is_active_today(weekday)]
        
        if required_for_day:
            # Check if all required tasks for this day are completed
            completed_for_day = session.query(TaskCompletion).filter(
                TaskCompletion.child_id == child_id,
                TaskCompletion.date == check_date,
                TaskCompletion.approved == True
            ).join(Task).filter(
                Task.is_required == True
            ).count()
            
            if completed_for_day < len(required_for_day):
                all_required_completed = False
                break
    
    # Calculate payout
    if all_required_completed:
        payout = settings.full_payout_amount
    else:
        # Find highest threshold met
        thresholds = settings.get_threshold_rules()
        payout = Decimal('0.00')
        
        # Ensure thresholds is a list before sorting
        if isinstance(thresholds, list):
            for threshold in sorted(thresholds, key=lambda x: x['min_points'], reverse=True):
                if total_points >= threshold['min_points']:
                    payout = Decimal(str(threshold['amount']))
                    break
    
    return {
        'total_points': total_points,
        'all_required_completed': all_required_completed,
        'payout': payout
    }

def close_week_for_all_children(session):
    """Close the current week for all children and calculate payouts"""
    from models import Child  # Import here to avoid circular imports
    
    week_start = get_week_start_date()
    children = session.query(Child).all()
    results = []
    
    for child in children:
        # Check if week summary already exists
        existing = session.query(WeekSummary).filter(
            WeekSummary.child_id == child.id,
            WeekSummary.week_start_date == week_start
        ).first()
        
        if existing:
            continue  # Week already closed for this child
        
        # Calculate payout
        payout_data = calculate_weekly_payout(session, child.id, week_start)
        
        # Create week summary
        summary = WeekSummary(
            week_start_date=week_start,
            child_id=child.id,
            total_points=payout_data['total_points'],
            required_tasks_completed=payout_data['all_required_completed'],
            payout_amount=payout_data['payout']
        )
        
        session.add(summary)
        
        results.append({
            'child_id': child.id,
            'child_name': child.name,
            'total_points': payout_data['total_points'],
            'all_required_completed': payout_data['all_required_completed'],
            'payout': float(payout_data['payout'])
        })
    
    session.commit()
    return results