#!/usr/bin/env bats
@test "does it compile and run" {
    run ./stagecache --foobar
    [ "$status" -gt 0 ]
    run ./stagecache -h
    [ "$status" -eq 0 ]
    ./stagecache --version
    run ./stagecache --version
    [ "$status" -eq 0 ]
    [ "$output" = "0.1.3" ]
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

@test "release lock on error" {
    rm -rf test/.cache.tmp

    run ./stagecache -c test/.cache.tmp nonexistent.file
    [ "$status" -gt 0 ]

    # the second run will hang if the lock wasn't released properly
    run ./stagecache -c test/.cache.tmp nonexistent.file
    [ "$status" -gt 0 ]
}

@test "print cache state" {
    run ./stagecache -c test/.cache.tmp
    [ "$status" -eq 0 ]
    run ./stagecache -c test/.cache.tmp --json
    [ "$status" -eq 0 ]
    run ./stagecache -c test/.cache.tmp --yaml
    [ "$status" -eq 0 ]
}
