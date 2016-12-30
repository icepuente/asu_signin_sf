### Author: Alec Puente     
### Email: icepuente@gmail.com

import requests, xml.dom.minidom, json

# get Salesforce session based on SOAP authentication
# payload will include a tech studio email sign in for Salesforce
# along with a randomly generated password appended with a security token 
# from Salesforce which resets upon resetting password. The username and password
# will be sent over a secure HTTPS connection to SF and the computer running the 
# server locally will be running a VPN to the ASU network for encryption and will
# remain locked inside the tech studio on an encrypted computer
def get_sf_session():
    soap_url = 'https://asu.my.salesforce.com/services/Soap/u/36.0'
    login_soap_request_body = """<?xml version="1.0" encoding="utf-8" ?>
        <env:Envelope
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
            <env:Body>
                <n1:login xmlns:n1="urn:partner.soap.sforce.com">
                    <n1:username>SF Email will go here</n1:username>
                    <n1:password>SF Password+Security Token</n1:password>
                </n1:login>
            </env:Body>
        </env:Envelope>"""

    login_soap_request_headers = {
        'content-type' : 'text/xml',
        'charset' : 'UTF-8',
        'SOAPAction' : 'login'
    }

    response = requests.post(soap_url, login_soap_request_body, 
        headers=login_soap_request_headers)

    if response.status_code != 200:
        except_code = getUniqueElementValueFromXmlString(
            response.content, 'sf:exceptionCode')
        except_msg = getUniqueElementValueFromXmlString(
            response.content, 'sf:exceptionMessage')
        raise SalesforceAuthenticationFailed(except_code, except_msg)

    session_id = getUniqueElementValueFromXmlString(
        response.content, 'sessionId')

    return session_id

# Query Salesforce based on ASURITE Username and ID and return
# a JSON object containing the contact ASU Email and specific 
# Salesforce ID
def query_salesforce(session_id, username, idnumber):
    query = """SELECT Email,Id FROM Contact WHERE ASURite_ID__c = '%s'
    AND EMPLID__c = '%s'""" % (username, idnumber)

    sf_url = 'https://asu.my.salesforce.com'

    response = requests.get(
        sf_url + '/services/data/v36.0/query/',
        params = {'q': query},
        headers = create_headers(session_id))

    json_response = response.json()

    return json_response

# Add case directly to Tech Studio Tempe queue
# input: SF session id, contact SF id, and issue input from
# customer
def add_case(session_id, id, subject):
    sf_url = 'https://asu.my.salesforce.com/services/data/v36.0/sobjects/case'

    data = {
    'Campus__c' : 'Tempe',
    'ContactId' : id,
    'Description' : subject,
    'Functional_Group__c' : 'Tech Studio',
    'Origin__c' : 'In Person',
    'OwnerId' : '00Gd00000028HtyEAE',
    'Priority' : 'Normal',
    'Status' : 'New',
    'Subject' : subject
    }

    response = requests.request('POST', sf_url,
     headers=create_headers(session_id),
     data=json.dumps(data))

    if response.status_code >= 300:
        except_code = getUniqueElementValueFromXmlString(
            response.content, 'sf:exceptionCode')
        except_msg = getUniqueElementValueFromXmlString(
            response.content, 'sf:exceptionMessage')
        raise SalesforceAuthenticationFailed(except_code, except_msg)

    return response


# create headers for requests from SF containing SF session
def create_headers(session_id):
    """Creating headers"""
    return {
        'Content-type' : 'application/json',
        'Authorization' : 'Bearer ' + session_id,
    }



# pylint: disable=invalid-name
def getUniqueElementValueFromXmlString(xmlString, elementName):
    """
    Extracts an element value from an XML string.
    For example, invoking
    getUniqueElementValueFromXmlString(
        '<?xml version="1.0" encoding="UTF-8"?><foo>bar</foo>', 'foo')
    should return the value 'bar'.
    """
    xmlStringAsDom = xml.dom.minidom.parseString(xmlString)
    elementsByName = xmlStringAsDom.getElementsByTagName(elementName)
    elementValue = None
    if len(elementsByName) > 0:
        elementValue = elementsByName[0].toxml().replace(
            '<' + elementName + '>', '').replace('</' + elementName + '>', '')
    return elementValue

class SalesforceError(Exception):
    """Base Salesforce API exception"""

    message = u'Unknown error occurred for {url}. Response content: {content}'

    def __init__(self, url, status, resource_name, content):
        # TODO exceptions don't seem to be using parent constructors at all.
        # this should be fixed.
        # pylint: disable=super-init-not-called
        self.url = url
        self.status = status
        self.resource_name = resource_name
        self.content = content

    def __str__(self):
        return self.message.format(url=self.url, content=self.content)

    def __unicode__(self):
        return self.__str__()

class SalesforceAuthenticationFailed(SalesforceError):
    """
    Thrown to indicate that authentication with Salesforce failed.
    """
    def __init__(self, code, message):
        # TODO exceptions don't seem to be using parent constructors at all.
        # this should be fixed.
        # pylint: disable=super-init-not-called
        self.code = code
        self.message = message

    def __str__(self):
        return u'{code}: {message}'.format(code=self.code,
                                           message=self.message)

