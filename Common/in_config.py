# Secret key to encode tokens
SECRET_KEY = "cf7259ae3010a68b5f12de2d567d49cc30b645811ed5f30dcf2a29bd42489586"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5
REFRESH_TOKEN_EXPIRE_DAYS = 1

PROJECT_NAME = "Intuit-Demo"
SERVICE_NAME = "Intuit Demo Service"
MY_USER = "naren"
MY_PASSWORD = "Python#123"
MY_DB_NAME = "players"
DATABASE_URL = f"mysql+pymysql://{MY_USER}:{MY_PASSWORD}@localhost/{MY_DB_NAME}"
URL_PREFIX = "/intuit-demo/api/v1"
