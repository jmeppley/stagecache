#!/usr/bin/env bats
@test "fill_it_up" {
    rm -rf test/.cache.tmp
    mkdir -p test/.cache.tmp/.stagecache.global

    # get size of three files:
    BD=test/bats
    F1=$BD/stage.bats
    F2=$BD/fill.bats
    F3=$BD/nose.bats
    SZF1=$(du -b $F1 | cut -f 1)
    SZF2=$(du -b $F2 | cut -f 1)
    SZF3=$(du -b $F3 | cut -f 1)

    # make cache too small to fit all three
    let CSZ=SZF1+SZF2+SZF3/2
    echo "cache_size: $CSZ" > test/.cache.tmp/.stagecache.global/config

    run ./stagecache -t 0:00:03 -c test/.cache.tmp $F1
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$BD/.stagecache.$(basename $F1)/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$F1 ]

    run ./stagecache -c test/.cache.tmp $F2
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$BD/.stagecache.$(basename $F2)/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$F2 ]

    # the third file won't fit
    run ./stagecache -c test/.cache.tmp $F3
    [ "$status" -gt 0 ]

    # wait for lock on first file to expire
    sleep 3
    # try again
    run ./stagecache -c test/.cache.tmp $F3
    [ "$status" -eq 0 ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$BD/.stagecache.$(basename $F3)/size ]
    [ -e test/.cache.tmp$(realpath $(pwd))/$F3 ]
    [ ! -e test/.cache.tmp$(realpath $(pwd))/$F1 ]

}
