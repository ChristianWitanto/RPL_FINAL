function setHarga(select){

    let harga =
        select.options[select.selectedIndex]
        .getAttribute('data-harga')

    let stok =
        select.options[select.selectedIndex]
        .getAttribute('data-stok')

    let tipe =
        select.options[select.selectedIndex]
        .getAttribute('data-tipe')

    let row = select.parentElement.parentElement

    row.querySelector('.harga').value = harga

    let stokInput = row.querySelector('.stok')
    if (tipe === 'langsung') {
        stokInput.value = stok || '0'
    } else {
        stokInput.value = '-'
    }

    hitungSubtotal(select)
}

function hitungSubtotal(element){

    let row = element.parentElement.parentElement

    let harga = row.querySelector('.harga').value
    let qty = row.querySelector('.qty').value

    let subtotal = harga * qty

    row.querySelector('.subtotal').value = subtotal

    hitungTotal()
}

function hitungTotal(){

    let subtotal =
        document.querySelectorAll('.subtotal')

    let total = 0

    subtotal.forEach(function(item){

        total += Number(item.value)

    })

    document.getElementById('total').value = total

    hitungKembalian()
}

function tambahBaris(){

    let table =
        document.querySelector('#tabelProduk tbody')

    let row = table.rows[0].cloneNode(true)

    row.querySelector('select').selectedIndex = 0
    row.querySelector('.harga').value = ""
    row.querySelector('.qty').value = 1
    row.querySelector('.subtotal').value = ""
    row.querySelector('.stok').value = ""

    table.appendChild(row)
}

function hapusBaris(button){

    let row = button.parentElement.parentElement

    row.remove()

    hitungTotal()
}

function hitungKembalian(){

    let total =
        Number(document.getElementById('total').value)

    let bayar =
        Number(document.getElementById('bayar').value)

    let kembalian = bayar - total

    document.getElementById('kembalian').value =
        kembalian
}


