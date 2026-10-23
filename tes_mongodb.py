
from pymongo import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://charisamarthadps18_db_user:<db_password>@cluster0.xnaoznz.mongodb.net/"

client = MongoClient(
    uri,
    server_api=ServerApi("1"),
    serverSelectionTimeoutMS=10000
)

try:
    client.admin.command("ping")
    print("Berhasil terhubung ke MongoDB Atlas!")

    db = client["dashboard_thermal"]
    collection = db["konten_dashboard"]

    print("Database:", db.name)
    print("Collection:", collection.name)
    print("Jumlah dokumen:", collection.count_documents({}))

except Exception as e:
    print("Koneksi gagal:", e)

finally:
    client.close()
