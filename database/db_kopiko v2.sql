create database db_kopiko2;

use db_kopiko2;

CREATE TABLE pengguna(
    idUser INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    sandi VARCHAR(255) NOT NULL,
    akses ENUM('admin','kasir','owner') NOT NULL
);

CREATE TABLE produk(
    idProduk INT AUTO_INCREMENT PRIMARY KEY,
    namaProduk VARCHAR(255) NOT NULL,
    kategori ENUM('Makanan','Minuman') NOT NULL,
    hargaJual INT NOT NULL,
    satuan VARCHAR(50) NOT NULL,
    tipeProduk ENUM('racikan','langsung') NOT NULL
);

CREATE TABLE bahanBaku(
    idBahan INT AUTO_INCREMENT PRIMARY KEY,
    namaBahan VARCHAR(100) NOT NULL,
    stok DECIMAL(10,2) NOT NULL DEFAULT 0,
    satuan VARCHAR(20) NOT NULL
);

CREATE TABLE resep(
    idResep INT AUTO_INCREMENT PRIMARY KEY,
    idProduk INT NOT NULL,
    idBahan INT NOT NULL,
    jumlahPakai DECIMAL(10,2) NOT NULL,

    FOREIGN KEY (idProduk)
    REFERENCES produk(idProduk)
    ON DELETE CASCADE,

    FOREIGN KEY (idBahan)
    REFERENCES bahanBaku(idBahan)
    ON DELETE RESTRICT
);

CREATE TABLE pembelian(
    idPembelian INT AUTO_INCREMENT PRIMARY KEY,
    tanggal DATE NOT NULL,
    total INT NOT NULL,
    namaSupplier VARCHAR(255),
    idUser INT,
    statusPembelian ENUM('pending','converted') NOT NULL DEFAULT 'pending',

    FOREIGN KEY (idUser)
    REFERENCES pengguna(idUser)
    ON DELETE RESTRICT
);

CREATE TABLE detailPembelian(
    idDetailPembelian INT AUTO_INCREMENT PRIMARY KEY,

    idPembelian INT NOT NULL,
    idBahan INT NOT NULL,

    jumlah DECIMAL(10,2) NOT NULL,
    hargaBeli INT NOT NULL,
    subtotal INT NOT NULL,

    FOREIGN KEY (idPembelian)
    REFERENCES pembelian(idPembelian)
    ON DELETE CASCADE,

    FOREIGN KEY (idBahan)
    REFERENCES bahanBaku(idBahan)
    ON DELETE RESTRICT
);

CREATE TABLE transaksi(
    idTransaksi INT AUTO_INCREMENT PRIMARY KEY,

    tanggal DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    total INT NOT NULL,
    bayar INT NOT NULL,
    kembalian INT NOT NULL,

    idUser INT,

    FOREIGN KEY (idUser)
    REFERENCES pengguna(idUser)
    ON DELETE RESTRICT
);

CREATE TABLE detailTransaksi(
    idDetailTransaksi INT AUTO_INCREMENT PRIMARY KEY,

    idTransaksi INT NOT NULL,
    idProduk INT NOT NULL,

    jumlah INT NOT NULL,
    harga INT NOT NULL,
    subtotal INT NOT NULL,

    FOREIGN KEY (idTransaksi)
    REFERENCES transaksi(idTransaksi)
    ON DELETE CASCADE,

    FOREIGN KEY (idProduk)
    REFERENCES produk(idProduk)
    ON DELETE RESTRICT
);

insert into pengguna(username,sandi,akses)values("admin","123","admin");
insert into pengguna(username,sandi,akses)values("owner","123","owner");
insert into pengguna(username,sandi,akses)values("kasir","123","kasir");

INSERT INTO bahanbaku
(namaBahan, stok, satuan)

VALUES
('Kopi', 1000, 'gram'),
('Susu', 5000, 'ml'),
('Gula', 2000, 'gram');

select * from pengguna;


show tables;
drop table bahanbaku;
drop table pengguna;
drop table produk;
drop table resep;
drop table detailtransaksi;
drop table transaksi;
drop table detailpembelian;
drop table pembelian;