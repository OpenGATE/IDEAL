import opengate as gate

red = [1, 0, 0, 1]
blue = [0, 0, 1, 1]
green = [0, 1, 0, 1]
yellow = [0.9, 0.9, 0.3, 1]
gray = [0.5, 0.5, 0.5, 1]
white = [1, 1, 1, 0.8]
transparent = [1, 1, 1, 0]

def add_vac_window(sim, name = "BeamPipeVacWindow", mother_name = "NozzleBox", vac_window_sad = 0):
    mm = gate.g4_units.mm
    um = gate.g4_units.um
    nm = gate.g4_units.nm
    
    holder = sim.add_volume("Tubs",f"{name} holder")
    holder.mother = mother_name
    holder.rmin = 0 * mm
    holder.rmax = 225 * mm
    holder.dz = 0.25 * mm #0.5/2
    holder.translation = [0 * mm, 0 * mm, vac_window_sad * mm]
    holder.material = "G4_AIR"
    holder.color = transparent
    
    window = sim.add_volume("Tubs",name)
    window.mother = holder.name
    window.rmin = 0 * mm
    window.rmax = 225 * mm
    window.dz = 95 * um #190/2
    window.translation = [0 * mm, 0 * mm, 0 * mm]
    window.material = "Mylar"
    window.color = green
    
    coat1 = sim.add_volume("Tubs",f"{name} coat1")
    coat1.mother = holder.name
    coat1.rmin = 0 * mm
    coat1.rmax = 225 * mm
    coat1.dz = 2.5 * nm #5/2
    coat1.translation = [0 * mm, 0 * mm, 95002.5 * nm]
    coat1.material = "TiO"
    coat1.color = white
    
    coat2 = sim.add_volume("Tubs",f"{name} coat2")
    coat2.mother = holder.name
    coat2.rmin = 0 * mm
    coat2.rmax = 225 * mm
    coat2.dz = 2.5 * um #5/2
    coat2.translation = [0 * mm, 0 * mm, -97.5 * um]
    coat2.material = "Aluminium"
    coat2.color = blue
    
    
    return holder