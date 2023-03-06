import textwrap
import os

write = "Write [hello world]"
paint = "paint"
erase = "erase"
quit = "quit"

ret_list = [write, paint, erase, quit]

for ret in ret_list:
    cmd = ret.lower().split(" ")[0]
    print(cmd)

    if cmd == "write":
        kw_start_idx = ret.find("[") + 1
        kw_end_idx = ret.find("]")
        kw = ret.lower()[kw_start_idx : kw_end_idx]
        print(kw)
