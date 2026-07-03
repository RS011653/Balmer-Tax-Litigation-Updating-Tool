import bcrypt
print(bcrypt.hashpw("11653".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"))