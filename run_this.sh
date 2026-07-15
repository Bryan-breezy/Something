# Function to check if a command exists
command_exists () {
  command -v "$1" >/dev/null 2>&1
}

echo " Bryan has started the PDF Scraper Automation Tool"

# 1. Check for Python 3
if ! command_exists python3;
then
  echo " Error: python3 is not installed. Please install Python 3 to run this script."
  exit 1
fi

# 2. Check for pip3
if ! command_exists pip3;
then
  echo " Error: pip3 is not installed. Please install pip3 to manage Python dependencies."
  exit 1
fi

# 3. Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
  echo " Bryan is installing Python dependencies from requirements.txt..."
  pip3 install -r requirements.txt
  if [ $? -ne 0 ]; then
    echo " Error: Failed to install Python dependencies. Please check your internet connection or permissions."
    exit 1
  fi
  echo " Dependencies installed successfully."
else
  echo "  Warning: requirements.txt not found. Skipping dependency installation."
fi

# 4. Execute main.py
echo "Ok Bryan is running the PDF scraper..."
python3 main.py

if [ $? -ne 0 ]; then
  echo " Error: The PDF scraper encountered an issue."
  exit 1
else
  echo " PDF scraper finished successfully."
fi
