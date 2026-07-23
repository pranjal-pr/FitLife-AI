# AI Fit Pro Project - Setup and Run Guide

## Quick Start (Already Set Up)

If the virtual environment is already created and dependencies are installed, simply run:

```powershell
.\run.ps1
```

Then open your browser to: **http://127.0.0.1:5000**

---

## First Time Setup

### 1. Create Virtual Environment

```powershell
py -3.14 -m venv venv
```

### 2. Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

**Note:** If you encounter issues with `scikit-image` (common with Python 3.14), the EasyOCR module has been patched to use `imageio` instead. This patch is located at:
- `venv\Lib\site-packages\easyocr\imgproc.py`

### 4. Run the Application

```powershell
python app.py
```

Or use the convenience script:

```powershell
.\run.ps1
```

---

## Project Structure

This project contains two main applications:

### 1. Health-O-Meter
- **Path:** `/fitlife_data/`
- **Features:**
  - OCR-based nutrition information extraction
  - Health scoring based on nutrient analysis
  - User profile management
  - Disease-specific dietary recommendations

### 2. Muscle AI
- **Path:** `/muscle_ai/`
- **Features:**
  - Video analysis for exercise form
  - YOLO-based pose detection
  - Form feedback for various exercises (squats, deadlifts, etc.)

---

## Accessing the Application

Once the server is running, access:

- **Homepage:** http://127.0.0.1:5000
- **Health-O-Meter:** http://127.0.0.1:5000/health (prefix routes)
- **Muscle AI:** http://127.0.0.1:5000/muscle (prefix routes)

---

## First Run Notes

- **EasyOCR Models:** On first run, EasyOCR will download detection and recognition models (~100MB). This is a one-time download and may take a few minutes depending on your internet connection.
- **CPU Mode:** By default, the application runs on CPU. For faster OCR processing, consider using a GPU-enabled setup.

---

## Stopping the Server

Press `CTRL+C` in the terminal where the server is running.

---

## Troubleshooting

### Virtual Environment Not Activating
If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Missing Dependencies
If you encounter import errors, reinstall dependencies:
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Scikit-Image Issues (Python 3.14)
The project has been patched to use `imageio` instead of `scikit-image`. If you need to reapply the patch:
1. Open `venv\Lib\site-packages\easyocr\imgproc.py`
2. Replace `from skimage import io` with `import imageio.v2 as io`

---

## Development

To make changes and have the server auto-reload, the app runs in debug mode by default. Any code changes will trigger an automatic restart.

---

## Requirements

- Python 3.14 (or 3.11+)
- Windows PowerShell
- ~500MB free space for models and dependencies
