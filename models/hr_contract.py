# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
import pypandoc
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

J_DATE_FORMAT = "%Y/%m/%d"
B_NAZANIN = 'B Nazanin'
B_YEKAN = 'B Yekan'
IRANSansFaNum = 'IRANSansFaNum'
class SdHrContractContract(models.Model):
    _inherit = 'hr.contract'

    doc_template = fields.Many2one('hr.contract.doc_template')
    output_file = fields.Binary(string="Generated File", readonly=True)
    output_pdf = fields.Binary(string="PDF File", readonly=True)

    subject = fields.Char(requird=True, translate=True)
    issue_date = fields.Date(required=True)
    identification_id = fields.Char(related='employee_id.identification_id')
    project_name = fields.Many2one('hr.employee.project_name')
    father_name = fields.Char(related='employee_id.father_name')
    representative = fields.Many2one('hr.employee')

    hourly_rate = fields.Integer()
    hourly_rate_text = fields.Char()
    bond = fields.Integer()





    def regenerate_template(self):
        def set_english_font(run):
            text_font = B_YEKAN
            run.font.name =  text_font # Set an appropriate English
            run._element.rPr.rFonts.set(qn('w:eastAsia'), text_font)
            run.font.size = Pt(12) # Set font size as needed

        for record in self:
            # Load the .docx file from the binary field
            template_data = base64.b64decode(record.doc_template.template_file)
            template = Document(BytesIO(template_data))
            html_content = ''

            # Replace placeholders with actual values
            variable_list = [('v_employee_name', 'record.employee_id.name'),
                             ('v_employee_father', 'record.employee_id.father_name'),
                             ('v_employee_id_no', 'record.employee_id.identification_id'),
                             ('v_contract_no', 'record.name'),
                             ('v_contract_type', 'record.contract_type_id.name'),
                             ('v_contract_project', 'record.project_name.name'),
                             ('v_contract_subject', 'record.subject'),
                             ('v_contract_job', 'record.job_id.name'),
                             ('v_contract_hourly_rate', 'f"{record.hourly_rate:,}"'),
                             ('v_contract_hourly_text', 'record.hourly_rate_text'),
                             ('v_contract_bond', 'str(record.bond)'),
                             ('v_contract_issue_date', 'jdatejs(record.issue_date, J_DATE_FORMAT)'),
                             ('v_contract_start_date', ' jdatejs(record.date_start, J_DATE_FORMAT)'),
                             ('v_contract_end_date', ' jdatejs(record.date_end, J_DATE_FORMAT)'),
                             ]
            for paragraph in template.paragraphs:
                for run in paragraph.runs:
                    for variable in variable_list:
                        if variable[0] in run.text:
                            run.text = run.text.replace(variable[0], eval(variable[1]) or '')
                            if variable[0] in ['v_contract_issue_date', 'v_contract_no',
                                               'v_contract_issue_date', 'v_contract_start_date',  'v_contract_end_date',  ]:
                                set_english_font(run)
                            else:
                                run.font.name = B_NAZANIN
                            # print(run.text)






                # self._replace_and_format(paragraph, '{{employee_name}}', record.employee_id.name or '', bold=True, )
                # self._replace_and_format(paragraph, '{{نام-کارمند}}', record.employee_id.name or '', bold=True, )
                # self._replace_and_format(paragraph, '{{employee_father}}', record.employee_id.father_name or '', bold=True, )
                # self._replace_and_format(paragraph, '{{employee_id_no}}', record.employee_id.identification_id or '', bold=True, )
                # self._replace_and_format(paragraph, '{{contract_no}}', record.name or '', bold=True, )
                # self._replace_and_format(paragraph, '{{contract_type}}', record.contract_type_id.name or '', bold=True, )
                # self._replace_and_format(paragraph, '{{contract_project}}', record.project_name.name or '', bold=True, )
                # self._replace_and_format(paragraph, '{{contract_subject}}', record.subject or '', bold=True, )
                # self._replace_and_format(paragraph, '{{موضوع-قرارداد}}', record.subject or '', bold=True, )
                # self._replace_and_format(paragraph, '{{contract_job}}', record.job_id.name or '', bold=True, )
                # self._replace_and_format(paragraph, '{{contract_hourly_rate}}', f"{record.hourly_rate}" or '', bold=True, )
                # self._replace_and_format(paragraph, '{{contract_hourly_rate_text}}', record.hourly_rate_text or '', bold=True, )
                # self._replace_and_format(paragraph, '{{contract_bond}}', f"{record.bond}" or '', bold=True, )
                # self._replace_and_format(paragraph, '{{contract_issue_date}}', jdatejs(record.issue_date, J_DATE_FORMAT) or '', bold=True, )
                # self._replace_and_format(paragraph, '{{contract_start_date}}', jdatejs(record.date_start, J_DATE_FORMAT) or '', bold=True, )
                # self._replace_and_format(paragraph, '{{contract_end_date}}', jdatejs(record.date_end, J_DATE_FORMAT) or '', bold=True, )



                # for run in paragraph.runs:
                #     run.font.name = B_NAZANIN

                html_content += f"<p>{html_escape(paragraph.text)}</p>"
                # paragraph.text = paragraph.text.replace('{{employee_name}}', record.employee_id.name or '')
                # paragraph.text = paragraph.text.replace('{{موضوع-قرارداد}}', record.employee_id.name or '')
                # paragraph.text = paragraph.text.replace('{{company_name}}', self.env.company.name or '')
                # paragraph.text = paragraph.text.replace('{{start_date}}', str(record.start_date) or '')
                # paragraph.text = paragraph.text.replace('{{manager_name}}', record.manager_name or '')
                pass
            # Step 2: Define placeholders and their replacements

            replacements = {
                'v_employee_name': record.employee_id.name or '',
                'v_company_representative': record.representative.name or '',
            }

            # Step 3: Replace placeholders in the document's tables
            self.replace_table_placeholders(template, replacements)



            # Save the modified file into a binary field
            output_stream = BytesIO()
            template.save(output_stream)
            record.output_file = base64.b64encode(output_stream.getvalue())
            output_stream.close()



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
            html_content += "</body></html>"
            pdf_content = self.env['ir.actions.report']._run_wkhtmltopdf([html_content])
            record.output_pdf = base64.b64encode(pdf_content).decode("UTF-8")

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

    def replace_table_placeholders(self, document, replacements):
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
                                run.font.name = B_NAZANIN


    def _replace_and_format(self, paragraph, placeholder, value, bold=False, italic=False, font_size=None, color=None):
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
            run.font.name = B_NAZANIN
            # Add text after the placeholder
            if parts[1]:
                paragraph.add_run(parts[1])



class SdHrContractContractType(models.Model):
    _name = 'hr.contract.doc_template'
    _description = "Keep contract type templates"


    name = fields.Char(required=True)
    contract_type = fields.Many2one('hr.contract.type')
    template_file = fields.Binary(string="Template File", required=True, attachment=True)


