const menu = document.querySelectorAll(".sidebar a");


menu.forEach(function(item){

    if(
        item.href == window.location.href
    ){
        item.classList.add("active");
    }
});