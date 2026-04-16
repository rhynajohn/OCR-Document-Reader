# run.py
import uvicorn
from main import app
from database import check_connection

if __name__ == "__main__":
    if check_connection():
        uvicorn.run(app, host="127.0.0.1", port=8000)
    else:
        print("Unable to establish a database connection.")

