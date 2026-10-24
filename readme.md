Private Social Network

A lightweight, private social web application built with Python and Flask. This app is designed to keep your updates private—there is no public feed. You only see updates from users who have mutually accepted your friend request.

Features

Private Feed: Only you and your approved friends can see your posts.

Rich Status Updates: Post text updates, tag your location, and upload photos.

Friend Request System: Send, accept, and decline connection requests.

Instant Invite Links: Share your unique profile link to instantly prompt others to connect with you.

Venmo Integration: Add your Venmo handle to your profile to let friends easily send you payments via a deep link on your posts.

Admin Dashboard: The first registered user automatically becomes the Admin, gaining the ability to moderate content and generate demo data for testing.

Stress Testing: Includes a Python script to simulate heavy concurrent traffic.

Project Structure

project_folder/
│
├── main.py               # The main Flask application
├── stress_test.py        # Script to simulate concurrent users
├── requirements.txt      # Python dependencies
├── static/
│   └── uploads/          # Directory where user photos are saved
└── templates/            # HTML templates
    ├── admin.html
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    └── settings.html


Setup & Installation

1. Clone or download the repository
Ensure you have all the files in the same folder structure as above.

2. Create a Virtual Environment (Recommended)

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate


3. Install Dependencies

pip install -r requirements.txt


4. Run the Application

python main.py


Note: The application will automatically generate the SQLite database (app.db) and the static/uploads/ folder on its first run.

5. Access the App
Open your web browser and navigate to: http://127.0.0.1:5000

Using the App

Admin Access: The very first account you register will automatically be granted Admin privileges. You will see an "Admin" link in the top navigation bar.

Demo Data: As an Admin, you can click "Generate Demo Data" on the dashboard to populate the database with test accounts (Alice, Bob, Charlie) and sample posts. You can log into these accounts using the password password123.

Invite Links: On the main feed, you will find a "Share your profile" card. Copy this link and send it to someone; if they open it and register/log in, it will automatically send you a friend request.