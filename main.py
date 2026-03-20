from dotenv import load_dotenv
load_dotenv()

from app import create_app

app = create_app() # можно передавать конфиг явно, а можно менять через getconfig() (.env)

if __name__ == "__main__":
    app.run()
