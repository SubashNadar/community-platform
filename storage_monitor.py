import schedule
import time
import logging
from app.storage_manager import storage_manager

def monitor_storage():
    """Monitor storage usage and send alerts"""
    usage = storage_manager.check_storage_usage()
    
    logging.info(f"Storage Usage: {usage['usage_percentage']:.1f}%")
    
    if usage['usage_percentage'] >= 95:
        logging.critical("Storage critically full!")
        if storage_manager.current_bucket_index < storage_manager.max_buckets:
            storage_manager.extend_storage()
        else:
            storage_manager._send_critical_alert(
                "Maximum storage capacity reached! Manual intervention required."
            )
    elif usage['usage_percentage'] >= 80:
        logging.warning("Storage usage high")
        storage_manager._send_storage_extended_notification()

def run_monitoring():
    """Run storage monitoring"""
    schedule.every(1).hours.do(monitor_storage)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_monitoring()