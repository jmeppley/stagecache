#!/usr/bin/env bats
@test "fill_it_up" {
    rm -rf test/.cache.tmp
    mkdir -p test/.cache.tmp/.stagecache.global
    echo "cache_size: 12000" > test/.cache.tmp/.stagecache.global/config

    run ./stage_cache -t 0:00:03 -c test/.cache.tmp stage_cache
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/.stagecache.stage_cache/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/stage_cache ]

    ./stage_cache -c test/.cache.tmp stagecache/config.py
    run ./stage_cache -c test/.cache.tmp stagecache/config.py
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/stagecache/.stagecache.config.py/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/stagecache/config.py ]

    sleep 3
    run ./stage_cache -c test/.cache.tmp stagecache/main.py
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/stagecache/.stagecache.main.py/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/stagecache/main.py ]
    [ ! -e test/.cache.tmp$(realpath $(pwd))/stage_cache ]

    run ./stage_cache -c test/.cache.tmp stagecache/text_metadata.py
    [ "$status" -gt 0 ]
}

@test "print cache state" {
    run ./stage_cache -c test/.cache.tmp
    [ "$status" -eq 0 ]
    run ./stage_cache -c test/.cache.tmp --json
    [ "$status" -eq 0 ]
    run ./stage_cache -c test/.cache.tmp --yaml
    [ "$status" -eq 0 ]
}
