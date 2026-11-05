# FaceAttend

FaceAttend is a face-recognition attendance manager with a Streamlit dashboard. It stores student, period, and attendance records in a local SQLite database.

## Requirements

- Python **3.11** (recommended; use it for the virtual environment)
- A webcam for registering student faces and taking attendance

## Setup on Windows

Open PowerShell in the project folder and run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `py -3.11` is not recognized, install Python 3.11 and make sure the Python launcher is available. If PowerShell blocks environment activation, you can run the app and install packages through the virtual environment directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

## Start the dashboard

With the virtual environment activated, run:

```powershell
streamlit run dashboard.py
```

Streamlit opens the dashboard in your browser, usually at `http://localhost:8501`. Keep the terminal running while you use it; press `Ctrl+C` there to stop the dashboard.

## Using the dashboard

Use the sidebar to move between pages:

- **Overview** — See attendance and student summaries, the weekly trend, and recent activity.
- **Students** — Register a student with their name and roll number. The app uses the webcam to capture face samples and trains the recognition model. You can also search, edit, deactivate/reactivate, or re-register a student's face.
- **Periods** — Create a period by entering a subject and duration, then start attendance and open the camera for that period.
- **Attendance** — Review and filter attendance records, then download available attendance data.
- **Analytics** — Explore attendance statistics and trends.
- **Reports** — Review period and student summaries and download reports.

For a typical first run, open **Students** and register students in good lighting, then open **Periods** to create a class period and start attendance. Keep the webcam connected and allow camera access if prompted. Once attendance is complete, use **Attendance**, **Analytics**, or **Reports** to review the results.

## Local data

The SQLite database is stored at `database/attendance.db`. Face samples are stored under `data/`, and the recognition model is stored under `models/`. Back up these folders if you need to preserve your records and trained face data. Treat face images and attendance records as sensitive personal information.
