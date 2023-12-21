#!/usr/bin/env python

import sys

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex_boards.platforms.muselab_icesugar_pro import *

# CRG ----------------------------------------------------------------------------------------------

class CRG(Module):
    def __init__(self, platform):
        self.rst_n = Signal()
        self.clock_domains.cd_sys   = ClockDomain()

        # # #

        clk = platform.request("clk25")
        rst_n = platform.request("cpu_reset_n")

        self.comb += self.cd_sys.clk.eq(clk)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~rst_n)

        platform.add_period_constraint(clk, 1e9/25e6)

# Design -------------------------------------------------------------------------------------------

class Tuto(Module):
    def __init__(self, platform):

        crg = CRG(platform)
        self.submodules += crg

        led = platform.request("user_led", 1)
        blink = Blink(24)
        self.submodules += blink
        self.comb += led.eq(blink.out)

        data = platform.request("do")
        ring = RingSerialCtrl()
        self.submodules += ring
        self.comb += data.eq(ring.do)

# Blinker -------------------------------------------------------------------------------------------

class Blink(Module):
    def __init__(self, bit):
        self.out = Signal()

        ###

        counter = Signal(25)
        self.comb += self.out.eq(counter[bit])
        self.sync += counter.eq(counter + 1)

# RingSerialCtrl -------------------------------------------------------------------------------------------

class RingSerialCtrl(Module):
    def __init__(self):
        self.do = Signal()

        ###

        pulse_cnt  = Signal(max=24)
        high       = Signal(1, reset=1)
        t_high_cnt = Signal(max=80)
        t_low_cnt  = Signal(max=160)

        self.sync += [
            If(pulse_cnt < 24,
                If(high,
                    self.do.eq(1),
                    t_high_cnt.eq(t_high_cnt + 1),
                    If(t_high_cnt == 80,
                        t_high_cnt.eq(0),
                        high.eq(0),
                    )
                ).Else(
                    self.do.eq(0),
                    t_low_cnt.eq(t_low_cnt + 1),
                    If(t_low_cnt == 160,
                        t_low_cnt.eq(0),
                        high.eq(1),
                        pulse_cnt.eq(pulse_cnt + 1),
                    ),
                )
            )
        ]

# Test -------------------------------------------------------------------------------------------

def test():
    loop = 0
    while (loop < 10000):
        yield
        loop = loop + 1

# Build --------------------------------------------------------------------------------------------

def main():

    build_dir= 'gateware'

    platform = Platform(toolchain="trellis")

    from litex.build.generic_platform import Pins, IOStandard
    platform.add_extension([("do", 0, Pins("M2"), IOStandard("LVCMOS33"))])
    
    design = Tuto(platform)
    platform.build(design, build_dir=build_dir)

    if "load" in sys.argv[1: ]:
        prog = platform.create_programmer()
        prog.load_bitstream(build_dir + "/top.bit")
        exit()

    if "sim" in sys.argv[1: ]:
        ring = RingSerialCtrl()
        run_simulation(ring, test(), clocks={"sys": 1e9/25e6}, vcd_name="sim.vcd")
        exit()

    

if __name__ == "__main__":
    main()
