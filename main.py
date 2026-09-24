import os
import threading
from flask import Flask

app = Flask("")


@app.route("/")
def home():
  return "Bot ishlamoqda!"


def run():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


threading.Thread(target=run).start()
8928425504:AAGnTWTJcwS3VhnHXWyLhaRjh0FVWlZOYL4
