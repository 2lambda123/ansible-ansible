# Copyright (c) 2017-2018 Dell EMC Inc.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
from ansible.module_utils.urls import open_url
from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves import http_client
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError

GET_HEADERS = {'accept': 'application/json', 'OData-Version': '4.0'}
POST_HEADERS = {'content-type': 'application/json', 'accept': 'application/json',
                'OData-Version': '4.0'}
PATCH_HEADERS = {'content-type': 'application/json', 'accept': 'application/json',
                 'OData-Version': '4.0'}
DELETE_HEADERS = {'accept': 'application/json', 'OData-Version': '4.0'}


class RedfishUtils(object):

    def __init__(self, creds, root_uri, timeout, module):
        self.root_uri = root_uri
        self.creds = creds
        self.timeout = timeout
        self.module = module
        self.service_root = '/redfish/v1/'
        self._init_session()

    # The following functions are to send GET/POST/PATCH/DELETE requests
    def get_request(self, uri):
        try:
            resp = open_url(uri, method="GET", headers=GET_HEADERS,
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            follow_redirects='all',
                            use_proxy=False, timeout=self.timeout)
            data = json.loads(resp.read())
            headers = dict((k.lower(), v) for (k, v) in resp.info().items())
        except HTTPError as e:
            msg = self._get_extended_message(e)
            return {'ret': False,
                    'msg': "HTTP Error %s on GET request to '%s', extended message: '%s'"
                           % (e.code, uri, msg),
                    'status': e.code}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error on GET request to '%s': '%s'"
                                         % (uri, e.reason)}
        # Almost all errors should be caught above, but just in case
        except Exception as e:
            return {'ret': False,
                    'msg': "Failed GET request to '%s': '%s'" % (uri, to_text(e))}
        return {'ret': True, 'data': data, 'headers': headers}

    def post_request(self, uri, pyld):
        try:
            resp = open_url(uri, data=json.dumps(pyld),
                            headers=POST_HEADERS, method="POST",
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            follow_redirects='all',
                            use_proxy=False, timeout=self.timeout)
        except HTTPError as e:
            msg = self._get_extended_message(e)
            return {'ret': False,
                    'msg': "HTTP Error %s on POST request to '%s', extended message: '%s'"
                           % (e.code, uri, msg),
                    'status': e.code}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error on POST request to '%s': '%s'"
                                         % (uri, e.reason)}
        # Almost all errors should be caught above, but just in case
        except Exception as e:
            return {'ret': False,
                    'msg': "Failed POST request to '%s': '%s'" % (uri, to_text(e))}
        return {'ret': True, 'resp': resp}

    def patch_request(self, uri, pyld):
        headers = PATCH_HEADERS
        r = self.get_request(uri)
        if r['ret']:
            # Get etag from etag header or @odata.etag property
            etag = r['headers'].get('etag')
            if not etag:
                etag = r['data'].get('@odata.etag')
            if etag:
                # Make copy of headers and add If-Match header
                headers = dict(headers)
                headers['If-Match'] = etag
        try:
            resp = open_url(uri, data=json.dumps(pyld),
                            headers=headers, method="PATCH",
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            follow_redirects='all',
                            use_proxy=False, timeout=self.timeout)
        except HTTPError as e:
            msg = self._get_extended_message(e)
            return {'ret': False,
                    'msg': "HTTP Error %s on PATCH request to '%s', extended message: '%s'"
                           % (e.code, uri, msg),
                    'status': e.code}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error on PATCH request to '%s': '%s'"
                                         % (uri, e.reason)}
        # Almost all errors should be caught above, but just in case
        except Exception as e:
            return {'ret': False,
                    'msg': "Failed PATCH request to '%s': '%s'" % (uri, to_text(e))}
        return {'ret': True, 'resp': resp}

    def delete_request(self, uri, pyld=None):
        try:
            data = json.dumps(pyld) if pyld else None
            resp = open_url(uri, data=data,
                            headers=DELETE_HEADERS, method="DELETE",
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            follow_redirects='all',
                            use_proxy=False, timeout=self.timeout)
        except HTTPError as e:
            msg = self._get_extended_message(e)
            return {'ret': False,
                    'msg': "HTTP Error %s on DELETE request to '%s', extended message: '%s'"
                           % (e.code, uri, msg),
                    'status': e.code}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error on DELETE request to '%s': '%s'"
                                         % (uri, e.reason)}
        # Almost all errors should be caught above, but just in case
        except Exception as e:
            return {'ret': False,
                    'msg': "Failed DELETE request to '%s': '%s'" % (uri, to_text(e))}
        return {'ret': True, 'resp': resp}

    @staticmethod
    def _get_extended_message(error):
        """
        Get Redfish ExtendedInfo message from response payload if present
        :param error: an HTTPError exception
        :type error: HTTPError
        :return: the ExtendedInfo message if present, else standard HTTP error
        """
        msg = http_client.responses.get(error.code, '')
        if error.code >= 400:
            try:
                body = error.read().decode('utf-8')
                data = json.loads(body)
                ext_info = data['error']['@Message.ExtendedInfo']
                msg = ext_info[0]['Message']
            except Exception:
                pass
        return msg

    def _init_session(self):
        pass

    def _find_accountservice_resource(self):
        response = self.get_request(self.root_uri + self.service_root)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'AccountService' not in data:
            return {'ret': False, 'msg': "AccountService resource not found"}
        else:
            account_service = data["AccountService"]["@odata.id"]
            response = self.get_request(self.root_uri + account_service)
            if response['ret'] is False:
                return response
            data = response['data']
            accounts = data['Accounts']['@odata.id']
            if accounts[-1:] == '/':
                accounts = accounts[:-1]
            self.accounts_uri = accounts
        return {'ret': True}

    def _find_sessionservice_resource(self):
        response = self.get_request(self.root_uri + self.service_root)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'SessionService' not in data:
            return {'ret': False, 'msg': "SessionService resource not found"}
        else:
            session_service = data["SessionService"]["@odata.id"]
            response = self.get_request(self.root_uri + session_service)
            if response['ret'] is False:
                return response
            data = response['data']
            sessions = data['Sessions']['@odata.id']
            if sessions[-1:] == '/':
                sessions = sessions[:-1]
            self.sessions_uri = sessions
        return {'ret': True}

    def _find_systems_resource(self):
        response = self.get_request(self.root_uri + self.service_root)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'Systems' not in data:
            return {'ret': False, 'msg': "Systems resource not found"}
        response = self.get_request(self.root_uri + data['Systems']['@odata.id'])
        if response['ret'] is False:
            return response
        self.systems_uris = [
            i['@odata.id'] for i in response['data'].get('Members', [])]
        if not self.systems_uris:
            return {
                'ret': False,
                'msg': "ComputerSystem's Members array is either empty or missing"}
        return {'ret': True}

    def _find_updateservice_resource(self):
        response = self.get_request(self.root_uri + self.service_root)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'UpdateService' not in data:
            return {'ret': False, 'msg': "UpdateService resource not found"}
        else:
            update = data["UpdateService"]["@odata.id"]
            self.update_uri = update
            response = self.get_request(self.root_uri + update)
            if response['ret'] is False:
                return response
            data = response['data']
            self.firmware_uri = self.software_uri = None
            if 'FirmwareInventory' in data:
                self.firmware_uri = data['FirmwareInventory'][u'@odata.id']
            if 'SoftwareInventory' in data:
                self.software_uri = data['SoftwareInventory'][u'@odata.id']
            return {'ret': True}

    def _find_chassis_resource(self):
        chassis_service = []
        response = self.get_request(self.root_uri + self.service_root)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'Chassis' not in data:
            return {'ret': False, 'msg': "Chassis resource not found"}
        else:
            chassis = data["Chassis"]["@odata.id"]
            response = self.get_request(self.root_uri + chassis)
            if response['ret'] is False:
                return response
            data = response['data']
            for member in data[u'Members']:
                chassis_service.append(member[u'@odata.id'])
            self.chassis_uri_list = chassis_service
            return {'ret': True}

    def _find_managers_resource(self):
        response = self.get_request(self.root_uri + self.service_root)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'Managers' not in data:
            return {'ret': False, 'msg': "Manager resource not found"}
        else:
            manager = data["Managers"]["@odata.id"]
            response = self.get_request(self.root_uri + manager)
            if response['ret'] is False:
                return response
            data = response['data']
            for member in data[u'Members']:
                manager_service = member[u'@odata.id']
            self.manager_uri = manager_service
            return {'ret': True}

    def get_logs(self):
        log_svcs_uri_list = []
        list_of_logs = []
        properties = ['Severity', 'Created', 'EntryType', 'OemRecordFormat',
                      'Message', 'MessageId', 'MessageArgs']

        # Find LogService
        response = self.get_request(self.root_uri + self.manager_uri)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'LogServices' not in data:
            return {'ret': False, 'msg': "LogServices resource not found"}

        # Find all entries in LogServices
        logs_uri = data["LogServices"]["@odata.id"]
        response = self.get_request(self.root_uri + logs_uri)
        if response['ret'] is False:
            return response
        data = response['data']
        for log_svcs_entry in data.get('Members', []):
            response = self.get_request(self.root_uri + log_svcs_entry[u'@odata.id'])
            if response['ret'] is False:
                return response
            _data = response['data']
            if 'Entries' in _data:
                log_svcs_uri_list.append(_data['Entries'][u'@odata.id'])

        # For each entry in LogServices, get log name and all log entries
        for log_svcs_uri in log_svcs_uri_list:
            logs = {}
            list_of_log_entries = []
            response = self.get_request(self.root_uri + log_svcs_uri)
            if response['ret'] is False:
                return response
            data = response['data']
            logs['Description'] = data.get('Description',
                                           'Collection of log entries')
            # Get all log entries for each type of log found
            for logEntry in data.get('Members', []):
                entry = {}
                for prop in properties:
                    if prop in logEntry:
                        entry[prop] = logEntry.get(prop)
                if entry:
                    list_of_log_entries.append(entry)
            log_name = log_svcs_uri.split('/')[-1]
            logs[log_name] = list_of_log_entries
            list_of_logs.append(logs)

        # list_of_logs[logs{list_of_log_entries[entry{}]}]
        return {'ret': True, 'entries': list_of_logs}

    def clear_logs(self):
        # Find LogService
        response = self.get_request(self.root_uri + self.manager_uri)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'LogServices' not in data:
            return {'ret': False, 'msg': "LogServices resource not found"}

        # Find all entries in LogServices
        logs_uri = data["LogServices"]["@odata.id"]
        response = self.get_request(self.root_uri + logs_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        for log_svcs_entry in data[u'Members']:
            response = self.get_request(self.root_uri + log_svcs_entry["@odata.id"])
            if response['ret'] is False:
                return response
            _data = response['data']
            # Check to make sure option is available, otherwise error is ugly
            if "Actions" in _data:
                if "#LogService.ClearLog" in _data[u"Actions"]:
                    self.post_request(self.root_uri + _data[u"Actions"]["#LogService.ClearLog"]["target"], {})
                    if response['ret'] is False:
                        return response
        return {'ret': True}

    def aggregate(self, func):
        ret = True
        entries = []
        for systems_uri in self.systems_uris:
            inventory = func(systems_uri)
            ret = inventory.pop('ret') and ret
            if 'entries' in inventory:
                entries.append(({'systems_uri': systems_uri},
                                inventory['entries']))
        return dict(ret=ret, entries=entries)

    def get_storage_controller_inventory(self, systems_uri):
        result = {}
        controller_list = []
        controller_results = []
        # Get these entries, but does not fail if not found
        properties = ['CacheSummary', 'FirmwareVersion', 'Identifiers',
                      'Location', 'Manufacturer', 'Model', 'Name',
                      'PartNumber', 'SerialNumber', 'SpeedGbps', 'Status']
        key = "StorageControllers"

        # Find Storage service
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        if 'Storage' not in data:
            return {'ret': False, 'msg': "Storage resource not found"}

        # Get a list of all storage controllers and build respective URIs
        storage_uri = data['Storage']["@odata.id"]
        response = self.get_request(self.root_uri + storage_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        # Loop through Members and their StorageControllers
        # and gather properties from each StorageController
        if data[u'Members']:
            for storage_member in data[u'Members']:
                storage_member_uri = storage_member[u'@odata.id']
                response = self.get_request(self.root_uri + storage_member_uri)
                data = response['data']

                if key in data:
                    controller_list = data[key]
                    for controller in controller_list:
                        controller_result = {}
                        for property in properties:
                            if property in controller:
                                controller_result[property] = controller[property]
                        controller_results.append(controller_result)
                result['entries'] = controller_results
            return result
        else:
            return {'ret': False, 'msg': "Storage resource not found"}

    def get_multi_storage_controller_inventory(self):
        return self.aggregate(self.get_storage_controller_inventory)

    def get_disk_inventory(self, systems_uri):
        result = {'entries': []}
        controller_list = []
        # Get these entries, but does not fail if not found
        properties = ['BlockSizeBytes', 'CapableSpeedGbs', 'CapacityBytes',
                      'EncryptionAbility', 'EncryptionStatus',
                      'FailurePredicted', 'HotspareType', 'Id', 'Identifiers',
                      'Manufacturer', 'MediaType', 'Model', 'Name',
                      'PartNumber', 'PhysicalLocation', 'Protocol', 'Revision',
                      'RotationSpeedRPM', 'SerialNumber', 'Status']

        # Find Storage service
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        if 'SimpleStorage' not in data and 'Storage' not in data:
            return {'ret': False, 'msg': "SimpleStorage and Storage resource \
                     not found"}

        if 'Storage' in data:
            # Get a list of all storage controllers and build respective URIs
            storage_uri = data[u'Storage'][u'@odata.id']
            response = self.get_request(self.root_uri + storage_uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']

            if data[u'Members']:
                for controller in data[u'Members']:
                    controller_list.append(controller[u'@odata.id'])
                for c in controller_list:
                    uri = self.root_uri + c
                    response = self.get_request(uri)
                    if response['ret'] is False:
                        return response
                    data = response['data']
                    controller_name = 'Controller 1'
                    if 'StorageControllers' in data:
                        sc = data['StorageControllers']
                        if sc:
                            if 'Name' in sc[0]:
                                controller_name = sc[0]['Name']
                            else:
                                sc_id = sc[0].get('Id', '1')
                                controller_name = 'Controller %s' % sc_id
                    drive_results = []
                    if 'Drives' in data:
                        for device in data[u'Drives']:
                            disk_uri = self.root_uri + device[u'@odata.id']
                            response = self.get_request(disk_uri)
                            data = response['data']

                            drive_result = {}
                            for property in properties:
                                if property in data:
                                    if data[property] is not None:
                                        drive_result[property] = data[property]
                            drive_results.append(drive_result)
                    drives = {'Controller': controller_name,
                              'Drives': drive_results}
                    result["entries"].append(drives)

        if 'SimpleStorage' in data:
            # Get a list of all storage controllers and build respective URIs
            storage_uri = data["SimpleStorage"]["@odata.id"]
            response = self.get_request(self.root_uri + storage_uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']

            for controller in data[u'Members']:
                controller_list.append(controller[u'@odata.id'])

            for c in controller_list:
                uri = self.root_uri + c
                response = self.get_request(uri)
                if response['ret'] is False:
                    return response
                data = response['data']
                if 'Name' in data:
                    controller_name = data['Name']
                else:
                    sc_id = data.get('Id', '1')
                    controller_name = 'Controller %s' % sc_id
                drive_results = []
                for device in data[u'Devices']:
                    drive_result = {}
                    for property in properties:
                        if property in device:
                            drive_result[property] = device[property]
                    drive_results.append(drive_result)
                drives = {'Controller': controller_name,
                          'Drives': drive_results}
                result["entries"].append(drives)

        return result

    def get_multi_disk_inventory(self):
        return self.aggregate(self.get_disk_inventory)

    def get_volume_inventory(self, systems_uri):
        result = {'entries': []}
        controller_list = []
        volume_list = []
        # Get these entries, but does not fail if not found
        properties = ['Id', 'Name', 'RAIDType', 'VolumeType', 'BlockSizeBytes',
                      'Capacity', 'CapacityBytes', 'CapacitySources',
                      'Encrypted', 'EncryptionTypes', 'Identifiers',
                      'Operations', 'OptimumIOSizeBytes', 'AccessCapabilities',
                      'AllocatedPools', 'Status']

        # Find Storage service
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        if 'SimpleStorage' not in data and 'Storage' not in data:
            return {'ret': False, 'msg': "SimpleStorage and Storage resource \
                     not found"}

        if 'Storage' in data:
            # Get a list of all storage controllers and build respective URIs
            storage_uri = data[u'Storage'][u'@odata.id']
            response = self.get_request(self.root_uri + storage_uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']

            if data.get('Members'):
                for controller in data[u'Members']:
                    controller_list.append(controller[u'@odata.id'])
                for c in controller_list:
                    uri = self.root_uri + c
                    response = self.get_request(uri)
                    if response['ret'] is False:
                        return response
                    data = response['data']
                    controller_name = 'Controller 1'
                    if 'StorageControllers' in data:
                        sc = data['StorageControllers']
                        if sc:
                            if 'Name' in sc[0]:
                                controller_name = sc[0]['Name']
                            else:
                                sc_id = sc[0].get('Id', '1')
                                controller_name = 'Controller %s' % sc_id
                    volume_results = []
                    if 'Volumes' in data:
                        # Get a list of all volumes and build respective URIs
                        volumes_uri = data[u'Volumes'][u'@odata.id']
                        response = self.get_request(self.root_uri + volumes_uri)
                        data = response['data']

                        if data.get('Members'):
                            for volume in data[u'Members']:
                                volume_list.append(volume[u'@odata.id'])
                            for v in volume_list:
                                uri = self.root_uri + v
                                response = self.get_request(uri)
                                if response['ret'] is False:
                                    return response
                                data = response['data']

                                volume_result = {}
                                for property in properties:
                                    if property in data:
                                        if data[property] is not None:
                                            volume_result[property] = data[property]

                                # Get related Drives Id
                                drive_id_list = []
                                if 'Links' in data:
                                    if 'Drives' in data[u'Links']:
                                        for link in data[u'Links'][u'Drives']:
                                            drive_id_link = link[u'@odata.id']
                                            drive_id = drive_id_link.split("/")[-1]
                                            drive_id_list.append({'Id': drive_id})
                                        volume_result['Linked_drives'] = drive_id_list
                                volume_results.append(volume_result)
                    volumes = {'Controller': controller_name,
                               'Volumes': volume_results}
                    result["entries"].append(volumes)
        else:
            return {'ret': False, 'msg': "Storage resource not found"}

        return result

    def get_multi_volume_inventory(self):
        return self.aggregate(self.get_volume_inventory)

    def restart_manager_gracefully(self):
        result = {}
        key = "Actions"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.manager_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        action_uri = data[key]["#Manager.Reset"]["target"]

        payload = {'ResetType': 'GracefulRestart'}
        response = self.post_request(self.root_uri + action_uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def manage_indicator_led(self, command):
        result = {}
        key = 'IndicatorLED'

        payloads = {'IndicatorLedOn': 'Lit', 'IndicatorLedOff': 'Off', "IndicatorLedBlink": 'Blinking'}

        result = {}
        for chassis_uri in self.chassis_uri_list:
            response = self.get_request(self.root_uri + chassis_uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']
            if key not in data:
                return {'ret': False, 'msg': "Key %s not found" % key}

            if command in payloads.keys():
                payload = {'IndicatorLED': payloads[command]}
                response = self.patch_request(self.root_uri + chassis_uri, payload)
                if response['ret'] is False:
                    return response
            else:
                return {'ret': False, 'msg': 'Invalid command'}

        return result

    def _map_reset_type(self, reset_type, allowable_values):
        equiv_types = {
            'On': 'ForceOn',
            'ForceOn': 'On',
            'ForceOff': 'GracefulShutdown',
            'GracefulShutdown': 'ForceOff',
            'GracefulRestart': 'ForceRestart',
            'ForceRestart': 'GracefulRestart'
        }

        if reset_type in allowable_values:
            return reset_type
        if reset_type not in equiv_types:
            return reset_type
        mapped_type = equiv_types[reset_type]
        if mapped_type in allowable_values:
            return mapped_type
        return reset_type

    def manage_system_power(self, command):
        key = "Actions"
        reset_type_values = ['On', 'ForceOff', 'GracefulShutdown',
                             'GracefulRestart', 'ForceRestart', 'Nmi',
                             'ForceOn', 'PushPowerButton', 'PowerCycle']

        # command should be PowerOn, PowerForceOff, etc.
        if not command.startswith('Power'):
            return {'ret': False, 'msg': 'Invalid Command (%s)' % command}
        reset_type = command[5:]

        # map Reboot to a ResetType that does a reboot
        if reset_type == 'Reboot':
            reset_type = 'GracefulRestart'

        if reset_type not in reset_type_values:
            return {'ret': False, 'msg': 'Invalid Command (%s)' % command}

        # read the system resource and get the current power state
        response = self.get_request(self.root_uri + self.systems_uris[0])
        if response['ret'] is False:
            return response
        data = response['data']
        power_state = data.get('PowerState')

        # if power is already in target state, nothing to do
        if power_state == "On" and reset_type in ['On', 'ForceOn']:
            return {'ret': True, 'changed': False}
        if power_state == "Off" and reset_type in ['GracefulShutdown', 'ForceOff']:
            return {'ret': True, 'changed': False}

        # get the #ComputerSystem.Reset Action and target URI
        if key not in data or '#ComputerSystem.Reset' not in data[key]:
            return {'ret': False, 'msg': 'Action #ComputerSystem.Reset not found'}
        reset_action = data[key]['#ComputerSystem.Reset']
        if 'target' not in reset_action:
            return {'ret': False,
                    'msg': 'target URI missing from Action #ComputerSystem.Reset'}
        action_uri = reset_action['target']

        # get AllowableValues from ActionInfo
        allowable_values = None
        if '@Redfish.ActionInfo' in reset_action:
            action_info_uri = reset_action.get('@Redfish.ActionInfo')
            response = self.get_request(self.root_uri + action_info_uri)
            if response['ret'] is True:
                data = response['data']
                if 'Parameters' in data:
                    params = data['Parameters']
                    for param in params:
                        if param.get('Name') == 'ResetType':
                            allowable_values = param.get('AllowableValues')
                            break

        # fallback to @Redfish.AllowableValues annotation
        if allowable_values is None:
            allowable_values = reset_action.get('ResetType@Redfish.AllowableValues', [])

        # map ResetType to an allowable value if needed
        if reset_type not in allowable_values:
            reset_type = self._map_reset_type(reset_type, allowable_values)

        # define payload
        payload = {'ResetType': reset_type}

        # POST to Action URI
        response = self.post_request(self.root_uri + action_uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True, 'changed': True}

    def _find_account_uri(self, username=None, acct_id=None):
        if not any((username, acct_id)):
            return {'ret': False, 'msg':
                    'Must provide either account_id or account_username'}

        response = self.get_request(self.root_uri + self.accounts_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        uris = [a.get('@odata.id') for a in data.get('Members', []) if
                a.get('@odata.id')]
        for uri in uris:
            response = self.get_request(self.root_uri + uri)
            if response['ret'] is False:
                continue
            data = response['data']
            headers = response['headers']
            if username:
                if username == data.get('UserName'):
                    return {'ret': True, 'data': data,
                            'headers': headers, 'uri': uri}
            if acct_id:
                if acct_id == data.get('Id'):
                    return {'ret': True, 'data': data,
                            'headers': headers, 'uri': uri}

        return {'ret': False, 'no_match': True, 'msg':
                'No account with the given account_id or account_username found'}

    def _find_empty_account_slot(self):
        response = self.get_request(self.root_uri + self.accounts_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        uris = [a.get('@odata.id') for a in data.get('Members', []) if
                a.get('@odata.id')]
        if uris:
            # first slot may be reserved, so move to end of list
            uris += [uris.pop(0)]
        for uri in uris:
            response = self.get_request(self.root_uri + uri)
            if response['ret'] is False:
                continue
            data = response['data']
            headers = response['headers']
            if data.get('UserName') == "" and not data.get('Enabled', True):
                return {'ret': True, 'data': data,
                        'headers': headers, 'uri': uri}

        return {'ret': False, 'no_match': True, 'msg':
                'No empty account slot found'}

    def list_users(self):
        result = {}
        # listing all users has always been slower than other operations, why?
        user_list = []
        users_results = []
        # Get these entries, but does not fail if not found
        properties = ['Id', 'Name', 'UserName', 'RoleId', 'Locked', 'Enabled']

        response = self.get_request(self.root_uri + self.accounts_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for users in data.get('Members', []):
            user_list.append(users[u'@odata.id'])   # user_list[] are URIs

        # for each user, get details
        for uri in user_list:
            user = {}
            response = self.get_request(self.root_uri + uri)
            if response['ret'] is False:
                return response
            data = response['data']

            for property in properties:
                if property in data:
                    user[property] = data[property]

            users_results.append(user)
        result["entries"] = users_results
        return result

    def add_user_via_patch(self, user):
        if user.get('account_id'):
            # If Id slot specified, use it
            response = self._find_account_uri(acct_id=user.get('account_id'))
        else:
            # Otherwise find first empty slot
            response = self._find_empty_account_slot()

        if not response['ret']:
            return response
        uri = response['uri']
        payload = {}
        if user.get('account_username'):
            payload['UserName'] = user.get('account_username')
        if user.get('account_password'):
            payload['Password'] = user.get('account_password')
        if user.get('account_roleid'):
            payload['RoleId'] = user.get('account_roleid')
        response = self.patch_request(self.root_uri + uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def add_user(self, user):
        if not user.get('account_username'):
            return {'ret': False, 'msg':
                    'Must provide account_username for AddUser command'}

        response = self._find_account_uri(username=user.get('account_username'))
        if response['ret']:
            # account_username already exists, nothing to do
            return {'ret': True, 'changed': False}

        response = self.get_request(self.root_uri + self.accounts_uri)
        if not response['ret']:
            return response
        headers = response['headers']

        if 'allow' in headers:
            methods = [m.strip() for m in headers.get('allow').split(',')]
            if 'POST' not in methods:
                # if Allow header present and POST not listed, add via PATCH
                return self.add_user_via_patch(user)

        payload = {}
        if user.get('account_username'):
            payload['UserName'] = user.get('account_username')
        if user.get('account_password'):
            payload['Password'] = user.get('account_password')
        if user.get('account_roleid'):
            payload['RoleId'] = user.get('account_roleid')

        response = self.post_request(self.root_uri + self.accounts_uri, payload)
        if not response['ret']:
            if response.get('status') == 405:
                # if POST returned a 405, try to add via PATCH
                return self.add_user_via_patch(user)
            else:
                return response
        return {'ret': True}

    def enable_user(self, user):
        response = self._find_account_uri(username=user.get('account_username'),
                                          acct_id=user.get('account_id'))
        if not response['ret']:
            return response
        uri = response['uri']
        data = response['data']

        if data.get('Enabled', True):
            # account already enabled, nothing to do
            return {'ret': True, 'changed': False}

        payload = {'Enabled': True}
        response = self.patch_request(self.root_uri + uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def delete_user_via_patch(self, user, uri=None, data=None):
        if not uri:
            response = self._find_account_uri(username=user.get('account_username'),
                                              acct_id=user.get('account_id'))
            if not response['ret']:
                return response
            uri = response['uri']
            data = response['data']

        if data and data.get('UserName') == '' and not data.get('Enabled', False):
            # account UserName already cleared, nothing to do
            return {'ret': True, 'changed': False}

        payload = {'UserName': ''}
        if 'Enabled' in data:
            payload['Enabled'] = False
        response = self.patch_request(self.root_uri + uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def delete_user(self, user):
        response = self._find_account_uri(username=user.get('account_username'),
                                          acct_id=user.get('account_id'))
        if not response['ret']:
            if response.get('no_match'):
                # account does not exist, nothing to do
                return {'ret': True, 'changed': False}
            else:
                # some error encountered
                return response

        uri = response['uri']
        headers = response['headers']
        data = response['data']

        if 'allow' in headers:
            methods = [m.strip() for m in headers.get('allow').split(',')]
            if 'DELETE' not in methods:
                # if Allow header present and DELETE not listed, del via PATCH
                return self.delete_user_via_patch(user, uri=uri, data=data)

        response = self.delete_request(self.root_uri + uri)
        if not response['ret']:
            if response.get('status') == 405:
                # if DELETE returned a 405, try to delete via PATCH
                return self.delete_user_via_patch(user, uri=uri, data=data)
            else:
                return response
        return {'ret': True}

    def disable_user(self, user):
        response = self._find_account_uri(username=user.get('account_username'),
                                          acct_id=user.get('account_id'))
        if not response['ret']:
            return response
        uri = response['uri']
        data = response['data']

        if not data.get('Enabled'):
            # account already disabled, nothing to do
            return {'ret': True, 'changed': False}

        payload = {'Enabled': False}
        response = self.patch_request(self.root_uri + uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def update_user_role(self, user):
        if not user.get('account_roleid'):
            return {'ret': False, 'msg':
                    'Must provide account_roleid for UpdateUserRole command'}

        response = self._find_account_uri(username=user.get('account_username'),
                                          acct_id=user.get('account_id'))
        if not response['ret']:
            return response
        uri = response['uri']
        data = response['data']

        if data.get('RoleId') == user.get('account_roleid'):
            # account already has RoleId , nothing to do
            return {'ret': True, 'changed': False}

        payload = {'RoleId': user.get('account_roleid')}
        response = self.patch_request(self.root_uri + uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def update_user_password(self, user):
        response = self._find_account_uri(username=user.get('account_username'),
                                          acct_id=user.get('account_id'))
        if not response['ret']:
            return response
        uri = response['uri']
        payload = {'Password': user['account_password']}
        response = self.patch_request(self.root_uri + uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def update_user_name(self, user):
        if not user.get('account_updatename'):
            return {'ret': False, 'msg':
                    'Must provide account_updatename for UpdateUserName command'}

        response = self._find_account_uri(username=user.get('account_username'),
                                          acct_id=user.get('account_id'))
        if not response['ret']:
            return response
        uri = response['uri']
        payload = {'UserName': user['account_updatename']}
        response = self.patch_request(self.root_uri + uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def update_accountservice_properties(self, user):
        if user.get('account_properties') is None:
            return {'ret': False, 'msg':
                    'Must provide account_properties for UpdateAccountServiceProperties command'}
        account_properties = user.get('account_properties')

        # Find AccountService
        response = self.get_request(self.root_uri + self.service_root)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'AccountService' not in data:
            return {'ret': False, 'msg': "AccountService resource not found"}
        accountservice_uri = data["AccountService"]["@odata.id"]

        # Check support or not
        response = self.get_request(self.root_uri + accountservice_uri)
        if response['ret'] is False:
            return response
        data = response['data']
        for property_name in account_properties.keys():
            if property_name not in data:
                return {'ret': False, 'msg':
                        'property %s not supported' % property_name}

        # if properties is already matched, nothing to do
        need_change = False
        for property_name in account_properties.keys():
            if account_properties[property_name] != data[property_name]:
                need_change = True
                break

        if not need_change:
            return {'ret': True, 'changed': False, 'msg': "AccountService properties already set"}

        payload = account_properties
        response = self.patch_request(self.root_uri + accountservice_uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True, 'changed': True, 'msg': "Modified AccountService properties"}

    def get_sessions(self):
        result = {}
        # listing all users has always been slower than other operations, why?
        session_list = []
        sessions_results = []
        # Get these entries, but does not fail if not found
        properties = ['Description', 'Id', 'Name', 'UserName']

        response = self.get_request(self.root_uri + self.sessions_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for sessions in data[u'Members']:
            session_list.append(sessions[u'@odata.id'])   # session_list[] are URIs

        # for each session, get details
        for uri in session_list:
            session = {}
            response = self.get_request(self.root_uri + uri)
            if response['ret'] is False:
                return response
            data = response['data']

            for property in properties:
                if property in data:
                    session[property] = data[property]

            sessions_results.append(session)
        result["entries"] = sessions_results
        return result

    def get_firmware_update_capabilities(self):
        result = {}
        response = self.get_request(self.root_uri + self.update_uri)
        if response['ret'] is False:
            return response

        result['ret'] = True

        result['entries'] = {}

        data = response['data']

        if "Actions" in data:
            actions = data['Actions']
            if len(actions) > 0:
                for key in actions.keys():
                    action = actions.get(key)
                    if 'title' in action:
                        title = action['title']
                    else:
                        title = key
                    result['entries'][title] = action.get('TransferProtocol@Redfish.AllowableValues',
                                                          ["Key TransferProtocol@Redfish.AllowableValues not found"])
            else:
                return {'ret': "False", 'msg': "Actions list is empty."}
        else:
            return {'ret': "False", 'msg': "Key Actions not found."}
        return result

    def _software_inventory(self, uri):
        result = {}
        response = self.get_request(self.root_uri + uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        result['entries'] = []
        for member in data[u'Members']:
            uri = self.root_uri + member[u'@odata.id']
            # Get details for each software or firmware member
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']
            software = {}
            # Get these standard properties if present
            for key in ['Name', 'Id', 'Status', 'Version', 'Updateable',
                        'SoftwareId', 'LowestSupportedVersion', 'Manufacturer',
                        'ReleaseDate']:
                if key in data:
                    software[key] = data.get(key)
            result['entries'].append(software)
        return result

    def get_firmware_inventory(self):
        if self.firmware_uri is None:
            return {'ret': False, 'msg': 'No FirmwareInventory resource found'}
        else:
            return self._software_inventory(self.firmware_uri)

    def get_software_inventory(self):
        if self.software_uri is None:
            return {'ret': False, 'msg': 'No SoftwareInventory resource found'}
        else:
            return self._software_inventory(self.software_uri)

    def get_bios_attributes(self, systems_uri):
        result = {}
        bios_attributes = {}
        key = "Bios"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        bios_uri = data[key]["@odata.id"]

        response = self.get_request(self.root_uri + bios_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        for attribute in data[u'Attributes'].items():
            bios_attributes[attribute[0]] = attribute[1]
        result["entries"] = bios_attributes
        return result

    def get_multi_bios_attributes(self):
        return self.aggregate(self.get_bios_attributes)

    def _get_boot_options_dict(self, boot):
        # Get these entries from BootOption, if present
        properties = ['DisplayName', 'BootOptionReference']

        # Retrieve BootOptions if present
        if 'BootOptions' in boot and '@odata.id' in boot['BootOptions']:
            boot_options_uri = boot['BootOptions']["@odata.id"]
            # Get BootOptions resource
            response = self.get_request(self.root_uri + boot_options_uri)
            if response['ret'] is False:
                return {}
            data = response['data']

            # Retrieve Members array
            if 'Members' not in data:
                return {}
            members = data['Members']
        else:
            members = []

        # Build dict of BootOptions keyed by BootOptionReference
        boot_options_dict = {}
        for member in members:
            if '@odata.id' not in member:
                return {}
            boot_option_uri = member['@odata.id']
            response = self.get_request(self.root_uri + boot_option_uri)
            if response['ret'] is False:
                return {}
            data = response['data']
            if 'BootOptionReference' not in data:
                return {}
            boot_option_ref = data['BootOptionReference']

            # fetch the props to display for this boot device
            boot_props = {}
            for prop in properties:
                if prop in data:
                    boot_props[prop] = data[prop]

            boot_options_dict[boot_option_ref] = boot_props

        return boot_options_dict

    def get_boot_order(self, systems_uri):
        result = {}

        # Retrieve System resource
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        # Confirm needed Boot properties are present
        if 'Boot' not in data or 'BootOrder' not in data['Boot']:
            return {'ret': False, 'msg': "Key BootOrder not found"}

        boot = data['Boot']
        boot_order = boot['BootOrder']
        boot_options_dict = self._get_boot_options_dict(boot)

        # Build boot device list
        boot_device_list = []
        for ref in boot_order:
            boot_device_list.append(
                boot_options_dict.get(ref, {'BootOptionReference': ref}))

        result["entries"] = boot_device_list
        return result

    def get_multi_boot_order(self):
        return self.aggregate(self.get_boot_order)

    def get_boot_override(self, systems_uri):
        result = {}

        properties = ["BootSourceOverrideEnabled", "BootSourceOverrideTarget",
                      "BootSourceOverrideMode", "UefiTargetBootSourceOverride", "BootSourceOverrideTarget@Redfish.AllowableValues"]

        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if 'Boot' not in data:
            return {'ret': False, 'msg': "Key Boot not found"}

        boot = data['Boot']

        boot_overrides = {}
        if "BootSourceOverrideEnabled" in boot:
            if boot["BootSourceOverrideEnabled"] is not False:
                for property in properties:
                    if property in boot:
                        if boot[property] is not None:
                            boot_overrides[property] = boot[property]
        else:
            return {'ret': False, 'msg': "No boot override is enabled."}

        result['entries'] = boot_overrides
        return result

    def get_multi_boot_override(self):
        return self.aggregate(self.get_boot_override)

    def set_bios_default_settings(self):
        result = {}
        key = "Bios"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uris[0])
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        bios_uri = data[key]["@odata.id"]

        # Extract proper URI
        response = self.get_request(self.root_uri + bios_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        reset_bios_settings_uri = data["Actions"]["#Bios.ResetBios"]["target"]

        response = self.post_request(self.root_uri + reset_bios_settings_uri, {})
        if response['ret'] is False:
            return response
        return {'ret': True, 'changed': True, 'msg': "Set BIOS to default settings"}

    def set_one_time_boot_device(self, bootdevice, uefi_target, boot_next):
        result = {}
        key = "Boot"

        if not bootdevice:
            return {'ret': False,
                    'msg': "bootdevice option required for SetOneTimeBoot"}

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uris[0])
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        boot = data[key]

        annotation = 'BootSourceOverrideTarget@Redfish.AllowableValues'
        if annotation in boot:
            allowable_values = boot[annotation]
            if isinstance(allowable_values, list) and bootdevice not in allowable_values:
                return {'ret': False,
                        'msg': "Boot device %s not in list of allowable values (%s)" %
                               (bootdevice, allowable_values)}

        # read existing values
        enabled = boot.get('BootSourceOverrideEnabled')
        target = boot.get('BootSourceOverrideTarget')
        cur_uefi_target = boot.get('UefiTargetBootSourceOverride')
        cur_boot_next = boot.get('BootNext')

        if bootdevice == 'UefiTarget':
            if not uefi_target:
                return {'ret': False,
                        'msg': "uefi_target option required to SetOneTimeBoot for UefiTarget"}
            if enabled == 'Once' and target == bootdevice and uefi_target == cur_uefi_target:
                # If properties are already set, no changes needed
                return {'ret': True, 'changed': False}
            payload = {
                'Boot': {
                    'BootSourceOverrideEnabled': 'Once',
                    'BootSourceOverrideTarget': bootdevice,
                    'UefiTargetBootSourceOverride': uefi_target
                }
            }
        elif bootdevice == 'UefiBootNext':
            if not boot_next:
                return {'ret': False,
                        'msg': "boot_next option required to SetOneTimeBoot for UefiBootNext"}
            if enabled == 'Once' and target == bootdevice and boot_next == cur_boot_next:
                # If properties are already set, no changes needed
                return {'ret': True, 'changed': False}
            payload = {
                'Boot': {
                    'BootSourceOverrideEnabled': 'Once',
                    'BootSourceOverrideTarget': bootdevice,
                    'BootNext': boot_next
                }
            }
        else:
            if enabled == 'Once' and target == bootdevice:
                # If properties are already set, no changes needed
                return {'ret': True, 'changed': False}
            payload = {
                'Boot': {
                    'BootSourceOverrideEnabled': 'Once',
                    'BootSourceOverrideTarget': bootdevice
                }
            }

        response = self.patch_request(self.root_uri + self.systems_uris[0], payload)
        if response['ret'] is False:
            return response
        return {'ret': True, 'changed': True}

    def set_bios_attributes(self, attr):
        result = {}
        key = "Bios"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uris[0])
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        bios_uri = data[key]["@odata.id"]

        # Extract proper URI
        response = self.get_request(self.root_uri + bios_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        # First, check if BIOS attribute exists
        if attr['bios_attr_name'] not in data[u'Attributes']:
            return {'ret': False, 'msg': "BIOS attribute not found"}

        # Find out if value is already set to what we want. If yes, return
        if data[u'Attributes'][attr['bios_attr_name']] == attr['bios_attr_value']:
            return {'ret': True, 'changed': False, 'msg': "BIOS attribute already set"}

        set_bios_attr_uri = data["@Redfish.Settings"]["SettingsObject"]["@odata.id"]

        # Example: bios_attr = {\"name\":\"value\"}
        bios_attr = "{\"" + attr['bios_attr_name'] + "\":\"" + attr['bios_attr_value'] + "\"}"
        payload = {"Attributes": json.loads(bios_attr)}
        response = self.patch_request(self.root_uri + set_bios_attr_uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True, 'changed': True, 'msg': "Modified BIOS attribute"}

    def set_boot_order(self, boot_list):
        if not boot_list:
            return {'ret': False,
                    'msg': "boot_order list required for SetBootOrder command"}

        # TODO(billdodd): change to self.systems_uri after PR 62921 merged
        systems_uri = self.systems_uris[0]
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        # Confirm needed Boot properties are present
        if 'Boot' not in data or 'BootOrder' not in data['Boot']:
            return {'ret': False, 'msg': "Key BootOrder not found"}

        boot = data['Boot']
        boot_order = boot['BootOrder']
        boot_options_dict = self._get_boot_options_dict(boot)

        # validate boot_list against BootOptionReferences if available
        if boot_options_dict:
            boot_option_references = boot_options_dict.keys()
            for ref in boot_list:
                if ref not in boot_option_references:
                    return {'ret': False,
                            'msg': "BootOptionReference %s not found in BootOptions" % ref}

        # If requested BootOrder is already set, nothing to do
        if boot_order == boot_list:
            return {'ret': True, 'changed': False,
                    'msg': "BootOrder already set to %s" % boot_list}

        payload = {
            'Boot': {
                'BootOrder': boot_list
            }
        }
        response = self.patch_request(self.root_uri + systems_uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True, 'changed': True, 'msg': "BootOrder set"}

    def set_default_boot_order(self):
        # TODO(billdodd): change to self.systems_uri after PR 62921 merged
        systems_uri = self.systems_uris[0]
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        # get the #ComputerSystem.SetDefaultBootOrder Action and target URI
        action = '#ComputerSystem.SetDefaultBootOrder'
        if 'Actions' not in data or action not in data['Actions']:
            return {'ret': False, 'msg': 'Action %s not found' % action}
        if 'target' not in data['Actions'][action]:
            return {'ret': False,
                    'msg': 'target URI missing from Action %s' % action}
        action_uri = data['Actions'][action]['target']

        # POST to Action URI
        payload = {}
        response = self.post_request(self.root_uri + action_uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True, 'changed': True,
                'msg': "BootOrder set to default"}

    def get_chassis_inventory(self):
        result = {}
        chassis_results = []

        # Get these entries, but does not fail if not found
        properties = ['ChassisType', 'PartNumber', 'AssetTag',
                      'Manufacturer', 'IndicatorLED', 'SerialNumber', 'Model']

        # Go through list
        for chassis_uri in self.chassis_uri_list:
            response = self.get_request(self.root_uri + chassis_uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']
            chassis_result = {}
            for property in properties:
                if property in data:
                    chassis_result[property] = data[property]
            chassis_results.append(chassis_result)

        result["entries"] = chassis_results
        return result

    def get_fan_inventory(self):
        result = {}
        fan_results = []
        key = "Thermal"
        # Get these entries, but does not fail if not found
        properties = ['FanName', 'Reading', 'ReadingUnits', 'Status']

        # Go through list
        for chassis_uri in self.chassis_uri_list:
            response = self.get_request(self.root_uri + chassis_uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']
            if key in data:
                # match: found an entry for "Thermal" information = fans
                thermal_uri = data[key]["@odata.id"]
                response = self.get_request(self.root_uri + thermal_uri)
                if response['ret'] is False:
                    return response
                result['ret'] = True
                data = response['data']

                for device in data[u'Fans']:
                    fan = {}
                    for property in properties:
                        if property in device:
                            fan[property] = device[property]
                    fan_results.append(fan)
        result["entries"] = fan_results
        return result

    def get_chassis_power(self):
        result = {}
        key = "Power"

        # Get these entries, but does not fail if not found
        properties = ['Name', 'PowerAllocatedWatts',
                      'PowerAvailableWatts', 'PowerCapacityWatts',
                      'PowerConsumedWatts', 'PowerMetrics',
                      'PowerRequestedWatts', 'RelatedItem', 'Status']

        chassis_power_results = []
        # Go through list
        for chassis_uri in self.chassis_uri_list:
            chassis_power_result = {}
            response = self.get_request(self.root_uri + chassis_uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']
            if key in data:
                response = self.get_request(self.root_uri + data[key]['@odata.id'])
                data = response['data']
                if 'PowerControl' in data:
                    if len(data['PowerControl']) > 0:
                        data = data['PowerControl'][0]
                        for property in properties:
                            if property in data:
                                chassis_power_result[property] = data[property]
                else:
                    return {'ret': False, 'msg': 'Key PowerControl not found.'}
                chassis_power_results.append(chassis_power_result)
            else:
                return {'ret': False, 'msg': 'Key Power not found.'}

        result['entries'] = chassis_power_results
        return result

    def get_chassis_thermals(self):
        result = {}
        sensors = []
        key = "Thermal"

        # Get these entries, but does not fail if not found
        properties = ['Name', 'PhysicalContext', 'UpperThresholdCritical',
                      'UpperThresholdFatal', 'UpperThresholdNonCritical',
                      'LowerThresholdCritical', 'LowerThresholdFatal',
                      'LowerThresholdNonCritical', 'MaxReadingRangeTemp',
                      'MinReadingRangeTemp', 'ReadingCelsius', 'RelatedItem',
                      'SensorNumber']

        # Go through list
        for chassis_uri in self.chassis_uri_list:
            response = self.get_request(self.root_uri + chassis_uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']
            if key in data:
                thermal_uri = data[key]["@odata.id"]
                response = self.get_request(self.root_uri + thermal_uri)
                if response['ret'] is False:
                    return response
                result['ret'] = True
                data = response['data']
                if "Temperatures" in data:
                    for sensor in data[u'Temperatures']:
                        sensor_result = {}
                        for property in properties:
                            if property in sensor:
                                if sensor[property] is not None:
                                    sensor_result[property] = sensor[property]
                        sensors.append(sensor_result)

        if sensors is None:
            return {'ret': False, 'msg': 'Key Temperatures was not found.'}

        result['entries'] = sensors
        return result

    def get_cpu_inventory(self, systems_uri):
        result = {}
        cpu_list = []
        cpu_results = []
        key = "Processors"
        # Get these entries, but does not fail if not found
        properties = ['Id', 'Manufacturer', 'Model', 'MaxSpeedMHz', 'TotalCores',
                      'TotalThreads', 'Status']

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        processors_uri = data[key]["@odata.id"]

        # Get a list of all CPUs and build respective URIs
        response = self.get_request(self.root_uri + processors_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for cpu in data[u'Members']:
            cpu_list.append(cpu[u'@odata.id'])

        for c in cpu_list:
            cpu = {}
            uri = self.root_uri + c
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            data = response['data']

            for property in properties:
                if property in data:
                    cpu[property] = data[property]

            cpu_results.append(cpu)
        result["entries"] = cpu_results
        return result

    def get_multi_cpu_inventory(self):
        return self.aggregate(self.get_cpu_inventory)

    def get_memory_inventory(self, systems_uri):
        result = {}
        memory_list = []
        memory_results = []
        key = "Memory"
        # Get these entries, but does not fail if not found
        properties = ['SerialNumber', 'MemoryDeviceType', 'PartNuber',
                      'MemoryLocation', 'RankCount', 'CapacityMiB', 'OperatingMemoryModes', 'Status', 'Manufacturer', 'Name']

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        memory_uri = data[key]["@odata.id"]

        # Get a list of all DIMMs and build respective URIs
        response = self.get_request(self.root_uri + memory_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for dimm in data[u'Members']:
            memory_list.append(dimm[u'@odata.id'])

        for m in memory_list:
            dimm = {}
            uri = self.root_uri + m
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            data = response['data']

            if "Status" in data:
                if "State" in data["Status"]:
                    if data["Status"]["State"] == "Absent":
                        continue
            else:
                continue

            for property in properties:
                if property in data:
                    dimm[property] = data[property]

            memory_results.append(dimm)
        result["entries"] = memory_results
        return result

    def get_multi_memory_inventory(self):
        return self.aggregate(self.get_memory_inventory)

    def get_nic_inventory(self, resource_uri):
        result = {}
        nic_list = []
        nic_results = []
        key = "EthernetInterfaces"
        # Get these entries, but does not fail if not found
        properties = ['Description', 'FQDN', 'IPv4Addresses', 'IPv6Addresses',
                      'NameServers', 'MACAddress', 'PermanentMACAddress',
                      'SpeedMbps', 'MTUSize', 'AutoNeg', 'Status']

        response = self.get_request(self.root_uri + resource_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        ethernetinterfaces_uri = data[key]["@odata.id"]

        # Get a list of all network controllers and build respective URIs
        response = self.get_request(self.root_uri + ethernetinterfaces_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for nic in data[u'Members']:
            nic_list.append(nic[u'@odata.id'])

        for n in nic_list:
            nic = {}
            uri = self.root_uri + n
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            data = response['data']

            for property in properties:
                if property in data:
                    nic[property] = data[property]

            nic_results.append(nic)
        result["entries"] = nic_results
        return result

    def get_multi_nic_inventory(self, resource_type):
        ret = True
        entries = []

        #  Given resource_type, use the proper URI
        if resource_type == 'Systems':
            resource_uris = self.systems_uris
        elif resource_type == 'Manager':
            # put in a list to match what we're doing with systems_uris
            resource_uris = [self.manager_uri]

        for resource_uri in resource_uris:
            inventory = self.get_nic_inventory(resource_uri)
            ret = inventory.pop('ret') and ret
            if 'entries' in inventory:
                entries.append(({'resource_uri': resource_uri},
                                inventory['entries']))
        return dict(ret=ret, entries=entries)

    def get_virtualmedia(self, resource_uri):
        result = {}
        virtualmedia_list = []
        virtualmedia_results = []
        key = "VirtualMedia"
        # Get these entries, but does not fail if not found
        properties = ['Description', 'ConnectedVia', 'Id', 'MediaTypes',
                      'Image', 'ImageName', 'Name', 'WriteProtected',
                      'TransferMethod', 'TransferProtocolType']

        response = self.get_request(self.root_uri + resource_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        virtualmedia_uri = data[key]["@odata.id"]

        # Get a list of all virtual media and build respective URIs
        response = self.get_request(self.root_uri + virtualmedia_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for virtualmedia in data[u'Members']:
            virtualmedia_list.append(virtualmedia[u'@odata.id'])

        for n in virtualmedia_list:
            virtualmedia = {}
            uri = self.root_uri + n
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            data = response['data']

            for property in properties:
                if property in data:
                    virtualmedia[property] = data[property]

            virtualmedia_results.append(virtualmedia)
        result["entries"] = virtualmedia_results
        return result

    def get_multi_virtualmedia(self):
        ret = True
        entries = []

        # Because _find_managers_resource() only find last Manager uri in self.manager_uri, not one list. This should be 1 issue.
        # I have to put manager_uri into list to reduce future changes when the issue is fixed.
        resource_uris = [self.manager_uri]

        for resource_uri in resource_uris:
            virtualmedia = self.get_virtualmedia(resource_uri)
            ret = virtualmedia.pop('ret') and ret
            if 'entries' in virtualmedia:
                entries.append(({'resource_uri': resource_uri},
                               virtualmedia['entries']))
        return dict(ret=ret, entries=entries)

    def get_psu_inventory(self):
        result = {}
        psu_list = []
        psu_results = []
        key = "PowerSupplies"
        # Get these entries, but does not fail if not found
        properties = ['Name', 'Model', 'SerialNumber', 'PartNumber', 'Manufacturer',
                      'FirmwareVersion', 'PowerCapacityWatts', 'PowerSupplyType',
                      'Status']

        # Get a list of all Chassis and build URIs, then get all PowerSupplies
        # from each Power entry in the Chassis
        chassis_uri_list = self.chassis_uri_list
        for chassis_uri in chassis_uri_list:
            response = self.get_request(self.root_uri + chassis_uri)
            if response['ret'] is False:
                return response

            result['ret'] = True
            data = response['data']

            if 'Power' in data:
                power_uri = data[u'Power'][u'@odata.id']
            else:
                continue

            response = self.get_request(self.root_uri + power_uri)
            data = response['data']

            if key not in data:
                return {'ret': False, 'msg': "Key %s not found" % key}

            psu_list = data[key]
            for psu in psu_list:
                psu_not_present = False
                psu_data = {}
                for property in properties:
                    if property in psu:
                        if psu[property] is not None:
                            if property == 'Status':
                                if 'State' in psu[property]:
                                    if psu[property]['State'] == 'Absent':
                                        psu_not_present = True
                            psu_data[property] = psu[property]
                if psu_not_present:
                    continue
                psu_results.append(psu_data)

        result["entries"] = psu_results
        if not result["entries"]:
            return {'ret': False, 'msg': "No PowerSupply objects found"}
        return result

    def get_multi_psu_inventory(self):
        return self.aggregate(self.get_psu_inventory)

    def get_system_inventory(self, systems_uri):
        result = {}
        inventory = {}
        # Get these entries, but does not fail if not found
        properties = ['Status', 'HostName', 'PowerState', 'Model', 'Manufacturer',
                      'PartNumber', 'SystemType', 'AssetTag', 'ServiceTag',
                      'SerialNumber', 'SKU', 'BiosVersion', 'MemorySummary',
                      'ProcessorSummary', 'TrustedModules']

        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for property in properties:
            if property in data:
                inventory[property] = data[property]

        result["entries"] = inventory
        return result

    def get_multi_system_inventory(self):
        return self.aggregate(self.get_system_inventory)
