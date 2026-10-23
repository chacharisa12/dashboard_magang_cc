
from pymongo import MongoClient
from pymongo.server_api import ServerApi

print("Memulai pemindahan data...")

# Koneksi ke MongoDB lokal
local_client = MongoClient("mongodb://localhost:27017/")

atlas_uri = "mongodb+srv://charisamarthadps18_db_user:akusukakucing@cluster0.xnaoznz.mongodb.net/"

atlas_client = MongoClient(
    atlas_uri,
    server_api=ServerApi("1"),
    serverSelectionTimeoutMS=10000
)

try:
    local_collection = local_client["dashboard_thermal"]["konten_dashboard"]
    atlas_collection = atlas_client["dashboard_thermal"]["konten_dashboard"]

    # Pastikan kedua koneksi bisa diakses
    local_client.admin.command("ping")
    atlas_client.admin.command("ping")

    documents = list(local_collection.find({}))

    print("Dokumen lokal:", len(documents))
    print("Dokumen Atlas sebelum pemindahan:",
          atlas_collection.count_documents({}))

    if not documents:
        print("Data lokal kosong. Pemindahan dibatalkan.")

    elif atlas_collection.count_documents({}) > 0:
        print("Atlas sudah berisi dokumen. Pemindahan dibatalkan agar tidak duplikat.")

    else:
        atlas_collection.insert_many(documents)
        print(f"Berhasil memindahkan {len(documents)} dokumen!")

except Exception as e:
    print("Terjadi kesalahan:", e)

finally:
    local_client.close()
    atlas_client.close()