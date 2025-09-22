from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from datetime import datetime, date, timedelta
from decimal import Decimal
import pytz
import json
import os

from models import (
    create_database, get_or_create_settings,
    Child, Task, TaskCompletion, Badge, WeekSummary, Settings
)
from services import (
    calculate_level, update_child_level, check_and_award_badges,
    update_streak, calculate_weekly_payout, get_week_start_date,
    close_week_for_all_children, get_random_praise
)

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'chore-champions-secret-key')
CORS(app)

# Initialize database
engine, Session = create_database()

def get_session():
    return Session()

def init_seed_data():
    """Initialize seed data if database is empty"""
    session = get_session()
    try:
        # Check if children already exist
        if session.query(Child).count() > 0:
            return
        
        # Create children
        martha = Child(
            name="Martha",
            avatar="🦊",
            color="indigo",
            xp=0,
            level=1,
            streak_count=0
        )
        
        betsy = Child(
            name="Betsy",
            avatar="🐣",
            color="emerald",
            xp=0,
            level=1,
            streak_count=0
        )
        
        session.add_all([martha, betsy])
        session.commit()
        
        # Create sample tasks
        tasks = [
            Task(
                name="Make Bed",
                description="Make your bed neatly every morning",
                points=5,
                category="DAILY",
                is_required=True,
                streakable=True,
                active_days=[0, 1, 2, 3, 4, 5, 6]  # Mon-Sun
            ),
            Task(
                name="Brush Teeth AM",
                description="Brush teeth in the morning",
                points=3,
                category="DAILY",
                is_required=True,
                streakable=True,
                active_days=[0, 1, 2, 3, 4, 5, 6]
            ),
            Task(
                name="Brush Teeth PM",
                description="Brush teeth before bed",
                points=3,
                category="DAILY",
                is_required=True,
                streakable=True,
                active_days=[0, 1, 2, 3, 4, 5, 6]
            ),
            Task(
                name="Homework",
                description="Complete daily homework assignments",
                points=8,
                category="DAILY",
                is_required=True,
                streakable=False,
                active_days=[0, 1, 2, 3, 4]  # Mon-Fri
            ),
            Task(
                name="Be Kind to Sibling",
                description="Show kindness and help your sibling",
                points=5,
                category="BEHAVIOUR",
                is_required=False,
                streakable=True,
                active_days=[0, 1, 2, 3, 4, 5, 6]
            ),
            Task(
                name="Tidy Room",
                description="Clean and organize your bedroom",
                points=15,
                category="WEEKLY",
                is_required=True,
                streakable=False,
                active_days=[6]  # Sunday
            )
        ]
        
        session.add_all(tasks)
        session.commit()
        
        # Create default settings
        get_or_create_settings(session)
        
        print("Seed data initialized successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error initializing seed data: {e}")
    finally:
        session.close()

# Routes
@app.route('/')
def index():
    """Login page with parent and child selection"""
    return render_template('index.html')

@app.route('/kid/<int:child_id>')
def kid_dashboard(child_id):
    """Child dashboard with today's quests and progress"""
    session_db = get_session()
    try:
        child = session_db.query(Child).get(child_id)
        if not child:
            return redirect(url_for('index'))
        
        # Get sibling for comparison
        sibling = session_db.query(Child).filter(Child.id != child_id).first()
        
        return render_template('kid_dashboard.html', child=child, sibling=sibling)
    finally:
        session_db.close()

@app.route('/parent')
def parent_dashboard():
    """Parent admin dashboard"""
    # Simple PIN check
    if not session.get('is_parent'):
        return redirect(url_for('parent_login'))
    
    return render_template('parent_dashboard.html')

@app.route('/parent/login', methods=['GET', 'POST'])
def parent_login():
    """Parent PIN verification"""
    if request.method == 'POST':
        pin = request.form.get('pin')
        session_db = get_session()
        try:
            settings = get_or_create_settings(session_db)
            if pin == settings.parent_pin:
                session['is_parent'] = True
                return redirect(url_for('parent_dashboard'))
            else:
                return render_template('parent_login.html', error="Invalid PIN")
        finally:
            session_db.close()
    
    return render_template('parent_login.html')

@app.route('/parent/logout')
def parent_logout():
    """Clear parent session"""
    session.pop('is_parent', None)
    return redirect(url_for('index'))

# API Routes
@app.route('/api/children')
def api_children():
    """Get all children with weekly stats"""
    session_db = get_session()
    try:
        children = session_db.query(Child).all()
        week_start = get_week_start_date()
        
        result = []
        for child in children:
            # Calculate weekly stats
            weekly_completions = session_db.query(TaskCompletion).filter(
                TaskCompletion.child_id == child.id,
                TaskCompletion.date >= week_start,
                TaskCompletion.approved == True
            ).all()
            
            weekly_points = sum(c.task.points for c in weekly_completions)
            
            result.append({
                'id': child.id,
                'name': child.name,
                'avatar': child.avatar,
                'color': child.color,
                'xp': child.xp,
                'level': child.current_level,
                'streak_count': child.streak_count,
                'weekly_points': weekly_points
            })
        
        return jsonify(result)
    finally:
        session_db.close()

