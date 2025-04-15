odoo.define('custom_expense_limit.analytic_field', function (require) {
    'use strict';

    const AnalyticField = require('@analytic/js/analytic_field')[Symbol.for('default')];
    const { patch } = require('@web/core/utils/patch');

    patch(AnalyticField.prototype, 'custom_expense_limit', {
        onProjectAdd() {
            if (Object.keys(this.props.value || {}).length >= 1) {
                this.env.services.notification.add(
                    _t("Only one project can be selected per expense."),
                    { type: 'danger' }
                );
                return;
            }
            this._super(...arguments);
        },
    });
});
