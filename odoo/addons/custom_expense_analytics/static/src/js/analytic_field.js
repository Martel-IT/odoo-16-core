odoo.define('custom_expense.analytic_field', function (require) {
"use strict";

var AnalyticField = require('analytic.AnalyticDistribution');
var registry = require('web.field_registry');

var CustomAnalyticField = AnalyticField.extend({
    template: 'AnalyticDistribution',
    
    _onAddLine: function (ev) {
        if (Object.keys(this.value || {}).length === 0) {
            return this._super.apply(this, arguments);
        }
        // Se esiste già una riga, non permettere l'aggiunta di altre
        return false;
    },
});

registry.add('analytic_distribution', CustomAnalyticField);

return CustomAnalyticField;

});
