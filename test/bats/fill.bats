#!/usr/bin/env bats
@test "fill_it_up" {
    rm -rf test/.cache.tmp
    mkdir -p test/.cache.tmp/.stagecache.global
    echo "cache_size: 12000" > test/.cache.tmp/.stagecache.global/config

    run ./stagecache.py -t 0:00:03 -c test/.cache.tmp stagecache.py
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/.stagecache.stagecache.py/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/stagecache.py ]

    ./stagecache.py -c test/.cache.tmp jme/stagecache/config.py
    run ./stagecache.py -c test/.cache.tmp jme/stagecache/config.py
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/jme/stagecache/.stagecache.config.py/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/jme/stagecache/config.py ]

    sleep 3
    run ./stagecache.py -c test/.cache.tmp jme/stagecache/main.py
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/jme/stagecache/.stagecache.main.py/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/jme/stagecache/main.py ]
    [ ! -e test/.cache.tmp$(realpath $(pwd))/stagecache.py ]

    run ./stagecache.py -c test/.cache.tmp jme/stagecache/text_metadata.py
    [ "$status" -gt 0 ]
}

@test "print cache state" {
    run ./stagecache.py -c test/.cache.tmp
    [ "$status" -eq 0 ]
    run ./stagecache.py -c test/.cache.tmp --json
    [ "$status" -eq 0 ]
    run ./stagecache.py -c test/.cache.tmp --yaml
    [ "$status" -eq 0 ]
}
