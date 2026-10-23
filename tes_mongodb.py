
from pymongo import MongoClient

try:
    client = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=5000
    )

    # Cek apakah MongoDB aktif
    client.admin.command("ping")
    print("Koneksi MongoDB berhasil!")

    # Akses database dan collection milikmu
    db = client["dashboard_thermal"]
    collection = db["konten_dashboard"]

    # Cek jumlah dokumen
    jumlah = collection.count_documents({})
    print("Jumlah dokumen:", jumlah)

    # Tampilkan judul setiap dokumen
    for dokumen in collection.find({}, {"judul": 1}):
        print("-", dokumen.get("judul", "Tanpa judul"))

    client.close()

except Exception as e:
    print("Koneksi gagal:", e)
