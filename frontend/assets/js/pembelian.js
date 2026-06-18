

            // TAMBAH BARIS
            document.getElementById('tambahBaris').addEventListener('click', function () {

                let tbody = document.querySelector('#tabelBarang tbody');

                let tr = document.createElement('tr');

                tr.innerHTML = `

    <td>
        <input
            type="text"
            name="nama_barang[]"
            class="form-control"
            required>
    </td>

    <td>
        <input
            type="number"
            name="jumlah[]"
            class="form-control jumlah"
            value="1"
            min="1"
            required>
    </td>

    <td>

        <select
            name="satuan[]"
            class="form-select"
            required>

            <option value="">
                Pilih
            </option>

            <option value="Kg">
                Kg
            </option>

            <option value="Gram">
                Gram
            </option>

            <option value="Liter">
                Liter
            </option>

            <option value="Ml">
                Ml
            </option>

            <option value="Pcs">
                Pcs
            </option>

        </select>

    </td>

    <td>
        <input
            type="number"
            name="harga_beli[]"
            class="form-control harga"
            value="0"
            min="0"
            required>
    </td>

    <td>
        <input
            type="text"
            class="form-control subtotal"
            value="0"
            readonly>
    </td>

    <td class="text-center">
        <button
            type="button"
            class="btn btn-danger btn-sm hapus">

            Hapus

        </button>
    </td>

`;
                tbody.appendChild(tr);

            });



            // HITUNG TOTAL
            document.addEventListener('input', function () {

                hitungTotal();

            });


            function hitungTotal() {

                let rows = document.querySelectorAll('#tabelBarang tbody tr');

                let grandTotal = 0;

                rows.forEach(function (row) {

                    let jumlah = row.querySelector('.jumlah').value || 0;
                    let harga = row.querySelector('.harga').value || 0;

                    let subtotal = jumlah * harga;

                    row.querySelector('.subtotal').value = subtotal;

                    grandTotal += subtotal;

                });

                document.getElementById('grandTotal').value = grandTotal;

            }



            // HAPUS BARIS
            document.addEventListener('click', function (e) {

                if (e.target.classList.contains('hapus')) {

                    e.target.closest('tr').remove();

                    hitungTotal();

                }

            });


        // --- 1. HITUNG OTOMATIS REAL-TIME (INPUT BARU & MODAL EDIT) ---
        document.addEventListener('input', function (e) {
            if (e.target.classList.contains('jumlah') || e.target.classList.contains('harga')) {
                let baris = e.target.closest('.baris-barang');
                let jumlah = parseFloat(baris.querySelector('.jumlah').value) || 0;
                let harga = parseFloat(baris.querySelector('.harga').value) || 0;
                
                // Set Nilai Sub Total pada baris bersangkutan
                baris.querySelector('.subtotal').value = jumlah * harga;
                
                // Cari tahu apakah perubahan terjadi di dalam form Modal atau Form Utama
                let dalamModal = e.target.closest('.modal');
                if (dalamModal) {
                    hitungTotalModal(dalamModal);
                } else {
                    hitungTotalUtama();
                }
            }
        });

        // Fungsi kalkulasi Grand Total Form Utama
        function hitungTotalUtama() {
            let subTotals = document.querySelectorAll('#tabelBarang .subtotal');
            let total = 0;
            subTotals.forEach(item => { total += parseFloat(item.value) || 0; });
            document.getElementById('grandTotal').value = total;
        }

        // Fungsi kalkulasi Grand Total Form Modal yang sedang aktif
        function hitungTotalModal(modalElement) {
            let subTotals = modalElement.querySelectorAll('.subtotal');
            let total = 0;
            subTotals.forEach(item => { total += parseFloat(item.value) || 0; });
            modalElement.querySelector('.modal-grand-total').value = total;
        }


        // --- 2. FITUR TAMBAH BARIS PADA FORM INPUT UTAMA ---
        document.getElementById('tambahBaris').addEventListener('click', function () {
            let tbody = document.querySelector('#tabelBarang tbody');
            let barisBaru = `
                <tr class="baris-barang">
                    <td><input type="text" name="nama_barang[]" class="form-control" placeholder="Nama barang" required></td>
                    <td><input type="number" name="jumlah[]" class="form-control jumlah" value="1" min="1" required></td>
                    <td>
                        <select name="satuan[]" class="form-select" required>
                            <option value="">Pilih</option>
                            <option value="Kg">Kg</option>
                            <option value="Gram">Gram</option>
                            <option value="Liter">Liter</option>
                            <option value="Ml">Ml</option>
                            <option value="Pcs">Pcs</option>
                        </select>
                    </td>
                    <td><input type="number" name="harga_beli[]" class="form-control harga" value="0" min="0" required></td>
                    <td><input type="text" class="form-control subtotal" value="0" readonly></td>
                    <td class="text-center"><button type="button" class="btn btn-danger btn-sm hapus">Hapus</button></td>
                </tr>`;
            tbody.insertAdjacentHTML('beforeend', barisBaru);
        });


        // --- 3. FITUR HAPUS BARIS PADA FORM INPUT UTAMA ---
        document.querySelector('#tabelBarang tbody').addEventListener('click', function (e) {
            if (e.target.classList.contains('hapus')) {
                let baris = e.target.closest('.baris-barang');
                let semuaBaris = document.querySelectorAll('#tabelBarang tbody .baris-barang');
                
                // Mencegah semua baris terhapus habis (minimal sisa 1 baris)
                if (semuaBaris.length > 1) {
                    baris.remove();
                    hitungTotalUtama();
                } else {
                    alert('Minimal harus ada 1 barang dalam daftar pembelian!');
                }
            }
        });
    