@app.route('/api/tasks')
def api_tasks():
    """Get all tasks"""
    session_db = get_session()
    try:
        tasks = session_db.query(Task).all()
        result = []
        for task in tasks:
            result.append({
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'points': task.points,
                'category': task.category,
                'is_required': task.is_required,
                'streakable': task.streakable,
                'active_days': task.active_days
            })
        return jsonify(result)
    finally:
        session_db.close()

@app.route('/api/tasks/today')
def api_tasks_today():
    """Get today's tasks for a specific child"""
    child_id = request.args.get('child_id', type=int)
    if not child_id:
        return jsonify({'error': 'child_id required'}), 400
    
    session_db = get_session()
    try:
        today = date.today()
        weekday = today.weekday()  # 0=Monday, 6=Sunday
        
        # Get tasks active today
        tasks = session_db.query(Task).all()
        today_tasks = [t for t in tasks if t.is_active_today(weekday)]
        
        # Check which tasks are already completed today
        completed_today = session_db.query(TaskCompletion).filter(
            TaskCompletion.child_id == child_id,
            TaskCompletion.date == today,
            TaskCompletion.approved == True
        ).all()
        
        completed_task_ids = {c.task_id for c in completed_today}
        
        result = []
        for task in today_tasks:
            result.append({
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'points': task.points,
                'category': task.category,
                'is_required': task.is_required,
                'completed_today': task.id in completed_task_ids
            })
        
        return jsonify(result)
    finally:
        session_db.close()

@app.route('/api/completions', methods=['POST'])
def api_complete_task():
    """Complete a task for a child"""
    data = request.get_json()
    child_id = data.get('child_id')
    task_id = data.get('task_id')
    
    if not child_id or not task_id:
        return jsonify({'error': 'child_id and task_id required'}), 400
    
    session_db = get_session()
    try:
        child = session_db.query(Child).get(child_id)
        task = session_db.query(Task).get(task_id)
        
        if not child or not task:
            return jsonify({'error': 'Child or task not found'}), 404
        
        today = date.today()
        
        # Check if already completed today
        existing = session_db.query(TaskCompletion).filter(
            TaskCompletion.child_id == child_id,
            TaskCompletion.task_id == task_id,
            TaskCompletion.date == today
        ).first()
        
        if existing:
            return jsonify({'error': 'Task already completed today'}), 400
        
        # Create completion
        completion = TaskCompletion(
            child_id=child_id,
            task_id=task_id,
            date=today,
            timestamp=datetime.utcnow()
        )
        session_db.add(completion)
        
        # Update child XP
        child.xp += task.points
        
        # Update level
        old_level = child.level
        new_level = update_child_level(child)
        level_up = new_level > old_level
        
        # Update streak
        update_streak(session_db, child, today)
        
        session_db.commit()
        
        # Check for badges (after commit)
        badges_earned = check_and_award_badges(session_db, child, task, today)
        
        # Get praise message
        praise = get_random_praise()
        
        result = {
            'success': True,
            'praise': praise,
            'xp_gained': task.points,
            'total_xp': child.xp,
            'level': child.level,
            'level_up': level_up,
            'streak_count': child.streak_count,
            'badges_earned': badges_earned
        }
        
        return jsonify(result)
        
    except Exception as e:
        session_db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()

@app.route('/api/settings')
def api_settings():
    """Get current settings"""
    session_db = get_session()
    try:
        settings = get_or_create_settings(session_db)
        return jsonify({
            'full_payout_amount': str(settings.full_payout_amount),
            'threshold_rules': settings.get_threshold_rules(),
            'timezone': settings.timezone
        })
    finally:
        session_db.close()

@app.route('/api/tasks', methods=['POST'])
def api_create_task():
    """Create a new task"""
    if not session.get('is_parent'):
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    session_db = get_session()
    try:
        task = Task(
            name=data.get('name'),
            description=data.get('description', ''),
            points=data.get('points'),
            category=data.get('category'),
            is_required=data.get('is_required', False),
            streakable=data.get('streakable', False),
            active_days=data.get('active_days', [0, 1, 2, 3, 4, 5, 6])
        )
        
        session_db.add(task)
        session_db.commit()
        
        return jsonify({'success': True, 'task_id': task.id})
    except Exception as e:
        session_db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    """Delete a task"""
    if not session.get('is_parent'):
        return jsonify({'error': 'Admin access required'}), 403
    
    session_db = get_session()
    try:
        task = session_db.query(Task).get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Delete associated completions first
        session_db.query(TaskCompletion).filter(TaskCompletion.task_id == task_id).delete()
        session_db.delete(task)
        session_db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        session_db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()

@app.route('/api/settings', methods=['PATCH'])
def api_update_settings():
    """Update settings"""
    if not session.get('is_parent'):
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    session_db = get_session()
    try:
        settings = get_or_create_settings(session_db)
        
        if 'full_payout_amount' in data:
            settings.full_payout_amount = Decimal(str(data['full_payout_amount']))
        
        if 'threshold_rules' in data:
            settings.threshold_rules = data['threshold_rules']
        
        if 'parent_pin' in data:
            settings.parent_pin = data['parent_pin']
        
        session_db.commit()
        return jsonify({'success': True})
    except Exception as e:
        session_db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()

