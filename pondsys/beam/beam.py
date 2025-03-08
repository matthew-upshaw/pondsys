# pondsys.beam.beam.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

from joistpy import sji
from steelpy import aisc
from Pynite import FEModel3D
import math
import matplotlib.pyplot as plt
import numpy as np
import re
from scipy.integrate import simpson

from pondsys.utils.divide_by_zero import divide_by_zero

valid_sections = []
for key, _ in sji.K_Series.designations.items():
    valid_sections.append(key.split('_')[1].upper())
for key, _ in sji.KCS_Series.designations.items():
    valid_sections.append(key.split('_')[1].upper())
for key, _ in aisc.W_shapes.sections.items():
    valid_sections.append(key.upper())

# Cases are [D, Lr, R, S, PR, PS]
load_cases = {
    '1.0D': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    '1.0Lr': [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    '1.0R': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    '1.0PR': [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    '1.0S': [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    '1.0PS': [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
}
# Combinations are [D, Lr, R, S, PR, PS]
load_combinations = {
    'asd': {
        '1.0D+1.0Lr': [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        '1.0D+1.0R': [1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        '1.0D+1.0R+1.0P': [1.0, 0.0, 1.0, 0.0, 1.0, 0.0],
        '1.0D+1.0S': [1.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        '1.0D+1.0S+1.0P': [1.0, 0.0, 0.0, 1.0, 0.0, 1.0],
    },
    'lrfd': {
        '1.4D': [1.4, 0.0, 0.0, 0.0, 0.0, 0.0],
        '1.2D+1.6Lr': [1.2, 1.6, 0.0, 0.0, 0.0, 0.0],
        '1.2D+1.6R': [1.2, 0.0, 1.6, 0.0, 0.0, 0.0],
        '1.2D+1.6R+1.6P': [1.2, 0.0, 1.6, 0.0, 1.6, 0.0],
        '1.2D+1.6S': [1.2, 0.0, 0.0, 1.6, 0.0, 0.0],
        '1.2D+1.6S+1.6P': [1.2, 0.0, 0.0, 1.6, 0.0, 1.6],
    }

}

class Beam:
    """
    A class represeting a beam to be analyzed for ponding.

    Attributes
    ----------
    beam_slope : float
        The slope of the beam in inches/foot.
    dead_load : float
        The dead load in psf.
    deflection_history : list
        The history of the deflection at each segment of the beam in inches.
    dist_loads : list
        The distributed loads on the beam, [start, stop, start_load, stop_load, case],
        in feet and plf.
    length : float
        The length of the beam in ft.
    model : Pynite.FEModel3D
        The Pynite model of the beam.
    point_loads : list
        The point loads on the beam, [location, load, case], in feet and pounds.
    ponding_depth_history : list
        The history of the ponding depth at each segment of the beam in inches.
    rain_depth : tuple
        The depth of (static head, hydraulic head) in inches.
    rain_load : numpy.ndarray
        The rain load extents and intensity at the extents.
    section : str
        The string representing the beam section, either standard AISC W-shape
        or SJI joist designation.
    section_properties : dict
        The properties of the beam section.
    segments : numpy.ndarray
        The segments of the beam.
    snow_uni : float
        The uniform snow load in psf.
    spring_constants : tuple
        The spring constants in kips/inch at each end of the beam;
        1e12 by default.
    stations : numpy.ndarray
        The stations along the beam.
    station_elevations : numpy.ndarray
        The elevations of the stations along the beam in inches.
    tributary_width : float
        The tributary width in feet.

    Methods
    -------
    add_or_update_dead_load(dead_load)
        Add a dead load to the beam.
    add_or_update_rain_load(rain_depth)
        Add a rain depth to the beam.
    add_or_update_snow_load(snow_uni)
        Add a uniform snow load to the beam.
    add_or_update_tributary_width(tributary_width)
        Add a tributary width to the beam.
    add_or_update_section(section)
        Add a section to the beam.
    """

    def __init__(self, length, name="PondSys Beam"):
        self.length = length
        self.name = name

        self._segment_beam()
        self.ponded_depth_history = [{
            'rain': np.zeros(
            len(self.stations)),
            'snow': np.zeros(
            len(self.stations))}]
        self.deflection_history = [{
            'rain': np.zeros((
            1,
            len(self.stations),
        )),
            'snow': np.zeros((
            1,
            len(self.stations),
        ))}]
        self.station_elevations = np.zeros(len(self.stations))
        self.add_or_update_beam_slope(0.0)
        self.add_or_update_rain_load((0.0, 0.0), auto_add_dist_load=False)
        self.add_or_update_section("W12X14")
        self.add_or_update_tributary_width(0.0)
        self.dist_loads = []
        self.point_loads = []
        self.supports = []
        self.support_nodes = {}
        self.reaction_envelope = {}
        self.max_moment_envelope = {
            'cases': {},
            'asd': {},
            'lrfd': {},
        }
        self.min_moment_envelope = {
            'cases': {},
            'asd': {},
            'lrfd': {},
        }
        self.max_shear_envelope = {
            'cases': {},
            'asd': {},
            'lrfd': {},
        }
        self.min_shear_envelope = {
            'cases': {},
            'asd': {},
            'lrfd': {},
        }
        self.max_defl_envelope = {
            'cases': {},
            'asd': {},
            'lrfd': {},
        }
        self.min_defl_envelope = {
            'cases': {},
            'asd': {},
            'lrfd': {},
        }
        self.analysis_stats = {}
        self.model = None
        self.valid_results = False
        self.analysis_ready = False

    def add_support(self, location, DX, DY, RZ):
        """
        Add a support to the beam.

        Parameters
        ----------
        location : float
            The location of the support from the left side of the beam in feet.
        DX : bool
            The spring constant in the x-direction in lb/ft.
        DY : bool
            The spring constant in the y-direction in lb/ft.
        RZ : bool
            The rotational spring constant in the z-direction in lb-ft/rad.
        """
        location = float(location)
        DX = float(DX)
        DY = float(DY)
        RZ = float(RZ)
        if location < 0:
            raise ValueError("Location must be positive.")
        if type(location) != float:
            raise TypeError("Location must be a float.")
        if type(DX) != float or type(DY) != float or type(RZ) != float:
            raise TypeError("DX, DY, and RZ must be floats.")
        self.supports.append([location, DX, DY, RZ])

        self.valid_results = False

    def delete_support(self, index):
        """
        Delete a support from the beam.

        Parameters
        ----------
        index : int
            The index of the support to delete.
        """
        if index < 0 or index >= len(self.supports):
            raise ValueError("Invalid index.")
        self.valid_results = False
        return self.supports.pop(index)

    def list_supports(self):
        """
        List the supports of the beam.
        """
        return self.supports

    def add_or_update_beam_slope(self, beam_slope):
        """
        Add a beam slope to the beam.

        Parameters
        ----------
        beam_slope : float
            The slope of the beam.
        """
        beam_slope = float(beam_slope)
        if beam_slope < 0:
            raise ValueError("Beam slope must be positive.")
        if type(beam_slope) != float:
            raise TypeError("Beam slope must be a float.")
        self.beam_slope = beam_slope
        self.station_elevations = self.stations * self.beam_slope

        self.valid_results = False

    def add_dist_load(self, start, stop, start_load, stop_load, case):
        """
        Add a distributed load to the beam.

        Parameters
        ----------
        start : float
            The start of the distributed load in feet.
        stop : float
            The stop of the distributed load in feet.
        start_load : float
            The start load in plf.
        stop_load : float
            The stop load in plf.
        case : str
            The case of the distributed load.
        """
        start = float(start)
        stop = float(stop)
        start_load = float(start_load)
        stop_load = float(stop_load)
        if start < 0 or stop < 0:
            raise ValueError("Start and stop locations must be positive.")
        if start > self.length or stop > self.length:
            raise ValueError("Start and stop locations must be less or equal to the length of the beam.")
        if type(start) != float or type(stop) != float:
            raise TypeError("Start and stop must be floats.")
        if type(start_load) != float or type(stop_load) != float:
            raise TypeError("Start and stop loads must be floats.")
        if case not in ['D', 'Lr', 'R', 'S']:
            raise ValueError("Case must be one of dead (D), roof live (Lr), rain (R), or snow (S).")
        self.dist_loads.append([start, stop, start_load, stop_load, case])

        self.valid_results = False

    def delete_dist_load(self, index):
        """
        Delete a distributed load from the beam.

        Parameters
        ----------
        index : int
            The index of the distributed load to delete.
        """
        if index < 0 or index >= len(self.dist_loads):
            raise ValueError("Invalid index.")
        self.valid_results = False
        return self.dist_loads.pop(index)
    
    def list_dist_loads(self):
        """
        List the distributed loads on the beam.
        """
        return self.dist_loads
    
    def clear_dist_loads(self, case):
        """
        Clear the distributed loads of a given case.

        Parameters
        ----------
        case : str
            The case of the distributed load to clear.
        """
        if case not in ['D', 'Lr', 'R', 'S']:
            raise ValueError("Case must be one of dead (D), roof live (Lr), rain (R), or snow (S).")
        self.dist_loads = [i for i in self.dist_loads if i[4] != case]

        self.valid_results = False

    def add_point_load(self, location, load, case):
        """
        Add a point load to the beam.

        Parameters
        ----------
        location : float
            The location of the point load in feet.
        load : float
            The load of the point load in pounds.
        case : str
            The case of the point load.
        """
        location = float(location)
        load = float(load)
        if location < 0:
            raise ValueError("Location must be positive.")
        if location > self.length:
            raise ValueError("Location must be less or equal to the length of the beam.")
        if type(location) != float:
            raise TypeError("Location must be a float.")
        if type(load) != float:
            raise TypeError("Load must be a float.")
        if case not in ['D', 'Lr', 'R', 'S']:
            raise ValueError("Case must be one of dead (D), roof live (Lr), rain (R), or snow (S).")
        self.point_loads.append([location, load, case])

        self.valid_results = False

    def delete_point_load(self, index):
        """
        Delete a point load from the beam.

        Parameters
        ----------
        index : int
            The index of the point load to delete.
        """
        if index < 0 or index >= len(self.point_loads):
            raise ValueError("Invalid index.")
        self.valid_results = False
        return self.point_loads.pop(index)
    
    def list_point_loads(self):
        """
        List the point loads on the beam.
        """
        return self.point_loads
    
    def clear_point_loads(self, case):
        """
        Clear the point loads of a given case.

        Parameters
        ----------
        case : str
            The case of the point load to clear.
        """
        if case not in ['D', 'Lr', 'R', 'S']:
            raise ValueError("Case must be one of dead (D), roof live (Lr), rain (R), or snow (S).")
        self.point_loads = [i for i in self.point_loads if i[2] != case]

        self.valid_results = False

    def add_or_update_rain_load(self, rain_depth, auto_add_dist_load=True):
        """
        Add a rain load to the beam.

        Parameters
        ----------
        rain_depth : float
            The rain depth in inches.
        """
        rain_depth = tuple([float(i) for i in rain_depth])
        if rain_depth[0] < 0 or rain_depth[1] < 0:
            raise ValueError("Rain depth must be positive.")
        if type(rain_depth) != tuple:
            raise TypeError("Rain depth must be entered as (static head, hydraulic head).")
        if any([type(i) != float for i in rain_depth]):
            raise TypeError("Rain depth must be a tuple of floats.")
        if len(rain_depth) != 2:
            raise ValueError("Rain depth must be a tuple of length 2.")
        self.rain_depth = rain_depth
        
        if divide_by_zero(sum(self.rain_depth), self.beam_slope) <= self.length:
            rain_load_limit = sum(self.rain_depth)/self.beam_slope
        else:
            rain_load_limit = self.length
        
        rain_load_start = 5.2*sum(self.rain_depth)
        rain_load_end = 5.2*(sum(self.rain_depth) - rain_load_limit*self.beam_slope)

        if auto_add_dist_load:
            self.clear_dist_loads('R')

            self.add_dist_load(
                0.0,
                rain_load_limit,
                rain_load_start*self.tributary_width,
                rain_load_end*self.tributary_width,
                'R',
            )
        
        self.valid_results = False

    def add_or_update_tributary_width(self, tributary_width):
        """
        Add a tributary width to the beam.

        Parameters
        ----------
        tributary_width : float
            The tributary width in feet.
        """
        tributary_width = float(tributary_width)
        if tributary_width < 0:
            raise ValueError("Tributary width must be positive.")
        if type(tributary_width) != float:
            raise TypeError("Tributary width must be a float.")
        self.tributary_width = tributary_width

        self.valid_results = False

    def add_or_update_section(self, section):
        """
        Add a section to the beam.

        Parameters
        ----------
        section : str
            The section of the beam.
        """
        w_shape_pattern = re.compile(r'w[0-9]+x[0-9]+', re.IGNORECASE)
        k_joist_pattern = re.compile(r'[0-9]+k[0-9]+', re.IGNORECASE)
        kcs_joist_pattern = re.compile(r'[0-9]+kcs[0-9]+', re.IGNORECASE)

        if section.upper() not in valid_sections:
            raise ValueError(
                "Invalid section. Please enter a W-shape, K-joist, or KCS-joist."
            )
        if type(section) != str:
            raise TypeError("Section must be a string.")
        self.section = section.upper()

        if re.match(w_shape_pattern, self.section.upper()):
            self.section_properties = {
                'Iy': aisc.W_shapes.sections[self.section.upper()].Iy,
                'Iz' : aisc.W_shapes.sections[self.section.upper()].Ix,
                'J' : aisc.W_shapes.sections[self.section.upper()].J,
                'A' : aisc.W_shapes.sections[self.section.upper()].area,
            }

        elif re.match(k_joist_pattern, self.section.upper()):
            des = 'K_' + self.section.upper()
            self.section_properties = {
                'Iy': sji.K_Series.designations[des].get_mom_inertia(span=self.length)*0.05,
                'Iz' : sji.K_Series.designations[des].get_mom_inertia(span=self.length),
                'J' : sji.K_Series.designations[des].get_mom_inertia(span=self.length)*1.05,
                'A' : sji.K_Series.designations[des].get_eq_area(),
            }

        elif re.match(kcs_joist_pattern, self.section.upper()):
            des = 'KCS_' + self.section.upper()
            self.section_properties = {
                'Iy': sji.KCS_Series.designations[des].get_mom_inertia(span=self.length)*0.05,
                'Iz' : sji.KCS_Series.designations[des].get_mom_inertia(span=self.length),
                'J' : sji.KCS_Series.designations[des].get_mom_inertia(span=self.length)*1.05,
                'A' : sji.KCS_Series.designations[des].get_eq_area(),
            }

        self.valid_results = False

    def create_model(self, ponding_load):
        """
        Create the model for the beam.

        Parameters
        ----------
        ponding_load : dict
            Dictionary containing numpy.ndarrays defining the ponding load due
            to either the rain or snow load.
        """
        # Define material properties of steel
        E = 29000.0
        G = 11200.0
        nu = 0.3
        rho = 2.836e-4

        # Initialize the model
        self.model = FEModel3D()

        # Define the material (steel) and section properties
        self.model.add_material("Steel", E, G, nu, rho)
        self.model.add_section(
            self.section.upper(),
            self.section_properties['A'],
            self.section_properties['Iy'],
            self.section_properties['Iz'],
            self.section_properties['J'],
        )

        # Define the member end nodes
        self.model.add_node('N1', 0.0, 0.0, 0.0)
        self.model.add_node('N2', self.length*12, 0.0, 0.0)

        # Define the support nodes
        if len(self.supports) == 0:
            raise ValueError("No supports defined. Please define supports.")
        for support in self.supports:
            # First check to see if a node is already defined at the support
            # location.
            check = any(
                np.isclose(
                    np.array((
                        node.X,
                        node.Y,
                        node.Z,
                    )),
                    np.array((
                        support[0]*12,
                        0.0,
                        0.0,
                    ))
                ).all() for node in self.model.nodes.values()
            )
            if not check:
                # If not, add the node
                self.model.add_node(
                    f'N{len(self.model.nodes)+1}',
                    support[0]*12,
                    0.0,
                    0.0,
                )

        # Define the member
        self.model.add_member(
            'M1',
            'N1',
            'N2',
            'Steel',
            self.section.upper(),
        )


        '''# Define the support conditions
        # First, simply-supported everywhere except DY
        self.model.def_support('N1', True, False, True, False, False, False)
        self.model.def_support('N2', True, False, True, True, False, False)

        # Now, the springs in DY
        self.model.def_support_spring('N1', 'DY', self.spring_constants[0])
        self.model.def_support_spring('N2', 'DY', self.spring_constants[1])'''

        # Define the support conditions
        self.support_nodes = {}
        for support in self.supports:
            # Find the node at the support location
            for node in self.model.nodes.values():
                if np.isclose(
                    np.array((
                        node.X,
                        node.Y,
                        node.Z,
                    )),
                    np.array((
                        support[0]*12,
                        0.0,
                        0.0,
                    ))
                ).all():
                    self.support_nodes[node.name] = support[0]
                    # Define the fixed degrees of freedom
                    self.model.def_support(
                        node.name,
                        False,
                        False,
                        True,
                        True,
                        False,
                        False,
                    )
                    # Define the spring constants
                    # x-direction
                    if not np.isclose(support[1], 0.0):
                        self.model.def_support_spring(
                            node.name,
                            'DX',
                            support[1]/12/1000,
                        )
                    # y-direction
                    if not np.isclose(support[2], 0.0):
                        self.model.def_support_spring(
                            node.name,
                            'DY',
                            support[2]/12/1000,
                        )
                    # z-direction
                    if not np.isclose(support[3], 0.0):
                        self.model.def_support_spring(
                            node.name,
                            'RZ',
                            support[3]*12/1000,
                        )

        # Add the distributed loads to the model
        for dist_load in self.dist_loads:
            self.model.add_member_dist_load(
                'M1',
                'Fy',
                dist_load[2]/12/1000,
                dist_load[3]/12/1000,
                dist_load[0]*12,
                dist_load[1]*12,
                dist_load[4],
            )

        # Add the point loads to the model
        for point_load in self.point_loads:
            self.model.add_member_pt_load(
                'M1',
                'Fy',
                point_load[1]/1000,
                point_load[0]*12,
                point_load[2],
            )

        # Add the ponding loads to the model
        # Start with ponding due to rain:
        for row in ponding_load['rain']:
            self.model.add_member_dist_load(
                'M1',
                'Fy',
                row[1]*self.tributary_width/12/1000,
                row[3]*self.tributary_width/12/1000,
                row[0]*12,
                row[2]*12,
                'PR',
            )

        # Next add ponding due to snow:
        for row in ponding_load['snow']:
            self.model.add_member_dist_load(
                'M1',
                'Fy',
                row[1]*self.tributary_width/12/1000,
                row[3]*self.tributary_width/12/1000,
                row[0]*12,
                row[2]*12,
                'PS',
            )

        # Define the load cases and combinations
        # Note: Ponding analysis must be performed with unfactored dead and
        # rain/snow loads, i.e. ASD load combinations
        for combo, factors in load_cases.items():
            self.model.add_load_combo(
                combo,
                {
                    'D': factors[0], 
                    'Lr': factors[1],
                    'R': factors[2],
                    'S': factors[3],
                    'PR': factors[4],
                    'PS': factors[5]
                },
            )
        for combo, factors in load_combinations['asd'].items():
            self.model.add_load_combo(
                combo,
                {
                    'D': factors[0], 
                    'Lr': factors[1],
                    'R': factors[2],
                    'S': factors[3],
                    'PR': factors[4],
                    'PS': factors[5]
                },
            )
        for combo, factors in load_combinations['lrfd'].items():
            self.model.add_load_combo(
                combo,
                {
                    'D': factors[0], 
                    'Lr': factors[1],
                    'R': factors[2],
                    'S': factors[3],
                    'PR': factors[4],
                    'PS': factors[5]
                },
            )

    def analyze_ponding(self):
        """
        Analyze the ponding of the beam.
        """
        self.ponded_depth_history = [self.ponded_depth_history[0]]
        self.deflection_history = [self.deflection_history[0]]

        iteration = 0
        ponded_area_stats = [{
            'rain': 0.0,
            'snow': 0.0,
        }]
        rel_err_stats = [{
            'rain': 0.0,
            'snow': 0.0,
        }]

        while True:
            iteration += 1
            self.create_model(
                ponding_load=self._calc_ponding_load(
                    ponded_depths=self.ponded_depth_history[-1]
                )
            )

            self.model.analyze()

            rain_defl = []
            snow_defl = []
            x_0 = 0
            for submember in self.model.members['M1'].sub_members.values():
                # Rain
                rain_x_sub, rain_defl_sub = submember.deflection_array(
                    Direction='dy',
                    n_points=len(self.stations[(self.stations*12 >= x_0) & (self.stations*12 <= x_0 + submember.L())]),
                    combo_name='1.0D+1.0R+1.0P',
                )
                rain_x_sub = [x_0 + x for x in rain_x_sub]
                rain_defl.extend(rain_defl_sub)
                # Snow
                snow_x_sub, snow_defl_sub = submember.deflection_array(
                    Direction='dy',
                    n_points=len(self.stations[(self.stations*12 >= x_0) & (self.stations*12 <= x_0 + submember.L())]),
                    combo_name='1.0D+1.0S+1.0P',
                )
                snow_x_sub = [x_0 + x for x in snow_x_sub]
                snow_defl.extend(snow_defl_sub)
                x_0 = submember.L()
            rain_defl = np.array(rain_defl)
            snow_defl = np.array(snow_defl)

            self.deflection_history.append({
                'rain': rain_defl,
                'snow': snow_defl,
            })
                
            self.ponded_depth_history.append({
                'rain': np.where(
                    self.station_elevations - self.deflection_history[-1]['rain'] <= sum(self.rain_depth),
                    sum(self.rain_depth) - (self.station_elevations - self.deflection_history[-1]['rain']),
                    0.0,
                ),
                'snow': np.where(
                    self.station_elevations - self.deflection_history[-1]['snow'] <= sum(self.rain_depth),
                    sum(self.rain_depth) - (self.station_elevations - self.deflection_history[-1]['snow']),
                    0.0,
                ),
            })

            ponded_area = {
                'rain': abs(simpson(
                    self.ponded_depth_history[-1]['rain'],
                    self.stations,
                )),
                'snow': abs(simpson(
                    self.ponded_depth_history[-1]['snow'],
                    self.stations,
                )),
            }
            ponded_area_stats.append(ponded_area)

            rel_err = {
                'rain': divide_by_zero(
                    abs(ponded_area['rain'] - ponded_area_stats[iteration-1]['rain']),
                    ponded_area_stats[-1]['rain'],
                ),
                'snow': divide_by_zero(
                    abs(ponded_area['snow'] - ponded_area_stats[iteration-1]['snow']),
                    ponded_area_stats[-1]['snow'],
                ),
            }
            rel_err_stats.append(rel_err)

            if iteration > 1:
                if rel_err['rain'] < 0.0001 and rel_err['snow'] < 0.0001:
                    self.valid_results = True

                    for node, _ in self.support_nodes.items():
                        self.reaction_envelope[node] = self.model.nodes[node].RxnFY

                    for case, _ in load_cases.items():
                        self.max_moment_envelope['cases'][case] = self.model.members['M1'].max_moment('Mz', case)
                        self.min_moment_envelope['cases'][case] = self.model.members['M1'].min_moment('Mz', case)

                        #self.max_shear_envelope['cases'][case] = -1*self.model.members['M1'].min_shear('Vy', case)
                        #self.min_moment_envelope['cases'][case] = -1*self.model.members['M1'].max_shear('Vy', case)

                        self.max_defl_envelope['cases'][case] = -1*self.model.members['M1'].min_deflection('dy', case)
                        self.min_defl_envelope['cases'][case] = -1*self.model.members['M1'].max_deflection('dy', case)

                    for combo, _ in load_combinations['asd'].items():
                        self.max_moment_envelope['asd'][combo] = self.model.members['M1'].max_moment('Mz', combo)
                        self.min_moment_envelope['asd'][combo] = self.model.members['M1'].min_moment('Mz', combo)

                        #self.max_shear_envelope['asd'][combo] = -1*self.model.members['M1'].min_shear('Vy', combo)
                        #self.min_moment_envelope['asd'][combo] = -1*self.model.members['M1'].max_shear('Vy', combo)

                        self.max_defl_envelope['asd'][combo] = -1*self.model.members['M1'].min_deflection('dy', combo)
                        self.min_defl_envelope['asd'][combo] = -1*self.model.members['M1'].max_deflection('dy', combo)

                    for combo, _ in load_combinations['lrfd'].items():
                        self.max_moment_envelope['lrfd'][combo] = self.model.members['M1'].max_moment('Mz', combo)
                        self.min_moment_envelope['lrfd'][combo] = self.model.members['M1'].min_moment('Mz', combo)

                        #self.max_shear_envelope['lrfd'][combo] = -1*self.model.members['M1'].min_shear('Vy', combo)
                        #self.min_moment_envelope['lrfd'][combo] = -1*self.model.members['M1'].max_shear('Vy', combo)

                        self.max_defl_envelope['lrfd'][combo] = -1*self.model.members['M1'].min_deflection('dy', combo)
                        self.min_defl_envelope['lrfd'][combo] = -1*self.model.members['M1'].max_deflection('dy', combo)
                    break
                elif iteration > 50:
                    raise RuntimeWarning("Convergence not reached after 50 iterations. Try a stiffer secction cross-section.")
                
        self.analysis_stats = {
            'iterations': iteration,
            'ponded_area': ponded_area_stats,
            'rel_err': rel_err_stats,
        }

    def reaction_envelope_at_node(self, node, combo_type='asd'):
        """
        Return the reaction envelope for a given node.

        Parameters
        ----------
        node : str
            The name of the node.
        combo_type : str
            The load combination type, either 'asd' or 'lrfd'.
        """
        if combo_type not in ['asd', 'lrfd']:
            raise ValueError("Invalid load combination type. Please enter 'asd' or 'lrfd'.")
        if node not in self.support_nodes.keys():
            raise ValueError("Invalid node. Please enter a valid support node name.")
        
        selected_combos = load_combinations[combo_type].keys()
        
        selected_reaction_envelope = {}

        for combo, value in self.reaction_envelope[node].items():
            if combo in selected_combos:
                selected_reaction_envelope[combo] = value
        
        return selected_reaction_envelope

    def plot_ponded_depth_history(self, iteration, load_type):
        """
        Plot the ponded depth history.

        Parameters
        ----------
        iteration : int
            The iteration number for which the ponded depth shall be plotted.
        load_type : str
            The load type for which the ponded depth shall be plotted, either
            rain or snow.
        """
        if iteration < 1 or iteration >= len(self.ponded_depth_history):
            raise ValueError(f"Invalid iteration number. Please enter a number between 1 and {len(self.ponded_depth_history)-1}.")
        if load_type not in ['rain', 'snow']:
            raise ValueError("Invalid load type. Please enter 'rain' or 'snow'.")
        
        plt.figure(figsize=(8, 4))

        deflection = self.deflection_history[iteration][load_type]
        if load_type == 'rain':
            datum = sum(self.rain_depth)
            title = f'Ponded Depth at Iteration {iteration} for 1.0D+1.0R+1.0P'
        else:
            datum = sum(self.rain_depth)
            title = f'Ponded Depth at Iteration {iteration} for 1.0D+1.0S+1.0P'

        plt.fill_between(
            self.stations,
            self.station_elevations - deflection,
            np.where(
                self.station_elevations - deflection <= datum,
                datum,
                self.station_elevations - deflection,
            ),
            color='#ACFFFC',
            alpha=0.5,
        )

        plt.plot(
            self.stations,
            self.station_elevations,
            color='black',
            label = 'Original Beam Shape'
        )

        plt.plot(
            self.stations,
            self.station_elevations - deflection,
            color='black',
            linestyle='--',
            label='Deflected Beam Shape',
        )

        plt.plot(self.stations,
            datum*np.ones(len(self.stations)),
            color='blue',
            linestyle='-.',
            label='Datum',
        )

        plt.plot(
            np.array([0, 0]),
            np.array([-12, 12]),
            color='#B9B7AE',
            lw=4,
            label='_Parapet'
        )

        plt.xlim(0, self.length)
        plt.xticks(np.arange(0, self.length+1, 1))
        plt.ylim(
            math.floor(min(self.station_elevations - deflection)-1),
            math.ceil(max(self.station_elevations)+6),
        )
        plt.yticks(np.arange(
            math.floor(min(self.station_elevations - deflection)-1),
            math.ceil(max(self.station_elevations)+6),
            1)
        )

        plt.xlabel("Location (ft)")
        plt.ylabel("Ponded Depth (in)")
        plt.legend(loc='upper right')
        plt.title(title)

        plt.grid(True)
        plt.show()

    def plot_moment_envelope(self, combo_type='asd'):
        """
        Plot the moment envelope at the converged analysis.

        Parameters
        ----------
        combo_type : str
            The load combination type for which the moment envelope should be
            plotted, either 'asd' or 'lrfd.'
        """
        if combo_type not in ['asd', 'lrfd']:
            raise ValueError("Invalid load combination type. Please enter 'asd' or 'lrfd'.")
        
        plt.figure(figsize=(10,6))        
        # Collect and store the moment array for each load case
        factored_moment_arrays = {}
        min_factored_moment = ['None', 0]
        max_factored_moment = ['None', 0]
        for combo, _ in load_combinations[combo_type].items():
            x, M = [], []
            # Iterate through each submember
            x_0 = 0
            for submember in self.model.members['M1'].sub_members.values():
                x_submember, M_submember = submember.moment_array(
                    Direction='Mz',
                    n_points=len(self.stations),
                    combo_name=combo,
                )
                x_submember = [x_0 + x for x in x_submember]
                x.extend(x_submember)
                M.extend(M_submember)
                x_0 += submember.L()
            x, factored_moment_arrays[combo] = np.array(x), np.array(M)
            if np.amax(factored_moment_arrays[combo]) > max_factored_moment[1]:
                max_factored_moment = [combo, np.amax(factored_moment_arrays[combo])]
            if np.amin(factored_moment_arrays[combo]) < min_factored_moment[1]:
                min_factored_moment = [combo, np.amin(factored_moment_arrays[combo])]

            plt.plot(
                x/12,
                factored_moment_arrays[combo]/12,
                label=combo,
            )
        
        plt.plot(
            [0.0, self.length],
            [0.0, 0.0],
            color='black',
            linestyle='-.',
            label='_Datum'
        )

        plt.xlim(0, self.length)
        plt.xticks(np.arange(0, self.length+1, 1))
        plt.ylim(
            -5*math.ceil(max_factored_moment[1]/12/5),
            5*math.ceil(max_factored_moment[1]/12/5),
        )
        plt.yticks(np.linspace(
            -5*math.ceil(max_factored_moment[1]/12/5),
            5*math.ceil(max_factored_moment[1]/12/5),
            11,
            endpoint=True)
        )

        plt.xlabel('Location (ft)')
        plt.ylabel('Moment (k-ft)')
        plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.tight_layout()
        plt.title('Moment Envelope')
        plt.grid(True)

        plt.show()
        
    def plot_shear_envelope(self, combo_type='asd'):
        """
        Plot the shear envelope at the converged analysis.

        Parameters
        ----------
        combo_type : str
            The load combination type for which the shear envelope should be
            plotted, either 'asd' or 'lrfd.'
        """
        if combo_type not in ['asd', 'lrfd']:
            raise ValueError("Invalid load combination type. Please enter 'asd' or 'lrfd'.")
        
        plt.figure(figsize=(10,6))        
        # Collect and store the moment array for each load case
        factored_shear_arrays = {}
        min_factored_shear = ['None', 0]
        max_factored_shear = ['None', 0]
        for combo, _ in load_combinations[combo_type].items():
            x, S = [], []
            # Iterate through each submember
            x_0 = 0
            for submember in self.model.members['M1'].sub_members.values():
                x_submember, S_submember = submember.shear_array(
                    Direction='Fy',
                    n_points=len(self.stations),
                    combo_name=combo,
                )
                x_submember = [x_0 + x for x in x_submember]
                x.extend(x_submember)
                S.extend(S_submember)
                x_0 += submember.L()
            x, factored_shear_arrays[combo] = np.array(x), -1*np.array(S)
            if np.amax(factored_shear_arrays[combo]) > max_factored_shear[1]:
                max_factored_shear = [combo, np.amax(factored_shear_arrays[combo])]
            if np.amin(factored_shear_arrays[combo]) < min_factored_shear[1]:
                min_factored_shear = [combo, np.amin(factored_shear_arrays[combo])]

            plt.plot(
                x/12,
                factored_shear_arrays[combo],
                label=combo,
            )
        
        plt.plot(
            [0.0, self.length],
            [0.0, 0.0],
            color='black',
            linestyle='-.',
            label='_Datum'
        )

        plt.xlim(0, self.length)
        plt.xticks(np.arange(0, self.length+1, 1))
        plt.ylim(
            5*math.floor(min_factored_shear[1]/5),
            5*math.ceil(max_factored_shear[1]/5),
        )
        plt.yticks(np.linspace(
            5*math.floor(min_factored_shear[1]/5),
            5*math.ceil(max_factored_shear[1]/5),
            11,
            endpoint=True)
        )

        plt.xlabel('Location (ft)')
        plt.ylabel('Shear (k)')
        plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.tight_layout()
        plt.title('Shear Envelope')
        plt.grid(True)

        plt.show()

    def _calc_initial_rain_depth(self):
        """
        Calculate the rain depth at each segment of the beam.
        """
        self.ponded_depth_history[0] = np.where(
            self.station_elevations <= sum(self.rain_depth),
            sum(self.rain_depth) - self.station_elevations,
            0.0
        )

    def _calc_ponding_load(self, ponded_depths):
        """
        Calculate the ponding load at each segment of the beam.

        Parameters
        ----------
        ponded_depths : numpy.ndarray
            The ponded depth at each segment of the beam, due to rain and snow
            load.
        """
        ponding_load = {
            'rain': np.column_stack((
                self.stations[:-1],
                5.2*ponded_depths['rain'][:-1],
                self.stations[1:],
                5.2*ponded_depths['rain'][1:],
            )),
            'snow': np.column_stack((
                self.stations[:-1],
                5.2*ponded_depths['snow'][:-1],
                self.stations[1:],
                5.2*ponded_depths['snow'][1:],
            )),
        }

        return ponding_load

    def _segment_beam(self):
        """
        Segment the beam into 100 equal segments.
        """
        self.stations = np.linspace(0, self.length, 101, endpoint=True)
        self.segments = np.column_stack((self.stations[:-1], self.stations[1:]))
        