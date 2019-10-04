#!/usr/bin/env bats
@test "does it compile and run" {
    run ./stage_cache --foobar
    [ "$status" -gt 0 ]
    run ./stage_cache -h
    [ "$status" -eq 0 ]
    ./stage_cache --version
    run ./stage_cache --version
    [ "$status" -eq 0 ]
    [ "$output" = "0.0.3" ]
}

@test "staging" {
    rm -rf test/.cache.tmp

    run ./stage_cache -c test/.cache.tmp stage_cache
    [ "$status" -eq 0 ]
    run ./stage_cache -c test/.cache.tmp stage_cache
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/.stagecache.stage_cache/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/stage_cache ]
    

    
}

