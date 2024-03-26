import math
import opengate as gate
#mm = gate.g4_units("mm")


def add_wedge(sim, name = "wedge",wedge_x = 200 , wedge_narrowerx = 40, wedge_y = 45.1, wedge_z = 100):

    deg = gate.g4_units.deg
    wedge = sim.add_volume("Trap",name)
    wedge.dz = 0.5 * wedge_z
    wedge.dy1 = 0.5 * wedge_y
    wedge.dy2 = wedge.dy1
    wedge.dx1 = wedge.dx3 = 0.5 * wedge_x
    wedge.dx2 = wedge.dx4 = 0.5 * wedge_narrowerx
    talp = 0.5 * (wedge_narrowerx - wedge_x)/wedge_y
    wedge.alp1 = wedge.alp2 = math.degrees(math.atan(talp)) * deg
    wedge.theta = wedge.phi = 0
    
    return wedge