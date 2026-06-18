from datetime import date

from flask import Flask, render_template, request,redirect,session, url_for
import pymysql
from urllib.parse import urlparse
import os

app = Flask(__name__,
            template_folder='../frontend',
            static_folder='../frontend/assets'
    )
app.secret_key = "kopiko123"

# koneksi database
b_url = os.getenv("DATABASE_URL")

url = urlparse(b_url)

db = pymysql.connect(
    host=url.hostname,
    user=url.username,
    password=url.password,
    database=url.path[1:],
    port=url.port
)

cursor = db.cursor()
# halaman awal
@app.route('/')
def home():
    return render_template('login.html')

# proses login
@app.route('/login', methods=['POST'])
def login():

    username = request.form['username']
    password = request.form['password']

    cursor.execute(
        "SELECT * FROM pengguna WHERE username=%s",
        (username,)
    )

    user = cursor.fetchone()

    if user:

        if password == user[2]:
            akses = user[3]

             # simpan session
            session['idUser'] = user[0]
            session['username'] = user[1]
            session['akses'] = user[3]

                # redirect sesuai role
            if akses == "admin":
                return redirect('/admin')

            elif akses == "owner":
                return redirect('/owner')

            elif akses == "kasir":
                return redirect('/kasir')

            else:
                return "Role tidak dikenali"

        else:
            return "Password salah"

    else:
        return "User tidak ditemukan"


# dashboard admin
@app.route('/admin')
def admin():
    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "admin":
        return "Akses ditolak"
    
    cursor = db.cursor()

    # total user
    cursor.execute(
        "SELECT COUNT(*) FROM pengguna"
    )
    totalUser = cursor.fetchone()[0]

    # total produk/menu
    cursor.execute(
        "SELECT COUNT(*) FROM produk"
    )
    totalProduk = cursor.fetchone()[0]

    # total transaksi hari ini
    cursor.execute("""
        SELECT COUNT(*)
        FROM transaksi
        WHERE DATE(tanggal)=CURDATE()
    """)
    totalTransaksi = cursor.fetchone()[0]

    # total pembelian hari ini
    cursor.execute("""
        SELECT COUNT(*)
        FROM pembelian
        WHERE DATE(tanggal)=CURDATE()
    """)
    totalPembelian = cursor.fetchone()[0]

    # stok bahan baku menipis
    cursor.execute("""
        SELECT *
        FROM bahanBaku
        WHERE stok <= 100
    """)
    stokTipis = cursor.fetchall()

    return render_template(
        'admin/admin.html',

        totalUser=totalUser,
        totalProduk=totalProduk,
        totalTransaksi=totalTransaksi,
        totalPembelian=totalPembelian,
        stokTipis=stokTipis
    )

    # dashboard owner
@app.route('/owner')
def owner():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "owner":
        return "Akses ditolak"

    cursor = db.cursor(buffered=True)

    # total transaksi
    cursor.execute("""
        SELECT COUNT(*)
        FROM transaksi
    """)
    totalTransaksi = cursor.fetchone()[0]

    # total pendapatan
    cursor.execute("""
        SELECT IFNULL(SUM(total),0)
        FROM transaksi
    """)
    totalPendapatan = cursor.fetchone()[0]

    # total pembelian
    cursor.execute("""
        SELECT IFNULL(SUM(total),0)
        FROM pembelian
    """)
    totalPembelian = cursor.fetchone()[0]

    # laporan transaksi terbaru
    cursor.execute("""
        SELECT
            idTransaksi,
            tanggal,
            total,
            bayar,
            kembalian
        FROM transaksi
        ORDER BY idTransaksi DESC
        LIMIT 5
    """)

    laporan = cursor.fetchall()

    return render_template(
        'owner/owner.html',
        totalTransaksi=totalTransaksi,
        totalPendapatan=totalPendapatan,
        totalPembelian=totalPembelian,
        laporan=laporan
    )

