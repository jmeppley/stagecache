from jme import stagecache

def test_time_parse():
    assert stagecache.parse_slurm_time('1-0:00') == 24*60*60
    assert stagecache.parse_slurm_time('10-3:00:15') == \
            10*24*60*60 + 3*60*60 + 15
    assert stagecache.parse_slurm_time('0:23') == 23*60
    assert stagecache.parse_slurm_time('1:23') == 83*60
    assert stagecache.parse_slurm_time('0:00:23') == 23
    assert stagecache.parse_slurm_time('0:01:23') == 83
    assert stagecache.parse_slurm_time('0123') == 123
