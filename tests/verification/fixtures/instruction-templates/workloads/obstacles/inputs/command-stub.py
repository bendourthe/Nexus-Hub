import pathlib, sys, time

marker = pathlib.Path(__file__).with_name(".stub-called")
if not marker.exists():
    marker.write_text("1")
    time.sleep(3600)
print("stub-output: 42 records")
