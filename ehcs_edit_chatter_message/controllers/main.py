# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class ChatterMessage(http.Controller):

    @http.route(['/get_message_details'], type='json', auth="user")
    def get_message_details(self, **kwargs):
        message = request.env['mail.message'].browse(kwargs.get('message_id'))
        msg_body = message.body[3:-4]
        return {'msg_body': msg_body}
