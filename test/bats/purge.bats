#!/usr/bin/env bats
@test "purge file" {
    rm -rf test/.cache.tmp
    BD=test/bats
    F1=$BD/stage.bats
    F2=$BD/fill.bats
    CACHE=test/.cache.tmp

    run ./stagecache -t 0:00:03 -c $CACHE $F1
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$BD/.stagecache.$(basename $F1)/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$F1 ]

    run ./stagecache --purge -c $CACHE $F1
    [ "$status" -ne 0 ]
    run ./stagecache -t -1 -c $CACHE $F1
    [ "$status" -ne 0 ]

    run ./stagecache --purge --force -t -1 -c $CACHE $F1
    [ "$status" -eq 0 ]
    [ ! -e test/.cache.tmp$(realpath $(pwd))/$F1 ]
}

@test "purge" {
    rm -rf test/.cache.tmp
    BD=test/bats
    F1=$BD/stage.bats
    F2=$BD/fill.bats
    CACHE=test/.cache.tmp

    run ./stagecache -t 0:00:03 -c $CACHE $F1
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$BD/.stagecache.$(basename $F1)/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$F1 ]

    run ./stagecache -t 0:00:03 -c $CACHE $F2
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$BD/.stagecache.$(basename $F2)/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$F2 ]

    run ./stagecache --purge -c $CACHE
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$F1 ]
 
    sleep 3
    run ./stagecache --purge -c $CACHE
    [ "$status" -eq 0 ]
    [ ! -e test/.cache.tmp$(realpath $(pwd))/$F1 ]
}
