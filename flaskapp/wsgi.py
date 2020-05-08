
from .create_db import app
from gevent.tests.test__threading_patched_local import t

if __name__ == "__main__":
    t.start()
    app.run()