# dashboard kasir
@app.route('/kasir')
def kasir():
    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "kasir":
        return "Akses ditolak"
    
    cursor = db.cursor()

    cursor.execute("""
        SELECT p.idProduk,
               p.namaProduk,
               p.kategori,
               p.hargaJual,
               p.satuan,
               p.tipeProduk,
               COALESCE(b.stok, 0) AS stokGudang
        FROM produk p
        LEFT JOIN bahanBaku b
          ON p.tipeProduk = 'langsung'
         AND b.namaBahan = p.namaProduk
        ORDER BY p.idProduk
    """)
    dataProduk = cursor.fetchall()

    return render_template(
        'kasir/kasir.html',
        produk=dataProduk
    )

# logout
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ==============================
# SIMPAN TRANSAKSI
# ==============================

@app.route('/simpan_transaksi', methods=['POST'])
def simpan_transaksi():
    cursor = db.cursor()

    idUser = session.get('idUser')
    if not idUser:
        return "Sesi login habis, silakan login kembali."

    total = int(request.form['total'])
    bayar = int(request.form['bayar'])

    if bayar < total:
        return "Uang pembayaran kurang"

    kembalian = bayar - total

    try:
        # 1. Simpan ke tabel transaksi utama
        cursor.execute("""
            INSERT INTO transaksi(tanggal, total, bayar, kembalian, idUser)
            VALUES(NOW(), %s, %s, %s, %s)
        """, (total, bayar, kembalian, idUser))

        idTransaksi = cursor.lastrowid

        # Ambil semua data produk dari form kasir
        idProduk_list = request.form.getlist('idProduk[]')
        qty_list = request.form.getlist('qty[]')
        harga_list = request.form.getlist('harga[]')
        subtotal_list = request.form.getlist('subtotal[]')

        # 2. Loop simpan detail transaksi & potong stok berdasarkan tipeProduk
        for i in range(len(idProduk_list)):
            id_produk = int(idProduk_list[i])
            qty_beli = int(qty_list[i])

            # Simpan item belanjaan ke detailTransaksi
            cursor.execute("""
                INSERT INTO detailTransaksi (idTransaksi, idProduk, jumlah, harga, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (idTransaksi, id_produk, qty_beli, harga_list[i], subtotal_list[i]))

            # Cek tipeProduk dan namaProduk terlebih dahulu di database
            cursor.execute("SELECT tipeProduk, namaProduk FROM produk WHERE idProduk = %s", (id_produk,))
            produk_info = cursor.fetchone()
            
            if not produk_info:
                continue
                
            tipe_produk = produk_info[0]
            nama_produk = produk_info[1]

            # ========================================================
            # KONDISI A: JIKA TIPE PRODUK LANGSUNG (POTONG STOK LANGSUNG)
            # ========================================================
            if tipe_produk == 'langsung':
                # Cari bahan baku yang namanya sama persis dengan nama produk langsung ini
                cursor.execute("SELECT idBahan FROM bahanBaku WHERE namaBahan = %s", (nama_produk,))
                bahan_langsung = cursor.fetchone()

                if bahan_langsung:
                    id_bahan_langsung = bahan_langsung[0]
                    # Langsung potong stok bahan baku sebanyak qty_beli
                    cursor.execute("""
                        UPDATE bahanBaku
                        SET stok = stok - %s
                        WHERE idBahan = %s
                    """, (float(qty_beli), id_bahan_langsung))
                else:
                    print(f"Peringatan: Produk langsung '{nama_produk}' belum terdaftar di tabel bahanBaku!")

            # ========================================================
            # KONDISI B: JIKA TIPE PRODUK RACIKAN (MEMOTONG LEWAT RESEP)
            # ========================================================
            elif tipe_produk == 'racikan':
                # Ambil semua bahan baku dan jumlah pakai berdasarkan resep
                cursor.execute("""
                    SELECT idBahan, jumlahPakai 
                    FROM resep 
                    WHERE idProduk = %s
                """, (id_produk,))
                
                resep_produk = cursor.fetchall()

                # Kurangi masing-masing stok bahan baku hasil racikan
                for bahan in resep_produk:
                    id_bahan = bahan[0]
                    jumlah_pakai_per_porsi = float(bahan[1])
                    total_dikurangi = jumlah_pakai_per_porsi * float(qty_beli)

                    # Update/Kurangi stok di tabel bahanBaku
                    cursor.execute("""
                        UPDATE bahanBaku
                        SET stok = stok - %s
                        WHERE idBahan = %s
                    """, (total_dikurangi, id_bahan))

        # Jika seluruh loop aman tanpa ada crash, commit data ke MySQL
        db.commit()
        print(f"Transaksi #{idTransaksi} sukses diproses & stok gudang terpotong.")

    except Exception as e:
        db.rollback()
        print(f"Transaksi gagal karena terjadi error: {e}")
        return f"Terjadi kesalahan sistem: {e}"
    finally:
        cursor.close()

    return redirect(f'/struk/{idTransaksi}')

# cetak struk
@app.route('/struk/<id_transaksi>')
def struk(id_transaksi):
    
    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "kasir":
        return "Akses ditolak"

    cursor = db.cursor()

    # header transaksi
    cursor.execute("""
        SELECT *
        FROM transaksi
        WHERE idTransaksi=%s
    """, (id_transaksi,))

    transaksi = cursor.fetchone()

    # detail item
    cursor.execute("""
        SELECT p.namaProduk,
               d.jumlah,
               d.harga,
               d.subtotal
        FROM detailTransaksi d
        JOIN produk p
            ON p.idProduk = d.idProduk
        WHERE d.idTransaksi=%s
    """, (id_transaksi,))

    detail = cursor.fetchall()

    return render_template(
        'kasir/struk.html',
        transaksi=transaksi,
        detail=detail
    )

# KELOLA PRODUK
# halaman produk - admin
@app.route('/kelola_produk')
def kelola_produk():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "admin":
        return "Akses ditolak"

    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM produk
        ORDER BY idProduk asc
    """)

    produk = cursor.fetchall()

    return render_template(
        'admin/kelola_produk.html',
        produk=produk
    )

