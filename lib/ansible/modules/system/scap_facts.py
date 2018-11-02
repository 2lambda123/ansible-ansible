#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, MindPoint Group, Jonathan Davila <jonathan@davila.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

try:
    from elementtree.ElementTree import parse
except ImportError:
    from xml.etree.ElementTree import parse

from os.path import dirname

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes

DOCUMENTATION = '''
---
module: scap_facts
version_added: 2.8
short_description: Processes XML results from oscap scans as facts and allow for score-based erroring
description:
    - Parses the XML of result data generated by openscap scanner and exposes it in hostvars under scap_scan.
    - It also allows for the definition of failure in terms of scoring.
    - In this manner you can have the module cause a task failure in the even that certain
    - thresholds aren't met for specific severity levels and/or overall score.
notes:
    - Currently only validated to work against output from open-scap scanner xccdf evaluations.
    - Has only been tested with output xccdf's installed from scap-security-guide and from DISA.
    - Scores within a severity level are calculated against the total number of rules in said severity
    - excluding notselected, notchecked, and notapplicable rules, regardless of what is supplied to C(include_results).
author:
    - Jonathan Davila
options:
    path:
        description:
            - path to the results XML file
        required: yes
    namespace:
        description:
            - the xml namespace to use
        default: '{http://checklists.nist.gov/xccdf/1.1}'
    include_results:
        description:
            - the result types to include in ansible_facts, this excludes notselected, notchecked, and notapplicable results by default.
            - this option has no influence on scoring calculations
        default:
            - pass
            - fail
    min_score:
        description:
            - the minimum overall score required, if not met, will cause the task to fail
        default: 0
    min_high_score:
        description:
            - the minimum high severity score required, if not met, will cause the task to fail
        default: 0
    min_medium_score:
        description:
            - the minimum medium severity score required, if not met, will cause the task to fail
        default: 0
    min_low_score:
        description:
            - the minimum low severity score required, if not met, will cause the task to fail
        default: 0
'''

EXAMPLES = '''
- name: Require that all high severity rules pass
  scap_facts:
    path: ./scan-results.xml
    min_high_score: 100

- name: Require that all high severity rules pass and 75% of everything else
  scap_facts:
    path: ./scan-results.xml
    min_high_score: 100
    min_medium_score: 75
    min_low_score: 75

- name: Include notselected rules in ansible_facts
  scap_facts:
    path: ./scan-results.xml
    include_results:
        - pass
        - fail
        - notselected

- name: Only store failures into ansible_facts
  scap_facts:
    path: ./scan-results.xml
    include_results:
        - fail
'''

RETURN = '''
scap_scan:
    description: Results of the scan
    returned: always
    type: complex
    contains:
        benchmark_id:
            description: The ID of the benchmark used in the scan
            returned: always
            type: string
            sample: xccdf_org.open-scap_testresult_stig-rhel7-disa
        start_time:
            description: time when the scan started
            returned: always
            type: string
            sample: '2018-10-20T09:57:26'
        end_time:
            description: time when the scan completed
            returned: always
            type: string
            sample: '2018-10-20T09:58:18'
        score:
            description: overall score across all rules
            returned: always
            type: float
            sample: 76.732140
        results:
            description: Results of the scan organized by severity
            returned: always
            type: complex
            contains:
                $SEVERITY_IDENTIFIER:
                    description: Data for a particular severity
                    returned: always
                    type: complex
                    contains:
                        score:
                            description: severity level score
                            returned: always
                            type: float
                            sample: 34.09090909090909
                        total_graded:
                            description: total number of rules checked in this severity
                            returned: always
                            type: int
                            sample: 44
                        total_failing:
                            description: total number of rules that failed the scan
                            returned: always
                            type: int
                            sample: 29
                        total_notselected:
                            description: total number of rules not scanned because they were not enabled by the selected profile during the scan
                            returned: always
                            type: int
                            sample: 0
                        total_notchecked:
                            description: total number of rules not checked because SCAP doesnt have check content for the rule
                            returned: always
                            type: int
                            sample: 33
                        total_notapplicable:
                            description: total number of rules not checked because they do not apply to the given system
                            returned: always
                            type: int
                            sample: 22
                        total_passing:
                            description: total number of rules that passed
                            returned: always
                            type: int
                            sample: 15
                        data:
                            description: the scan results specific to the severity level
                            returned: always
                            type: complex
                            contains:
                                $RULE_IDENTIFIER:
                                    description: the identifier of the rule scanned
                                    returned: always
                                    type: complex
                                    contains:
                                        title:
                                            description: human readable description of the rule
                                            returned: always
                                            type: string
                                            sample: Set Account Expiration Following Inactivity
                                        severity:
                                            description: the severity of the rule
                                            returned: always
                                            type: string
                                            sample: medium
                                        result:
                                            type: string
                                            returned: always
                                            sample: fail
                                        references:
                                            description: dict of reference urls and corresponding reference ids
                                            returned: always
                                            sample:
                                                - id: SRG-OS-000480-GPOS-00227
                                                  source: http://iase.disa.mil/stigs/os/general/Pages/index.aspx
                                            type: list
'''


