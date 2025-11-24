# Installing Python on Windows

## Option 1: Install from python.org (Recommended)

1. **Download Python:**
   - Go to: https://www.python.org/downloads/
   - Click "Download Python 3.x.x" (latest version)

2. **Run the installer:**
   - **IMPORTANT:** Check the box "Add Python to PATH" at the bottom of the installer
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify installation:**
   - Close and reopen your terminal/PowerShell
   - Run: `python --version`
   - Run: `pip --version`

4. **Install project dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

## Option 2: Install from Microsoft Store

1. Open Microsoft Store
2. Search for "Python 3.12" (or latest version)
3. Click "Install"
4. After installation, close and reopen your terminal
5. Run: `python --version`
6. Install dependencies: `pip install -r requirements.txt`

## Option 3: Disable Windows Store Python Alias (if Python is already installed elsewhere)

If you have Python installed but it's not working:

1. Go to: **Settings** → **Apps** → **Advanced app settings** → **App execution aliases**
2. Turn OFF the toggles for:
   - `python.exe`
   - `python3.exe`
3. Restart your terminal
4. Try `python --version` again

## After Installation

Once Python is installed, run:

```powershell
# Install dependencies
pip install -r requirements.txt

# Run the application
python jarvis_chat.py
```

## Troubleshooting

If `pip` still doesn't work after installing Python:

```powershell
# Try using python -m pip instead
python -m pip install -r requirements.txt
```

