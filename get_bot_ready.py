import sqlite3
import os

db = sqlite3.connect("db/bot.db")

c = db.cursor()
try:
    c.execute("DROP TABLE profiles")
except:
    pass

c.execute("CREATE TABLE profiles (id, Name, Bio, Image)")

try:
    c.execute("DROP TABLE matches")
except:
    pass

c.execute("CREATE TABLE matches (id, Matches)")

db.commit()

f=open("token", "w+")
f.write(input("Please type your user token. >> "))
f.close()
f=open("mainserverid", "w+")
f.write(input("Please type the id of the server >> "))
f.close()
f=open("verifiedroleid", "w+")
f.write(input("Please type the id of the server's veriified role >> "))
f.close()
print("Done.\nYou can now run main.py and the bot will start.")

input("Press enter to exit >> ")