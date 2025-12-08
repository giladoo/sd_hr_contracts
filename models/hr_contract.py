# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
# import pypandoc
import datetime
import pytz

import jdatetime
from jdatetimext import j_start, j_start_end_js, jdatejs
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.shared import Pt
from io import BytesIO
import base64
import os
from tempfile import NamedTemporaryFile
from odoo.tools import html_escape
from bs4 import BeautifulSoup
from icecream import ic
import zipfile
import io


J_DATE_FORMAT = "%Y/%m/%d"
B_NAZANIN = 'B Nazanin'
B_YEKAN = 'B Yekan'
IRANSansFaNum = 'IRANSansFaNum'
ARIAL = 'Arial'


class SdHrContractContract(models.Model):
    _inherit = 'hr.contract'

    name = fields.Char('Reference', copy=False, readonly=True, default=lambda x: _('New'))
    doc_template = fields.Many2one('hr.contract.doc_template', )
    output_file = fields.Binary(string="Generated File", readonly=False, copy=False,)
    output_file_name = fields.Char(copy=False, )
    output_pdf_name = fields.Char(copy=False, )
    output_pdf = fields.Binary(string="PDF File", readonly=True, copy=False, )

    subject = fields.Char(requird=True, translate=True)
    issue_date = fields.Date(required=False, copy=False, default=lambda self: fields.date.today())
    project_name = fields.Many2one('sd_projects.projects', default=lambda self: self.employee_id.project_name.id or False)
    # TODO: It must have a default value
    representative = fields.Many2one('hr.employee', )
    manager = fields.Many2one('hr.employee', )
    contract_type_id_payment = fields.Selection(related='contract_type_id.payment')
    # PartTime Contract
    hourly_rate = fields.Integer()
    hourly_rate_text = fields.Char()
    bond = fields.Integer(default=10)

    # FullTime Contract
    pr_base = fields.Integer()
    pr_absorbent = fields.Integer()
    pr_job = fields.Integer()
    pr_marriage = fields.Integer()
    pr_commute = fields.Integer()
    pr_other = fields.Integer()
    pr_children = fields.Integer()
    pr_housing = fields.Integer()
    pr_groceries = fields.Integer()
    pr_yearly_raise = fields.Integer()
    pr_bonus = fields.Integer()
    pr_rotation = fields.Integer()

    pr_friday_work = fields.Integer()
    pr_over_time = fields.Integer()
    pr_shift_work = fields.Integer()
    pr_environment_bonus = fields.Integer()
    pr_onshore_rig_bonus = fields.Integer()

    pr_sum = fields.Integer(compute='_pr_sum', store=True)

    extra_payment = fields.Integer()
    total_payment = fields.Integer(compute='_pr_sum', store=True)

    extra_commute = fields.Integer()
    '''
        pr_base         حقوق پایه 
        فوق العاده جذب    pr_absorbent
        فوق العاده      شغل pr_job
        حق تاهل     pr_marriage
        ایاب و ذهاب      pr_commute
        سایر مزایا        pr_other
        حق اولاد     pr_children
        حق مسکن      pr_housing
        بن و خواروبار    pr_groceries
        پاداش و بهره وری     pr_bonus
        فوق العاده اقماری     pr_rotation
        جمع قرارداد          pr_sum
    '''

    additional_note = fields.Text(copy=False, )

    @api.onchange('contract_type_id')
    def contract_type_changed(self):
        for rec in self:
            rec.doc_template = rec.doc_template.search([('contract_type', '=', rec.contract_type_id.id)], limit=1).id or False


    @api.depends('contract_type_id','pr_base',
                 'pr_absorbent', 'pr_job', 'pr_marriage', 'pr_commute', 'pr_other', 'pr_yearly_raise',
                 'pr_children', 'pr_housing', 'pr_groceries', 'pr_rotation', 'extra_payment')
    def _pr_sum(self):
        '''
        Calculates sum of all payroll items
        :return:
        '''
        for rec in self:
            if rec.contract_type_id_payment == 'monthly':
                rec.pr_sum = (rec.pr_base +
                              rec.pr_absorbent  +
                              rec.pr_job  +
                              rec.pr_marriage  +
                              rec.pr_commute  +
                              rec.pr_other  +
                              rec.pr_children  +
                              rec.pr_housing  +
                              rec.pr_groceries +
                              rec.pr_yearly_raise +
                              rec.pr_bonus)
            elif rec.contract_type_id_payment == 'rotational':
                rec.pr_sum = (rec.pr_base +
                              rec.pr_absorbent  +
                              rec.pr_job  +
                              rec.pr_marriage  +
                              rec.pr_children  +
                              rec.pr_housing  +
                              rec.pr_groceries  +
                              rec.pr_friday_work +
                              rec.pr_over_time +
                              rec.pr_shift_work +
                              rec.pr_yearly_raise +
                              rec.pr_environment_bonus +
                              rec.pr_onshore_rig_bonus +
                              rec.pr_rotation)

            elif rec.contract_type_id_payment == 'retired':
                rec.pr_sum = rec.pr_base
            else:
                rec.pr_sum = 0

            rec.total_payment = rec.pr_sum + rec.extra_payment

    def get_select(self, rec, field_name):
        field_name = dict(rec._fields[field_name]._description_selection(self.env)).get(rec[field_name])
        return field_name

    def regenerate_template(self):
        '''
        Get variables from 'sd_hr.variables' then replaces new_values on the docx document.

        :return:
        '''
        for record in self:
            if not record.doc_template:
                record.output_file = ''
                raise ValidationError('There is no template file')
                continue
            variables = []
            value_function_list = []
            numeral_variables = []
            html_variables = []
            variables_dict = {}
            html_content = ''
            # TODO: to make it general we need to make document template module as a general module.

            hr_contract_model = self.env['ir.model'].sudo().search([('model', '=', 'hr.contract')])
            if hr_contract_model:
                variables = self.env['sd_hr.variables'].sudo().search([('model_id', '=', hr_contract_model.id),
                                                                       ('variable', '!=', False),
                                                                       ('model_res_id', '=', record.doc_template.id)])
                if variables:
                    variables_dict = dict({rec.variable: (rec.value_text, self.get_select(rec, 'value_fonts')) if rec.value_source == 'text' else (rec.value_function, self.get_select(rec, 'value_fonts')) for rec in variables})
                    value_function_list = list([rec.variable for rec in variables if rec.value_source == 'function'])

            # Load the .docx file from the binary field
            template_data = base64.b64decode(record.doc_template.template_file)
            template = Document(BytesIO(template_data))

            for paragraph in template.paragraphs:
                for run in paragraph.runs:
                    for variable, new_value in variables_dict.items():
                        if variable in run.text:
                            self.replace_run(record, paragraph, run, variable, value_function_list, numeral_variables,
                                        html_variables, new_value[0], new_value[1] )

            for table in template.tables:
                for row in table.rows:
                    for cell in row.cells:
                        runs = cell.paragraphs[0].runs
                        for run in runs:
                            for variable, new_value in variables_dict.items():
                                if variable in run.text:
                                    self.replace_run(record, table, run, variable, value_function_list, numeral_variables,
                                                     html_variables, new_value[0], new_value[1])

            for doc_sections in template.sections:
                doc_sections_list = [doc_sections.header,
                                     doc_sections.footer,
                                     doc_sections.first_page_header,
                                     doc_sections.first_page_footer,
                                     ]
                for doc_section in doc_sections_list:
                    for paragraph in doc_section.paragraphs:
                        for run in paragraph.runs:
                            for variable, new_value in variables_dict.items():
                                if variable in run.text:
                                    self.replace_run(record, paragraph, run, variable, value_function_list, numeral_variables,
                                                     html_variables, new_value[0], new_value[1])

                    for table in doc_section.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                runs = cell.paragraphs[0].runs
                                for run in runs:
                                    for variable, new_value in variables_dict.items():
                                        if variable in run.text:
                                            self.replace_run(record, table, run, variable, value_function_list,
                                                             numeral_variables,
                                                             html_variables, new_value[0], new_value[1])







            html_content += f"<p>{html_escape(paragraph.text)}</p>"


            # Save the modified file into a binary field
            output_stream = BytesIO()
            template.save(output_stream)

            record.output_file_name = f"{record.with_context(lang='en_US').employee_id.name_cv or 'file'}_{record.name}.docx"
            record.output_pdf_name = f"{record.with_context(lang='en_US').employee_id.name_cv or 'file'}_{record.name}.pdf"
            record.output_file = base64.b64encode(output_stream.getvalue())
            output_stream.close()
            # # Save the modified .docx file to memory
            docx_stream = BytesIO()
            template.save(docx_stream)
            docx_stream.seek(0)
        return docx_stream.getvalue()


            # # Save the modified .docx file to memory
            # docx_stream = BytesIO()
            # template.save(docx_stream)
            # docx_stream.seek(0)
            #
            # # Convert the .docx file to PDF using pypandoc
            # pdf_output = BytesIO()
            # pdf_output.write(pypandoc.convert_file(docx_stream, 'pdf', format='docx'))
            # pdf_output.seek(0)
            #
            # # Save the generated PDF into a binary field
            # record.output_pdf = base64.b64encode(pdf_output.getvalue())
            # pdf_output.close()




            # # Save the modified .docx file to a temporary file
            # with NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
            #     template.save(tmp_docx.name)
            #     tmp_docx_path = tmp_docx.name
            #
            # # Convert the .docx file to PDF using pypandoc
            # try:
            #     # Specify the output PDF file path
            #     with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            #         tmp_pdf_path = tmp_pdf.name
            #
            #     pypandoc.convert_file(tmp_docx_path, 'pdf', format='docx', outputfile=tmp_pdf_path)
            #
            #     # Read the generated PDF and save it to the binary field
            #     with open(tmp_pdf_path, 'rb') as pdf_file:
            #         record.output_file = base64.b64encode(pdf_file.read())
            #
            # except Exception as e:
            #     raise RuntimeError(f"Error during PDF conversion: {e}")
            # finally:
            #     # Clean up temporary files
            #     os.remove(tmp_docx_path)
            #     os.remove(tmp_pdf_path)

            # Step 2: Generate PDF using Odoo's report generation
            # html_content += "</body></html>"
            # pdf_content = self.env['ir.actions.report']._run_wkhtmltopdf([html_content])
            # record.output_pdf = base64.b64encode(pdf_content).decode("UTF-8")

    def generate_and_download_docx(self):
        if self.env.context.get('active_model', False) == 'hr.contract':
            # records = self.browse(self.env.context.get('active_ids', False))
            records = self
        else:
            records = []

        print(f"\n records:\n {self.env.context}\n {records} {self}")
        attachment_model = self.env['ir.attachment']
        if len(records) > 1:
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for rec in records:
                    doc_content = rec.regenerate_template()  # Your function to create `.docx` content
                    # print(doc_content)
                    zip_file.writestr(f"{rec.employee_id.work_location_id.name if rec.employee_id.work_location_id else 'Other'}/{(rec.name).replace('/', '-')} [{rec.employee_id.barcode}] [{rec.employee_id.name}].docx", doc_content)
                    # TODO: if name contains "/", it creates a folder based of str befor it
                    # zip_file.writestr(f"[{rec.name}][{rec.employee_id.name}].docx", doc_content)

            zip_buffer.seek(0)
            zip_buffer = base64.b64encode(zip_buffer.getvalue()).decode('utf-8')
            today = datetime.datetime.now(pytz.timezone(self.env.context.get('tz', 'GMT')))

            # zip_buffer
            # print(zip_buffer)
            attach_id = attachment_model.create({
                'res_model': self._name,
                'res_field': 'output_file',
                'res_id': rec.id,
                'datas': zip_buffer,
                'name': f"Contracts_{jdatejs(today, '%Y%m%d')}_{today.strftime('%H%M%S')}",
                'type': 'binary',
            })
            download_url = '/web/content/%s' % attach_id.id
            return { 'type': 'ir.actions.act_url',
                     'url': download_url,
                     'target': 'self',
                     }
        else:
            record = records if len(records) == 1 else self
            doc_content = record.regenerate_template()  # Your function to create `.docx` content

            attach_id = attachment_model.search([('res_model', '=', self._name),
                                                 ('res_id', '=', record.id),
                                                 ('res_field', '=', 'output_file'),
                                                 ])
            logging.warning(f">>>>>>>>>  attach_id {attach_id}")
            # return
            if  len(attach_id) > 1:
                for att in attach_id:
                    att.unlink()
                attach_id = False

            if attach_id:
                attach_id.write({
                    'datas': record.output_file,
                    'name': f"{(record.name).replace('/', '-')} [{record.employee_id.barcode}] [{record.employee_id.name}].docx",

                })
                logging.warning(f">>>>>>>>> is attach_id")
            else:
                logging.warning(f">>>>>>>>> is NOT attach_id")
                attach_id = attachment_model.create({
                    'res_model': self._name,
                    'res_field': record.output_file,
                    'res_id': record.id,
                    'datas': record.output_file,
                    'name': f"{(record.name).replace('/', '-')} [{record.employee_id.barcode}] [{record.employee_id.name}].docx",
                    'type': 'binary',
                })


            download_url = '/web/content/%s' % attach_id.id
            return { 'type': 'ir.actions.act_url',
                     'url': download_url,
                     'target': 'self',
                     }


    def generate_and_download_docx_old(self):
        self.regenerate_template()

