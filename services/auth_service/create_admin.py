
from app.database import SessionLocal
from app.models import User


def main():
    email = input("Enter the registered email to promote to admin: ").strip().lower()

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if user is None:
            print("User not found. Register this user first.")
            return

        if user.role == "admin":
            print(f"{user.email} is already an admin.")
            return

        user.role = "admin"
        db.commit()

        print(f"Success! {user.email} is now an admin.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
