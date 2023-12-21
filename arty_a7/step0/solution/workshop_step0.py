#!/usr/bin/env python

from migen import *
from migen import run_simulation
# from platform_arty_a7 import *

from litex.build.generic_platform import *
from litex_boards.platforms.muselab_icesugar_pro import *

# Blinker -------------------------------------------------------------------------------------------


class Blink(Module):
    def __init__(self, bit):
        # This signal, declared as a attribute of the class
        # can be accessed from outside the module.
        self.out_r = Signal()
        self.out_g = Signal()
        self.out_b = Signal()

        # Internal signal
        counter = Signal(25)

        # This is the actual counter. It is incremented each clock cycle.
        # Because it's not just only wires, it needs some memory (registers)
        # it has to be in a synchronous block.
        self.sync += counter.eq(counter + 1)

        # Combinatorial assignments can be seen as wires.
        # Here we connect a bit of the counter to the self.out signal
        self.comb += self.out_r.eq(counter[bit])
        self.comb += self.out_g.eq(counter[bit-2])
        self.comb += self.out_b.eq(counter[bit-4])
        
class Tuto(Module):
    def __init__(self, platform):

        # Get pin from ressources
        clk = platform.request("clk25")
        led_r = platform.request("user_led", 0)
        led_g = platform.request("user_led", 1)
        led_b = platform.request("user_led", 2)

        # Creates a "sys" clock domain and generates a startup reset
        crg = CRG(clk)
        self.submodules.crg = crg

        # Instance of Blink
        blink = Blink(24)
        self.submodules += blink
        self.comb += led_r.eq(blink.out_r)
        self.comb += led_g.eq(blink.out_g)
        self.comb += led_b.eq(blink.out_b)

        # Add a timing constraint
        platform.add_period_constraint(clk, 1e9/25e6)

# Test -------------------------------------------------------------------------------------------

def test():
    loop = 0
    while (loop < 1000000000000):
        yield
        loop = loop + 1

# Build -------------------------------------------------------------------------------------------

def main():

    build_dir="gateware"

    # Instance of our platform (which is in platform_arty_a7.py)
    platform = Platform(toolchain="trellis")
    design = Tuto(platform)
    
    platform.build(design, build_dir=build_dir)

    if "load" in sys.argv[1: ]:
        prog = platform.create_programmer()
        prog.load_bitstream(build_dir + "/top.bit")
        exit()

    if "sim" in sys.argv[1: ]:
        ring = Blink(4)
        run_simulation(ring, test(), clocks={"sys": 1e9/25e6}, vcd_name="sim.vcd")
        exit()

    

if __name__ == "__main__":
    main()
