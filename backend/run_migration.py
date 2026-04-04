import os
import sys
import subprocess


def main() -> int:
    # Рабочая директория должна быть backend/
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    try:
        # Выполняем alembic upgrade head
        return subprocess.call([sys.executable, "-m", "alembic", "upgrade", "head"])
    except Exception as e:
        print(f"Migration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
