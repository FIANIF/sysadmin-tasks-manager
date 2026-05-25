import logging
import os
from datetime import datetime

class TaskLogger:
    """Кастомный логгер для задач"""
    
    def __init__(self, log_dir='logs'):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
    
    def get_logger(self, task_name):
        """Получить логгер для задачи"""
        logger = logging.getLogger(task_name)
        logger.setLevel(logging.DEBUG)
        
        # File handler
        log_file = os.path.join(self.log_dir, f"{task_name}_{datetime.now().strftime('%Y%m%d')}.log")
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    @staticmethod
    def get_task_log_file(task_name, log_dir='logs'):
        """Получить путь к логу задачи"""
        log_file = os.path.join(log_dir, f"{task_name}_{datetime.now().strftime('%Y%m%d')}.log")
        return log_file
