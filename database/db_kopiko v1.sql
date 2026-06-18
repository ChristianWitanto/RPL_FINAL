create database db_kopiko;

use db_kopiko;

create table pengguna(
	idUser int auto_increment primary key,
    username varchar(255) not null,
    sandi varchar(255) not null,
    akses enum("admin","kasir","owner") not null
);
create table produk(
	idProduk int auto_increment primary key,
    namaProduk varchar(255) not null,
    hargaJual int not null,
    stok int not null
);

create table transaksi(
	idTransaksi int auto_increment primary key,
    tanggal date not null,
    total int not null,
    idUser int,
    bayar INT NOT NULL,
    kembalian INT NOT NULL,
    foreign key (idUser) references pengguna(idUser)
    on delete restrict
);

create table detailTransaksi(
	idDetailTransaksi int auto_increment primary key,
    idTransaksi int,
    idProduk int,
    jumlah int not null,
    harga int not null,
    subtotal int not null,
    foreign key (idTransaksi) references transaksi(idTransaksi) on delete cascade,
    foreign key (idProduk) references produk(idProduk) on delete restrict
);

create table pembelian(
	idPembelian int auto_increment primary key,
    tanggal date not null,
    total int not null,
    idUser int,
    namaSupplier varchar(255),
    status enum('pending','converted') not null default 'pending',
    foreign key (idUser) references pengguna(idUser) on delete restrict
);

create table detailPembelian(
	idDetailPembelian int auto_increment primary key,
    idPembelian int,
    idProduk int,
    jumlah int not null,
    hargabeli int,
    subtotal int,
    foreign key (idPembelian) references pembelian(idPembelian) on delete cascade,
    foreign key (idProduk) references produk(idProduk) on delete restrict
);