#         download_url = f'/web/hrcontracts/download/?id={self.id}'
#         print(f"""
#         self._name: {self._name}
#         self._origin.id: {self._origin.id}
#     download_url: {download_url}
# """)
        attachment_model = self.env['ir.attachment']
        attach_id = attachment_model.search([('res_model', '=', self._name),
                                             ('res_id', '=', self.id),
                                             ('res_field', '=', 'output_file'),
                                             ])
        logging.warning(f">>>>>>>>>  attach_id {attach_id}")
        if  len(attach_id) > 1:
            for rec in attach_id:
                rec.unlink()
            attach_id = False

        if attach_id:
            attach_id.write({
                'datas': self.output_file,
                'name': self.output_file_name,

            })
            logging.warning(f">>>>>>>>> is attach_id")
        else:
            logging.warning(f">>>>>>>>> is NOT attach_id")
            attach_id = attachment_model.create({
                'res_model': self._name,
                'res_field': 'output_file',
                'res_id': self.id,
                'datas': self.output_file,
                'name': self.output_file_name,
                'type': 'binary',
            })

        download_url = '/web/content/%s' % attach_id.id
        return { 'type': 'ir.actions.act_url',
                 'url': download_url,
                 'target': 'self',
                 }



    def set_english_font(self, run, font_name=B_NAZANIN):
        run.font.name =  font_name
        # Set an appropriate English
        # run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
        run.font.size = Pt(12) # Set font size as needed

    def replace_run(self, record, paragraph, run, variable, value_function_list, numeral_variables, html_variables, new_value, font_name=B_NAZANIN):
        try:
            if variable in value_function_list:
                run.text = run.text.replace(variable, str(eval(new_value) or ''))
            else:
                run.text = run.text.replace(variable, str(new_value) or '')

            if variable in numeral_variables:
                self.set_english_font(run, font_name)
            elif variable in html_variables:
                self.add_html_to_paragraph(paragraph, str(eval(new_value)  or ''), font_name)
            else:
                run.font.name = font_name
        except Exception as e:
            logging.error(f"replace_run > {variable} > {e} ")

    def add_html_to_paragraph(self, paragraph, html, font_name=B_NAZANIN):
        soup = BeautifulSoup(html, 'html.parser')

        for element in soup:
            if element.name == 'strong':
                run = paragraph.add_run(element.get_text())
                run.bold = True
                run.font.name = font_name

            elif element.name == 'li':
                run = paragraph.add_run(f"• {element.get_text()}\n")
                run.font.name = font_name

            elif element.name is None:
                run = paragraph.add_run(element)
                run.font.name = font_name

    def fix_persian(self, date_text):
        """
        Replaces standard slashes with Persian slashes.
        :param date_text: The input date string (e.g., '1403/10/01').
        :return: The date string with Persian slashes.
        """
        return date_text
        return date_text.replace("/", ",").replace("-", "\u659C")

    def fix_persian_ordering(self, text):
        """
        Fixes Persian numbering and text ordering issues by applying RTL control characters.
        :param text: The input text (e.g., '1403/10/01').
        :return: The fixed text for proper display.
        """
        rtl_override = "\u202E"
        pop_directional = "\u202C"
        # return f"{rtl_override}{text}{pop_directional}"
        return f"{text}{pop_directional}"


    def replace_table_placeholders(self, document, replacements, font_name=B_NAZANIN):
        """
        Replaces placeholders in tables within a Word document.
        :param document: Document object
        :param replacements: Dictionary with placeholder keys and their values
        """
        for table in document.tables:
            # table.font.name = B_NAZANIN
            for row in table.rows:
                for cell in row.cells:
                    runs = cell.paragraphs[0].runs
                    for run in runs:
                        for placeholder, value in replacements.items():
                            if placeholder in run.text:
                                run.text = run.text.replace(placeholder, value)
                                run.font.name = font_name


    def _replace_and_format(self, paragraph, placeholder, value, bold=False, font_name=B_NAZANIN, italic=False, font_size=None, color=None):
        """
        Replace a placeholder with formatted text in a paragraph.
        """
        if placeholder in paragraph.text:
            # Split the paragraph text and preserve formatting
            parts = paragraph.text.split(placeholder)
            paragraph.clear()  # Clear existing text

            # Add text before the placeholder
            if parts[0]:
                run = paragraph.add_run(parts[0])

            # Add the formatted variable value
            run = paragraph.add_run(value)
            if bold:
                run.bold = True
            if italic:
                run.italic = True
            if font_size:
                run.font.size = Pt(font_size)
            if color:
                run.font.color.rgb = RGBColor(*color)  # RGB tuple
            run.font.name = font_name
            # Add text after the placeholder
            if parts[1]:
                paragraph.add_run(parts[1])

    def write(self, vals):
        # print(f"\n  >>>   vals: {vals} \n >>>  res: \n")
        if vals.get('contract_type_id', False):
            raise ValidationError(_("Contract Type cannot be updated as contract number is based on it."))
        return super().write(vals)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # print(f"\n >>>>> vals: {vals}\n")
            if not vals.get('name') or vals['name'] == _('New'):
                if not vals.get('contract_type_id'):
                    raise ValidationError(_("Please select a 'Contract Type'"))
                contract_type = self.env['hr.contract.type'].browse(int(vals.get('contract_type_id')))
                year = jdatejs()[0:4]

                contract_no = self.env['ir.sequence'].next_by_code('sd_hr.contracts.name') or _('New')
                vals['name'] = f"{contract_type.code}{year}/{contract_no}"
        return super().create(vals_list)

class SdHrContractContractDocTemplate(models.Model):
    _name = 'hr.contract.doc_template'
    _description = "Keep contract type templates"


    name = fields.Char(required=True)
    contract_type = fields.Many2one('hr.contract.type')
    template_file = fields.Binary(string="Template File", required=True, attachment=True)
    filename = fields.Char()
    variable_no = fields.Char(default=lambda self: _('New'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('variable_no') or vals['variable_no'] == _('New'):
                vals['variable_no'] = self.env['ir.sequence'].next_by_code('sd_hr.variables') or _('New')
        return super().create(vals_list)


class SdHrContractContractType(models.Model):
    _inherit = 'hr.contract.type'


    payment = fields.Selection([('monthly', 'Monthly'),
                                ('hourly', 'Hourly'),
                                ('rotational', 'Rotational'),
                                ('retired', 'Retired'),
                                ('trainee', 'Trainee'),
                                ],
                               default="monthly", required=True)