@app.route('/api/weeks/close', methods=['POST'])
def api_close_week():
    """Manually close the current week"""
    if not session.get('is_parent'):
        return jsonify({'error': 'Admin access required'}), 403
    
    session_db = get_session()
    try:
        results = close_week_for_all_children(session_db)
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        session_db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()

@app.route('/api/weeks/reset', methods=['POST'])
def reset_week():
    """Reset the current week - remove all completions and recalculate XP/levels"""
    if not session.get('is_parent'):
        return jsonify({'error': 'Admin access required'}), 403
    
    session_db = get_session()
    try:
        # Get current week start date
        week_start = get_week_start_date()
        
        # Get all completions from this week with proper joins
        this_week_completions = session_db.query(TaskCompletion).join(Task).filter(
            TaskCompletion.date >= week_start
        ).all()
        
        # Track changes for each child
        results = []
        for child in session_db.query(Child).all():
            # Calculate XP to remove for this child
            child_completions = [c for c in this_week_completions if c.child_id == child.id]
            xp_to_remove = sum(c.task.points for c in child_completions)
            
            # Store original stats
            original_level = child.level
            
            # Remove XP and recalculate level using proper service
            child.xp = max(0, child.xp - xp_to_remove)
            new_level = update_child_level(child)
            
            # Reset streak since we're clearing the week
            child.streak_count = 0
            child.last_completion_date = None
            
            results.append({
                'child_name': child.name,
                'xp_removed': xp_to_remove,
                'new_level': new_level,
                'level_changed': original_level != new_level
            })
        
        # Delete all completions from this week
        session_db.query(TaskCompletion).filter(
            TaskCompletion.date >= week_start
        ).delete()
        
        session_db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Week reset successfully',
            'results': results
        })
        
    except Exception as e:
        session_db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session_db.close()

@app.route('/api/completions/recent')
def get_recent_completions():
    """Get recent completions from the last 7 days"""
    if not session.get('is_parent'):
        return jsonify({'error': 'Admin access required'}), 403
    
    session_db = get_session()
    try:
        uk_tz = pytz.timezone('Europe/London')
        seven_days_ago = date.today() - timedelta(days=7)
        
        completions = session_db.query(TaskCompletion).join(Child).join(Task).filter(
            TaskCompletion.date >= seven_days_ago,
            TaskCompletion.approved == True
        ).order_by(TaskCompletion.timestamp.desc()).all()
        
        completion_data = []
        for completion in completions:
            # Convert UTC timestamp to UK timezone
            completion_time = completion.timestamp.replace(tzinfo=pytz.UTC).astimezone(uk_tz)
            completion_data.append({
                'id': completion.id,
                'child_id': completion.child_id,
                'child_name': completion.child.name,
                'child_avatar': completion.child.avatar,
                'task_name': completion.task.name,
                'points': completion.task.points,
                'date': completion_time.strftime('%d %b'),
                'time': completion_time.strftime('%H:%M'),
                'day_name': completion_time.strftime('%A')
            })
        
        return jsonify(completion_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()

@app.route('/api/completions/<int:completion_id>', methods=['DELETE'])
def delete_completion(completion_id):
    """Remove a specific task completion and recalculate child stats"""
    if not session.get('is_parent'):
        return jsonify({'error': 'Admin access required'}), 403
    
    session_db = get_session()
    try:
        # Find the completion
        completion = session_db.query(TaskCompletion).filter_by(id=completion_id).first()
        if not completion:
            return jsonify({'success': False, 'error': 'Completion not found'}), 404
        
        # Get child and original stats
        child = completion.child
        original_level = child.level
        points_to_remove = completion.task.points
        
        # Remove XP and recalculate level using proper service
        child.xp = max(0, child.xp - points_to_remove)
        new_level = update_child_level(child)
        
        # Check if we need to recalculate streaks
        # If this was a streakable required task, we may need to update streak
        completion_date = completion.date
        if completion.task.streakable and completion.task.is_required:
            # Find the most recent completion date after removing this one
            remaining_completions = session_db.query(TaskCompletion).filter(
                TaskCompletion.child_id == child.id,
                TaskCompletion.id != completion_id,
                TaskCompletion.approved == True
            ).order_by(TaskCompletion.date.desc()).first()
            
            if remaining_completions:
                child.last_completion_date = remaining_completions.date
                # Recalculate streak from scratch
                update_streak(session_db, child, remaining_completions.date)
            else:
                child.streak_count = 0
                child.last_completion_date = None
        
        # Delete the completion
        child_name = child.name
        session_db.delete(completion)
        session_db.commit()
        
        return jsonify({
            'success': True,
            'message': f'Task completion removed successfully',
            'child_name': child_name,
            'new_level': new_level,
            'level_changed': original_level != new_level,
            'xp_removed': points_to_remove
        })
        
    except Exception as e:
        session_db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session_db.close()

if __name__ == '__main__':
    # Initialize seed data on startup
    init_seed_data()
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)