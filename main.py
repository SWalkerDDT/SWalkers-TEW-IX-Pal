from app import MainApp
from models.database import Database

def main():
    db = Database()  # Uses default backend and DB_PATH
    db.init_db()

    app = MainApp()
    app.mainloop()

if __name__ == "__main__":
    main()
