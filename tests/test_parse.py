# -*- coding: utf-8 -*-

#    Copyright (C) 2021 Mathew Topper
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


import pytest

from dtocean_reliability.parse import SubNetwork, check_nodes


def test_check_nodes_unique():
    
    hierarchy_a = {"array": {}, "device001": {}}
    hierarchy_b = {"array": {}, "device001": {}, "device002": {}}
    
    network_a = SubNetwork(hierarchy_a, None)
    network_b = SubNetwork(hierarchy_b, None)
    
    with pytest.raises(ValueError) as excinfo:
        check_nodes(network_a, network_b)
    
    assert "Unique nodes detected" in str(excinfo.value)
    assert "device002" in str(excinfo.value)
