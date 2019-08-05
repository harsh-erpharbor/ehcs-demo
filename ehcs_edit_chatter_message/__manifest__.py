# -*- coding: utf-8 -*-
{
    'name': 'EHCS Edit Chatter Message',
    'version': '11.0.1.0.0',
    'category': 'Mail',
    'author': 'ERP Harbor Consulting Services',
    'website': 'http://www.erpharbor.com',
    'summary': 'EHCS Edit Chatter Message',
    'description': """
EHCS Edit Chatter Message
     """,
    'depends': [
        'mail',
    ],
    'data': [
        'views/message_templates.xml',
    ],
    'qweb': [
        'static/src/xml/thread.xml',
    ],
    'installable': True,
}
