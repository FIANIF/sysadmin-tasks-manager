from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_migrate import Migrate
import os
import logging
from datetime import datetime

from config import config
from models import db, User, Task, TaskExecution, SystemMetrics, Notification, AuditLog
from services.auth import AuthService
from tasks.system_tasks import SystemTasks
from utils.notifications import NotificationService
from utils.system_monitor import SystemMonitor
from utils.logger import TaskLogger

# Configuration
env = os.getenv('FLASK_ENV', 'development')
app = Flask(__name__)
app.config.from_object(config[env])

# Extensions
db.init_app(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)
CORS(app)

# Services
notification_service = NotificationService(app.config)
task_logger = TaskLogger(app.config['LOG_DIR'])

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = AuthService.register(username, email, password)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Missing username or password'}), 400
        
        result = AuthService.login(username, password)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change password"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Missing password fields'}), 400
        
        result = AuthService.change_password(user_id, old_password, new_password)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== TASKS ROUTES ====================

@app.route('/api/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get all tasks"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        tasks = Task.query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'tasks': [{
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'task_type': task.task_type,
                'schedule': task.schedule,
                'is_active': task.is_active,
                'priority': task.priority,
                'created_at': task.created_at.isoformat()
            } for task in tasks.items],
            'total': tasks.total,
            'pages': tasks.pages,
            'current_page': page
        }), 200
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """Get task by ID"""
    try:
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify({
            'id': task.id,
            'name': task.name,
            'description': task.description,
            'task_type': task.task_type,
            'schedule': task.schedule,
            'is_active': task.is_active,
            'priority': task.priority,
            'params': task.params,
            'notify_on_success': task.notify_on_success,
            'notify_on_failure': task.notify_on_failure,
            'notification_channels': task.notification_channels,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting task: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
@jwt_required()
def create_task():
    """Create new task"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        task = Task(
            name=data.get('name'),
            description=data.get('description'),
            task_type=data.get('task_type'),
            schedule=data.get('schedule'),
            is_active=data.get('is_active', True),
            priority=data.get('priority', 'medium'),
            params=data.get('params', {}),
            notify_on_success=data.get('notify_on_success', False),
            notify_on_failure=data.get('notify_on_failure', True),
            notification_channels=data.get('notification_channels', ['email']),
            creator_id=user_id
        )
        
        db.session.add(task)
        db.session.commit()
        
        logger.info(f"Task created: {task.name}")
        
        return jsonify({
            'message': 'Task created successfully',
            'task_id': task.id
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating task: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update task"""
    try:
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json()
        
        task.name = data.get('name', task.name)
        task.description = data.get('description', task.description)
        task.schedule = data.get('schedule', task.schedule)
        task.is_active = data.get('is_active', task.is_active)
        task.priority = data.get('priority', task.priority)
        task.params = data.get('params', task.params)
        task.notify_on_success = data.get('notify_on_success', task.notify_on_success)
        task.notify_on_failure = data.get('notify_on_failure', task.notify_on_failure)
        task.notification_channels = data.get('notification_channels', task.notification_channels)
        
        db.session.commit()
        
        logger.info(f"Task updated: {task.name}")
        
        return jsonify({'message': 'Task updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating task: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Delete task"""
    try:
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        db.session.delete(task)
        db.session.commit()
        
        logger.info(f"Task deleted: {task.name}")
        
        return jsonify({'message': 'Task deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting task: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== SYSTEM METRICS ROUTES ====================

@app.route('/api/metrics/system', methods=['GET'])
@jwt_required()
def get_system_metrics():
    """Get system metrics"""
    try:
        cpu_info = SystemMonitor.get_cpu_info()
        memory_info = SystemMonitor.get_memory_info()
        disk_info = SystemMonitor.get_disk_info()
        network_info = SystemMonitor.get_network_info()
        system_info = SystemMonitor.get_system_info()
        
        return jsonify({
            'cpu': cpu_info,
            'memory': memory_info,
            'disk': disk_info,
            'network': network_info,
            'system': system_info
        }), 200
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/disk-partitions', methods=['GET'])
@jwt_required()
def get_disk_partitions():
    """Get disk partitions"""
    try:
        partitions = SystemMonitor.get_disk_partitions()
        return jsonify({'partitions': partitions}), 200
    except Exception as e:
        logger.error(f"Error getting disk partitions: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

@app.route('/api/health', methods=['GET'])
def api_health():
    """API health check"""
    return jsonify({'status': 'ok', 'service': 'SysAdmin Tasks Manager'}), 200

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        logger.info("Database initialized")

if __name__ == '__main__':
    init_db()
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
