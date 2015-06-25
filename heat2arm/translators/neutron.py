# Copyright 2015 Cloudbase Solutions Srl
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from heat2arm import constants
from heat2arm.translators import base

'''
ARM Network Resource Provider:
https://azure.microsoft.com/en-gb/documentation/articles/resource-groups-networking/
'''


class NeutronNetARMTranslator(base.BaseHeatARMTranslator):
    # No direct ARM resource translation
    # Azure virtual networks encompass both Neutron networks and subnets
    heat_resource_type = "OS::Neutron::Net"

    def get_variables(self):
        return {
            "virtualNetworkName%s" % self._name: self._name,
            "virtualNetworkSubnetName%s" % self._name:
            "%s_subnet1" % self._name,
            "virtualNetworkName_ref_%s" % self._name:
            "[resourceId('Microsoft.Network/virtualNetworks', "
            "variables('virtualNetworkName%s'))]" % self._name,
            "virtualNetworkSubnetName_ref_%s" % self._name:
            "[concat(variables('virtualNetworkName_ref_%(net_name)s'),"
            "'/subnets/',variables('virtualNetworkSubnetName%(net_name)s'))]" %
            {"net_name": self._name}
        }


class NeutronSubnetARMTranslator(base.BaseHeatARMTranslator):
    heat_resource_type = "OS::Neutron::Subnet"

    def get_variables(self):
        cidr = self._heat_resource.properties['cidr']
        return {
            "subNetAddressPrefix%s" % self._name: cidr
        }

    def get_resource_data(self):
        heat_net_resource = base.get_ref_heat_resource(
            self._heat_resource, "network_id")
        net_name = heat_net_resource.name

        return [{
            "apiVersion": constants.ARM_API_2015_05_01_PREVIEW,
            "type": "Microsoft.Network/virtualNetworks",
            "name":
            "[variables('virtualNetworkName%s')]" % net_name,
            "location": "[variables('location')]",
            "properties": {
                "addressSpace": {
                    "addressPrefixes": [
                        # TODO: support multiple subnets
                        "[variables('subNetAddressPrefix%s')]" % self._name
                    ]
                },
                "subnets": [{
                    # TODO: support multiple subnets
                    # Main issue here is that ARM networkInterfaces contain a
                    # reference to a subnet, while a Neutron port contains a
                    # reference to a network
                    "name":
                    "[variables('virtualNetworkSubnetName%s')]" % net_name,
                    "properties": {
                        "addressPrefix":
                        "[variables('subNetAddressPrefix%s')]" % self._name
                    }
                }]
            }
        }]


class NeutronPortARMTranslator(base.BaseHeatARMTranslator):
    heat_resource_type = "OS::Neutron::Port"

    def get_variables(self):
        return {
            "nicName%s" % self._name: self._name,
        }

    def get_dependencies(self):
        heat_net_resource = base.get_ref_heat_resource(
            self._heat_resource, "network_id")
        net_name = heat_net_resource.name

        return [
            "[concat('Microsoft.Network/virtualNetworks/', "
            "variables('virtualNetworkName%s'))]" % net_name
        ]

    def get_resource_data(self):
        heat_net_resource = base.get_ref_heat_resource(
            self._heat_resource, "network_id")
        net_name = heat_net_resource.name

        nic_properties_data = {
            # TODO: check the Heat net dhcp property
            "privateIPAllocationMethod": "Dynamic",
            "subnet": {
                "id":
                "[variables('virtualNetworkSubnetName_ref_%s')]" % net_name
            }
        }

        depends_on = {

        }

        return [{
            "apiVersion": constants.ARM_API_2015_05_01_PREVIEW,
            "type": "Microsoft.Network/networkInterfaces",
            "name": "[variables('nicName%s')]" % self._name,
            "location": "[variables('location')]",
            "dependsOn": self.get_dependencies(),
            "properties": {
                "ipConfigurations": [{
                    "name": "ipconfig%s" % self._name,
                    "properties": nic_properties_data,
                }]
            }
        }]


class NeutronFloatingIPARMTranslator(base.BaseHeatARMTranslator):
    heat_resource_type = "OS::Neutron::FloatingIP"


class NeutronRouterARMTranslator(base.BaseHeatARMTranslator):
    # No direct ARM resource translation
    heat_resource_type = "OS::Neutron::Router"


class NeutronRouterInterfaceARMTranslator(base.BaseHeatARMTranslator):
    # No direct ARM resource translation
    heat_resource_type = "OS::Neutron::RouterInterface"