@app.route('/tambah_produk', methods=['POST'])
def tambah_produk():

    namaProduk = request.form['namaProduk']
    kategori = request.form['kategori']
    hargaJual = request.form['hargaJual']
    satuan = request.form['satuan']
    tipeProduk = request.form['tipeProduk']

    cursor = db.cursor()

    query = """
        INSERT INTO produk
        (
            namaProduk,
            kategori,
            hargaJual,
            satuan,
            tipeProduk
        )
        VALUES (%s,%s,%s,%s,%s)
    """

    value = (
        namaProduk,
        kategori,
        hargaJual,
        satuan,
        tipeProduk
    )

    cursor.execute(query, value)

    db.commit()

    return redirect('/kelola_produk')

@app.route('/edit_produk', methods=['POST'])
def edit_produk():

    idProduk = request.form['idProduk']
    namaProduk = request.form['namaProduk']
    kategori = request.form['kategori']
    hargaJual = request.form['hargaJual']
    satuan = request.form['satuan']
    tipeProduk = request.form['tipeProduk']

    cursor = db.cursor()

    cursor.execute("""
        UPDATE produk
        SET
            namaProduk=%s,
            kategori=%s,
            hargaJual=%s,
            satuan=%s,
            tipeProduk=%s
        WHERE idProduk=%s
    """, (
        namaProduk,
        kategori,
        hargaJual,
        satuan,
        tipeProduk,
        idProduk
    ))

    db.commit()

    return redirect('/kelola_produk')

