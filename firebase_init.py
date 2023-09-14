from firebase_admin import credentials, initialize_app, get_app


def initialize_firebase():
    try:
        get_app()
    except ValueError:
        cred = credentials.Certificate("firebaseAccessKey.json")
        initialize_app(cred)
