#!/usr/bin/env python3
from famraft import app
from famraft import views
import os

app.secret_key = os.urandom(24)
app.run(debug=True)
