#!/usr/bin/python
# bridge_ctm.py

"""
(c) 2020 Volker Scheithauer
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice (including the next paragraph) shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

https://opensource.org/licenses/MIT
# SPDX-License-Identifier: MIT
For information on SDPX, https://spdx.org/licenses/MIT.html

BMC Software Python Core Tools 
Provide core functions for BMC Software related python scripts

Change Log
Date (YMD)    Name                  What
--------      ------------------    ------------------------
20200601      Volker Scheithauer    Initial Development 
20200730      Volker Scheithauer    Modify json handling for WCM
20201009      Volker Scheithauer    Externalize Helix functions
20220701      Volker Scheithauer    Migrate to W3rkstatt project
"""

import logging
import w3rkstatt
import bmcs_ctm_wcm as wcm
import os
import logging
import time
import datetime
import platform
import json
import jsonpath_ng
import core_itsm as helix

# pip install flask, flask_restful, flask-restplus, flask-marshmallow, flask-restplus-marshmallow

# Define global variables from w3rkstatt.ini file
jCfgFile = w3rkstatt.jCfgFile
jCfgData = w3rkstatt.getFileJson(jCfgFile)

# ITSM Details
itsm_smrtit_host = w3rkstatt.getJsonValue(path="$.SMARTIT.host", data=jCfgData)
itsm_smrtit_port = w3rkstatt.getJsonValue(path="$.SMARTIT.port", data=jCfgData)
itsm_smrtit = "http://" + itsm_smrtit_host + ":" + \
    itsm_smrtit_port + "/smartit/app/#/change/displayid/"

# ITSM template IDs
itsm_tmpl_crq = w3rkstatt.getJsonValue(
    path="$.ITSM.change.template_id", data=jCfgData)


# Assign module defaults
_localDebug = True
_modVer = "1.0"
_timeFormat = '%Y-%m-%dT%H:%M:%S'
logger = logging.getLogger(__name__)
logFile = w3rkstatt.logFile
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel", data=jCfgData)
epoch = time.time()

# CTM WCM variables
STATE_REQUESTER_WORKS = "RequesterWorks"
STATE_SUBMITTED = "Submitted"
STATE_SCHEDULER_WORKS = "SchedulerWorks"
STATE_RETURNED = "Returned"
STATE_APPROVED = "Approved"

# WCM REST API Calls
# WCM - validateChangeState
# WCM - stateChanged
# WCM - getChangeStatus


