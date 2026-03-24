import time
import datetime
from plyer import notification
import database

def check_notifications():
    while True:
        try:
            tasks = database.get_pending_tasks_to_notify()
            now = datetime.datetime.now()

            for task in tasks:
                task_id, name, priority, start_datetime_str, repeat_days = task
                start_datetime = datetime.datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")

                if now >= start_datetime:
                    # Time has come or passed
                    try:
                        notification.notify(
                            title=f"Recordatorio de Tarea - {priority}",
                            message=f"{name}",
                            app_name="AgendaApp",
                            timeout=10
                        )
                    except Exception as e:
                        print(f"Error al enviar notificacion: {e}")

                    if repeat_days > 0:
                        database.complete_task(task_id)
                    else:
                        database.update_last_notified(task_id, start_datetime_str)

        except Exception as e:
            print(f"Error in notification thread: {e}")

        # Check every 30 seconds
        time.sleep(30)
