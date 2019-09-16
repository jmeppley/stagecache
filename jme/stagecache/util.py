from numpy import log, power, abs
LN_BASE = log(power(1024, 1/3))
def human_readable_bytes(x): 
    """ fixed version of https://stackoverflow.com/a/17754143/663466
     hybrid of https://stackoverflow.com/a/10171475/2595465 
      with https://stackoverflow.com/a/5414105/2595465  """
	# return bytes if small 
    if x <= 99: return str(int(x)) 
    magnitude = int(log(abs(x)) / LN_BASE)
    if magnitude > 19: 
        float_fmt = '%i' 
        illion = 20 // 3  
    else: 
        mag3 = (magnitude+1) % 3 
        float_fmt = '%' + str(mag3) + "." + str(3-mag3) + 'f' 
        illion = (magnitude + 1) // 3 
    format_str = float_fmt + ['', 'K', 'M', 'G', 'T', 'P', 'E'][illion] 
    return (format_str % (x * 1.0 / (1024 ** illion))).lstrip('0') 
