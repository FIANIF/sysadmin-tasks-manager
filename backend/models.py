from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='operator')  # admin, operator, viewer
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tasks = db.relationship('Task', backref='creator', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Task(db.Model):
    """Модель регламентной задачи"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    task_type = db.Column(db.String(50), nullable=False)  # disk_check, memory_check, backup, log_cleanup, service_health, system_update, security_check
    schedule = db.Column(db.String(100), nullable=False)  # cron expression
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    # Параметры задачи
    params = db.Column(db.JSON, default={})
    
    # Уведомления
    notify_on_success = db.Column(db.Boolean, default=False)
    notify_on_failure = db.Column(db.Boolean, default=True)
    notification_channels = db.Column(db.JSON, default=['email'])  # email, telegram, slack
    
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    executions = db.relationship('TaskExecution', backref='task', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Task {self.name}>'

class TaskExecution(db.Model):
    """Модель выполнения задачи"""
    __tablename__ = 'task_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, running, success, failed, warning
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # seconds
    
    # Результат
    result_data = db.Column(db.JSON)  # Данные результата
    output = db.Column(db.Text)  # Лог вывода
    error_message = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TaskExecution {self.task_id} - {self.status}>'

class SystemMetrics(db.Model):
    """Модель системных метрик"""
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # CPU
    cpu_percent = db.Column(db.Float)
    cpu_count = db.Column(db.Integer)
    
    # Memory
    memory_total = db.Column(db.Float)  # GB
    memory_used = db.Column(db.Float)  # GB
    memory_percent = db.Column(db.Float)
    
    # Disk
    disk_total = db.Column(db.Float)  # GB
    disk_used = db.Column(db.Float)  # GB
    disk_percent = db.Column(db.Float)
    
    # Network
    network_bytes_sent = db.Column(db.Float)
    network_bytes_recv = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<SystemMetrics {self.created_at}>'

class Notification(db.Model):
    """Модель уведомления"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    task_execution_id = db.Column(db.Integer, db.ForeignKey('task_executions.id'))
    
    channel = db.Column(db.String(20), nullable=False)  # email, telegram, slack
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255))
    message = db.Column(db.Text, nullable=False)
    
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    sent_at = db.Column(db.DateTime)
    error = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.channel} - {self.status}>'

class AuditLog(db.Model):
    """Модель журнала аудита"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action} - {self.created_at}>'