@app.route('/hapus_produk/<id>')
def hapus_produk(id):

    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM produk
        WHERE idProduk=%s
    """, (id,))

    db.commit()

    return redirect('/kelola_produk')


# kelola resep produk
@app.route('/resep/<int:idProduk>')
def resep(idProduk):

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "admin":
        return "Akses ditolak"
    
    cursor = db.cursor()

    # ambil data produk
    cursor.execute("""
        SELECT *
        FROM produk
        WHERE idProduk = %s
    """, (idProduk,))

    produk = cursor.fetchone()

    # jika produk tidak ada
    if not produk:
        return "Produk tidak ditemukan"

    # ambil semua bahan baku
    cursor.execute("""
        SELECT *
        FROM bahanBaku
        ORDER BY namaBahan ASC
    """)

    bahan = cursor.fetchall()

    # ambil resep produk
    cursor.execute("""
        SELECT
            resep.idResep,
            bahanBaku.namaBahan,
            resep.jumlahPakai,
            bahanBaku.satuan

        FROM resep

        JOIN bahanBaku
        ON resep.idBahan = bahanBaku.idBahan

        WHERE resep.idProduk = %s
    """, (idProduk,))

    dataResep = cursor.fetchall()

    return render_template(
        'admin/resep.html',
        produk=produk,
        bahan=bahan,
        dataResep=dataResep
    )

@app.route('/tambah_resep', methods=['POST'])
def tambah_resep():

    idProduk = request.form['idProduk']
    idBahan = request.form['idBahan']
    jumlahPakai = request.form['jumlahPakai']

    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO resep
        (
            idProduk,
            idBahan,
            jumlahPakai
        )
        VALUES
        (
            %s,
            %s,
            %s
        )
    """, (
        idProduk,
        idBahan,
        jumlahPakai
    ))

    db.commit()

    return redirect('/resep/' + idProduk)

