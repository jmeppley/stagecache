#!/usr/bin/env bats
@test "does it compile and run" {
    run ./stagecache --foobar
    [ "$status" -gt 0 ]
    run ./stagecache -h
    [ "$status" -eq 0 ]
    ./stagecache --version
    run ./stagecache --version
    [ "$status" -eq 0 ]
    [ "$output" = "0.0.5" ]
}

@test "staging" {
    rm -rf test/.cache.tmp

    run ./stagecache -c test/.cache.tmp stagecache
    [ "$status" -eq 0 ]
    run ./stagecache -c test/.cache.tmp stagecache
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/.stagecache.stagecache/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/stagecache ]
    

    
}

