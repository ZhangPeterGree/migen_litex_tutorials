#!/usr/bin/env python

import argparse

from migen import *
from migen.genlib.cdc import *
from migen.genlib.cdc import MultiReg

from litex.build.generic_platform import *
from litex_boards.platforms import muselab_icesugar_pro

def delay(self, delay, input, output):
    r = Signal(delay)
    for i in range(delay):
        if i == 0:
            self.sync += r[0].eq(input)
        else:
            self.sync += r[i].eq(r[i-1])

    self.comb += output.eq(r[delay-1])

class Compute(Module):
    def __init__(self, pipeline):
        self.out          = Signal(4)
        self.out_valid    = Signal()
        self.input1       = Signal(4)
        self.input1_valid = Signal()
        self.input2       = Signal(4)
        self.input2_valid = Signal()

        ###

        a = Signal(32)
        b = Signal(32)

        a1 = Signal(32)
        a2 = Signal(32)
        a3 = Signal(32)
        a4 = Signal(32)
        a5 = Signal(32)

        a11 = Signal(32)
        a12 = Signal(32)
        a13 = Signal(32)

        a111 = Signal(32)
        a112 = Signal(32)

        if pipeline == False:

            self.comb += a.eq((self.input1 * 0x99887733) +                 # a1--+---a11----+-----a111------+--- b
                              (self.input1 * 0x11223344) +                 # a2--+          |               |
                                                                           #                |               |
                              (self.input1 * 0x55667788) +                 # a3--+---a12----+               |
                              (self.input2 * Replicate(self.input1, 8)) +  # a4--+                          |
                                                                           #                                |
                              (self.input1 * 0x99aabbcc) +                 # a5--+---a13----------a112------+
                              0x12345678)                                  # ----+

            self.sync += b.eq(a)
            self.comb += self.out.eq(b[0:4] ^ b[4:8] ^ b[8:12] ^ b[12:16] ^ b[16:20] ^ b[20:24] ^ b[24:28] ^ b[28:32])

            delay(self, 1, self.input1_valid & self.input2_valid, self.out_valid)

        else:

            self.sync += [
                a1.eq(self.input1 * 0x99887733),
                a2.eq(self.input1 * 0x11223344),
                a3.eq(self.input1 * 0x55667788),
                a4.eq(self.input2 * Replicate(self.input1, 8)),
                a5.eq(self.input1 * 0x99aabbcc),

                a11.eq(a1 + a2),
                a12.eq(a3 + a4),
                a13.eq(a5 + 0x12345678),

                a111.eq(a11 + a12),
                a112.eq(a13),

                b.eq(a111 + a112),
            ]

            self.comb += self.out.eq(b[0:4] ^ b[4:8] ^ b[8:12] ^ b[12:16] ^ b[16:20] ^ b[20:24] ^ b[24:28] ^ b[28:32]),

            delay(self, 4, self.input1_valid & self.input2_valid, self.out_valid)

# Design -------------------------------------------------------------------------------------------

class TestPipeline(Module):
    def __init__(self, platform, pipeline):

        # Get pin from ressources
        clk = platform.request("clk25")
        leds = platform.request_all("user_led")

        btn = platform.request_all("user_btn")
        btn_sync = Signal(len(btn))
        for i in range(len(btn)):
            self.specials += MultiReg(btn[i], btn_sync[i])


        sw = platform.request_all("user_sw")
        sw_sync = Signal(len(sw))
        for i in range(len(sw)):
            self.specials += MultiReg(sw[i], sw_sync[i])

        # Creates a "sys" clock domain and generates a startup reset
        # Clock Reset Generator (CRG)
        crg = CRG(clk)
        self.submodules.crg = crg

        # Instance of Blink
        cnt = Signal(32)
        compute = Compute(pipeline)
        self.submodules += compute
        self.sync += cnt.eq(cnt + 1)
        self.comb += [
            compute.input1.eq(cnt),
            compute.input2.eq(btn_sync),
            compute.input1_valid.eq(1),
            compute.input2_valid.eq(1),
            leds.eq(compute.out)
        ]

# Test -------------------------------------------------------------------------------------------

def test(dut):
    loop = 0
    yield dut.input1_valid.eq(1)
    yield dut.input2_valid.eq(1)
    yield dut.input1.eq(5)
    yield dut.input2.eq(6)
    yield

    yield dut.input1.eq(8)
    yield dut.input2.eq(8)
    yield

    yield dut.input1.eq(9)
    yield dut.input2.eq(4)
    yield

    yield dut.input1_valid.eq(0)
    yield dut.input2_valid.eq(0)
    yield dut.input1.eq(0)
    yield dut.input2.eq(0)

    for i in range(20):
        yield

# Build -------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="The Muselab IceSugar Pro PCB and IOs have been documented by @wuxx")
    
    parser.add_argument("--build", action="store_true", help="Build bitstream")
    parser.add_argument("--sim",  action="store_true", help="Build bitstream")
    parser.add_argument("--load",  action="store_true", help="Load bitstream")
    

    args = parser.parse_args()
    
    pipeline = False
    # if args.pipe:
    #     pipeline = True

    build_dir="gateware"
    # Instance of our platform (which is in platform_arty_a7.py)
    platform = muselab_icesugar_pro.Platform(toolchain="trellis")
    design = TestPipeline(platform, pipeline)
    
    if args.build:
        prog = platform.build(design, build_dir=build_dir)
        
    if args.sim:
        pipeline = True
        dut = Compute(pipeline)
        run_simulation(dut, test(dut), clocks={"sys": 1e9/25e6}, vcd_name="sim.vcd")
        exit()

    if args.load:
        # prog.load_bitstream("gateware" + "/top.bit")
        # exit()
        prog = platform.create_programmer()
        prog.load_bitstream(build_dir.get_bitstream_filename("top.bit"))
        exit()

if __name__ == "__main__":
    main()
