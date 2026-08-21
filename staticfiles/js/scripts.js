/*!
* Start Bootstrap - Shop Homepage v5.0.6 (https://startbootstrap.com/template/shop-homepage)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-shop-homepage/blob/master/LICENSE)
*/
document.addEventListener('DOMContentLoaded', function () {
    var nav = document.getElementById('navbarPrincipal');
    var menuToggle = document.getElementById('menu-toggle');

    if (nav) {
        var actualizarSombra = function () {
            nav.classList.toggle('con-sombra', window.scrollY > 10);
        };
        actualizarSombra();
        window.addEventListener('scroll', actualizarSombra);
    }

    if (menuToggle) {
        document.querySelectorAll('.lista-nav a[href], .boton-carrito').forEach(function (enlace) {
            enlace.addEventListener('click', function () {
                menuToggle.checked = false;
            });
        });
    }
});