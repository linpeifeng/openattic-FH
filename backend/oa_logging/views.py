# -*- coding: utf-8 -*-
"""
 *   Copyright (c) 2017 SUSE LLC
 *
 *  openATTIC is free software; you can redistribute it and/or modify it
 *  under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; version 2.
 *
 *  This package is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
"""

import logging
import re
import os

from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class JSExceptionView(APIView):
    def post(self, request):
        logger.error('Error from client ({}): {}\n  {}\n  {}'.format(
            request.DATA.get('url', ''),
            request.DATA.get('errorMessage', ''),
            request.DATA.get('errorStack', ''),
            request.DATA.get('errorCause', '')))
        return Response()

class OALoggingView(APIView):
    def get(self, request):
        filename = "/var/log/openattic/openattic.log"
        #r = re.compile(r"REQUEST_PATH|ExternalCommandError|ERROR", flags=re.I)
        r = re.compile(r"request_url", flags=re.I)
        search = request.GET.get('search')
        index = 1
        logging_list = []
        for line in reversed(list(open(filename))):
            if r.findall(line):
                if search is not None:
                    if re.search(search.encode('utf8'),line.encode('utf8'), re.I | re.DOTALL | re.VERBOSE) is None:
                        continue
                index = index + 1
                if index > 100:
                    pass
                    #break
                message1 = line.rstrip().split(',', 4)
                messDict = {}
                if len(message1) >= 5:
                    messDict['date'] = message1[0]
                    messDict['type'] = "INFO"
                    messDict['user'] = message1[1].split(':', 1).pop()
                    messDict['operation'] = message1[2].split(':', 1).pop().lstrip()
                    messDict['resource'] = message1[3].split(':', 1).pop().lstrip()
                    messDict['data'] = message1[4].split(':', 1).pop()
                    if messDict['resource'] == '/api/auth':
                        if messDict['operation'] == 'POST':
                            messDict['operation'] = 'LOGIN'
                        if messDict['operation'] == 'DELETE':
                            messDict['operation'] = "LOGOUT"
                    logging_list.append(messDict)

        return Response({
            'success': True,
            'message': logging_list
        })
