#!/usr/bin/env bats
@test "does it compile and run" {
    run ./stagecache.py --foobar
    [ "$status" -gt 0 ]
    run ./stagecache.py -h
    [ "$status" -eq 0 ]
    ./stagecache.py --version
    run ./stagecache.py --version
    [ "$status" -eq 0 ]
    [ "$output" = "0.0.3" ]
}

@test "staging" {
    rm -rf test/.cache.tmp

    run ./stagecache.py -c test/.cache.tmp stagecache.py
    [ "$status" -eq 0 ]
    run ./stagecache.py -c test/.cache.tmp stagecache.py
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/.stagecache.stagecache.py/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/stagecache.py ]
    

    
}

