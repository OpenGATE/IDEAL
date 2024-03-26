from dds import add_dds
from vac_window import add_vac_window
from rifi import add_rifi
from scipy.spatial.transform import Rotation
import opengate as gate

red = [1, 0, 0, 1]
blue = [0, 0, 1, 1]
green = [0, 1, 0, 1]
yellow = [0.9, 0.9, 0.3, 1]
gray = [0.5, 0.5, 0.5, 1]
white = [1, 1, 1, 0.8]
transparent = [1, 1, 1, 0]
grey = [0.46, 0.53, 0.6, 1]

def add_nozzle(sim, nozzle_rot = None, flag_RiFi_1 = True, flag_RiFi_2 = True, flag_RaShi = True):
    
    mm = gate.g4_units.mm
    um = gate.g4_units.um
    
    ##== nozzle ==##
    nozzlebox = sim.add_volume("Box","NozzleBox")
    nozzlebox.size = [500 * mm, 500 * mm, 1000 * mm]
    #nozzlebox.translation = [0 *mm, 0 * mm, 1148 * mm] #[1148 *mm, 0 * mm, 0 * mm]
    nozzlebox.rotation = (Rotation.from_euler('z',nozzle_rot,degrees=True)*Rotation.from_euler('x',-90,degrees=True)).as_matrix()
    if nozzle_rot == 0:
        nozzlebox.translation = [0 *mm, -1148 * mm, 0 * mm] #[1148 *mm, 0 * mm, 0 * mm]
    elif nozzle_rot == 90:
        nozzlebox.translation = [1148 *mm, 0 * mm, 0 * mm]
    nozzlebox.material = "Vacuum"
    nozzlebox.color = blue
    
    #exit window
    exitwindow = sim.add_volume("Box","ExitWindow")
    exitwindow.mother = "NozzleBox"
    exitwindow.size = [240 * mm, 240 * mm, 25 * um]
    exitwindow.translation = [0 * mm, 0 * mm, 473.275 * mm]
    exitwindow.material = "Kapton"
    exitwindow.color = white
    
    ## nozzle passive elements
    #ripple filter
    if flag_RiFi_1 :
        rifi1 = add_rifi(sim, name = "RiFi1", mother_name = "NozzleBox", rifi_rot = Rotation.from_euler("z", 0, degrees=True).as_matrix(), rifi_sad = 361.6)
    if flag_RiFi_2 :    
        rifi2 = add_rifi(sim, name = "RiFi2", mother_name = "NozzleBox", rifi_rot = Rotation.from_euler("z", 90, degrees=True).as_matrix(), rifi_sad = 344.0)
    
    #range shifter
    if flag_RaShi :
        rangeshifter = sim.add_volume("Box","RangeShifter")
        rangeshifter.mother = "NozzleBox"
        rangeshifter.size = [270 * mm, 270 * mm, 30 * mm]
        rangeshifter.translation = [0 * mm, 0 * mm, 416.8 * mm]
        rangeshifter.material = "PMMA"
        rangeshifter.color = grey
    
    return nozzlebox