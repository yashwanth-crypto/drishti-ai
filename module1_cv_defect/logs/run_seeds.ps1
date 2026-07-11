Set-Location C:\dev\drishti-ai\module1_cv_defect
& ..\.venv\Scripts\python.exe -u src\train_proper.py --seed 1 --out models\casting_mobilenetv2_proper.pt *> logs\proper_seed1.log
& ..\.venv\Scripts\python.exe -u src\train_proper.py --seed 2 --out models\casting_mobilenetv2_proper.pt *> logs\proper_seed2.log
