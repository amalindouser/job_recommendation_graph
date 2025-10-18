import pymysql

try:
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",  # isi sesuai password kamu
        database="job_recommendation"
    )
    print("✅ Koneksi ke MySQL berhasil!")
    conn.close()
except Exception as e:
    print("❌ Gagal konek ke MySQL:", e)
