from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import time
from datetime import timezone
import os
import subprocess
import sys

CRON_TRIGGER = os.getenv("CRON_TRIGGER", "0 0 * * *")


def run_update() -> None:
    # Run main.py with the same interpreter, without a shell.
    subprocess.run([sys.executable, "main.py"], check=False)


def my_task():
    print("CRON task：", time.strftime("%Y-%m-%d %H:%M:%S"), flush=True)
    run_update()


# 创建一个调度器
scheduler = BlockingScheduler()

# 使用CronTrigger来定义Cron表达式
try:
    cron_trigger = CronTrigger.from_crontab(CRON_TRIGGER, timezone.utc)
except ValueError as exc:
    print(f"!!!Invalid CRON_TRIGGER {CRON_TRIGGER!r}: {exc}!!!")
    sys.exit(1)

# 添加任务和触发器
scheduler.add_job(my_task, cron_trigger)

# 启动调度器
print("Run first update...", flush=True)
run_update()
print(f"Start scheduler with cron trigger: {CRON_TRIGGER}", flush=True)
scheduler.start()
