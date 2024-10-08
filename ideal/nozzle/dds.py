from opengate.geometry.utility import  get_grid_repetition
import opengate as gate

red = [1, 0, 0, 1]
blue = [0, 0, 1, 1]
green = [0, 1, 0, 1]
yellow = [0.9, 0.9, 0.3, 1]
gray = [0.5, 0.5, 0.5, 1]
white = [1, 1, 1, 0.8]
transparent = [1, 1, 1, 0]

def add_dds(sim, name = "DDS", mother_name = "NozzleBox", sad = 0):
    
    mm = gate.g4_units.mm
    um = gate.g4_units.um
    
    ddsx, ddsy, ddsz = [212 * mm, 212 * mm, 120 * mm]
    dds = sim.add_volume("Box",name)
    dds.mother = mother_name
    dds.size = [ddsx, ddsy, ddsz]
    dds.translation = [0 * mm, 0 * mm, sad * mm]
    dds.material = "NitrogenGas"
    dds.color = red
    
    #---window2 position 1
    dds_w2_1 = sim.add_volume("Box",f"{name} Win2 Pos1")
    dds_w2_1.mother = name
    dds_w2_1.size = [ddsx, ddsy, 25 * um]
    dds_w2_1.translation = [0 * mm, 0 * mm, -50 * mm]
    dds_w2_1.material = "Mylar"
    dds_w2_1.color = green
    
    dds_w2cover_1 = sim.add_volume("Box",f"{name} Win2cover Pos1")
    dds_w2cover_1.mother = name
    dds_w2cover_1.size = [ddsx, ddsy, 0.5 * um]
    dds_w2cover_1.translation = [0 * mm, 0 * mm, -49987.25 * um]
    dds_w2cover_1.material = "Aluminium"
    dds_w2cover_1.color = blue
    
    #---window1 position 3
    dds_w1_3 = sim.add_volume("Box",f"{name} Win1 Pos3")
    dds_w1_3.mother = name
    dds_w1_3.size = [ddsx, ddsy, 12 * um]
    dds_w1_3.translation = [0 * mm, 0 * mm, -15 * mm]
    dds_w1_3.material = "Mylar"
    dds_w1_3.color = green
    
    dds_w1cover_1 = sim.add_volume("Box",f"{name} Win1cover Pos1")
    dds_w1cover_1.mother = name
    dds_w1cover_1.size = [ddsx, ddsy, 0.3 * um]
    dds_w1cover_1.translation = [0 * mm, 0 * mm, -14993.85 * um]
    dds_w1cover_1.material = "Aluminium"
    dds_w1cover_1.color = blue
    
    #--cathode1 position 5
    dds_c1_5 = sim.add_volume("Box",f"{name} Cathode1 Pos5")
    dds_c1_5.mother = name
    dds_c1_5.size = [ddsx, ddsy, 12 * um]
    dds_c1_5.translation = [0 * mm, 0 * mm, -10 * mm]
    dds_c1_5.material = "Mylar"
    dds_c1_5.color = green
    
    dds_c1cover_1 = sim.add_volume("Box",f"{name} Cathode1cover Pos1")
    dds_c1cover_1.mother = name
    dds_c1cover_1.size = [ddsx, ddsy, 0.3 * um]
    dds_c1cover_1.translation = [0 * mm, 0 * mm, -9993.85 * um]
    dds_c1cover_1.material = "Aluminium"
    dds_c1cover_1.color = blue
    
    #--anode position 7
    dds_a_7 = sim.add_volume("Box",f"{name} Anode Pos7")
    dds_a_7.mother = name
    dds_a_7.size = [ddsx, ddsy, 25 * um]
    dds_a_7.translation = [0 * mm, 0 * mm, -5 * mm]
    dds_a_7.material = "Kapton"
    dds_a_7.color = white
    
    dds_acover_1 = sim.add_volume("Box",f"{name} Anodecover Pos1")
    dds_acover_1.mother = name
    dds_acover_1.size = [ddsx, ddsy, 25 * um]
    dds_acover_1.translation = [0 * mm, 0 * mm, -5025 * um]
    dds_acover_1.material = "Aluminium"
    dds_acover_1.color = blue
    
    #--anode position 9
    dds_a_9 = sim.add_volume("Box",f"{name} Anode Pos9")
    dds_a_9.mother = name
    dds_a_9.size = [ddsx, ddsy, 25 * um]
    dds_a_9.translation = [0 * mm, 0 * mm, 5 * mm]
    dds_a_9.material = "Kapton"
    dds_a_9.color = white
    
    dds_acover_2 = sim.add_volume("Box",f"{name} Anodecover Pos2")
    dds_acover_2.mother = name
    dds_acover_2.size = [ddsx, ddsy, 25 * um]
    dds_acover_2.translation = [0 * mm, 0 * mm, 5025 * um]
    dds_acover_2.material = "Aluminium"
    dds_acover_2.color = blue
    
    
    #--cathode2 position 11
    dds_c2_11 = sim.add_volume("Box",f"{name} Cathode2 Pos11")
    dds_c2_11.mother = name
    dds_c2_11.size = [ddsx, ddsy, 25 * um]
    dds_c2_11.translation = [0 * mm, 0 * mm, 10 * mm]
    dds_c2_11.material = "Mylar"
    dds_c2_11.color = green
    
    stripe_width = 1.60 * mm
    
    dds_c2_1 = sim.add_volume("Box",f"{name} Cathode2 Strips1 Box")
    dds_c2_1.mother = name
    dds_c2_1.size = [ddsx, ddsy, 0.5 * um]
    dds_c2_1.translation = [0 * mm, 0 * mm, 9987.25 * um]
    dds_c2_1.material = "NitrogenGas"
    dds_c2_1.color = transparent
    
    dds_c2_1_stripe = sim.add_volume("Box",f"{name} Cathode2 Strips1")
    dds_c2_1_stripe.mother = dds_c2_1.name
    dds_c2_1_stripe.size = [ddsx, stripe_width, 0.5 * um]
    # dds_c2_1_stripe.translation = None
    # dds_c2_1_stripe.rotation = None
    dds_c2_1_stripe.material = "Aluminium"
    dds_c2_1_stripe.color = blue
    translations = get_grid_repetition([1, 128, 1], [0, 1.65 * mm, 0])
    dds_c2_1_stripe.translation = translations
    
    dds_c2_2 = sim.add_volume("Box",f"{name} Cathode2 Strips2 Box")
    dds_c2_2.mother = name
    dds_c2_2.size = [ddsx, ddsy, 0.5 * um]
    dds_c2_2.translation = [0 * mm, 0 * mm, 10012.75 * um]
    dds_c2_2.material = "NitrogenGas"
    dds_c2_2.color = transparent
    
    dds_c2_2_stripe = sim.add_volume("Box",f"{name} Cathode2 Strips2")
    dds_c2_2_stripe.mother = dds_c2_2.name
    dds_c2_2_stripe.size = [stripe_width, ddsy, 0.5 * um]
    # dds_c2_2_stripe.translation = None
    # dds_c2_2_stripe.rotation = None
    dds_c2_2_stripe.material = "Aluminium"
    dds_c2_2_stripe.color = blue
    translations = get_grid_repetition([128, 1, 1], [1.65 * mm, 0, 0])
    dds_c2_2_stripe.translation = translations
    
    #--anode position 13
    dds_a_13 = sim.add_volume("Box",f"{name} Anode Pos13")
    dds_a_13.mother = name
    dds_a_13.size = [ddsx, ddsy, 25 * um]
    dds_a_13.translation = [0 * mm, 0 * mm, 15 * mm]
    dds_a_13.material = "Kapton"
    dds_a_13.color = white
    
    dds_acover_3 = sim.add_volume("Box",f"{name} Anodecover Pos3")
    dds_acover_3.mother = name
    dds_acover_3.size = [ddsx, ddsy, 25 * um]
    dds_acover_3.translation = [0 * mm, 0 * mm, 14975 * um]
    dds_acover_3.material = "Aluminium"
    dds_acover_3.color = blue
    
    #---window1 position 15
    dds_w1_15 = sim.add_volume("Box",f"{name} Win1 Pos15")
    dds_w1_15.mother = name
    dds_w1_15.size = [ddsx, ddsy, 12 * um]
    dds_w1_15.translation = [0 * mm, 0 * mm, 20 * mm]
    dds_w1_15.material = "Mylar"
    dds_w1_15.color = green
    
    dds_w1cover_2 = sim.add_volume("Box",f"{name} Win1cover Pos2")
    dds_w1cover_2.mother = name
    dds_w1cover_2.size = [ddsx, ddsy, 0.3 * um]
    dds_w1cover_2.translation = [0 * mm, 0 * mm, 19993.85 * um]
    dds_w1cover_2.material = "Aluminium"
    dds_w1cover_2.color = blue
    
    #---window2 position 17
    dds_w2_17 = sim.add_volume("Box",f"{name} Win2 Pos17")
    dds_w2_17.mother = name
    dds_w2_17.size = [ddsx, ddsy, 25 * um]
    dds_w2_17.translation = [0 * mm, 0 * mm, 50 * mm]
    dds_w2_17.material = "Mylar"
    dds_w2_17.color = green
    
    dds_w2cover_2 = sim.add_volume("Box",f"{name} Win2cover Pos2")
    dds_w2cover_2.mother = name
    dds_w2cover_2.size = [ddsx, ddsy, 0.5 * um]
    dds_w2cover_2.translation = [0 * mm, 0 * mm, 49987.25 * um]
    dds_w2cover_2.material = "Aluminium"
    dds_w2cover_2.color = blue
    
    return dds
