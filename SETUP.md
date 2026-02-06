# Praying Diary - Project Setup Guide

This guide covers how to set up and run the **Praying Diary** application, including configuration for new features like Social Login and Donations.

## 1. Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_folder>
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the database:**
    The application will automatically create the database tables and a master admin user (`admin` / `admin123`) on the first run if `SKIP_DB_INIT` is not set.

## 2. Configuration

The application uses environment variables for sensitive configuration. You can set these in a `.env` file or your system environment.

### Social Login (OAuth)
To enable "Login with Google" or Facebook, you need to register your application with these providers.

*   **Google:** [Google Cloud Console](https://console.cloud.google.com/) -> APIs & Services -> Credentials -> Create OAuth Client ID.
*   **Facebook:** [Meta for Developers](https://developers.facebook.com/) -> Create App -> Facebook Login.

Add the keys to your config (currently simulated in `routes/auth_routes.py` for this demo version, but in a production app using Authlib, you would add):

```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
FACEBOOK_CLIENT_ID=your_facebook_client_id
FACEBOOK_CLIENT_SECRET=your_facebook_client_secret
```

### Donations (Stripe)
The donation feature is currently in **Mock Mode**. To enable real payments:

1.  Sign up at [Stripe](https://stripe.com/).
2.  Get your **Publishable Key** and **Secret Key**.
3.  Update `routes/donation_routes.py` to use the Stripe API library instead of the mock logic.

### Push Notifications
VAPID keys are required for browser push notifications. The app includes default keys for testing in `config.py`. For production, generate your own:

```bash
vapid --gen
```
Then update `VAPID_PRIVATE_KEY` and `VAPID_PUBLIC_KEY` in `config.py` or environment variables.

## 3. Running the Application

**Development:**
```bash
python app.py
```
Access at `http://localhost:8080`.

**Production:**
```bash
gunicorn app:app
```

## 4. Features & Troubleshooting

*   **Translations:** If you change text, run:
    ```bash
    pybabel extract -F babel.cfg -k _ -k gettext -k ngettext -k lazy_gettext -o messages.pot .
    pybabel update -i messages.pot -d translations
    # Edit translations/es/LC_MESSAGES/messages.po
    pybabel compile -d translations
    ```

*   **CSRF Errors:** Ensure all forms in templates include `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>`.
