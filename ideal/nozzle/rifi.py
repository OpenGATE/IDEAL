from scipy.spatial.transform import Rotation
from .wedge import add_wedge
import opengate as gate
from opengate.geometry import utility

red = [1, 0, 0, 1]
blue = [0, 0, 1, 1]
green = [0, 1, 0, 1]
yellow = [0.9, 0.9, 0.3, 1]
gray = [0.5, 0.5, 0.5, 1]
white = [1, 1, 1, 0.8]
transparent = [1, 1, 1, 0]

def add_rifi(sim, name = "RiFi", mother_name = "NozzleBox", rifi_rot = None, rifi_sad = 361.6):
    
    mm = gate.g4_units.mm
    pmma_mat = "PMMArifi"
    
    rifix, rifiy, rifiz = [220 * mm, 220 * mm, 2.3 * mm]
    rifi = sim.add_volume("Box",name)
    rifi.mother = mother_name
    rifi.size = [rifiz, rifiy, rifix]
    rifi.translation = [0 * mm, 0 * mm, rifi_sad * mm]
    rot_rifi = Rotation.from_matrix(rifi_rot)
    rot_align = Rotation.from_euler("y", 90, degrees=True)
    rifi.rotation = (rot_rifi * rot_align).as_matrix()
    rifi.material = "G4_AIR"
    rifi.color = transparent
    
    rifi_element = sim.add_volume("Box",f"{name} Element")
    rifi_element.mother = name
    rifi_element.size = [rifiz, 1.0 * mm, rifix]
    rifi_element.translation = None
    rifi_element.rotation = None
    rifi_element.material = "G4_AIR"
    rifi_element.color = transparent
    
    rifi_wedge1 = add_wedge(sim, name = f"{name} Wedge1",wedge_x = 2.0 * mm, wedge_narrowerx = 0.4 * mm, wedge_y = 0.451 * mm, wedge_z = rifix)
    rifi_wedge1.mother = rifi_element.name
    rifi_wedge1.translation = [-0.4 * mm, 0.2655 * mm, 0 * mm]
    rifi_wedge1.material = pmma_mat
    rifi_wedge1.color = yellow
    
    rifi_wedge2 = add_wedge(sim, name = f"{name} Wedge2",wedge_x = 2.0 * mm, wedge_narrowerx = 0.4 * mm, wedge_y = 0.451 * mm, wedge_z = rifix)
    rifi_wedge2.mother = rifi_element.name
    rifi_wedge2.translation = [-0.4 * mm, -0.2655 * mm, 0 * mm]
    rifi_wedge2.rotation = Rotation.from_euler("x", 180, degrees=True).as_matrix()
    rifi_wedge2.material = pmma_mat
    rifi_wedge2.color = yellow
    
    rifi_flattop = sim.add_volume("Box", f"{name} Flattop")
    rifi_flattop.mother = rifi_element.name
    rifi_flattop.size = [2.0 * mm, 0.08 * mm, rifix]
    rifi_flattop.translation = [0 * mm, 0 * mm, 0 * mm]
    rifi_flattop.material = pmma_mat
    rifi_flattop.color = yellow
    
    rifi_flatbottom1 = sim.add_volume("Box", f"{name} Flatbottom1")
    rifi_flatbottom1.mother = rifi_element.name
    rifi_flatbottom1.size = [0.4 * mm, 0.009 * mm, rifix]
    rifi_flatbottom1.translation = [-0.8 * mm, 0.4955 * mm, 0 * mm]
    rifi_flatbottom1.material = pmma_mat
    rifi_flatbottom1.color = yellow
    
    rifi_flatbottom2 = sim.add_volume("Box", f"{name} Flatbottom2")
    rifi_flatbottom2.mother = rifi_element.name
    rifi_flatbottom2.size = [0.4 * mm, 0.009 * mm, rifix]
    rifi_flatbottom2.translation = [-0.8 * mm, -0.4955 * mm, 0 * mm]
    rifi_flatbottom2.material = pmma_mat
    rifi_flatbottom2.color = yellow
    
    translations = utility.get_grid_repetition([1, 220, 1], [0, 1.0 * mm, 0])
    rifi_element.translation = translations
