from odoo import models, fields, api, _
import json

from odoo.exceptions import ValidationError
from icecream import ic
from jdatetimext import jdatejs
import io
import xlsxwriter
import base64





class SdHrContractDuplacate(models.TransientModel):
    _name = 'sd_hr_contracts.contract_report'
    _description = "sd_hr_contracts.contract_report"
    # _rec_name = 'employee_id'
    employee_id = fields.Many2one('hr.employee')

    def all_employees_contract(self):
        emp_domain = []
        contract_model = self.env['hr.contract']
        employee_model = self.env['hr.employee']
        attachment_model = self.env['ir.attachment']
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        contract_url = f"{base_url}/odoo/employee-contracts/"
        employee_url = f"{base_url}/odoo/employees/"
        today = fields.Date.today()
        YES = _('Yes')
        NO = _('No')

        employees = employee_model.search(emp_domain, order='barcode')

        # for employee in employees:
        #     self.create({'employee_id': employee.id})
        contracts = contract_model.search([ ('employee_id.active', '!=', False)], order='date_end desc').grouped('employee_id')

        # create list of employees with no contract
        employees_has_contract = contracts.keys()
        # employees_no_contract = list([emp for emp in employees if emp not in employees_has_contract])
        # create list of contracts base on employees

        report_1 = [[_('Name'),
                     _('Barcode'),
                     _('Location'),
                     _('Department'),
                     _('Contract No'),
                     _('State'),
                     _('Is Valid?'),
                     _('End Date'),
                     _('Running Count')]]
        EMP_COL = 0
        CON_COL = 4
        ISVALID_COL = 6

        for emp, emp_contracts in contracts.items():
            # print(f">>>>>>>>>>>>\n {emp.barcode}\n {emp_contracts}")
            # check if there is only one active contract
            running_count = len(list(con for con in emp_contracts if con.state == 'open'))
            running_contract = '' if running_count == 1 else f"{_('Running contract count: ')}[{running_count}]"
            if running_count == 1:
                emp_contract = list([rec for rec in emp_contracts if rec.state == 'open'])[0]
            else:
                emp_contract = emp_contracts[0]

            # check if the active contract is valid at the time
            if emp_contract and emp_contract.date_end:
                state = dict(emp_contract._fields['state']._description_selection(self.env)).get(emp_contract.state)
                is_valid = YES if emp_contract.date_end > today else NO
                date_end = jdatejs(emp_contract.date_end, "%Y/%m/%d")
                report_1.append([(emp.id, emp.name), emp.barcode, emp.work_location_id.name, emp.department_id.name, (emp_contract.id, emp_contract.name), state, is_valid, date_end, running_contract])
            else:
                report_1.append([(emp.id, emp.name), emp.barcode, emp.work_location_id.name, emp.department_id.name, (False, ''), '', ''])
            # check the validity days of the active contract
            pass

        # print(f">>>>>>>>>>>>>>>>>>\n {employees}")
        # ic(report_1[:50])
        # is_valid = sum(list(rec for rec in report_1 if str(rec[3]) == YES))
        # no_barcode = sum(list(rec for rec in report_1 if not rec[1]))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        is_fa = self.env.context.get('lang', '') == 'fa_IR'
        header_style = workbook.add_format({'text_wrap': True,
                                            'font_size': 14,
                                            'bold': True,
                                            'bg_color': '#d0d0d0'})
        header_style.set_align('center')
        row_style = workbook.add_format({'text_wrap': True, 'font_size': '14',  })
        link_style = workbook.add_format({'text_wrap': True, 'font_size': '14', 'font_color': 'blue' })
        row_style_yes = workbook.add_format({'text_wrap': True, 'font_size': '14', 'font_color': 'green',  })
        sheet = workbook.add_worksheet("Data")
        sheet.freeze_panes(1, 0)
        sheet.autofilter(0, 0, len(report_1), len(report_1[0]), )

        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 10)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 35)
        sheet.set_column(4, 7, 15)
        sheet.set_column(8, 8, 40)

        if is_fa:
            font_name = 'B Nazanin'
            font_charset = 178
            sheet.right_to_left()
        else:
            font_name = 'Calibri'
            font_charset = 0
        header_style.set_font(font_name)
        header_style.set_font_family(0)
        header_style.set_font_charset(font_charset)
        row_style.set_font(font_name)
        row_style.set_font_family(0)
        row_style.set_font_charset(font_charset)
        link_style.set_font(font_name)
        link_style.set_font_family(0)
        link_style.set_font_charset(font_charset)

        for row_idx, row in enumerate(report_1):
            for col_idx, value in enumerate(row):
                if row_idx:
                    if col_idx == EMP_COL:
                        sheet.write_url(row_idx, col_idx, f"{employee_url}{value[0]}", link_style, string=value[1])
                    elif col_idx == CON_COL and value[0]:
                        sheet.write_url(row_idx, col_idx, f"{contract_url}{value[0]}", string=value[1])
                    elif col_idx == ISVALID_COL and value == YES:
                        sheet.write(row_idx, col_idx, value, row_style_yes)
                    else:
                        value = '' if isinstance(value, tuple) else value
                        sheet.write(row_idx, col_idx, value or '', row_style)
                else:
                    sheet.write(row_idx, col_idx, value, header_style)


        workbook.close()
        output.seek(0)
        output = base64.b64encode(output.read())


        attach_id = attachment_model.search([('res_model', '=', self._name),
                                             ('res_id', '=', self.id),
                                             ('res_field', '=', 'output_file'),
                                             ])

        # export_data = {
        #     "model": "sd_hr_contracts.contract_report",
        #     "ids": self.ids,
        #     "fields": [
        #         {"name": "employee_id", "label": "Name"},
        #
        #     ],
        #     "domain": [],
        #     "context": self.env.context,
        #     "import_compat": False,
        # }
        #
        # json_data = json.dumps(export_data)
        #
        # url = "/web/export/xlsx?data=" + json_data
        #
        # return {
        #     "type": "ir.actions.act_url",
        #     "url": url,
        #     "target": "self",
        # }





        if len(attach_id) > 1:
            for att in attach_id:
                att.unlink()
            attach_id = False

        if attach_id:
            attach_id.write({
                'datas': output,
                # 'name': self.file_name_generator(record, file_prefix, file_name, output_ext),
                'name': 'HR_Contract_Validation_List.xlsx',

            })
            # logging.warning(f">>>>>>>>> is attach_id")
        else:
            # logging.warning(f">>>>>>>>> is NOT attach_id")
            attach_id = attachment_model.create({
                'res_model': self._name,
                'res_field': False,
                'res_id': self.id,
                'datas': output,
                'name': 'HR_Contract_Validation_List.xlsx',
                # 'name': self.file_name_generator(record, file_prefix, file_name, output_ext),
                'type': 'binary',
            })
        # Note: If not download=1, it opens the pdf file instead of download.
        download_url = '/web/content/%s?download=1' % attach_id.id
        # download_url = '/web/content/%s' % attach_id.id
        # logging.info(f"\n >>>>>>>> download_url DOCX: {download_url}")
        return {'type': 'ir.actions.act_url',
                'url': download_url,
                'target': 'self',
                }


