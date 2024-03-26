from .dds import add_dds
from .vac_window import add_vac_window
from .rifi import add_rifi
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

def add_nozzle(sim, gantry_angle = None, flag_RiFi_1 = True, flag_RiFi_2 = True, flag_RaShi = True):  
    mm = gate.g4_units.mm
    um = gate.g4_units.um
    
    ##== nozzle ==##
    nozzlebox = sim.add_volume("Box","NozzleBox")
    nozzlebox.size = [500 * mm, 500 * mm, 1000 * mm]
    #nozzlebox.translation = [0 *mm, 0 * mm, 1148 * mm] #[1148 *mm, 0 * mm, 0 * mm]
    nozzlebox.rotation = (Rotation.from_euler('z',gantry_angle,degrees=True)*Rotation.from_euler('x',-90,degrees=True)).as_matrix()
    if gantry_angle == 0:
        nozzlebox.translation = [0 *mm, -1148 * mm, 0 * mm] #[1148 *mm, 0 * mm, 0 * mm]
    elif gantry_angle == 90:
        nozzlebox.translation = [1148 *mm, 0 * mm, 0 * mm]
    nozzlebox.material = "Vacuum"
    nozzlebox.color = blue
    
    ## nozzle permanent elements
    #VacPipe
    vacpipe = sim.add_volume("Tubs","VacPipe")
    vacpipe.mother = "NozzleBox"
    vacpipe.rmin = 0 * mm
    vacpipe.rmax = 225 * mm
    vacpipe.dz = 150 * mm #300/2, half of IDEAL
    vacpipe.translation = [0 * mm, 0 * mm, -286.425 * mm]
    vacpipe.material = "Vacuum"
    vacpipe.color = yellow
    
    vac_window1 = add_vac_window(sim, name = "BeamPipeVacWindow1", mother_name = "NozzleBox", vac_window_sad = -121.675)
    vac_window2 = add_vac_window(sim, name = "BeamPipeVacWindow2", mother_name = "NozzleBox", vac_window_sad = -136.175)
    
    #ITS
    itsx, itsy, itsz = [211 * mm, 211 * mm, 90.025 * mm]
    its = sim.add_volume("Box","ITS")
    its.mother = "NozzleBox"
    its.size = [itsx, itsy, itsz]
    its.translation = [0 * mm, 0 * mm, -38.4125 * mm]
    its.material = "G4_AIR"
    its.color = red
    
    #---window2 position 1
    its_w2_1 = sim.add_volume("Box","ITS Win2 Pos1")
    its_w2_1.mother = "ITS"
    its_w2_1.size = [itsx, itsy, 25 * um]
    its_w2_1.translation = [0 * mm, 0 * mm, -45 * mm]
    its_w2_1.material = "Mylar"
    its_w2_1.color = green
    
    its_w2cover_1 = sim.add_volume("Box","ITS Win2cover Pos1")
    its_w2cover_1.mother = "ITS"
    its_w2cover_1.size = [itsx, itsy, 0.5 * um]
    its_w2cover_1.translation = [0 * mm, 0 * mm, -44987.25 * um]
    its_w2cover_1.material = "Aluminium"
    its_w2cover_1.color = blue
    
    #---window1 position 3
    its_w1_3 = sim.add_volume("Box","ITS Win1 Pos3")
    its_w1_3.mother = "ITS"
    its_w1_3.size = [itsx, itsy, 12 * um]
    its_w1_3.translation = [0 * mm, 0 * mm, -10 * mm]
    its_w1_3.material = "Mylar"
    its_w1_3.color = green
    
    its_w1cover_1 = sim.add_volume("Box","ITS Win1cover Pos1")
    its_w1cover_1.mother = "ITS"
    its_w1cover_1.size = [itsx, itsy, 0.3 * um]
    its_w1cover_1.translation = [0 * mm, 0 * mm, -9993.85 * um]
    its_w1cover_1.material = "Aluminium"
    its_w1cover_1.color = blue
    
    #--cathode1 position 5
    its_c1_5 = sim.add_volume("Box","ITS Cathode1 Pos5")
    its_c1_5.mother = "ITS"
    its_c1_5.size = [itsx, itsy, 12 * um]
    its_c1_5.translation = [0 * mm, 0 * mm, 0 * mm]
    its_c1_5.material = "Mylar"
    its_c1_5.color = green
    
    its_c1cover_1 = sim.add_volume("Box","ITS Cathode1cover Pos1")
    its_c1cover_1.mother = "ITS"
    its_c1cover_1.size = [itsx, itsy, 0.3 * um]
    its_c1cover_1.translation = [0 * mm, 0 * mm, 6.15 * um]
    its_c1cover_1.material = "Aluminium"
    its_c1cover_1.color = blue
    
    #--anode position 7
    its_a_7 = sim.add_volume("Box","ITS Anode Pos7")
    its_a_7.mother = "ITS"
    its_a_7.size = [itsx, itsy, 25 * um]
    its_a_7.translation = [0 * mm, 0 * mm, 5 * mm]
    its_a_7.material = "Kapton"
    its_a_7.color = white
    
    its_acover_1 = sim.add_volume("Box","ITS Anodecover Pos1")
    its_acover_1.mother = "ITS"
    its_acover_1.size = [itsx, itsy, 25 * um]
    its_acover_1.translation = [0 * mm, 0 * mm, 4975 * um]
    its_acover_1.material = "Aluminium"
    its_acover_1.color = blue
    
    #---window1 position 15
    its_w1_15 = sim.add_volume("Box","ITS Win1 Pos15")
    its_w1_15.mother = "ITS"
    its_w1_15.size = [itsx, itsy, 12 * um]
    its_w1_15.translation = [0 * mm, 0 * mm, 15 * mm]
    its_w1_15.material = "Mylar"
    its_w1_15.color = green
    
    its_w1cover_2 = sim.add_volume("Box","ITS Win1cover Pos2")
    its_w1cover_2.mother = "ITS"
    its_w1cover_2.size = [itsx, itsy, 0.3 * um]
    its_w1cover_2.translation = [0 * mm, 0 * mm, 14993.85 * um]
    its_w1cover_2.material = "Aluminium"
    its_w1cover_2.color = blue
    
    #---window2 position 17
    its_w2_17 = sim.add_volume("Box","ITS Win2 Pos17")
    its_w2_17.mother = "ITS"
    its_w2_17.size = [itsx, itsy, 25 * um]
    its_w2_17.translation = [0 * mm, 0 * mm, 45 * mm]
    its_w2_17.material = "Mylar"
    its_w2_17.color = green
    
    its_w2cover_2 = sim.add_volume("Box","ITS Win2cover Pos2")
    its_w2cover_2.mother = "ITS"
    its_w2cover_2.size = [itsx, itsy, 0.5 * um]
    its_w2cover_2.translation = [0 * mm, 0 * mm, 44987.25 * um]
    its_w2cover_2.material = "Aluminium"
    its_w2cover_2.color = blue
    
    dds1 = add_dds(sim, name = "DDS1", mother_name = "NozzleBox", dds_sad = 236.6 )    
    dds2 = add_dds(sim, name = "DDS2", mother_name = "NozzleBox", dds_sad = 114.6)
    
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