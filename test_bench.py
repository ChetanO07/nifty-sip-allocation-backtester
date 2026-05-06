import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from main import build_report_project2
from project2_asset_allocation import load_config as project2_load_config

config = project2_load_config()

report = build_report_project2(config)
print("benchmark_stats in report:", "benchmark_stats" in report)
if "benchmark_stats" in report:
    print(report["benchmark_stats"])
else:
    print("NO BENCHMARK STATS")
