# Private Social Network

A lightweight, private social web application built with Python and Flask. This app is designed to keep your updates private—there is no public feed. You only see updates from users who have mutually accepted your friend request.

It is designed to run locally right out of the box, but automatically adapts into a fully stateless, infinitely scalable application when deployed to the cloud.

## Features

* **Private Feed:** Only you and your approved friends can see your posts.

* **Rich Status Updates:** Post text updates, tag your location, and upload photos.

* **Friend Request System:** Send, accept, and decline connection requests.

* **Instant Invite Links:** Share your unique profile link to instantly prompt others to connect with you.

* **Venmo Integration:** Add your Venmo handle to your profile to let friends easily send you payments via a deep link on your posts.

* **Admin Dashboard:** The first registered user automatically becomes the Admin, gaining the ability to moderate content and generate demo data for testing.

* **Cloud-Ready & Scalable:** Runs locally with SQLite and local file storage, but automatically switches to PostgreSQL and Google Cloud Storage (GCS) when environment variables are provided.

## Project Structure

```
project_folder/
│
├── main.py               # The main Flask application
├── stress_test.py        # Script to simulate concurrent users
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker configuration for containerization
├── .dockerignore         # Excludes local files from Docker builds
├── .gitignore            # Excludes local files from Git
├── static/
│   └── uploads/          # Directory where local user photos are saved
└── templates/            # HTML templates
    ├── admin.html
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    └── settings.html

```

## Option 1: Local Setup (Standard)

**1. Clone or download the repository**

**2. Create a Virtual Environment (Recommended)**

```
# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate

```

**3. Install Dependencies**

```
pip install -r requirements.txt

```

**4. Run the Application**

```
python main.py

```

*Note: The application will automatically generate the SQLite database (`app.db`) and the local `static/uploads/` folder on its first run.*

**5. Access the App**
Open your web browser and navigate to: `http://127.0.0.1:5000`

## Option 2: Run with Docker

To run the app in an isolated container:

**1. Build the Image**

```
docker build -t flask-social-app .

```

**2. Run the Container**

```
docker run -p 5000:5000 flask-social-app

```

*(To persist local data, mount volumes for `app.db` and the `static/uploads` directory).*

## Option 3: Scalable Production Deployment (Google Cloud)

If you want to deploy this app to Google Cloud Run and allow it to scale to hundreds of instances, you must configure it to be **stateless**. The code automatically handles this if you provide the correct environment variables.

1. **Database:** Set up a PostgreSQL database (e.g., Google Cloud SQL) and get the connection string.

2. **Storage:** Create a Google Cloud Storage bucket and ensure objects are publicly readable.

3. **Environment Variables:** When deploying your container to Cloud Run, provide the following variables:

   * `DATABASE_URL`: Your PostgreSQL connection string (e.g., `postgresql://user:pass@ip/db`)

   * `GCS_BUCKET_NAME`: The name of your Google Cloud Storage bucket.

When these variables are present, the app will bypass local SQLite and local file storage, allowing multiple server instances to share the same data and scale seamlessly.

## Using the App

* **Admin Access:** The very first account you register will automatically be granted Admin privileges. You will see an "Admin" link in the top navigation bar.

* **Demo Data:** As an Admin, you can click "Generate Demo Data" on the dashboard to populate the database with test accounts (Alice, Bob, Charlie) and sample posts. You can log into these accounts using the password `password123`.

* **Invite Links:** On the main feed, you will find a "Share your profile" card. Copy this link and send it to someone; if they open it and register/log in, it will automatically send you a friend request.
