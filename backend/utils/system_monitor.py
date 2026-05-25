import psutil
import platform
import shutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Класс для мониторинга системных ресурсов"""
    
    @staticmethod
    def get_cpu_info():
        """Получить информацию о CPU"""
        try:
            return {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'count_logical': psutil.cpu_count(logical=True),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }
        except Exception as e:
            logger.error(f"Error getting CPU info: {str(e)}")
            return None
    
    @staticmethod
    def get_memory_info():
        """Получить информацию о памяти"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total': round(memory.total / (1024**3), 2),  # GB
                'used': round(memory.used / (1024**3), 2),  # GB
                'available': round(memory.available / (1024**3), 2),  # GB
                'percent': memory.percent,
                'free': round(memory.free / (1024**3), 2)  # GB
            }
        except Exception as e:
            logger.error(f"Error getting memory info: {str(e)}")
            return None
    
    @staticmethod
    def get_disk_info(path='/'):
        """Получить информацию о диске"""
        try:
            disk = shutil.disk_usage(path)
            return {
                'total': round(disk.total / (1024**3), 2),  # GB
                'used': round(disk.used / (1024**3), 2),  # GB
                'free': round(disk.free / (1024**3), 2),  # GB
                'percent': (disk.used / disk.total) * 100 if disk.total > 0 else 0,
                'path': path
            }
        except Exception as e:
            logger.error(f"Error getting disk info for {path}: {str(e)}")
            return None
    
    @staticmethod
    def get_disk_partitions():
        """Получить информацию о всех разделах диска"""
        try:
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    disk_usage = shutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': round(disk_usage.total / (1024**3), 2),
                        'used': round(disk_usage.used / (1024**3), 2),
                        'free': round(disk_usage.free / (1024**3), 2),
                        'percent': (disk_usage.used / disk_usage.total) * 100 if disk_usage.total > 0 else 0
                    })
                except:
                    pass
            return partitions
        except Exception as e:
            logger.error(f"Error getting disk partitions: {str(e)}")
            return []
    
    @staticmethod
    def get_network_info():
        """Получить информацию о сети"""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errin': net_io.errin,
                'errout': net_io.errout,
                'dropin': net_io.dropin,
                'dropout': net_io.dropout
            }
        except Exception as e:
            logger.error(f"Error getting network info: {str(e)}")
            return None
    
    @staticmethod
    def get_system_info():
        """Получить общую информацию о системе"""
        try:
            return {
                'system': platform.system(),
                'node': platform.node(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return None
    
    @staticmethod
    def check_disk_space(warning_percent=80, critical_percent=90):
        """Проверить дисковое пространство"""
        try:
            partitions = SystemMonitor.get_disk_partitions()
            result = {
                'status': 'ok',
                'partitions': []
            }
            
            for partition in partitions:
                partition_status = 'ok'
                if partition['percent'] >= critical_percent:
                    partition_status = 'critical'
                    result['status'] = 'critical'
                elif partition['percent'] >= warning_percent:
                    partition_status = 'warning'
                    if result['status'] != 'critical':
                        result['status'] = 'warning'
                
                partition['partition_status'] = partition_status
                result['partitions'].append(partition)
            
            return result
        except Exception as e:
            logger.error(f"Error checking disk space: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def check_memory(warning_percent=80, critical_percent=90):
        """Проверить память"""
        try:
            mem_info = SystemMonitor.get_memory_info()
            status = 'ok'
            
            if mem_info['percent'] >= critical_percent:
                status = 'critical'
            elif mem_info['percent'] >= warning_percent:
                status = 'warning'
            
            mem_info['status'] = status
            return mem_info
        except Exception as e:
            logger.error(f"Error checking memory: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def check_cpu(warning_percent=80, critical_percent=90):
        """Проверить CPU"""
        try:
            cpu_info = SystemMonitor.get_cpu_info()
            status = 'ok'
            
            if cpu_info['percent'] >= critical_percent:
                status = 'critical'
            elif cpu_info['percent'] >= warning_percent:
                status = 'warning'
            
            cpu_info['status'] = status
            return cpu_info
        except Exception as e:
            logger.error(f"Error checking CPU: {str(e)}")
            return {'status': 'error', 'message': str(e)}
