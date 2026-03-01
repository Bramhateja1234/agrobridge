🌟 HOW TO START AGROBRIDGE (FOR MY FRIEND) 🌾

Hey! Here is the super simple way to run this website on your computer:

STEP 1: INSTALL PYTHON 🐍
- Go here: https://www.python.org/downloads/
- Download and install Python (Make sure to check the box that says "Add Python to PATH"!)

STEP 2: RENAME ONE FILE 📄
- Open the project folder.
- Find a file named ".env.example".
- Right-click it and Rename it to just ".env" (remove the ".example" part).

STEP 3: OPEN THE BLACK BOX (TERMINAL) 💻
- Press the Start button on your keyboard.
- Type "cmd" and press Enter.
- Type this inside the black box and press Enter:
  cd "the path to where you saved this folder"
  (Example: cd "C:\Users\Name\Desktop\agro_platform")

STEP 4: SET UP THE ENGINE 🛠️
- Type these commands one by one (press Enter after each):
  python -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt

STEP 5: PREPARE THE DATA 🗄️
- Type these commands one by one:
  python manage.py migrate --settings=agro_platform.settings.dev
  python manage.py createsuperuser --settings=agro_platform.settings.dev
  (Follow the instructions to make an Email and Password)

STEP 6: TEACH IT TO SPEAK HINDI & TELUGU 🗣️
- Type this and press Enter:
  python manage.py compilemessages --settings=agro_platform.settings.dev

STEP 7: START THE WEBSITE! 🚀
- Type this and press Enter:
  python manage.py runserver --settings=agro_platform.settings.dev

STEP 8: SEE IT! 🌐
- Open Google Chrome and go to: http://127.0.0.1:8000

THAT'S IT! YOU ARE A PRO! 🎉
- You can change the language at the top of the website.
- You can join as a Farmer or a Consumer.
