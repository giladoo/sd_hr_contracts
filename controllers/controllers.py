# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request, content_disposition
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import datetime
import jdatetime
import logging
import io
from io import BytesIO
import base64
from docx import Document


class SdHrContractDownload(http.Controller):
    @http.route('/web/hrcontracts/download/', type='http', auth="user",)
    def download(self, **kwargs):
        # print(f'\n download: {kwargs}')
        params = ''
        record = []
        context = request.env.context
        contract_model = http.request.env['hr.contract']
        lang = context and context.get('lang')
        res_id = kwargs.get('id', False)
        if request.env.user.has_group('hr.group_hr_manager'):
            record = contract_model.search([('id', '=', int(res_id))]) if res_id else []
        logging.info(f'\n   res_id: {res_id} >> record: {record}')
        if record:
            try:
                output_file = base64.b64decode(record.output_file)
                docx = Document(BytesIO(output_file))
                buffer = BytesIO()
                docx.save(buffer)
                buffer.seek(0)
                file_data = buffer.read()
            except Exception as e:
                logging.error(f"/web/hrcontracts/download/ : rec_id:{record.id} \n ERROR: {e}")
                file_data = ''
            # Return the file as a download response
            res = request.make_response( file_data,
                                          headers=[
                                              ('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                                              ('Content-Disposition', f'attachment; filename={record.output_file_name or "generated_doc.docx"}')
                                                ]
                                          )

        else:
            res = request.not_found()

        return res





