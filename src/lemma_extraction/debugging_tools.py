from sys import stdout

ESC_SEQ = "\033["
charc = 90  # charcoal
purp = 35  # purple
green = 32  # green -- might be just my eyes, but green(32) and yellow(33) look almost identical
dull_cyan = 36  # dull-cyan
bright_purp = 95  # bright-purple
bright_red = 91  # bright-red
RESET = ESC_SEQ + "0m"
formatted_red = f"{ESC_SEQ}1;{bright_red}m"
formatted_green = f"{ESC_SEQ}1;{green}m"
target_match = formatted_green
non_target_match = f"{ESC_SEQ}1;{dull_cyan}m"

allow_debugging = False # True
dbg_id_to_look_for = r"e03b018e3df65eb5dde6fafcec5447c10e120f5d298f82959a402235"
dbg_active_id = ""


def dbg_structure(root,msg, level=0, include_default=False):
    """A handy debugging aid"""
    tab = ' ' * (level * 4)
    ret = []
    # if fp==out_fd:
    #     color_format = target_match if root is msg else non_target_match
    #     reset = RESET
    # else:
    #     color_format = "* " if root is msg else ""
    #     reset = " *" if color_format else ""
    ret.append({"str":f"{tab} {{color_format}}{root.get_content_type()}{{suffix}}","suffix":(f' [{root.get_default_type()}]{{reset}}' if include_default else "{reset}"),"is_target":root is msg})
    if root.is_multipart():
        for subpart in root.get_payload():
            ret.extend(dbg_structure(subpart,msg, level+1, include_default))
    return ret


def dbg_capture_msg_structures(msg,sample_body0,file_descriptors:list=None):
    fp = file_descriptors if file_descriptors is not None else []
    result = dbg_structure(msg, sample_body0)
    print_out = [stdout] if fp is None else [stdout, *fp]
    intro = f"\n\n{'':=<120}\nSubject: '{msg.get('Subject', 'subject is None')}'\n{{encoding}}\n{'':=<120}"
    for fd in print_out:
        print(intro.format(encoding=fd.encoding), file=fd)
    for d in result:
        s = d.pop("str")
        is_target = d.pop("is_target")
        suffix = d.pop("suffix")
        for out in print_out:
            if out.encoding.lower() == "utf-8":
                color_format = target_match if is_target else non_target_match
                reset = RESET
            else:
                color_format = "* " if is_target else ""
                reset = " *" if is_target else ""
            print(s.format(color_format=color_format, suffix=suffix.format(reset=reset)), file=out)
    for fd in print_out:
        print(file=fd)

