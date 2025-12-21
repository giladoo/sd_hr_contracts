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

    def all_employees_contract(self):
        LIMIT_COUNT = 50

        emp_domain = []
        contract_model = self.env['hr.contract']
        employee_model = self.env['hr.employee']
        attachment_model = self.env['ir.attachment']
        today = fields.Date.today()
        YES = _('Yes')
        NO = _('No')

        employees = employee_model.search(emp_domain, order='barcode')
        contracts = contract_model.search([ ('employee_id.active', '!=', False)], order='date_end desc').grouped('employee_id')

        employees_dict = dict()

        # create list of employees with no contract
        employees_has_contract = contracts.keys()
        employees_no_contract = list([emp for emp in employees if emp not in employees_has_contract])
        # create list of contracts base on employees

        print(f">>>>>>>>>>>>>>>>>>\n {len(employees_has_contract)}    {len(employees_no_contract)}")

        report_1 = [[_('Name'), _('Barcode'), _('State'), _('Is Valid?'), _('End Date'), _('Running Count')]]

        for emp, emp_contracts in contracts.items():
            print(f">>>>>>>>>>>>\n {emp.barcode}\n {emp_contracts}")
            # check if there is only one active contract
            running_count = len(list(con for con in emp_contracts if con.state == 'open'))
            running_contract = '' if running_count == 1 else f"{_('Running contract count: ')}[{running_count}]"


            # check if the active contract is valid at the time
            if emp_contracts and emp_contracts[0].date_end:
                # if emp_contracts[0].state in ['open', 'draft']
                if running_count == 1:
                    emp_contract = list([rec for rec in emp_contracts if rec.state == 'open'])[0]
                else:
                    emp_contract = emp_contracts[0]


                state = dict(emp_contract._fields['state']._description_selection(self.env)).get(emp_contract.state)
                is_valid = YES if emp_contract.date_end > today else NO
                date_end = jdatejs(emp_contract.date_end, "%Y/%m/%d")
                report_1.append([emp.name, emp.barcode, state, is_valid, date_end, running_contract])
            else:
                report_1.append([emp.name, emp.barcode, '', '', ''])
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
        row_style_yes = workbook.add_format({'text_wrap': True, 'font_size': '14', 'font_color': 'green',  })
        sheet = workbook.add_worksheet("Data")
        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 4, 20)
        sheet.set_column(5, 5, 40)
        sheet.autofilter('A1:E3000')
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

        for row_idx, row in enumerate(report_1):
            for col_idx, value in enumerate(row):
                if row_idx:
                    if col_idx == 3 and value == YES:
                        sheet.write(row_idx, col_idx, value, row_style_yes)
                    else:
                        sheet.write(row_idx, col_idx, value, row_style)
                else:
                    sheet.write(row_idx, col_idx, value, header_style)


        workbook.close()
        output.seek(0)
        output = base64.b64encode(output.read())


        attach_id = attachment_model.search([('res_model', '=', self._name),
                                             ('res_id', '=', self.id),
                                             ('res_field', '=', 'output_file'),
                                             ])
        # logging.warning(f">>>>>>>>>  attach_id {attach_id}")
        # return
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