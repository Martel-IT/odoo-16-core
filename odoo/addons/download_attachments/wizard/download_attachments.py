from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import PyPDF2
import base64
import io
from PIL import Image

class DownloadExpAttachment(models.TransientModel):
    _name = "download_exp_attachment"
    _description = 'Download Expense Attachment'

    @api.model
    def generate_pdf(self):
        active_ids = self.env.context.get('active_ids', [])
        return {
            'type': 'ir.actions.act_url',
            'url': f'/download/expense_attachments?active_ids={",".join(map(str, active_ids))}',
            'target': 'new',
        }

    def convert_image_to_pdf(self, image_data):
        image = Image.open(io.BytesIO(image_data))
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        pdf_buffer = io.BytesIO()
        image.save(pdf_buffer, 'PDF')
        pdf_buffer.seek(0)
        return pdf_buffer

    @api.model
    def generate_pdf_data(self):
        related_exp_ids = self.env['hr.expense'].search([
            ('sheet_id', 'in', self.env.context.get('active_ids', []))
        ]).ids
        
        atms = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.expense'),
            ('res_id', 'in', related_exp_ids)
        ])

        if not atms:
            raise ValidationError('The report does not have attachments')

        pdfWriter = PyPDF2.PdfFileWriter()
        
        for atm in atms:
            decoded_data = base64.b64decode(atm.datas)
            
            if atm.mimetype == "application/pdf":
                file_reader = PyPDF2.PdfFileReader(io.BytesIO(decoded_data), strict=False)
                for pageNum in range(file_reader.numPages):
                    pdfWriter.addPage(file_reader.getPage(pageNum))
            
            elif atm.mimetype in ['image/jpeg', 'image/png', 'image/jpg']:
                try:
                    pdf_buffer = self.convert_image_to_pdf(decoded_data)
                    image_pdf = PyPDF2.PdfFileReader(pdf_buffer)
                    pdfWriter.addPage(image_pdf.getPage(0))
                except Exception as e:
                    raise ValidationError(f'Error converting image {atm.name}: {str(e)}')
            
            else:
                raise ValidationError(f'Unsupported file format for {atm.name}')

        pdf_data = io.BytesIO()
        pdfWriter.write(pdf_data)
        pdf_data.seek(0)
        return pdf_data.getvalue()
