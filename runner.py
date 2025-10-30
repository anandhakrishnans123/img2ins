from schedule import every, repeat, run_pending
import time
import os

@repeat(every().day.at("12:47"))
def run_main():
    os.system("python C:/Users/USER/Desktop/FMH_Aud2Ins_GraphQl_S3/main.py")

while True:
    run_pending()
    time.sleep(60)
