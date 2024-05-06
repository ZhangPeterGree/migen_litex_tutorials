#!/usr/bin/env python

import argparse
from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litex_boards.platforms import muselab_icesugar_pro
from ring import *

# CRG ------------clock request generate------------------------------------------------------------


class CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.rst = Signal()
        self.clock_domains.cd_sys = ClockDomain()
        
        # # #

        clk = platform.request("clk25")
        rst_n = platform.request("cpu_reset_n")

        self.comb += self.cd_sys.clk.eq(clk)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~rst_n)

        platform.add_period_constraint(clk, 1e9/25e6)

# BaseSoC ---------------------------------------------------------------------


class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(25e6), mode=mode.SINGLE, **kwargs):

        platform = muselab_icesugar_pro.Platform(toolchain="trellis")

        from litex.build.generic_platform import Pins, IOStandard
        # platform.add_extension([("do", 0, Pins("P11"), IOStandard("LVCMOS33"))])
        platform.add_extension(
            [("do", 0, Pins("P11"), IOStandard("LVCMOS33"))])

        SoCCore.__init__(self, platform, sys_clk_freq,
                         ident="Muselab IceSugar Pro device LFE5U-25F-6BG256C",
                         **kwargs
                         )

        self.submodules.crg = CRG(platform, sys_clk_freq)
        # self.add_uart(name="uart", uart_name="serial", baudrate=115200)

        led = RingControl(platform.request("do"), mode, 12, sys_clk_freq)
        self.submodules.ledring = led
        self.add_csr("ledring")


# Build -----------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="LiteX SoC on LFE5U-25F-6BG256C")

    parser.add_argument("--build",       action="store_true",
                        help="Build bitstream")
    parser.add_argument("--mode-single", action="store_true",
                        help="Build bitstream")
    parser.add_argument("--load",        action="store_true",
                        help="Load bitstream")
    parser.add_argument("--flash",       action="store_true",
                        help="Flash Bitstream")

    builder_args(parser)

    soc_core_args(parser)

    args = parser.parse_args()

    m = mode.DOUBLE
    if args.mode_single:
        m = mode.SINGLE

    soc = BaseSoC(
        sys_clk_freq=25e6,
        mode=m,
        **soc_core_argdict(args)
    )

    builder = Builder(soc, **builder_argdict(args))

    builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        print(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))
        prog.load_bitstream(os.path.join(
            builder.gateware_dir, soc.build_name + ".bit"))
        exit()


if __name__ == "__main__":
    main()