class ScapEvalXccdfResultReader:
    """ Parses the XML results of the output generated by `oscap eval xccdf...`"""
    def __init__(self, path, namespace, include_results):
        b_path = to_bytes(path, errors='surrogate_or_strict')
        tree = parse(open(b_path, 'rb'))
        self.root = tree.getroot()
        self.results = dict()
        self.include_results = include_results
        self.ns = namespace
        self.res_node = self.root.find(self.ns +'TestResult')

    def _get_results(self):
        for rule in self.root.findall('.//' + self.ns + 'Rule'):
            rule_id = rule.get('id')  # This is the id as as represented in the XML, example: 'sshd_required'
            self.results[rule_id] = dict(
                severity=rule.get('severity'),
                title=rule.find(self.ns + 'title').text, # Human-friendly title
                references=[]
            )
            for ref in rule.findall(self.ns + 'reference'):
                self.results[rule_id]['references'].append(dict(
                    source=ref.get('href'),  # References are where the rules are derived from, unfortunately it's only URLs so the output is a bit more verbose but
                    id=ref.text  # this is the ID where the rule lives within the associated reference, example '5.2.1.3' for CIS
                ))

        for res in self.res_node.findall('.//' + self.ns + 'rule-result'):
            id = res.get('idref') # this is how we map the result to the data gathered above
            result = res.find(self.ns + 'result').text
            self.results[id]['result'] = result

    def _organize_data(self, severity, data):
        def percentage(part, whole):
            return 100 * float(part) / float(whole)
        raw = dict((k, v) for k, v in data.items() if v['severity'] == severity)
        wanted = dict((k, v) for k, v in raw.items() if v['result'] in self.include_results)
        fail = dict((k, v) for k, v in raw.items() if v['result'] == 'fail')
        passing = dict((k, v) for k,v in raw.items() if v['result'] == 'pass')
        ns = dict((k, v) for k, v in raw.items() if v['result'] == 'notselected')
        na = dict((k, v) for k, v in raw.items() if v['result'] == 'notapplicable')
        nc = dict((k, v) for k, v in raw.items() if v['result'] == 'notchecked')
        total_count = len(raw.keys())
        pass_count = len(passing.keys())
        fail_count = len(fail.keys())
        ns_count = len(ns.keys())
        na_count = len(na.keys())
        nc_count = len(nc.keys())
        graded_count = total_count - ns_count - na_count - nc_count

        return dict(
                total_graded=graded_count,
                total_passing=pass_count,
                total_failing=fail_count,
                total_notselected=ns_count,
                total_notapplicable=na_count,
                total_notchecked=nc_count,
                score=percentage(pass_count, graded_count),
                data=wanted
            )

    def get_stats(self):
        self._get_results()
        data = self.results
        return dict(
            high=self._organize_data('high', data),
            medium=self._organize_data('medium', data),
            low=self._organize_data('low', data)
        )

    @property
    def id(self):
        """ ID of the scap test itself """
        return self.res_node.get('id')

    @property
    def start_time(self):
        return self.res_node.get('start-time')

    @property
    def end_time(self):
        return self.res_node.get('end-time')

    @property
    def max_score(self):
        return self.res_node.find(self.ns + 'score').get('maximum')

    @property
    def score(self):
        return float(self.res_node.find(self.ns + 'score').text)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=True, type='path'),
            namespace=dict(required=False, type='str', default='{http://checklists.nist.gov/xccdf/1.1}'),
            include_results=dict(required=False, type='list', default=['pass', 'fail']),
            min_score=dict(required=False, type='int', default=0),
            min_high_score=dict(required=False, type='int', default=0),
            min_medium_score=dict(required=False, type='int', default=0),
            min_low_score=dict(required=False, type='int', default=0)
        ),
        supports_check_mode=True # We can let this module run in check mode because it doesnt ever 'change' anything
    )
    path = module.params['path']
    namespace = module.params['namespace']
    include_results = module.params['include_results']
    min_score = module.params['min_score']
    min_high_score = module.params['min_high_score']
    min_medium_score = module.params['min_medium_score']
    min_low_score = module.params['min_low_score']

    scap = ScapEvalXccdfResultReader(path, namespace, include_results)

    if int(float(scap.score)) < min_score:
        module.fail_json(msg='Minimum overall score of ' + min_score + ' was not met.')

    data = scap.get_stats()

    if int(float(data['high']['score'])) < min_high_score:
        module.fail_json(msg='Minimum high severity score of ' + min_high_score + ' was not met.')

    if int(float(data['medium']['score'])) < min_medium_score:
        module.fail_json(msg='Minimum medium severity score of ' + min_medium_score + ' was not met.')

    if int(float(data['low']['score'])) < min_low_score:
        module.fail_json(msg='Minimum low severity score of ' + min_low_score + ' was not met.')

    module.exit_json(
        ansible_facts=dict(
            scap_scan=dict(
                    benchmark_id=scap.id,
                    start_time=scap.start_time,
                    end_time=scap.end_time,
                    score=scap.score,
                    results=data
            )
        )
    )


if __name__ == '__main__':
    main()