def createHelixCrq(data):

    jCtmData = json.loads(data)
    ctmRequestID = w3rkstatt.getJsonValue(path="$.ctmRequestID", data=jCtmData)
    ctmWorkspace = w3rkstatt.getJsonValue(path="$.name", data=jCtmData)
    newState = w3rkstatt.getJsonValue(path="$.newState", data=jCtmData)
    oldState = w3rkstatt.getJsonValue(path="$.oldState", data=jCtmData)
    creationTime = w3rkstatt.getJsonValue(path="$.creationTime", data=jCtmData)
    endUser = w3rkstatt.getJsonValue(path="$.endUser", data=jCtmData)
    timeDelta = w3rkstatt.getJsonValue(
        path="$.ITSM.defaults.timedelta", data=jCfgData)
    startDate = w3rkstatt.getCurrentDate(timeFormat=_timeFormat)
    endDate = w3rkstatt.addTimeDelta(
        date=startDate, timeFormat=_timeFormat, delta=timeDelta)

    if _localDebug:
        logger.info('CTM: Create CRQ: "%s": %s ', "Request ID", ctmRequestID)
        logger.info('CTM: Create CRQ: "%s": %s ', "Workspace", ctmWorkspace)
        logger.info('CTM: Create CRQ: "%s": %s ', "New State", newState)
        logger.info('CTM: Create CRQ: "%s": %s ', "Old State", oldState)
        logger.info('CTM: Create CRQ: "%s": %s ',
                    "Creation Time", creationTime)
        logger.info('CTM: Create CRQ: "%s": %s ', "End User", endUser)

    jHelixCrq = {
        "values": {
            "z1D_Action": "CREATE",
            "Description": "CTM WCM Workspace: " + ctmWorkspace + " ",
            "Detailed Description": "CTM WCM Workspace: " + ctmWorkspace + " for:" + endUser,
            "Vendor Ticket Number": ctmRequestID,

            "First Name": w3rkstatt.getJsonValue(path="$.ITSM.defaults.name-first", data=jCfgData),
            "Last Name": w3rkstatt.getJsonValue(path="$.ITSM.defaults.name-last", data=jCfgData),
            "Impact": w3rkstatt.getJsonValue(path="$.ITSM.change.impact", data=jCfgData),
            "Urgency": w3rkstatt.getJsonValue(path="$.ITSM.change.urgency", data=jCfgData),
            "Status": w3rkstatt.getJsonValue(path="$.ITSM.change.status", data=jCfgData),
            "Status Reason": w3rkstatt.getJsonValue(path="$.ITSM.change.status_reason", data=jCfgData),
            "ServiceCI": w3rkstatt.getJsonValue(path="$.ITSM.defaults.service-ci", data=jCfgData),
            "Company3": w3rkstatt.getJsonValue(path="$.ITSM.defaults.support-company", data=jCfgData),
            "Support Organization": w3rkstatt.getJsonValue(path="$.ITSM.defaults.support-organization", data=jCfgData),
            "Support Group Name": w3rkstatt.getJsonValue(path="$.ITSM.defaults.assigned-group", data=jCfgData),
            "Location Company": w3rkstatt.getJsonValue(path="$.ITSM.defaults.location-company", data=jCfgData),
            "Region": w3rkstatt.getJsonValue(path="$.ITSM.defaults.region", data=jCfgData),
            "Site Group": w3rkstatt.getJsonValue(path="$.ITSM.defaults.site-group", data=jCfgData),
            "Site": w3rkstatt.getJsonValue(path="$.ITSM.defaults.site", data=jCfgData),
            "Categorization Tier 1": w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_1", data=jCfgData),
            "Categorization Tier 2": w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_2", data=jCfgData),
            "Categorization Tier 3": w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_3", data=jCfgData),
            "Product Cat Tier 1(2)": w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_1", data=jCfgData),
            "Product Cat Tier 2 (2)": w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_2", data=jCfgData),
            "Product Cat Tier 3 (2)": w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_3", data=jCfgData),
            "Scheduled Start Date": startDate,
            "Scheduled End Date": endDate,
            "TemplateID": itsm_tmpl_crq

        }
    }
    if _localDebug:
        logger.info('Helix: CRQ JSON: %s ', jHelixCrq)

    authToken = helix.itsmAuthenticate()
    ctmChangeID = helix.createChange(token=authToken, data=jHelixCrq)

    if _localDebug:
        logger.info('CTM: Create CRQ: "%s": %s ', "Change ID", ctmChangeID)

    return ctmChangeID


def getHelixCrq(change):
    ctmChangeID = change
    authToken = helix.itsmAuthenticate()
    crgInfo = helix.getChange(token=authToken, change=ctmChangeID)
    return crgInfo


def getHelixCrqStatus(data):
    ctmChangeID = data
    crgInfo = getHelixCrq(change=ctmChangeID)
    if _localDebug:
        logger.info('Helix: Status CRQ ID: "%s"', ctmChangeID)
        logger.info('Helix: Status CRQ Info: "%s"', crgInfo)

    crqStatus = helix.extractChangeState(change=crgInfo)
    return crqStatus


def translateCrqStatus(status):
    # httpResponseCode
    # - 200 = Approved
    # - 400 = Not Approved
    if(status == "Draft"):
        httpResponseCode = 400
    elif(status == "Request For Authorization"):
        httpResponseCode = 400
    elif(status == "Request For Change"):
        httpResponseCode = 400
    elif(status == "Planning In Progress"):
        httpResponseCode = 400
    elif(status == "Scheduled For Review"):
        httpResponseCode = 400
    elif(status == "Scheduled For Approval"):
        httpResponseCode = 400
    elif(status == "Scheduled"):
        httpResponseCode = 200
    elif(status == "Implementation In Progress"):
        httpResponseCode = 200
    elif(status == "Pending"):
        httpResponseCode = 400
    elif(status == "Rejected"):
        httpResponseCode = 400
    elif(status == "Completed"):
        httpResponseCode = 400
    elif(status == "Closed"):
        httpResponseCode = 400
    elif(status == "Cancelled"):
        httpResponseCode = 400
    else:
        httpResponseCode = 400

    return httpResponseCode


if __name__ == "__main__":
    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger.info('CTM: CTM Helix Bridge: "Start"')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: "%s" ', platform.system())
    logger.info('Log Level: "%s"', loglevel)
    logger.info('Epoch: %s', epoch)

    logger.info('CTM: CTM Helix Bridge: "End"')
    logging.shutdown()

    print(f"Version: {_modVer}")