@app.route('/hapus_resep/<idResep>/<idProduk>')
def hapus_resep(idResep, idProduk):

    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM resep
        WHERE idResep=%s
    """, (idResep,))

    db.commit()

    return redirect(f'/resep/{idProduk}')

# kelola user -- admin
@app.route('/kelola_user')
def kelola_user():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "admin":
        return "Akses ditolak"

    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM pengguna"
    )

    users = cursor.fetchall()

    return render_template(
        'admin/kelola_user.html',
        users=users
    )

@app.route('/tambah_user', methods=['POST'])
def tambah_user():

    username = request.form['username']
    sandi = request.form['password']
    akses = request.form['akses']


    cursor = db.cursor()


    cursor.execute("""
        INSERT INTO pengguna
        (username,sandi,akses)
        VALUES(%s,%s,%s)
    """,(
        username,
        sandi,
        akses
    ))

    db.commit()


    return redirect('/kelola_user')

@app.route('/hapus_user/<id>')
def hapus_user(id):

    try:

        cursor = db.cursor()

        cursor.execute(
            "DELETE FROM pengguna WHERE idUser=%s",
            (id,)
        )

        db.commit()

    except Exception as e:

        return f"User tidak bisa dihapus: {e}"

    return redirect('/kelola_user')

@app.route('/edit_user', methods=['POST'])
def edit_user():

    idUser = request.form['idUser']
    username = request.form['username']
    sandi = request.form['sandi']
    akses = request.form['akses']

    cursor = db.cursor()

    cursor.execute("""
        UPDATE pengguna
        SET username=%s,
            sandi=%s,
            akses=%s
        WHERE idUser=%s
    """,(
        username,
        sandi,
        akses,
        idUser
    ))

    db.commit()

    return redirect('/kelola_user')

@app.route('/pembelian')
def pembelian():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "admin":
        return "Akses ditolak"
    
    cursor = db.cursor()

    # Query asli Anda tetap dipertahankan agar data detail tidak hilang
    cursor.execute("""
        SELECT
            p.idPembelian,
            p.tanggal,
            p.namaSupplier,
            b.namaBahan,
            d.jumlah,
            d.hargaBeli,
            d.subtotal,
            p.total
        FROM pembelian p
        LEFT JOIN detailPembelian d
            ON p.idPembelian = d.idPembelian
        LEFT JOIN bahanBaku b
            ON d.idBahan = b.idBahan
        ORDER BY p.idPembelian DESC
    """)

    riwayat_raw = cursor.fetchall()

    # Proses pengelompokkan (Grouping) berdasarkan idPembelian
    pembelian_dict = {}
    for row in riwayat_raw:
        id_pembelian = row[0]
        
        # Jika ID Pembelian belum ada di dictionary, buat struktur dasarnya
        if id_pembelian not in pembelian_dict:
            pembelian_dict[id_pembelian] = {
                'idPembelian': row[0],
                'tanggal': row[1],
                'namaSupplier': row[2],
                'total': row[7],
                'detail_barang': [] # Tempat menampung banyak barang
            }
        
        # Masukkan detail barang jika datanya ada (tidak null)
        if row[3] is not None:
            pembelian_dict[id_pembelian]['detail_barang'].append({
                'namaBahan': row[3],
                'jumlah': row[4],
                'hargaBeli': row[5],
                'subtotal': row[6]
            })

    # Mengubah dictionary kembali menjadi list agar mudah di-loop oleh Jinja2 di HTML
    riwayat = list(pembelian_dict.values())

    return render_template('admin/pembelian.html', riwayat=riwayat)

@app.route('/simpan_pembelian', methods=['POST'])
def simpan_pembelian():
    cursor = db.cursor()
    tanggal = date.today()
    supplier = request.form['supplier']

    namaBarang = request.form.getlist('nama_barang[]')
    jumlah = request.form.getlist('jumlah[]')
    satuan = request.form.getlist('satuan[]')
    hargaBeli = request.form.getlist('harga_beli[]')

    total = 0
    # Hitung total semua barang
    for i in range(len(namaBarang)):
        subtotal = int(jumlah[i]) * int(hargaBeli[i])
        total += subtotal

    # 1. Simpan tabel pembelian (Induk)
    cursor.execute("""
        INSERT INTO pembelian (tanggal, total, namaSupplier)
        VALUES (%s,%s,%s)
    """, (tanggal, total, supplier))

    idPembelian = cursor.lastrowid

    # 2. Simpan ke detail pembelian
    for i in range(len(namaBarang)):
        subtotal = int(jumlah[i]) * int(hargaBeli[i])

        # Cek apakah bahan baku sudah ada di master database
        cursor.execute("""
            SELECT idBahan
            FROM bahanBaku
            WHERE namaBahan = %s
        """, (namaBarang[i],))

        bahan = cursor.fetchone()

        if bahan is None:
            # JIKA BELUM ADA: Daftarkan namanya ke database master, TAPI STOK BERI NILAI 0
            # Stok riil baru akan bertambah saat diklik 'Terima di Gudang'
            cursor.execute("""
                INSERT INTO bahanBaku (namaBahan, stok, satuan)
                VALUES (%s, 0, %s)
            """, (namaBarang[i], satuan[i]))

            idBahan = cursor.lastrowid
        else:
            idBahan = bahan[0]
            # --- BAGIAN "UPDATE bahanBaku SET stok = stok + %s" DI SINI SUDAH DIHAPUS ---
            # Hal ini dilakukan agar stok tidak bocor/bertambah duluan sebelum diconvert.

        # 3. Simpan detail transaksi pembelian
        cursor.execute("""
            INSERT INTO detailPembelian (idPembelian, idBahan, jumlah, hargaBeli, subtotal)
            VALUES (%s,%s,%s,%s,%s)
        """, (idPembelian, idBahan, jumlah[i], hargaBeli[i], subtotal))

    db.commit()
    cursor.close()

    return redirect('/pembelian')

@   app.route('/hapus_pembelian/<id>')
def hapus_pembelian(id):

    cursor = db.cursor()

    # hapus detail pembelian
    cursor.execute("""
        DELETE FROM detailPembelian
        WHERE idPembelian=%s
    """, (id,))

    # hapus pembelian
    cursor.execute("""
        DELETE FROM pembelian
        WHERE idPembelian=%s
    """, (id,))

    db.commit()

    return redirect('/pembelian')

@app.route('/edit_pembelian', methods=['POST'])
def edit_pembelian():
    idPembelian = request.form['idPembelian']
    tanggal = request.form['tanggal']
    supplier = request.form['supplier'] # Ini mengambil data dari input name="supplier"
    total = request.form['total']

    # Pastikan nama kolom di bawah (namaSupplier) sesuai dengan yang ada di database MySQL Anda
    cursor.execute("""
        UPDATE pembelian
        SET tanggal = %s,
            namaSupplier = %s,
            total = %s
        WHERE idPembelian = %s
    """, (tanggal, supplier, total, idPembelian)) # Urutan tuple ini harus pas dengan urutan %s di atas
    
    db.commit() # Jangan lupa di-commit agar perubahan tersimpan ke database
    return redirect('/pembelian') # Sesuaikan dengan rute halaman riwayat Anda

@app.route('/kelola_gudang')
def kelola_gudang():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "admin":
        return "Akses ditolak"
    
    cursor = db.cursor(dictionary=True)


    try:
        # 1. Ambil data stok bahan baku saat ini
        cursor.execute("SELECT idBahan, namaBahan, stok, satuan FROM bahanBaku")
        bahan_baku = cursor.fetchall()
     
        # 2. Ambil semua riwayat pembelian yang belum dikonversi
        cursor.execute("SELECT idPembelian, tanggal, total, namaSupplier FROM pembelian WHERE status='pending'")    
        semua_pembelian = cursor.fetchall()
     
        riwayat = []
        for p in semua_pembelian:
            cursor.execute("""
                SELECT dp.idBahan, b.namaBahan, dp.jumlah, b.satuan 
                FROM detailPembelian dp
                JOIN bahanBaku b ON dp.idBahan = b.idBahan
                WHERE dp.idPembelian = %s
            """, (p['idPembelian'],))
            p['detail_barang'] = cursor.fetchall()
            riwayat.append(p)
            
    except Exception as e:
        print(f"Terjadi kesalahan database: {e}")
        bahan_baku = []
        riwayat = []
    finally:
        cursor.close()
    
    return render_template('admin/kelola_gudang.html', 
                           bahan_baku_list=bahan_baku, 
                           pembelian_belum_masuk=riwayat)


@app.route('/kelola_gudang/tambah_bahan', methods=['POST'])
def tambah_bahan():
    nama_bahan = request.form.get('namaBahan')
    satuan = request.form.get('satuan')
    stok = request.form.get('stok', '0')
    try:
        stok_value = float(stok)
    except ValueError:
        stok_value = 0.0

    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO bahanBaku (namaBahan, stok, satuan) VALUES (%s, %s, %s)",
            (nama_bahan, stok_value, satuan)
        )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Gagal menambah bahan baku: {e}")
    finally:
        cursor.close()

    return redirect('/kelola_gudang')


@app.route('/kelola_gudang/update_bahan', methods=['POST'])
def update_bahan():
    id_bahan = request.form.get('idBahan')
    action = request.form.get('action')
    mode = request.form.get('mode', 'set')
    qty = request.form.get('qty', '0')

    cursor = db.cursor()
    try:
        if action == 'delete':
            cursor.execute("DELETE FROM bahanBaku WHERE idBahan = %s", (id_bahan,))
        else:
            try:
                jumlah = float(qty)
            except ValueError:
                jumlah = 0.0

            if mode == 'add':
                cursor.execute(
                    "UPDATE bahanBaku SET stok = stok + %s WHERE idBahan = %s",
                    (jumlah, id_bahan)
                )
            elif mode == 'subtract':
                cursor.execute(
                    "UPDATE bahanBaku SET stok = GREATEST(stok - %s, 0) WHERE idBahan = %s",
                    (jumlah, id_bahan)
                )
            else:
                cursor.execute(
                    "UPDATE bahanBaku SET stok = %s WHERE idBahan = %s",
                    (jumlah, id_bahan)
                )

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Gagal memperbarui bahan baku: {e}")
    finally:
        cursor.close()

    return redirect('/kelola_gudang')


@app.route('/gudang/convert/<int:id_pembelian>')
def convert_pembelian_ke_gudang(id_pembelian):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT status FROM pembelian WHERE idPembelian = %s", (id_pembelian,))
        pembelian_data = cursor.fetchone()
        if pembelian_data is None or pembelian_data['status'] == 'converted':
            return redirect('/kelola_gudang')

        # 1. Ambil idBahan dan jumlah yang dibeli
        cursor.execute("SELECT idBahan, jumlah FROM detailPembelian WHERE idPembelian = %s", (id_pembelian,))
        daftar_barang = cursor.fetchall()

        # 2. Update stok ke tabel bahanBaku
        for barang in daftar_barang:
            id_bahan = barang['idBahan']
            jumlah_beli = barang['jumlah']

            cursor.execute("""
                UPDATE bahanBaku 
                SET stok = stok + %s 
                WHERE idBahan = %s
            """, (jumlah_beli, id_bahan))

        # 3. Tandai pembelian sebagai sudah dikonversi
        cursor.execute(
            "UPDATE pembelian SET status = 'converted' WHERE idPembelian = %s",
            (id_pembelian,)
        )

        db.commit()
        print(f"Sukses mengonversi Pembelian #{id_pembelian}")
        
    except Exception as e:
        db.rollback()
        print(f"Gagal melakukan konversi gudang. Error: {e}")
    finally:
        cursor.close()
        
    return redirect('/kelola_gudang')

def ensure_pembelian_status_column():
    cursor = db.cursor()
    try:
        cursor.execute("SHOW COLUMNS FROM pembelian LIKE 'status'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE pembelian ADD COLUMN status ENUM('pending','converted') NOT NULL DEFAULT 'pending'")
            db.commit()
    except Exception as e:
        print(f"Gagal memastikan kolom status pada tabel pembelian: {e}")
    finally:
        cursor.close()


@app.route('/laporan_owner')
def laporan_owner():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "owner":
        return "Akses ditolak"

    cursor = db.cursor(buffered=True)

    cursor.execute("""
        SELECT
            idTransaksi,
            tanggal,
            total,
            bayar,
            kembalian
        FROM transaksi
        ORDER BY idTransaksi asc
    """)

    laporan = cursor.fetchall()

    return render_template(
        'owner/laporan_owner.html',
        laporan=laporan
    )
# pendapatan owner
@app.route('/pendapatan_owner')
def pendapatan_owner():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "owner":
        return "Akses ditolak"

    cursor = db.cursor(buffered=True)

    cursor.execute("""
        SELECT IFNULL(SUM(total),0)
        FROM transaksi
    """)

    totalPendapatan = cursor.fetchone()[0]

    return render_template(
        'owner/pendapatan_owner.html',
        totalPendapatan=totalPendapatan
    )
@app.route('/statistika_owner')
def statistika_owner():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "owner":
        return "Akses ditolak"

    cursor = db.cursor(buffered=True)

    # total transaksi
    cursor.execute("SELECT COUNT(*) FROM transaksi")
    totalTransaksi = cursor.fetchone()[0]

    # total pembelian
    cursor.execute("SELECT COUNT(*) FROM pembelian")
    totalPembelian = cursor.fetchone()[0]

    # total pendapatan
    cursor.execute("SELECT IFNULL(SUM(total),0) FROM transaksi")
    totalPendapatan = cursor.fetchone()[0]

    # data grafik per bulan
    cursor.execute("""
        SELECT MONTH(tanggal), SUM(total)
        FROM transaksi
        GROUP BY MONTH(tanggal)
        ORDER BY MONTH(tanggal)
    """)

    data = cursor.fetchall()

    bulan = []
    pendapatan = []

    for x in data:
        bulan.append(str(x[0]))
        pendapatan.append(int(x[1]))

    return render_template(
        'owner/statistika_owner.html',
        totalTransaksi=totalTransaksi,
        totalPembelian=totalPembelian,
        totalPendapatan=totalPendapatan,
        bulan=bulan,
        pendapatan=pendapatan
    )

# pembelian owner
@app.route('/pembelian_owner')
def pembelian_owner():

    if 'idUser' not in session:
        return redirect('/')

    if session['akses'] != "owner":
        return "Akses ditolak"

    cursor = db.cursor(buffered=True)

    cursor.execute("""
        SELECT *
        FROM pembelian
        ORDER BY idPembelian DESC
    """)

    pembelian = cursor.fetchall()

    return render_template(
        'owner/pembelian_owner.html',
        pembelian=pembelian
    )


if __name__ == '__main__':
    app.run(debug=True)