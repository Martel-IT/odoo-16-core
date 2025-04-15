/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, 'fix_list_dropdown_position', {
    async render() {
        await this._super.apply(this, arguments);
        console.log("🔧 Fixing Odoo ListView dropdown positioning...");

        setTimeout(() => {
            document.querySelectorAll('.o-dropdown--menu.dropdown-menu.d-block').forEach(menu => {
                let filterButton = document.querySelector('.o_list_buttons .o_dropdown_toggle');

                if (filterButton) {
                    let buttonRect = filterButton.getBoundingClientRect();

                    console.log("📌 Manually repositioning dropdown...");

                    menu.style.setProperty('position', 'absolute', 'important');
                    menu.style.setProperty('top', (buttonRect.bottom + 5) + 'px', 'important');
                    menu.style.setProperty('left', (buttonRect.left - 200) + 'px', 'important'); 
                    menu.style.setProperty('min-width', '250px', 'important');
                    menu.style.setProperty('z-index', '1051', 'important');
                    menu.style.setProperty('display', 'block', 'important');
                }
            });
        }, 200);
    }
});
