odoo.define('custom_menu_style.DropdownPosition', function (require) {
    'use strict';

    const { Component } = require('web.core');

    function updateDropdownPosition(e) {
        if (e.target.closest('.o_add_custom_filter_menu')) {
            const button = e.target;
            const menu = e.target.querySelector('.dropdown-menu, .o-dropdown-menu');
            if (!button || !menu) return;

            const rect = button.getBoundingClientRect();
            const menuRect = menu.getBoundingClientRect();
            
            let top = rect.top;
            let left = rect.right + 4;
            
            if (left + menuRect.width > window.innerWidth) {
                left = rect.left - menuRect.width - 4;
            }
            
            if (top + menuRect.height > window.innerHeight) {
                top = window.innerHeight - menuRect.height - 4;
            }
            
            menu.style.setProperty('--dropdown-top', `${top}px`);
            menu.style.setProperty('--dropdown-left', `${left}px`);
        }
    }

    // Aggiunge l'event listener per il posizionamento del dropdown
    document.addEventListener('shown.bs.dropdown', updateDropdownPosition);
    
    // Aggiunge event listener per ricalcolare la posizione in caso di resize della finestra
    window.addEventListener('resize', function() {
        const openDropdowns = document.querySelectorAll('.o_add_custom_filter_menu.show');
        openDropdowns.forEach(dropdown => {
            const event = { target: dropdown };
            updateDropdownPosition(event);
        });
    });

    return {
        updateDropdownPosition: updateDropdownPosition,
    };
});
